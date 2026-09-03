import pandas as pd
from pathlib import Path
import sys

def main():
    csv_path = Path("logs/benchmark_results.csv")
    if not csv_path.exists():
        print(f"Error: {csv_path} not found.")
        sys.exit(1)
        
    df = pd.read_csv(csv_path)
    
    # Filter by the latest run_id if it exists
    if 'run_id' in df.columns:
        latest_run = df['run_id'].max()
        print(f"--- Benchmark Analysis (Latest Run: {latest_run}) ---")
        df = df[df['run_id'] == latest_run]
    else:
        print("--- Benchmark Analysis (All Data) ---")
        
    print(f"{'Model':<25} | {'Success %':<10} | {'Avg Latency (s)':<15} | {'Luhn Error %':<12} | {'Cloud Esc %':<10}")
    print("-" * 70)
    
    for model in df['model'].unique():
        m_df = df[df['model'] == model]
        
        success_pct = (m_df['success'].sum() / len(m_df)) * 100
        avg_latency_s = m_df['latency_ms'].mean() / 1000
        
        # Count Luhn errors: where principal.value or attorney_in_fact.value is missing
        luhn_errors = m_df['principal.value'].isna().sum() + m_df['attorney_in_fact.value'].isna().sum()
        total_id_fields = len(m_df) * 2
        luhn_error_pct = (luhn_errors / total_id_fields) * 100
        esc_pct = (m_df["flag_cloud_escalation"].sum() / len(m_df)) * 100 if "flag_cloud_escalation" in m_df.columns else 0.0
        
        print(f"{model:<25} | {success_pct:>8.1f}% | {avg_latency_s:>13.2f}s | {luhn_error_pct:>11.1f}% | {esc_pct:>8.1f}%")

if __name__ == "__main__":
    main()
