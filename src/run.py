from __future__ import annotations

import asyncio
import logging
import sys
import time
from pathlib import Path
import pandas as pd
from dotenv import load_dotenv
from tqdm.asyncio import tqdm

from router import CloudModelRouter
from ground_truth import load_ground_truth_outputs
from evaluate import score_extraction, write_scores
from compare import write_compare_report
from schemas import Form939Output

# Exp03 Config: Weekend Stress Test
LOCAL_MODELS = ["ollama/qwen2.5:7b", "ollama/llama3.1"] # Qwen is the leader, Llama is the runner up
INPUT_DIR = Path("data/synthetic_inputs")
GT_CSV = Path("data/gold/synthetic_ground_truth.csv")
LOG_DIR = Path("logs")

async def weekend_run():
    load_dotenv()
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        handlers=[
            logging.FileHandler(LOG_DIR / "weekend_run.log"),
            logging.StreamHandler(sys.stdout)
        ]
    )
    logger = logging.getLogger("WeekendExp03")
    
    if not INPUT_DIR.exists():
        logger.error(f"Input directory {INPUT_DIR} not found.")
        return

    # Load all inputs
    inputs = {f.stem: f.read_text(encoding="utf-8") for f in INPUT_DIR.glob("*.txt")}
    if not inputs:
        logger.error("No input files found.")
        return

    # Initialize Router with Concurrency=1 for local stability
    router = CloudModelRouter(
        models=LOCAL_MODELS,
        max_concurrency=1,
        timeout_s=400.0, # Extra breathing room for local CPU
    )

    logger.info(f"Starting Exp03: Weekend stress test on {len(inputs)} files with {LOCAL_MODELS}")
    
    # Task A: Incremental checkpointing is handled by router.extract(persist=True)
    # This loop ensures we process file by file and save immediately.
    pbar = tqdm(total=len(inputs), desc="Weekend Benchmark")
    
    for filename, text in inputs.items():
        try:
            # This call invokes all models for the file and appends to CSV immediately
            await router.extract(filename, text, persist=True)
            pbar.update(1)
        except Exception as e:
            logger.error(f"Critical failure on file {filename}: {e}")
            # Continue to next file - bulletproof execution
            continue
            
    pbar.close()
    logger.info("Weekend run iteration complete. Results saved incrementally.")

if __name__ == "__main__":
    if sys.platform.startswith("win"):
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    try:
        asyncio.run(weekend_run())
    except KeyboardInterrupt:
        print("\nStopped by user.")
