import pandas as pd
from pathlib import Path

def test_generate_dashboard(tmp_path):
    from dashboard import generate_dashboard
    
    eval_csv = tmp_path / "eval_scores.csv"
    bench_csv = tmp_path / "benchmark_results.csv"
    
    eval_df = pd.DataFrame([
        {"model": "ollama/gemma4:e4b", "Filename": "f1", "success": True, "exact_record": True, "id_number_ok": True},
        {"model": "ollama/gemma4:e4b", "Filename": "f2", "success": True, "exact_record": False, "id_number_ok": True},
    ])
    eval_df.to_csv(eval_csv, index=False)
    
    bench_df = pd.DataFrame([
        {"model": "ollama/gemma4:e4b", "Filename": "f1", "latency_ms": 1500, "cost_usd": 0.01, "completion_tokens": 100},
        {"model": "ollama/gemma4:e4b", "Filename": "f2", "latency_ms": 2500, "cost_usd": 0.02, "completion_tokens": 150},
    ])
    bench_df.to_csv(bench_csv, index=False)
    
    md = generate_dashboard(eval_csv, bench_csv)
    
    assert "Form 939 IDP Benchmark Dashboard" in md
    assert "ollama/gemma4:e4b" in md
    assert "2" in md  # files processed
    assert "50.0%" in md  # exact match
    assert "100.0%" in md  # id ok
    assert "2.00s" in md  # avg latency
    assert "$0.0300" in md  # total cost
