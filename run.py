"""Exp03 weekend benchmark: incremental CSV checkpoint per file+model, resume support."""
from __future__ import annotations

import argparse
import asyncio
import json
import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))

from dotenv import load_dotenv
from router import CloudModelRouter

LOCAL_MODELS = ["ollama/qwen2.5:7b", "ollama/llama3.1"]
INPUT_DIR = Path("data/synthetic_inputs")
LOG_DIR = Path("logs")
CHECKPOINT_PATH = LOG_DIR / "run_checkpoint.json"


def _load_checkpoint() -> set[tuple[str, str]]:
    if not CHECKPOINT_PATH.is_file():
        return set()
    try:
        data = json.loads(CHECKPOINT_PATH.read_text(encoding="utf-8"))
        return {tuple(pair) for pair in data.get("done", [])}
    except (json.JSONDecodeError, OSError, TypeError):
        return set()


def _save_checkpoint(done: set[tuple[str, str]], pass_num: int) -> None:
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    CHECKPOINT_PATH.write_text(
        json.dumps({"pass": pass_num, "done": [list(p) for p in sorted(done)]}, indent=2),
        encoding="utf-8",
    )


def _clear_checkpoint() -> None:
    if CHECKPOINT_PATH.is_file():
        CHECKPOINT_PATH.unlink(missing_ok=True)


async def _run_iteration(
    models: list[str],
    inputs: dict[str, str],
    timeout_s: float,
    *,
    pass_num: int,
    resume: bool,
) -> None:
    done = _load_checkpoint() if resume else set()
    if not resume:
        _clear_checkpoint()
    total = len(inputs) * len(models)
    logging.info("Pass %d: %d file×model pairs (%d already done)", pass_num, total, len(done))
    for filename, text in inputs.items():
        for model in models:
            key = (filename, model)
            if key in done:
                logging.info("Resume skip: %s on %s", model, filename)
                continue
            try:
                router = CloudModelRouter(models=[model], max_concurrency=1, timeout_s=timeout_s)
                await router.extract(filename, text, persist=True)
                done.add(key)
                _save_checkpoint(done, pass_num)
            except Exception:
                logging.exception("Skipped %s on %s", model, filename)
    _clear_checkpoint()
    logging.info("Pass %d iteration finished (%d/%d pairs)", pass_num, len(done), total)


async def weekend_run(
    *,
    loops: int,
    sleep_s: int,
    models: list[str],
    timeout_s: float,
    pass_num: int,
    resume: bool,
) -> None:
    load_dotenv()
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        handlers=[
            logging.FileHandler(LOG_DIR / "weekend_run.log", encoding="utf-8"),
            logging.StreamHandler(sys.stdout),
        ],
        force=True,
    )
    if not INPUT_DIR.exists():
        logging.error("Missing input dir: %s", INPUT_DIR)
        return
    inputs = {f.stem: f.read_text(encoding="utf-8") for f in sorted(INPUT_DIR.glob("*.txt"))}
    if not inputs:
        logging.error("No .txt files in %s", INPUT_DIR)
        return
    logging.info("Weekend run: %d files x %d models (incremental save ON)", len(inputs), len(models))
    iteration = 0
    while loops == 0 or iteration < loops:
        iteration += 1
        logging.info("=== Iteration %d ===", iteration)
        await _run_iteration(models, inputs, timeout_s, pass_num=pass_num, resume=resume and iteration == 1)
        if loops and iteration >= loops:
            break
        logging.info("Sleeping %ds before next iteration...", sleep_s)
        await asyncio.sleep(sleep_s)


def main() -> int:
    parser = argparse.ArgumentParser(description="Form939 local model weekend stress test")
    parser.add_argument("--loops", type=int, default=0, help="Iterations (0 = run forever)")
    parser.add_argument("--sleep", type=int, default=300, help="Seconds between iterations")
    parser.add_argument("--timeout", type=float, default=400.0, help="Per-request timeout (seconds)")
    parser.add_argument("--pass-num", type=int, default=1, help="Supervisor pass number (for checkpoint)")
    parser.add_argument("--resume", action="store_true", help="Resume from run_checkpoint.json")
    parser.add_argument("--models", nargs="+", default=LOCAL_MODELS, help="Ollama models")
    args = parser.parse_args()
    if sys.platform.startswith("win"):
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    try:
        asyncio.run(
            weekend_run(
                loops=args.loops,
                sleep_s=args.sleep,
                models=args.models,
                timeout_s=args.timeout,
                pass_num=args.pass_num,
                resume=args.resume,
            )
        )
    except KeyboardInterrupt:
        print("\nStopped by user. Partial results are in logs/benchmark_results.csv")
        return 130
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
