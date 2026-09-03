from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pandas as pd

try:
    from .schemas import Form939Output
except ImportError:
    from schemas import Form939Output

LEAF_FIELDS = (
    "principal.value",
    "principal.is_handwritten",
    "attorney_in_fact.value",
    "attorney_in_fact.is_handwritten",
)

VALUE_FIELDS = ("principal.value", "attorney_in_fact.value")


def _leaf_str(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, bool):
        return "true" if value else "false"
    return str(value).strip()


def _get_path(payload: dict[str, Any], path: str) -> Any:
    current: Any = payload
    for part in path.split("."):
        if not isinstance(current, dict):
            return None
        current = current.get(part)
    return current


def flatten_record(record: Form939Output | dict[str, Any]) -> dict[str, str]:
    payload = record.model_dump_utf8() if isinstance(record, Form939Output) else record
    return {field: _leaf_str(_get_path(payload, field)) for field in LEAF_FIELDS}


def score_extraction(
    predicted: Form939Output | dict[str, Any],
    gold: Form939Output | dict[str, Any],
) -> dict[str, Any]:
    """Exact match on production compare fields (values + handwriting flags)."""
    pred_flat = flatten_record(predicted)
    gold_flat = flatten_record(gold)
    field_hits = {field: pred_flat[field] == gold_flat[field] for field in LEAF_FIELDS}
    matched = sum(1 for hit in field_hits.values() if hit)
    value_hits = sum(1 for field in VALUE_FIELDS if field_hits[field])
    return {
        "field_hits": field_hits,
        "matched_fields": matched,
        "total_fields": len(LEAF_FIELDS),
        "field_accuracy": matched / len(LEAF_FIELDS),
        "required_accuracy": value_hits / len(VALUE_FIELDS),
        "exact_record": all(field_hits.values()),
        "principal_value_ok": field_hits["principal.value"],
        "attorney_in_fact_value_ok": field_hits["attorney_in_fact.value"],
        "id_number_ok": value_hits == len(VALUE_FIELDS),
    }


def score_frame(
    frame: pd.DataFrame,
    gold: Form939Output | dict[str, Any],
) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    gold_payload = gold.model_dump_utf8() if isinstance(gold, Form939Output) else gold
    empty_score = {
        "field_hits": {field: False for field in LEAF_FIELDS},
        "matched_fields": 0,
        "total_fields": len(LEAF_FIELDS),
        "field_accuracy": 0.0,
        "required_accuracy": 0.0,
        "exact_record": False,
        "principal_value_ok": False,
        "attorney_in_fact_value_ok": False,
        "id_number_ok": False,
    }
    for _, row in frame.iterrows():
        parsed_raw = row.get("parsed_output")
        success = bool(row.get("success"))
        predicted: dict[str, Any] | None = None
        error = None
        if success and isinstance(parsed_raw, str) and parsed_raw.strip():
            try:
                predicted = json.loads(parsed_raw)
            except json.JSONDecodeError as exc:
                error = str(exc)
                success = False
        score = score_extraction(predicted, gold_payload) if predicted is not None else empty_score
        rows.append(
            {
                "model": row.get("model"),
                "success": success,
                "latency_ms": row.get("latency_ms"),
                "cost_usd": row.get("cost_usd"),
                "exact_record": score["exact_record"],
                "id_number_ok": score["id_number_ok"],
                "principal_value_ok": score["principal_value_ok"],
                "attorney_in_fact_value_ok": score["attorney_in_fact_value_ok"],
                "field_accuracy": score["field_accuracy"],
                "required_accuracy": score["required_accuracy"],
                "error": error or row.get("error"),
            }
        )
    return pd.DataFrame(rows)


def write_scores(frame: pd.DataFrame, path: str | Path) -> Path:
    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    write_header = not destination.exists() or destination.stat().st_size == 0
    frame.to_csv(
        destination,
        mode="a",
        header=write_header,
        index=False,
        encoding="utf-8-sig",
    )
    return destination
