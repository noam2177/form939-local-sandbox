from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from evaluate import score_extraction, score_frame, write_scores
from schemas import Form939Output

GOLD = {
    "principal": {
        "value": "516190899",
        "is_handwritten": False,
        "_type": "text",
        "_low_OCR_score": False,
    },
    "attorney_in_fact": {
        "value": "024481863",
        "is_handwritten": True,
        "_type": "text",
        "_low_OCR_score": False,
    },
}


def test_score_extraction_exact() -> None:
    score = score_extraction(GOLD, GOLD)
    assert score["id_number_ok"] is True
    assert score["exact_record"] is True
    assert score["principal_value_ok"] is True
    assert score["required_accuracy"] == 1.0


def test_score_extraction_detects_wrong_id() -> None:
    predicted = {
        **GOLD,
        "principal": {**GOLD["principal"], "value": "515240802"},
    }
    score = score_extraction(predicted, GOLD)
    assert score["principal_value_ok"] is False
    assert score["id_number_ok"] is False
    assert score["exact_record"] is False


def test_score_frame_and_write_csv(tmp_path: Path) -> None:
    parsed = Form939Output.model_validate(GOLD).model_dump_utf8()
    frame = pd.DataFrame(
        [
            {
                "model": "ollama/gemma4:e4b",
                "success": True,
                "latency_ms": 12.3,
                "cost_usd": 0.0,
                "parsed_output": json.dumps(parsed, ensure_ascii=False),
                "error": None,
            }
        ]
    )
    scored = score_frame(frame, GOLD)
    assert bool(scored.iloc[0]["exact_record"]) is True
    out = write_scores(scored, tmp_path / "eval_scores.csv")
    logged = pd.read_csv(out, encoding="utf-8-sig")
    assert logged.iloc[0]["id_number_ok"] in {True, "True"}


def test_write_scores_appends(tmp_path: Path) -> None:
    scored = pd.DataFrame(
        [
            {
                "model": "ollama/gemma4:e4b",
                "success": True,
                "exact_record": True,
                "id_number_ok": True,
            }
        ]
    )
    path = tmp_path / "eval_scores.csv"
    write_scores(scored, path)
    scored.loc[0, "model"] = "gemini/gemini-1.5-pro"
    write_scores(scored, path)
    logged = pd.read_csv(path, encoding="utf-8-sig")
    assert len(logged) == 2
    assert set(logged["model"]) == {"ollama/gemma4:e4b", "gemini/gemini-1.5-pro"}


def test_gold_fixture_file_is_valid() -> None:
    path = Path(__file__).resolve().parents[1] / "data" / "gold" / "form939_samples.json"
    payload = json.loads(path.read_text(encoding="utf-8"))
    assert payload["compare_fields"] == [
        "principal.value",
        "principal.is_handwritten",
        "attorney_in_fact.value",
        "attorney_in_fact.is_handwritten",
    ]
    for sample in payload["samples"]:
        record = Form939Output.model_validate(sample["gold"])
        assert record.principal is not None
        assert len(record.principal.value or "") == 9
