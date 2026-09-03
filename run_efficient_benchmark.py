import asyncio
import argparse
import logging
import sys
from pathlib import Path
import pandas as pd
from dotenv import load_dotenv

from compare import write_compare_report
from evaluate import score_extraction, write_scores
from ground_truth import DEFAULT_SYNTHETIC_GT, load_ground_truth_outputs
from router import CloudModelRouter, DEFAULT_RESULTS_PATH
from schemas import Form939Output
from dashboard import generate_dashboard

LOCAL_MODELS = ["ollama/gemma4:e4b", "ollama/llama3.1", "ollama/qwen2.5:7b"]

async def main():
    load_dotenv()
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
    Path("logs").mkdir(parents=True, exist_ok=True)

    input_path = Path("data/synthetic_inputs")
    inputs = {}
    for txt_file in input_path.glob("*.txt"):
        inputs[txt_file.stem] = txt_file.read_text(encoding="utf-8")
        
    print(f"Processing {len(inputs)} files efficiently by grouping by model to prevent VRAM thrashing...")

    all_frames = []
    
    # Process one model at a time completely
    for model in LOCAL_MODELS:
        print(f"\n--- Starting benchmark for {model} ---")
        router = CloudModelRouter(
            models=[model],
            timeout_s=300.0,
            max_retries=2,
            temperature=0.0,
            max_concurrency=1,
        )
        
        for filename, text in inputs.items():
            frame = await router.extract(filename, text, persist=False)
            all_frames.append(frame)
            
    final_frame = pd.concat(all_frames, ignore_index=True) if all_frames else pd.DataFrame()

    if not final_frame.empty:
        # Write to CSV
        router = CloudModelRouter(models=["dummy"])
        router._write_csv(final_frame)
        
    print("\n--- Scoring ---")
    gold_by_stem = load_ground_truth_outputs(Path("data/gold/synthetic_ground_truth.csv"))
    
    scores_list = []
    records_by_stem_by_model = {m: {} for m in LOCAL_MODELS}
    
    for _, row in final_frame.iterrows():
        model = row["model"]
        filename = row["Filename"]
        parsed_raw = row.get("parsed_output")
        if not parsed_raw or pd.isna(parsed_raw):
            record = Form939Output()
        else:
            payload = json.loads(parsed_raw) if isinstance(parsed_raw, str) else parsed_raw
            record = Form939Output.model_validate(payload)
            
        records_by_stem_by_model[model][filename] = record
        
        gold = gold_by_stem.get(filename) or Form939Output()
        score = score_extraction(record, gold)
        scores_list.append({
            "model": model,
            "Filename": filename,
            "success": row["success"],
            "exact_record": score["exact_record"],
            "id_number_ok": score["id_number_ok"],
            "principal_value_ok": score["principal_value_ok"],
            "attorney_in_fact_value_ok": score["attorney_in_fact_value_ok"],
            "field_accuracy": score["field_accuracy"],
            "required_accuracy": score["required_accuracy"],
        })
        
    scores_path = Path("logs") / "eval_scores.csv"
    write_scores(pd.DataFrame(scores_list), scores_path)
    
    for model in LOCAL_MODELS:
        write_compare_report(
            records_by_stem_by_model[model],
            gold_by_stem,
            Path("logs") / "compare_report.csv",
            model=model,
        )
        
    print("\n--- Generating Dashboard ---")
    generate_dashboard(Path("logs/eval_scores.csv"), Path("logs/benchmark_results.csv"))
    print("Done!")

if __name__ == "__main__":
    import json
    if sys.platform.startswith("win"):
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(main())
