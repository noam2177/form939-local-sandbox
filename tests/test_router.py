from __future__ import annotations

import json
from types import SimpleNamespace
from typing import Any

import pandas as pd
import pytest

from litellm.exceptions import APIConnectionError
from router import CloudModelRouter
from schemas import Form939Output

VALID_JSON = {
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


def _fake_response(content: str, cost: float = 0.0) -> SimpleNamespace:
    return SimpleNamespace(
        choices=[SimpleNamespace(message=SimpleNamespace(content=content))],
        usage=SimpleNamespace(prompt_tokens=11, completion_tokens=22),
        _hidden_params={"response_cost": cost},
    )


@pytest.fixture
def results_path(tmp_path):
    return tmp_path / "benchmark_results.csv"


@pytest.mark.asyncio
async def test_extract_writes_quoted_csv(monkeypatch, results_path) -> None:
    async def fake_complete(*_args: Any, **_kwargs: Any) -> SimpleNamespace:
        return _fake_response(json.dumps(VALID_JSON, ensure_ascii=False), cost=0.012)

    monkeypatch.setattr("router.acompletion", fake_complete)
    router = CloudModelRouter(
        models=["ollama/gemma4:e4b"],
        results_path=results_path,
        max_retries=0,
        timeout_s=5,
    )
    frame = await router.extract("test_file", "principal 516190899 attorney 24481863")
    assert len(frame) == 1
    assert bool(frame.iloc[0]["success"]) is True
    assert frame.iloc[0]["principal.value"] == "516190899"
    assert frame.iloc[0]["attorney_in_fact.value"] == "024481863"
    assert frame.iloc[0]["cost_usd"] == 0.012

    logged = pd.read_csv(
        results_path,
        encoding="utf-8-sig",
        dtype={"principal.value": "string", "attorney_in_fact.value": "string"},
    )
    assert str(logged.iloc[0]["principal.value"]) == "516190899"
    payload = json.loads(logged.iloc[0]["parsed_output"])
    record = Form939Output.model_validate(payload)
    assert record.principal is not None
    assert record.principal.value == "516190899"


@pytest.mark.asyncio
async def test_extract_appends_csv_rows(monkeypatch, results_path) -> None:
    async def fake_complete(*_args: Any, **_kwargs: Any) -> SimpleNamespace:
        return _fake_response(json.dumps(VALID_JSON, ensure_ascii=False))

    monkeypatch.setattr("router.acompletion", fake_complete)
    router = CloudModelRouter(models=["ollama/gemma4:e4b"], results_path=results_path, max_retries=0)
    await router.extract("doc1", "מסמך 1")
    await router.extract("doc2", "מסמך 2")
    logged = pd.read_csv(results_path, encoding="utf-8-sig")
    assert len(logged) == 2


@pytest.mark.asyncio
async def test_extract_handles_api_failure_gracefully(monkeypatch, results_path) -> None:
    async def boom(*_args: Any, **_kwargs: Any) -> None:
        raise APIConnectionError(message="connection refused", llm_provider="ollama", model="gemma4:e4b")

    monkeypatch.setattr("router.acompletion", boom)
    router = CloudModelRouter(
        models=["ollama/gemma4:e4b"],
        results_path=results_path,
        max_retries=0,
        timeout_s=1,
    )
    frame = await router.extract("test_file", "טקסט עברי")
    assert bool(frame.iloc[0]["success"]) is False
    assert "APIConnectionError" in str(frame.iloc[0]["error"])
    logged = pd.read_csv(results_path, encoding="utf-8-sig")
    assert len(logged) == 1


@pytest.mark.asyncio
async def test_extract_runs_models_concurrently(monkeypatch, results_path) -> None:
    seen: list[str] = []

    async def fake_complete(*, model: str, **_kwargs: Any) -> SimpleNamespace:
        seen.append(model)
        return _fake_response(json.dumps(VALID_JSON, ensure_ascii=False))

    monkeypatch.setattr("router.acompletion", fake_complete)
    router = CloudModelRouter(
        models=["gemini-1.5-pro", "deepseek-chat", "claude-3-5-sonnet-20240620"],
        results_path=results_path,
        max_retries=0,
        max_concurrency=3,
    )
    frame = await router.extract("test_file", "ת.ז 516190899")
    assert len(frame) == 3
    assert frame["success"].all()
    assert set(seen) == {
        "gemini/gemini-1.5-pro",
        "deepseek/deepseek-chat",
        "anthropic/claude-3-5-sonnet-20240620",
    }


@pytest.mark.asyncio
async def test_empty_input_rejected(results_path) -> None:
    router = CloudModelRouter(models=["ollama/gemma4:e4b"], results_path=results_path)
    with pytest.raises(ValueError):
        await router.extract("test_file", "   ")


def test_loads_json_from_fences_and_trailing_commas() -> None:
    fenced = '```json\n{"principal": {"value": "516190899"},}\n```'
    parsed = CloudModelRouter._loads_json(fenced)
    assert parsed["principal"]["value"] == "516190899"


def test_ollama_uses_prompt_json_mode_only() -> None:
    router = CloudModelRouter(models=["ollama/gemma4:e4b"])
    assert router._json_modes_for("ollama/gemma4:e4b") == ("prompt",)
    assert router._json_modes_for("gemini/gemini-1.5-pro") == ("schema", "json", "prompt")


@pytest.mark.asyncio
async def test_invalid_luhn_id_is_nulled_without_llm_retry(monkeypatch, results_path) -> None:
    calls: list[int] = []
    invalid = {
        "principal": {"value": "123456789", "is_handwritten": False},
        "attorney_in_fact": {"value": "024481863", "is_handwritten": True},
    }

    async def fake_complete(*, messages, **_kwargs: Any) -> SimpleNamespace:
        calls.append(len(messages))
        joined = json.dumps(messages, ensure_ascii=False)
        assert "checksum" not in joined.lower()
        assert "luhn" not in joined.lower()
        return _fake_response(json.dumps(invalid, ensure_ascii=False))

    monkeypatch.setattr("router.acompletion", fake_complete)
    router = CloudModelRouter(models=["ollama/gemma4:e4b"], results_path=results_path, max_retries=0)
    frame = await router.extract("test_file", "principal 123456789 attorney 24481863")
    assert len(calls) == 1
    assert bool(frame.iloc[0]["success"]) is True
    assert frame.iloc[0]["principal.value"] in (None, "") or pd.isna(frame.iloc[0]["principal.value"])
    assert frame.iloc[0]["attorney_in_fact.value"] == "024481863"


@pytest.mark.asyncio
async def test_luhn_failure_flags_cloud_escalation(monkeypatch, results_path) -> None:
    invalid = {
        "principal": {"value": "123456789", "is_handwritten": False},
        "attorney_in_fact": {"value": "024481863", "is_handwritten": True},
    }

    async def fake_complete(*_args: Any, **_kwargs: Any) -> SimpleNamespace:
        return _fake_response(json.dumps(invalid, ensure_ascii=False))

    monkeypatch.setattr("router.acompletion", fake_complete)
    router = CloudModelRouter(models=["ollama/gemma4:e4b"], results_path=results_path, max_retries=0)
    frame = await router.extract("test_file", "principal 123456789 attorney 24481863")
    assert bool(frame.iloc[0]["flag_cloud_escalation"]) is True
    assert frame.iloc[0]["cloud_escalation_target"] == "anthropic/claude-3-5-sonnet-20240620"
    assert frame.iloc[0]["error_type"] == "LuhnValidationError"


def test_format_unsupported_detection() -> None:
    err = RuntimeError('{"error":"failed to load model vocabulary required for format"}')
    assert CloudModelRouter._is_format_unsupported(err) is True
    assert CloudModelRouter._is_format_unsupported(RuntimeError("timeout")) is False
