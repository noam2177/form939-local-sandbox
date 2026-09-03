"""Fault-tolerant discovery and PII-safe loading of benchmark artifacts."""
from __future__ import annotations

import csv
import json
import logging
from collections import defaultdict
from pathlib import Path
from typing import Any

from domain_models import BenchmarkMetricRow

logger = logging.getLogger(__name__)

# Keys that indicate PII-bearing payloads — never ingest.
_PII_RISK_KEYS = frozenset(
    {
        "principal",
        "attorney_in_fact",
        "parsed_output",
        "samples",
        "document",
        "gold",
        "predicted",
        "value",
        "Filename",
        "filename",
    }
)

_BENCH_SAFE_COLS = frozenset({"model", "success", "latency_ms", "cost_usd", "run_id"})
_EVAL_SAFE_COLS = frozenset({"model", "field_accuracy", "exact_record", "required_accuracy"})


def _json_has_pii_risk(payload: Any) -> bool:
    if isinstance(payload, dict):
        if _PII_RISK_KEYS.intersection(payload.keys()):
            return True
        return any(_json_has_pii_risk(v) for v in payload.values())
    if isinstance(payload, list):
        return any(_json_has_pii_risk(item) for item in payload)
    return False


def _coerce_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in {"1", "true", "yes", "y"}


def _load_json_file(path: Path) -> dict[str, Any] | None:
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError, UnicodeDecodeError) as exc:
        logger.warning("Skipping corrupted JSON %s: %s", path.name, exc)
        return None
    if not isinstance(raw, dict):
        logger.warning("Skipping non-object JSON %s", path.name)
        return None
    if _json_has_pii_risk(raw):
        logger.warning("Skipping PII-risk JSON %s", path.name)
        return None
    return raw


def _read_csv_rows(path: Path) -> list[dict[str, str]]:
    try:
        with path.open(encoding="utf-8-sig", newline="") as handle:
            return list(csv.DictReader(handle))
    except OSError as exc:
        logger.warning("Skipping unreadable CSV %s: %s", path.name, exc)
        return []


def _aggregate_benchmark_csv(rows: list[dict[str, str]]) -> dict[str, dict[str, float | int]]:
    buckets: dict[str, dict[str, float | int]] = defaultdict(
        lambda: {"calls": 0, "successes": 0, "latency_sum_ms": 0.0, "cost_sum": 0.0}
    )
    for row in rows:
        model = (row.get("model") or "").strip()
        if not model:
            continue
        bucket = buckets[model]
        bucket["calls"] = int(bucket["calls"]) + 1
        if _coerce_bool(row.get("success")):
            bucket["successes"] = int(bucket["successes"]) + 1
        try:
            bucket["latency_sum_ms"] = float(bucket["latency_sum_ms"]) + float(row.get("latency_ms") or 0)
        except (TypeError, ValueError):
            pass
        try:
            bucket["cost_sum"] = float(bucket["cost_sum"]) + float(row.get("cost_usd") or 0)
        except (TypeError, ValueError):
            pass
    return buckets


def _accuracy_from_eval(rows: list[dict[str, str]]) -> dict[str, float]:
    scores: dict[str, list[float]] = defaultdict(list)
    for row in rows:
        model = (row.get("model") or "").strip()
        if not model:
            continue
        for col in ("field_accuracy", "required_accuracy", "exact_record"):
            raw = row.get(col)
            if raw in (None, ""):
                continue
            try:
                val = float(raw)
                scores[model].append(val * 100 if val <= 1.0 else val)
                break
            except (TypeError, ValueError):
                continue
    return {model: sum(vals) / len(vals) for model, vals in scores.items() if vals}


def _row_from_aggregate(
    model: str,
    agg: dict[str, float | int],
    accuracy_pct: float | None,
) -> BenchmarkMetricRow | None:
    calls = int(agg["calls"])
    if calls == 0:
        return None
    successes = int(agg["successes"])
    latency_s = float(agg["latency_sum_ms"]) / calls / 1000.0
    total_cost = float(agg["cost_sum"])
    acc = accuracy_pct if accuracy_pct is not None else (successes / calls * 100.0)
    cpve = total_cost / max(successes, 1)
    return BenchmarkMetricRow.model_validate(
        {
            "model": model,
            "resolution": f"{calls} calls",
            "Accuracy (%)": round(acc, 2),
            "Latency (s)": round(latency_s, 3),
            "Total Cost ($)": round(total_cost, 6),
            "Calls": calls,
            "CPVE": round(cpve, 6),
        }
    )


class FileRepository:
    """Loads publisher-safe metrics from JSON summaries and/or benchmark CSVs."""

    def __init__(self, input_dir: Path) -> None:
        self.input_dir = input_dir

    def discover_json_paths(self) -> list[Path]:
        if not self.input_dir.is_dir():
            return []
        paths: list[Path] = []
        for path in sorted(self.input_dir.rglob("*.json")):
            lowered = str(path).lower()
            if any(token in lowered for token in ("gold", "samples", "node_modules", "venv")):
                continue
            paths.append(path)
        return paths

    def discover_csv_paths(self) -> list[Path]:
        if not self.input_dir.is_dir():
            return []
        names = ("benchmark_results_clean.csv", "benchmark_results.csv")
        found: list[Path] = []
        for name in names:
            candidate = self.input_dir / name
            if candidate.is_file():
                found.append(candidate)
                break
        eval_csv = self.input_dir / "eval_scores.csv"
        return found

    def load_json_metrics(self) -> list[BenchmarkMetricRow]:
        rows: list[BenchmarkMetricRow] = []
        for path in self.discover_json_paths():
            raw = _load_json_file(path)
            if raw is None:
                continue
            try:
                rows.append(BenchmarkMetricRow.model_validate(raw))
            except Exception as exc:
                logger.warning("Skipping invalid publisher JSON %s: %s", path.name, exc)
        return rows

    def load_csv_metrics(self) -> list[BenchmarkMetricRow]:
        bench_paths = self.discover_csv_paths()
        if not bench_paths:
            return []
        bench_rows = _read_csv_rows(bench_paths[0])
        safe_bench = [{k: v for k, v in row.items() if k in _BENCH_SAFE_COLS} for row in bench_rows]
        aggregates = _aggregate_benchmark_csv(safe_bench)

        eval_path = self.input_dir / "eval_scores.csv"
        accuracy_map: dict[str, float] = {}
        if eval_path.is_file():
            eval_rows = _read_csv_rows(eval_path)
            safe_eval = [{k: v for k, v in row.items() if k in _EVAL_SAFE_COLS} for row in eval_rows]
            accuracy_map = _accuracy_from_eval(safe_eval)

        rows: list[BenchmarkMetricRow] = []
        for model, agg in sorted(aggregates.items()):
            row = _row_from_aggregate(model, agg, accuracy_map.get(model))
            if row:
                rows.append(row)
        return rows

    def load_all(self) -> list[BenchmarkMetricRow]:
        """Prefer explicit JSON publisher files; fall back to CSV aggregation."""
        json_rows = self.load_json_metrics()
        if json_rows:
            return json_rows
        return self.load_csv_metrics()
