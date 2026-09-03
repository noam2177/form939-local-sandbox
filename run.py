"""Exp03 weekend benchmark: incremental CSV checkpoint per file+model, optional infinite loop."""
from __future__ import annotations

import argparse
import asyncio
import logging
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))

from dotenv import load_dotenv
from router import CloudModelRouter

LOCAL_MODELS = ["ollama/qwen2.5:7b", "ollama/llama3.1"]  # glm4 not pulled; add when available
INPUT_DIR = Path("data/synthetic_inputs")
LOG_DIR = Path("logs")


async def _run_iteration(models: list[str], inputs: dict[str, str], timeout_s: float) -> None:
    """Task A: one model per extract() call so each success appends to CSV immediately."""
    for filename, text in inputs.items():
        for model in models:
            try:
                router = CloudModelRouter(models=[model], max_concurrency=1, timeout_s=timeout_s)
                await router.extract(filename, text, persist=True)
            except Exception:
                logging.exception("Skipped %s on %s", model, filename)


async def weekend_run(*, loops: int, sleep_s: int, models: list[str], timeout_s: float) -> None:
    load_dotenv()
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        handlers=[
            logging.FileHandler(LOG_DIR / "weekend_run.log", encoding="utf-8"),
            logging.StreamHandler(sys.stdout),
        ],
    )
    if not INPUT_DIR.exists():
        logging.error("Missing input dir: %s", INPUT_DIR)
        return
    inputs = {f.stem: f.read_text(encoding="utf-8") for f in INPUT_DIR.glob("*.txt")}
    if not inputs:
        logging.error("No .txt files in %s", INPUT_DIR)
        return
    logging.info("Weekend run: %d files x %d models (incremental save ON)", len(inputs), len(models))
    iteration = 0
    while loops == 0 or iteration < loops:
        iteration += 1
        logging.info("=== Iteration %d ===", iteration)
        await _run_iteration(models, inputs, timeout_s)
        if loops and iteration >= loops:
            break
        logging.info("Sleeping %ds before next iteration...", sleep_s)
        await asyncio.sleep(sleep_s)


def main() -> None:
    parser = argparse.ArgumentParser(description="Form939 local model weekend stress test")
    parser.add_argument("--loops", type=int, default=0, help="Iterations (0 = run forever)")
    parser.add_argument("--sleep", type=int, default=300, help="Seconds between iterations")
    parser.add_argument("--timeout", type=float, default=400.0, help="Per-request timeout (seconds)")
    parser.add_argument(
        "--models",
        nargs="+",
        default=LOCAL_MODELS,
        help="Ollama models to benchmark (one at a time)",
    )
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
            )
        )
    except KeyboardInterrupt:
        print("\nStopped by user. Partial results are in logs/benchmark_results.csv")


if __name__ == "__main__":
    main()
