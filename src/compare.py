from __future__ import annotations

import csv
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Mapping

try:
    from .evaluate import flatten_record
    from .ground_truth import FORM_939_COMPARE_FIELDS, GroundTruthRow
    from .schemas import Form939Output
except ImportError:
    from evaluate import flatten_record
    from ground_truth import FORM_939_COMPARE_FIELDS, GroundTruthRow
    from schemas import Form939Output

DEFAULT_COMPARE_REPORT = Path(__file__).resolve().parent.parent / "logs" / "compare_report.csv"

REPORT_FIELDNAMES = (
    "row_type",
    "Filename",
    "model",
    "field",
    "predicted",
    "gold",
    "match",
    "timestamp_utc",
)

SUMMARY_FILENAME = "_SUMMARY"
DETAIL_ROW = "detail"
SUMMARY_ROW = "summary"

GoldLike = Form939Output | dict[str, Any] | GroundTruthRow


def _as_output(gold: GoldLike) -> Form939Output:
    if isinstance(gold, Form939Output):
        return gold
    if isinstance(gold, GroundTruthRow):
        return gold.to_output()
    return Form939Output.model_validate(gold)


def _as_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in {"true", "1", "yes"}


def _is_summary_row(row: Mapping[str, Any]) -> bool:
    return row.get("row_type") == SUMMARY_ROW or row.get("Filename") == SUMMARY_FILENAME


def compare_records(
    filename: str,
    predicted: Form939Output | dict[str, Any],
    gold: GoldLike,
    *,
    model: str | None = None,
    timestamp_utc: str | None = None,
) -> list[dict[str, Any]]:
    pred_flat = flatten_record(
        predicted if isinstance(predicted, Form939Output) else Form939Output.model_validate(predicted)
    )
    gold_flat = flatten_record(_as_output(gold))
    stamped = timestamp_utc or datetime.now(timezone.utc).isoformat()
    rows: list[dict[str, Any]] = []
    for field in FORM_939_COMPARE_FIELDS:
        rows.append(
            {
                "row_type": DETAIL_ROW,
                "Filename": filename,
                "model": model or "",
                "field": field,
                "predicted": pred_flat[field],
                "gold": gold_flat[field],
                "match": pred_flat[field] == gold_flat[field],
                "timestamp_utc": stamped,
            }
        )
    return rows


def summarize_compare_rows(rows: Iterable[dict[str, Any]]) -> dict[str, dict[str, int]]:
    summary = {field: {"success": 0, "fail": 0} for field in FORM_939_COMPARE_FIELDS}
    for row in rows:
        if _is_summary_row(row):
            continue
        field = row.get("field")
        if field not in summary:
            continue
        if _as_bool(row.get("match")):
            summary[field]["success"] += 1
        else:
            summary[field]["fail"] += 1
    return summary


def _read_existing_details(path: Path) -> list[dict[str, str]]:
    if not path.exists() or path.stat().st_size == 0:
        return []
    with path.open(newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        return [row for row in reader if not _is_summary_row(row)]


def _normalize_detail(row: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "row_type": DETAIL_ROW,
        "Filename": row.get("Filename") or "",
        "model": row.get("model") or "",
        "field": row.get("field") or "",
        "predicted": "" if row.get("predicted") is None else str(row.get("predicted")),
        "gold": "" if row.get("gold") is None else str(row.get("gold")),
        "match": _as_bool(row.get("match")),
        "timestamp_utc": row.get("timestamp_utc") or "",
    }


def build_summary_rows(details: Iterable[dict[str, Any]]) -> list[dict[str, Any]]:
    """Per-model, per-field success/fail counts (form_939_test.py style)."""
    counts: dict[str, dict[str, dict[str, int]]] = defaultdict(
        lambda: {field: {"success": 0, "fail": 0} for field in FORM_939_COMPARE_FIELDS}
    )
    for row in details:
        if _is_summary_row(row):
            continue
        field = row.get("field")
        if field not in FORM_939_COMPARE_FIELDS:
            continue
        model = row.get("model") or ""
        if _as_bool(row.get("match")):
            counts[model][field]["success"] += 1
        else:
            counts[model][field]["fail"] += 1

    stamped = datetime.now(timezone.utc).isoformat()
    summaries: list[dict[str, Any]] = []
    for model in sorted(counts):
        for field in FORM_939_COMPARE_FIELDS:
            success = counts[model][field]["success"]
            fail = counts[model][field]["fail"]
            summaries.append(
                {
                    "row_type": SUMMARY_ROW,
                    "Filename": SUMMARY_FILENAME,
                    "model": model,
                    "field": field,
                    "predicted": success,
                    "gold": fail,
                    "match": fail == 0 and success > 0,
                    "timestamp_utc": stamped,
                }
            )
    return summaries


def write_compare_report(
    predictions: Mapping[str, Form939Output | dict[str, Any]],
    gold: Mapping[str, GoldLike],
    path: str | Path | None = None,
    *,
    model: str | None = None,
) -> Path:
    destination = Path(path) if path is not None else DEFAULT_COMPARE_REPORT
    destination.parent.mkdir(parents=True, exist_ok=True)

    stamped = datetime.now(timezone.utc).isoformat()
    incoming: list[dict[str, Any]] = []
    for filename, predicted in predictions.items():
        if filename not in gold:
            continue
        incoming.extend(
            compare_records(
                filename,
                predicted,
                gold[filename],
                model=model,
                timestamp_utc=stamped,
            )
        )

    details = [_normalize_detail(row) for row in _read_existing_details(destination)]
    details.extend(_normalize_detail(row) for row in incoming)
    details.sort(key=lambda row: (row["model"], row["Filename"], row["field"], row["timestamp_utc"]))
    summaries = build_summary_rows(details)

    with destination.open("w", newline="", encoding="utf-8-sig") as handle:
        writer = csv.DictWriter(handle, fieldnames=REPORT_FIELDNAMES)
        writer.writeheader()
        writer.writerows(details)
        writer.writerows(summaries)

    return destination
