from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path
from typing import Sequence

try:
    from .schemas import Form939Output, clean_field_value, normalize_valid_israeli_id
except ImportError:
    from schemas import Form939Output, clean_field_value, normalize_valid_israeli_id

FORM_939_COMPARE_FIELDS = (
    "principal.value",
    "principal.is_handwritten",
    "attorney_in_fact.value",
    "attorney_in_fact.is_handwritten",
)

ID_VALUE_COLUMNS = ("principal.value", "attorney_in_fact.value")
BOOL_COLUMNS = ("principal.is_handwritten", "attorney_in_fact.is_handwritten")

DEFAULT_SYNTHETIC_GT = Path(__file__).resolve().parent.parent / "data" / "gold" / "ground_truth_939.csv"


@dataclass(frozen=True)
class GroundTruthRow:
    stem: str
    fields: dict[str, str]

    def to_output(self) -> Form939Output:
        return row_to_output(self)


def coerce_id_column(raw: str | None) -> str:
    """Keep IDs as digit strings. 8-digit values are left-padded; never a float."""
    digits = clean_field_value(raw) or ""
    if not digits:
        return ""
    if len(digits) == 8:
        padded = f"0{digits}"
        return padded
    return digits


def _coerce_bool_column(raw: str | None) -> str:
    text = (raw or "").strip().lower()
    if text in {"1", "true", "yes", "y"}:
        return "true"
    if text in {"0", "false", "no", "n", ""}:
        return "false"
    return text


def load_ground_truth_csv(
    csv_path: Path | str | None = None,
    field_columns: Sequence[str] = FORM_939_COMPARE_FIELDS,
) -> list[GroundTruthRow]:
    path = Path(csv_path) if csv_path is not None else DEFAULT_SYNTHETIC_GT
    if not path.is_file():
        raise FileNotFoundError(f"Ground truth not found: {path}")

    with path.open(newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames is None or "Filename" not in reader.fieldnames:
            raise ValueError(f"{path} must have a 'Filename' column.")
        rows: list[GroundTruthRow] = []
        for record in reader:
            stem = (record.get("Filename") or "").strip()
            if not stem:
                continue
            fields: dict[str, str] = {}
            for column in field_columns:
                raw = record.get(column) or ""
                if column in ID_VALUE_COLUMNS:
                    fields[column] = coerce_id_column(raw)
                elif column in BOOL_COLUMNS:
                    fields[column] = _coerce_bool_column(raw)
                else:
                    fields[column] = str(raw).strip()
            rows.append(GroundTruthRow(stem=stem, fields=fields))
        return rows


def row_to_output(row: GroundTruthRow) -> Form939Output:
    def _leaf(value_key: str, hand_key: str) -> dict[str, object] | None:
        value = row.fields.get(value_key, "")
        if not value:
            return None
        normalized = normalize_valid_israeli_id(value) or value
        return {
            "value": normalized,
            "is_handwritten": row.fields.get(hand_key, "false") == "true",
            "_type": "text",
            "_low_OCR_score": False,
        }

    return Form939Output.model_validate(
        {
            "principal": _leaf("principal.value", "principal.is_handwritten"),
            "attorney_in_fact": _leaf("attorney_in_fact.value", "attorney_in_fact.is_handwritten"),
        }
    )


def load_ground_truth_outputs(
    csv_path: Path | str | None = None,
) -> dict[str, Form939Output]:
    return {row.stem: row.to_output() for row in load_ground_truth_csv(csv_path)}
