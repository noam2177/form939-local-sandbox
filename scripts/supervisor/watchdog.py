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
    HEARTBEAT_PATH,
    LOG_DIR,
    PROJECT_ROOT,
    STATE_PATH,
    SUMMARY_PATH,
    SUPERVISOR_LOG,
    SupervisorConfig,
)
from health import run_health_suite

logger = logging.getLogger(__name__)


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
    """Watches Ollama, restarts benchmark on stall/crash, publishes between iterations."""

    def __init__(self, config: SupervisorConfig) -> None:
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
            "last_csv_rows": 0,
            "last_progress_utc": _utc_now(),
            "restarts": 0,
            "status": "initializing",
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
        return [
            sys.executable,
            str(PROJECT_ROOT / "run.py"),
            "--loops",
            str(self.config.loops_per_child),
            "--sleep",
            str(self.config.sleep_between_loops_s),
            "--timeout",
            str(self.config.request_timeout_s),
            *["--models", *self.config.models],
        ]

    def _start_benchmark(self) -> None:
        if self._process and self._process.poll() is None:
            logger.warning("Benchmark already running (pid=%s)", self._process.pid)
            return
        cmd = self._benchmark_cmd()
        logger.info("Starting benchmark child: %s", " ".join(cmd))
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

    def _run_post_iteration_tasks(self) -> None:
        logger.info("Running post-iteration tasks (publish + analyze)")
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
        summary = analyze.stdout or analyze.stderr or "(no output)"
        SUMMARY_PATH.write_text(f"# Weekend summary @ {_utc_now()}\n\n{summary}\n", encoding="utf-8")
        logger.info("Summary saved to %s", SUMMARY_PATH)

    def _on_iteration_complete(self) -> None:
        self._state["iterations_completed"] = int(self._state.get("iterations_completed", 0)) + 1
        self._state["status"] = "iteration_complete"
        self._state["last_iteration_utc"] = _utc_now()
        self._save_state()
        self._run_post_iteration_tasks()

    def _check_progress(self) -> bool:
        """Return True if CSV row count increased since last check."""
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
        target = self.config.target_iterations
        if target <= 0:
            return False
        return int(self._state.get("iterations_completed", 0)) >= target

    def run(self) -> int:
        self._setup_logging()
        self._state["status"] = "supervisor_running"
        self._save_state()
        logger.info(
            "Supervisor started | models=%s | target_iterations=%s | stall_timeout=%ds",
            self.config.models,
            self.config.target_iterations or "infinite",
            self.config.stall_timeout_s,
        )

        try:
            while True:
                health = run_health_suite()
                ollama_ok, ollama_msg = health["ollama"]
                disk_ok, disk_msg = health["disk"]
                dirs_ok, dirs_msg = health["directories"]
                self._write_heartbeat(
                    f"iter={self._state.get('iterations_completed', 0)} "
                    f"| ollama={'OK' if ollama_ok else 'DOWN'} "
                    f"| csv_rows={self._state.get('last_csv_rows', 0)} "
                    f"| restarts={self._state.get('restarts', 0)}"
                )
                logger.info("Health: %s | %s | %s", ollama_msg, disk_msg, dirs_msg)

                if not dirs_ok or not disk_ok:
                    logger.error("Fatal environment issue — supervisor pausing 60s")
                    time.sleep(60)
                    continue

                if not ollama_ok:
                    self._state["status"] = "waiting_for_ollama"
                    self._save_state()
                    logger.warning("%s — retry in %ds", ollama_msg, self.config.ollama_retry_s)
                    time.sleep(self.config.ollama_retry_s)
                    continue

                if self._target_reached():
                    logger.info("Target iterations reached (%s). Supervisor done.", self.config.target_iterations)
                    self._state["status"] = "completed"
                    self._save_state()
                    self._run_post_iteration_tasks()
                    return 0

                child_alive = self._process is not None and self._process.poll() is None
                if not child_alive:
                    self._drain_child_output()
                    if self._process and self._process.poll() is not None:
                        rc = self._process.returncode
                        logger.info("Benchmark child exited (code=%s)", rc)
                        if rc == 0:
                            self._on_iteration_complete()
                    self._start_benchmark()
                else:
                    progressed = self._check_progress()
                    stall_s = self._seconds_since_progress()
                    if not progressed and stall_s > self.config.stall_timeout_s:
                        self._stop_benchmark(reason=f"stalled {stall_s:.0f}s without CSV growth")
                        continue

                time.sleep(self.config.health_interval_s)

        except KeyboardInterrupt:
            logger.info("Supervisor stopped by user")
            self._stop_benchmark(reason="keyboard interrupt")
            self._state["status"] = "stopped"
            self._save_state()
            return 0
