from __future__ import annotations

import argparse
import asyncio
import json
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

LOCAL_MODELS: list[str] = ["ollama/gemma4:e4b", "ollama/llama3.1", "ollama/qwen2.5:7b"]

GOLD_FORM939 = {
    "principal": {
        "value": "516190899",
        "is_handwritten": False,
        "_type": "text",
        "_low_OCR_score": False,
    },
    "attorney_in_fact": {
        "value": "024481863",
        "is_handwritten": True,
        "_type": "text",
        "_low_OCR_score": False,
    },
}

MESSY_HEBREW_FORM939 = """
=== SCAN / OCR DUMP — טופס 939 ייפוי כוח (איכות ירודה) ===
<RTL>  מדינת ישראל  |  רשות האוכלוסין

נותן ההרשאה / מייפה כוח / PRINCIPAL / giving_permission:
  ת.ז:  \u200e5-1 6 1 9 0 8 9 9\u200f
  id_value_left: 516190899
  מודפס (לא בכתב יד)

מקבל ההרשאה / מיופה כוח / ATTORNEY IN FACT / get_permission:
  ת.ז (8 ספרות, חסרה אפס משמאל): 24481863
  id_value_down: 24481863
  בכתב יד / handwritten = TRUE

אין לחלץ שמות, תאריכים או כתובות. רק מספרי זהות.
=== END OCR ===
"""

def _record_from_row(row: pd.Series) -> Form939Output:
    parsed_raw = row.get("parsed_output")
    if not parsed_raw or (isinstance(parsed_raw, float) and pd.isna(parsed_raw)):
        return Form939Output()
    payload = json.loads(parsed_raw) if isinstance(parsed_raw, str) else parsed_raw
    return Form939Output.model_validate(payload)

async def main() -> None:
    load_dotenv()
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )
    Path("logs").mkdir(parents=True, exist_ok=True)

    parser = argparse.ArgumentParser(description="Form 939 IDP Batch Evaluation")
    parser.add_argument("--models", nargs="+", default=LOCAL_MODELS, help="List of models to evaluate (space separated)")
    parser.add_argument("--input-dir", type=str, help="Directory containing .txt files to process")
    parser.add_argument("--gt-csv", type=str, default=str(DEFAULT_SYNTHETIC_GT), help="Path to ground truth CSV")
    args = parser.parse_args()

    models = args.models
    router = CloudModelRouter(
        models=models,
        timeout_s=300.0,
        max_retries=2,
        temperature=0.0,
        max_concurrency=1,
    )

    inputs: dict[str, str] = {}
    if args.input_dir:
        input_path = Path(args.input_dir)
        if input_path.is_dir():
            for txt_file in input_path.glob("*.txt"):
                inputs[txt_file.stem] = txt_file.read_text(encoding="utf-8")
        else:
            logging.error(f"Input directory not found: {args.input_dir}")
            sys.exit(1)
    else:
        # Fallback to hardcoded sample for quick testing
        inputs["two_role_ids_luhn"] = MESSY_HEBREW_FORM939

    if not inputs:
        logging.error("No input texts found.")
        sys.exit(1)

    print(f"Processing {len(inputs)} files with models: {models}")
    
    async def process_file(filename: str, text: str) -> pd.DataFrame:
        return await router.extract(filename, text, persist=False)

    tasks = [process_file(filename, text) for filename, text in inputs.items()]
    all_frames = await asyncio.gather(*tasks)

    final_frame = pd.concat(all_frames, ignore_index=True) if all_frames else pd.DataFrame()

    # Save the full batch to benchmark_results.csv at once to avoid dropped records
    if not final_frame.empty:
        router._write_csv(final_frame)

    pd.set_option("display.max_columns", None)
    pd.set_option("display.width", 200)
    pd.set_option("display.max_colwidth", 120)
    print("\n--- Extraction Results ---")
    print(final_frame.to_string(index=False))

    gold_by_stem = load_ground_truth_outputs(Path(args.gt_csv))
    if "two_role_ids_luhn" not in gold_by_stem:
        gold_by_stem["two_role_ids_luhn"] = Form939Output.model_validate(GOLD_FORM939)

    for model in models:
        model_frame = final_frame[final_frame["model"] == model]
        if model_frame.empty:
            continue
            
        records_by_stem = {}
        scores_list = []
        for _, row in model_frame.iterrows():
            filename = row["Filename"]
            record = _record_from_row(row)
            records_by_stem[filename] = record
            
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

        compare_path = write_compare_report(
            records_by_stem,
            gold_by_stem,
            Path("logs") / "compare_report.csv",
            model=model,
        )
        
        scores_path = Path("logs") / "eval_scores.csv"
        write_scores(pd.DataFrame(scores_list), scores_path)

    print(f"\nCSV: {DEFAULT_RESULTS_PATH}")
    print(f"SCORES: {Path('logs') / 'eval_scores.csv'}")
    print(f"COMPARE: {Path('logs') / 'compare_report.csv'}")

if __name__ == "__main__":
    if sys.platform.startswith("win"):
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(main())
