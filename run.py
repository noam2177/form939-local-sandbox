import asyncio, sys, logging
from pathlib import Path
from router import CloudModelRouter
from dotenv import load_dotenv

async def weekend_run():
    load_dotenv()
    inputs = {f.stem: f.read_text(encoding="utf-8") for f in Path("data/synthetic_inputs").glob("*.txt")}
    router = CloudModelRouter(models=["ollama/qwen2.5:7b", "ollama/llama3.1"], max_concurrency=1)
    print(f"Weekend Run: {len(inputs)} files. Incremental saving enabled.")
    for filename, text in inputs.items():
        try: await router.extract(filename, text, persist=True) # Task A: Incremental save
        except Exception as e: print(f"Skipped {filename}: {e}")

if __name__ == "__main__":
    if sys.platform.startswith("win"): asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(weekend_run())
