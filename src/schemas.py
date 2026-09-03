from __future__ import annotations

import re
from typing import Any, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator

ID_DIGIT_LENGTH = 9
FIELD_TYPE_JSON_KEY = "_type"
LOW_OCR_SCORE_JSON_KEY = "_low_OCR_score"


def clean_field_value(value: Optional[str]) -> Optional[str]:
    """
    Extract only digits from a given string.
    
    Args:
        value (Optional[str]): The raw string to clean.
        
    Returns:
        Optional[str]: A string containing only digits, or None if no digits are found.
    """
    digits = re.sub(r"\D", "", value or "")
    return digits if digits else None


def is_valid_israeli_id(digits: Optional[str]) -> bool:
    """
    Validate an Israeli ID number using the Luhn algorithm.
    
    Args:
        digits (Optional[str]): The 9-digit ID string to validate.
        
    Returns:
        bool: True if the ID is valid according to the Luhn checksum, False otherwise.
    """
    if digits is None or len(digits) != ID_DIGIT_LENGTH or not digits.isdigit():
        return False
    total = 0
    for position, character in enumerate(digits):
        weighted = int(character) * (1 if position % 2 == 0 else 2)
        total += weighted if weighted < 10 else weighted - 9
    return total % 10 == 0


def normalize_valid_israeli_id(digits: Optional[str]) -> Optional[str]:
    """
    Normalize and validate an Israeli ID.
    
    Pads 8-digit IDs with a leading zero and validates the result using the Luhn algorithm.
    
    Args:
        digits (Optional[str]): The raw ID string.
        
    Returns:
        Optional[str]: The normalized 9-digit valid ID, or None if invalid.
    """
    cleaned_digits = clean_field_value(digits)
    if not cleaned_digits:
        return None
    if len(cleaned_digits) == 8:
        cleaned_digits = f"0{cleaned_digits}"
    if not is_valid_israeli_id(cleaned_digits):
        return None
    return cleaned_digits


def apply_israeli_id_luhn_gate_to_element(element: Optional[dict[str, Any]]) -> Optional[dict[str, Any]]:
    """
    Apply Luhn validation to a dictionary element containing an ID value.
    
    Args:
        element (Optional[dict[str, Any]]): The dictionary containing a 'value' key.
        
    Returns:
        Optional[dict[str, Any]]: The element with a normalized ID, or None if validation fails.
    """
    if element is None:
        return None
    normalized_id = normalize_valid_israeli_id(element.get("value"))
    if normalized_id is None:
        return None
    element["value"] = normalized_id
    return element


class IdFieldLeaf(BaseModel):
    """Production ID leaf: value + handwriting + MeloD metadata aliases."""

    model_config = ConfigDict(
        extra="ignore",
        populate_by_name=True,
        serialize_by_alias=True,
    )

    value: str | None = None
    is_handwritten: bool = False
    type: Literal["text"] = Field(alias="_type", default="text")
    low_ocr_score: bool = Field(alias="_low_OCR_score", default=False)

    @field_validator("value", mode="before")
    @classmethod
    def _normalize_id_value(cls, value: Any) -> Any:
        if value is None or value == "":
            return None
        if isinstance(value, bool):
            raise ValueError("ID value must be digits")
        if isinstance(value, float) and value.is_integer():
            value = int(value)
        if isinstance(value, int):
            value = str(value)
        if not isinstance(value, str):
            value = str(value)
        raw = value.strip()
        if not raw:
            return None
        normalized = normalize_valid_israeli_id(raw)
        if normalized is None:
            raise ValueError("Israeli ID failed Luhn gate after 8-digit zero-pad")
        return normalized

    @field_validator("is_handwritten", "low_ocr_score", mode="before")
    @classmethod
    def _coerce_bool(cls, value: Any) -> Any:
        if isinstance(value, str):
            lowered = value.strip().lower()
            if lowered in {"true", "1", "yes"}:
                return True
            if lowered in {"false", "0", "no"}:
                return False
        return value


class Form939Output(BaseModel):
    """Octave production JSON: principal and attorney_in_fact ID leaves only."""

    model_config = ConfigDict(
        extra="ignore",
        populate_by_name=True,
        serialize_by_alias=True,
        json_schema_extra={
            "title": "Form939Output",
            "description": "Form 939 production extract: two Israeli ID roles.",
        },
    )

    principal: IdFieldLeaf | None = None
    attorney_in_fact: IdFieldLeaf | None = None

    @field_validator("principal", "attorney_in_fact", mode="before")
    @classmethod
    def _coerce_leaf(cls, value: Any) -> Any:
        if value is None or value == "":
            return None
        if isinstance(value, str):
            return {"value": value}
        if isinstance(value, dict) and "value" not in value:
            for key in ("id", "id_number", "מספר_זהות"):
                if key in value:
                    return {**value, "value": value[key]}
        return value

    def model_dump_utf8(self) -> dict[str, Any]:
        """
        Dump the model to a dictionary with UTF-8 support and alias serialization.
        
        Returns:
            dict[str, Any]: The serialized model data.
        """
        return self.model_dump(mode="json", by_alias=True)


Form939Schema = Form939Output
