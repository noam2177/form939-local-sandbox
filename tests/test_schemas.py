from __future__ import annotations

import pytest
from pydantic import ValidationError

from schemas import (
    Form939Output,
    IdFieldLeaf,
    apply_israeli_id_luhn_gate_to_element,
    is_valid_israeli_id,
    normalize_valid_israeli_id,
)


def test_normalize_eight_digit_ground_truth_padded() -> None:
    assert normalize_valid_israeli_id("24481863") == "024481863"


def test_normalize_nine_digit_valid_unchanged() -> None:
    assert normalize_valid_israeli_id("516190899") == "516190899"


def test_normalize_invalid_checksum_rejected() -> None:
    assert normalize_valid_israeli_id("201401691") is None
    assert normalize_valid_israeli_id("12345678") is None


def test_is_valid_israeli_id_mirrors_production() -> None:
    assert is_valid_israeli_id("516190899") is True
    assert is_valid_israeli_id("515240802") is True
    assert is_valid_israeli_id("201401691") is False
    assert is_valid_israeli_id("032249548") is False
    assert is_valid_israeli_id("12345678") is False
    assert is_valid_israeli_id(None) is False


def test_luhn_gate_drops_invalid_element() -> None:
    element = {"value": "201401691", "is_handwritten": True, "_type": "text", "_low_OCR_score": False}
    assert apply_israeli_id_luhn_gate_to_element(element) is None


def test_luhn_gate_pads_valid_eight_digit_in_place() -> None:
    element = {"value": "24481863", "is_handwritten": False, "_type": "text", "_low_OCR_score": False}
    gated = apply_israeli_id_luhn_gate_to_element(element)
    assert gated is element
    assert gated["value"] == "024481863"


def test_id_leaf_accepts_production_aliases() -> None:
    leaf = IdFieldLeaf.model_validate(
        {
            "value": "24481863",
            "is_handwritten": True,
            "_type": "text",
            "_low_OCR_score": False,
        }
    )
    assert leaf.value == "024481863"
    dumped = leaf.model_dump(mode="json", by_alias=True)
    assert dumped["_type"] == "text"
    assert dumped["_low_OCR_score"] is False


def test_id_leaf_rejects_failed_luhn() -> None:
    with pytest.raises(ValidationError):
        IdFieldLeaf.model_validate({"value": "123456789"})


def test_form939_output_two_roles() -> None:
    record = Form939Output.model_validate(
        {
            "principal": {"value": "516190899", "is_handwritten": False},
            "attorney_in_fact": {"value": "24481863", "is_handwritten": "TRUE"},
        }
    )
    assert record.principal is not None
    assert record.principal.value == "516190899"
    assert record.attorney_in_fact is not None
    assert record.attorney_in_fact.value == "024481863"
    assert record.attorney_in_fact.is_handwritten is True
    dumped = record.model_dump_utf8()
    assert set(dumped) == {"principal", "attorney_in_fact"}
    assert dumped["principal"]["_type"] == "text"


def test_form939_output_allows_null_roles() -> None:
    record = Form939Output.model_validate({"principal": None, "attorney_in_fact": None})
    assert record.principal is None
    assert record.attorney_in_fact is None


def test_form939_output_coerces_bare_id_string() -> None:
    record = Form939Output.model_validate({"principal": "516190899"})
    assert record.principal is not None
    assert record.principal.value == "516190899"
