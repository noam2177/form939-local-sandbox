from __future__ import annotations

from ground_truth import (
    DEFAULT_SYNTHETIC_GT,
    coerce_id_column,
    load_ground_truth_csv,
    load_ground_truth_outputs,
)


def test_coerce_id_column_never_float_and_pads_eight_digits() -> None:
    assert coerce_id_column("24481863") == "024481863"
    assert coerce_id_column("516190899") == "516190899"
    assert coerce_id_column("5-1 6 1 9 0 8 9 9") == "516190899"
    assert isinstance(coerce_id_column("24481863"), str)


def test_load_synthetic_gt_forces_nine_digit_strings() -> None:
    rows = load_ground_truth_csv(DEFAULT_SYNTHETIC_GT)
    assert {row.stem for row in rows} == {"two_role_ids_luhn", "eight_digit_pad"}
    by_stem = {row.stem: row for row in rows}
    eight = by_stem["eight_digit_pad"]
    assert eight.fields["attorney_in_fact.value"] == "024481863"
    assert eight.fields["attorney_in_fact.value"].isdigit()
    assert len(eight.fields["attorney_in_fact.value"]) == 9
    assert eight.fields["attorney_in_fact.is_handwritten"] == "true"


def test_load_ground_truth_outputs_validates_schema() -> None:
    outputs = load_ground_truth_outputs(DEFAULT_SYNTHETIC_GT)
    record = outputs["eight_digit_pad"]
    assert record.attorney_in_fact is not None
    assert record.attorney_in_fact.value == "024481863"
    assert record.attorney_in_fact.is_handwritten is True
    assert record.principal is not None
    assert record.principal.value == "516190899"
