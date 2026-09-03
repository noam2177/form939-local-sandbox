"""Autonomous weekend watchdog — supervises Ollama + benchmark loop."""
from __future__ import annotations

import json
import logging
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

from config import (
    CSV_PATH,
    CHECKPOINT_PATH,
    HEARTBEAT_PATH,
    LOG_DIR,
    PROJECT_ROOT,
    STATE_PATH,
    SUMMARY_PATH,
    SUPERVISOR_LOG,
    DEFAULT_TARGET_ITERATIONS,
    models_for_pass,
    SupervisorConfig,
)
from health import check_ollama, run_health_suite

logger = logging.getLogger(__name__)

WEEKEND_PASSES = DEFAULT_TARGET_ITERATIONS  # strict: exactly 3


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _count_csv_rows(path: Path) -> int:
    if not path.is_file():
        return 0
    try:
        with path.open(encoding="utf-8-sig") as handle:
            return max(sum(1 for _ in handle) - 1, 0)
    except OSError:
        return 0


class WeekendSupervisor:
    """Watches Ollama, runs exactly N passes, rests between them, exits with one report."""

    def __init__(self, config: SupervisorConfig) -> None:
        if config.target_iterations != WEEKEND_PASSES:
            raise ValueError(
                f"Weekend supervisor requires exactly {WEEKEND_PASSES} passes "
                f"(got {config.target_iterations}). Use --target-iterations {WEEKEND_PASSES}."
            )
        self.config = config
        self._process: subprocess.Popen[str] | None = None
        self._state = self._load_state()

    def _load_state(self) -> dict:
        if STATE_PATH.is_file():
            try:
                return json.loads(STATE_PATH.read_text(encoding="utf-8"))
            except (json.JSONDecodeError, OSError):
                pass
        return {
            "started_utc": _utc_now(),
            "iterations_completed": 0,
            "last_csv_rows": _count_csv_rows(CSV_PATH),
            "last_progress_utc": _utc_now(),
            "restarts": 0,
            "status": "initializing",
            "target_passes": WEEKEND_PASSES,
        }

    def _save_state(self) -> None:
        LOG_DIR.mkdir(parents=True, exist_ok=True)
        STATE_PATH.write_text(json.dumps(self._state, indent=2), encoding="utf-8")

    def _write_heartbeat(self, message: str) -> None:
        LOG_DIR.mkdir(parents=True, exist_ok=True)
        HEARTBEAT_PATH.write_text(f"{_utc_now()} | {message}\n", encoding="utf-8")

    def _setup_logging(self) -> None:
        LOG_DIR.mkdir(parents=True, exist_ok=True)
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
            handlers=[
                logging.FileHandler(SUPERVISOR_LOG, encoding="utf-8"),
                logging.StreamHandler(sys.stdout),
            ],
            force=True,
        )

    def _benchmark_cmd(self) -> list[str]:
        pass_num = int(self._state.get("iterations_completed", 0)) + 1
        models = models_for_pass(pass_num)
        resume = CHECKPOINT_PATH.is_file()
        cmd = [
            sys.executable,
            str(PROJECT_ROOT / "run.py"),
            "--loops",
            "1",
            "--sleep",
            "0",
            "--timeout",
            str(self.config.request_timeout_s),
            "--pass-num",
            str(pass_num),
            *["--models", *models],
        ]
        if resume:
            cmd.append("--resume")
        return cmd

    def _start_benchmark(self) -> None:
        if self._target_reached():
            return
        if self._process and self._process.poll() is None:
            logger.warning("Benchmark already running (pid=%s)", self._process.pid)
            return
        pass_num = int(self._state.get("iterations_completed", 0)) + 1
        models = models_for_pass(pass_num)
        logger.info(
            "Starting pass %d/%d (%d models: %s)%s",
            pass_num,
            WEEKEND_PASSES,
            len(models),
            ", ".join(m.split("/")[-1] for m in models),
            " [resume]" if CHECKPOINT_PATH.is_file() else "",
        )
        cmd = self._benchmark_cmd()
        self._process = subprocess.Popen(
            cmd,
            cwd=PROJECT_ROOT,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
        self._state["status"] = "benchmark_running"
        self._state["child_pid"] = self._process.pid
        self._state["current_pass"] = pass_num
        self._state["last_child_start_utc"] = _utc_now()
        self._state["last_progress_utc"] = _utc_now()
        self._save_state()

    def _stop_benchmark(self, *, reason: str) -> None:
        if not self._process or self._process.poll() is not None:
            return
        logger.warning("Stopping benchmark child (pid=%s): %s", self._process.pid, reason)
        self._process.terminate()
        try:
            self._process.wait(timeout=30)
        except subprocess.TimeoutExpired:
            self._process.kill()
            self._process.wait(timeout=10)
        self._state["restarts"] = int(self._state.get("restarts", 0)) + 1
        self._save_state()
        time.sleep(self.config.restart_cooldown_s)

    def _drain_child_output(self) -> None:
        if not self._process or not self._process.stdout:
            return
        while True:
            line = self._process.stdout.readline()
            if not line:
                break
            logger.info("[benchmark] %s", line.rstrip())

    def _rest_between_passes(self) -> None:
        rest_s = self.config.pass_rest_s
        logger.info("Pass complete — resting %ds before next pass (Ollama cooldown)", rest_s)
        self._state["status"] = "resting"
        self._save_state()
        elapsed = 0
        while elapsed < rest_s:
            ok, msg = check_ollama()
            self._write_heartbeat(
                f"resting {elapsed}/{rest_s}s | pass={self._state.get('iterations_completed', 0)}/{WEEKEND_PASSES} "
                f"| ollama={'OK' if ok else 'DOWN'}"
            )
            if not ok:
                logger.warning("Ollama down during rest: %s", msg)
            time.sleep(min(30, rest_s - elapsed))
            elapsed += min(30, rest_s - elapsed)
        self._state["status"] = "supervisor_running"
        self._save_state()

    def _run_final_report(self) -> None:
        logger.info("Generating consolidated final report (pass %d/%d)", WEEKEND_PASSES, WEEKEND_PASSES)
        pub = subprocess.run(
            [
                sys.executable,
                str(PROJECT_ROOT / "scripts" / "publisher" / "cli.py"),
                "--input-dir",
                str(LOG_DIR),
                "--output-dir",
                str(LOG_DIR / "published"),
                "--write",
            ],
            cwd=PROJECT_ROOT,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
        if pub.returncode == 0:
            logger.info("Publisher OK")
        else:
            logger.warning("Publisher failed: %s", pub.stderr[-500:] if pub.stderr else pub.stdout)

        analyze = subprocess.run(
            [sys.executable, str(PROJECT_ROOT / "analyze_results.py")],
            cwd=PROJECT_ROOT,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
        header = (
            f"# Weekend Final Summary\n\n"
            f"- Completed: {_utc_now()}\n"
            f"- Passes: {WEEKEND_PASSES}/{WEEKEND_PASSES}\n"
            f"- Plan: pass1=all 3 models, pass2-3=qwen+llama (consistency)\n"
            f"- CSV rows (total): {self._state.get('last_csv_rows', 0)}\n"
            f"- Restarts: {self._state.get('restarts', 0)}\n\n"
        )
        body = analyze.stdout or analyze.stderr or "(no analyze output)"
        SUMMARY_PATH.write_text(header + body + "\n", encoding="utf-8")
        logger.info("Final summary saved to %s", SUMMARY_PATH)

    def _on_pass_complete(self) -> bool:
        """Record pass completion. Returns True if all passes are done."""
        self._state["iterations_completed"] = int(self._state.get("iterations_completed", 0)) + 1
        n = int(self._state["iterations_completed"])
        self._state["status"] = "pass_complete"
        self._state["last_iteration_utc"] = _utc_now()
        self._check_progress()
        self._save_state()
        logger.info("Pass %d/%d complete (%d CSV rows total)", n, WEEKEND_PASSES, self._state.get("last_csv_rows", 0))
        return n >= WEEKEND_PASSES

    def _check_progress(self) -> bool:
        rows = _count_csv_rows(CSV_PATH)
        prev = int(self._state.get("last_csv_rows", 0))
        if rows > prev:
            self._state["last_csv_rows"] = rows
            self._state["last_progress_utc"] = _utc_now()
            self._save_state()
            logger.info("Progress: CSV rows %d -> %d", prev, rows)
            return True
        return False

    def _seconds_since_progress(self) -> float:
        last = self._state.get("last_progress_utc")
        if not last:
            return 0.0
        try:
            dt = datetime.fromisoformat(last)
            return (datetime.now(timezone.utc) - dt).total_seconds()
        except ValueError:
            return 0.0

    def _target_reached(self) -> bool:
        return int(self._state.get("iterations_completed", 0)) >= WEEKEND_PASSES

    def _finish(self) -> int:
        self._state["status"] = "completed"
        self._state["completed_utc"] = _utc_now()
        self._save_state()
        self._run_final_report()
        logger.info("Weekend supervisor finished gracefully after %d passes.", WEEKEND_PASSES)
        return 0

    def run(self) -> int:
        self._setup_logging()
        self._state["status"] = "supervisor_running"
        self._save_state()
        logger.info(
            "Supervisor started | passes=%d (strict) | models=%s | rest=%ds | stall_timeout=%ds",
            WEEKEND_PASSES,
            self.config.models,
            self.config.pass_rest_s,
            self.config.stall_timeout_s,
        )

        if self._target_reached():
            logger.info("All %d passes already completed in prior run.", WEEKEND_PASSES)
            return self._finish()

        try:
            while not self._target_reached():
                health = run_health_suite()
                ollama_ok, ollama_msg = health["ollama"]
                disk_ok, disk_msg = health["disk"]
                dirs_ok, dirs_msg = health["directories"]
                self._write_heartbeat(
                    f"pass={self._state.get('iterations_completed', 0)}/{WEEKEND_PASSES} "
                    f"| ollama={'OK' if ollama_ok else 'DOWN'} "
                    f"| csv_rows={self._state.get('last_csv_rows', 0)} "
                    f"| restarts={self._state.get('restarts', 0)}"
                )
                logger.info("Health: %s | %s | %s", ollama_msg, disk_msg, dirs_msg)

                if not dirs_ok or not disk_ok:
                    logger.error("Fatal environment issue — pausing 60s")
                    time.sleep(60)
                    continue

                if not ollama_ok:
                    self._state["status"] = "waiting_for_ollama"
                    self._save_state()
                    logger.warning("%s — retry in %ds", ollama_msg, self.config.ollama_retry_s)
                    time.sleep(self.config.ollama_retry_s)
                    continue

                child_alive = self._process is not None and self._process.poll() is None
                if not child_alive:
                    self._drain_child_output()
                    if self._process and self._process.poll() is not None:
                        rc = self._process.returncode
                        self._process = None
                        logger.info("Benchmark child exited (code=%s)", rc)
                        if rc != 0:
                            logger.error("Pass failed (exit %s) — will retry same pass", rc)
                            time.sleep(self.config.restart_cooldown_s)
                            continue
                        if self._on_pass_complete():
                            break
                        self._rest_between_passes()
                    if not self._target_reached():
                        self._start_benchmark()
                else:
                    progressed = self._check_progress()
                    stall_s = self._seconds_since_progress()
                    if not progressed and stall_s > self.config.stall_timeout_s:
                        self._stop_benchmark(reason=f"stalled {stall_s:.0f}s without CSV growth")
                        continue

                time.sleep(self.config.health_interval_s)

            return self._finish()

        except KeyboardInterrupt:
            logger.info("Supervisor stopped by user")
            self._stop_benchmark(reason="keyboard interrupt")
            self._state["status"] = "stopped"
            self._save_state()
            return 1
