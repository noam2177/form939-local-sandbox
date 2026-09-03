from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

_PUBLISHER = Path(__file__).resolve().parents[1] / "scripts" / "publisher"
sys.path.insert(0, str(_PUBLISHER))

from domain_models import BenchmarkMetricRow  # noqa: E402
from file_repository import FileRepository  # noqa: E402
from orchestrator import BenchmarkPublisherOrchestrator  # noqa: E402
from writers import DryRunConsoleWriter, MarkdownWriter, TsvWriter  # noqa: E402


def test_benchmark_metric_row_drops_extra_fields() -> None:
    row = BenchmarkMetricRow.model_validate(
        {
            "model": "ollama/qwen2.5:7b",
            "resolution": "10 calls",
            "Accuracy (%)": 80.0,
            "Latency (s)": 12.5,
            "Total Cost ($)": 0.0,
            "Calls": 10,
            "CPVE": 0.0,
            "principal": {"value": "123456789"},
            "parsed_output": "should be ignored",
        }
    )
    assert row.model == "ollama/qwen2.5:7b"
    assert not hasattr(row, "principal")


def test_repository_skips_pii_json(tmp_path: Path) -> None:
    pii = {"model": "x", "samples": [{"gold": {"principal": {"value": "516190899"}}}]}
    (tmp_path / "bad.json").write_text(json.dumps(pii), encoding="utf-8")
    safe = {
        "model": "ollama/test",
        "resolution": "1 calls",
        "Accuracy (%)": 100.0,
        "Latency (s)": 1.0,
        "Total Cost ($)": 0.0,
        "Calls": 1,
        "CPVE": 0.0,
    }
    (tmp_path / "good.json").write_text(json.dumps(safe), encoding="utf-8")
    rows = FileRepository(tmp_path).load_json_metrics()
    assert len(rows) == 1
    assert rows[0].model == "ollama/test"


def test_repository_aggregates_csv_without_pii(tmp_path: Path) -> None:
    bench = (
        "model,success,latency_ms,cost_usd\n"
        "ollama/qwen2.5:7b,True,2000,0.0\n"
        "ollama/qwen2.5:7b,False,1000,0.0\n"
    )
    (tmp_path / "benchmark_results.csv").write_text(bench, encoding="utf-8")
    eval_csv = "model,field_accuracy\nollama/qwen2.5:7b,0.9\n"
    (tmp_path / "eval_scores.csv").write_text(eval_csv, encoding="utf-8")
    rows = FileRepository(tmp_path).load_csv_metrics()
    assert len(rows) == 1
    assert rows[0].calls == 2
    assert rows[0].accuracy_pct == 90.0
    assert rows[0].latency_s == 1.5


def test_dry_run_writes_nothing(tmp_path: Path) -> None:
    row = BenchmarkMetricRow.model_validate(
        {
            "model": "m",
            "resolution": "1 calls",
            "Accuracy (%)": 50.0,
            "Latency (s)": 1.0,
            "Total Cost ($)": 0.0,
            "Calls": 1,
            "CPVE": 0.0,
        }
    )
    out = tmp_path / "out"
    assert "DRY-RUN" in MarkdownWriter().write([row], out, dry_run=True)
    assert "DRY-RUN" in TsvWriter().write([row], out, dry_run=True)
    assert not out.exists()


def test_write_mode_creates_reports(tmp_path: Path) -> None:
    row = BenchmarkMetricRow.model_validate(
        {
            "model": "m",
            "resolution": "1 calls",
            "Accuracy (%)": 50.0,
            "Latency (s)": 1.0,
            "Total Cost ($)": 0.0,
            "Calls": 1,
            "CPVE": 0.0,
        }
    )
    out = tmp_path / "out"
    MarkdownWriter().write([row], out, dry_run=False)
    TsvWriter().write([row], out, dry_run=False)
    assert (out / "benchmark_report.md").is_file()
    assert (out / "benchmark_report.tsv").is_file()


def test_orchestrator_end_to_end(tmp_path: Path) -> None:
    bench = "model,success,latency_ms,cost_usd\nollama/a,True,1000,0.01\n"
    (tmp_path / "benchmark_results.csv").write_text(bench, encoding="utf-8")
    result = BenchmarkPublisherOrchestrator(FileRepository(tmp_path)).run(
        tmp_path / "published", dry_run=True
    )
    assert len(result.rows) == 1
    assert result.rows[0].total_cost_usd == 0.01
