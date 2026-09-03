import pandas as pd
from pathlib import Path

def generate_dashboard(eval_csv: Path, bench_csv: Path) -> str:
    if not eval_csv.exists() or not bench_csv.exists():
        return "No data available. Please run the benchmark first."

    eval_df = pd.read_csv(eval_csv)
    bench_df = pd.read_csv(bench_csv)

    # Calculate metrics per model
    models = eval_df["model"].unique()
    
    md = ["# Form 939 IDP Benchmark Dashboard\n"]
    md.append("| Model | Files Processed | Exact Match % | ID Numbers OK % | Avg Latency (s) | Tokens/Sec (TPS) | Total Cost ($) |")
    md.append("|---|---|---|---|---|---|---|")
    
    for model in models:
        m_eval = eval_df[eval_df["model"] == model]
        m_bench = bench_df[bench_df["model"] == model]
        
        files_processed = len(m_eval)
        
        exact_match_pct = (m_eval["exact_record"].sum() / files_processed) * 100 if files_processed else 0
        id_ok_pct = (m_eval["id_number_ok"].sum() / files_processed) * 100 if files_processed else 0
        
        avg_latency_ms = m_bench["latency_ms"].mean() if not m_bench.empty else 0
        avg_latency_s = avg_latency_ms / 1000
        
        tps = m_bench["completion_tokens"].sum() / (m_bench["latency_ms"].sum() / 1000) if not m_bench.empty and m_bench["latency_ms"].sum() > 0 else 0
        
        total_cost = m_bench["cost_usd"].sum() if not m_bench.empty else 0
        
        md.append(f"| {model} | {files_processed} | {exact_match_pct:.1f}% | {id_ok_pct:.1f}% | {avg_latency_s:.2f}s | {tps:.1f} | ${total_cost:.4f} |")
        
    return "\n".join(md)

if __name__ == "__main__":
    eval_csv = Path("logs/eval_scores.csv")
    bench_csv = Path("logs/benchmark_results.csv")
    
    dashboard_md = generate_dashboard(eval_csv, bench_csv)
    print(dashboard_md)
    
    Path("logs/dashboard.md").write_text(dashboard_md, encoding="utf-8")
    print("\nDashboard saved to logs/dashboard.md")
