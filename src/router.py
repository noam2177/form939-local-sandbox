from __future__ import annotations

import asyncio
import csv
import json
import logging
import re
import sys
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, ClassVar, Sequence

import pandas as pd
from pydantic import ValidationError

from utils import log_execution_time_async

import litellm
from litellm import acompletion, completion_cost
from litellm.exceptions import (
    APIConnectionError,
    BadRequestError,
    InternalServerError,
    RateLimitError,
    ServiceUnavailableError,
    Timeout,
)

try:
    from .schemas import Form939Output, normalize_valid_israeli_id
except ImportError:
    from schemas import Form939Output, normalize_valid_israeli_id

logger = logging.getLogger(__name__)

_PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_RESULTS_PATH = _PROJECT_ROOT / "logs" / "benchmark_results.csv"

_JSON_FENCE_RE = re.compile(r"```(?:json)?\s*([\s\S]*?)\s*```", re.IGNORECASE)
_JSON_OBJECT_RE = re.compile(r"\{[\s\S]*\}")

RETRYABLE = (
    RateLimitError,
    APIConnectionError,
    Timeout,
    ServiceUnavailableError,
    InternalServerError,
)

# PoC: Monday cloud escalation target when local + Luhn gate fails (no API call here).
CLOUD_ESCALATION_MODEL = "anthropic/claude-3-5-sonnet-20240620"

LITELLM_MODEL_MAP: dict[str, str] = {
    "gemini-1.5-pro": "gemini/gemini-1.5-pro",
    "deepseek-chat": "deepseek/deepseek-chat",
    "claude-3-5-sonnet-20240620": CLOUD_ESCALATION_MODEL,
    "ollama/gemma4:e4b": "ollama/gemma4:e4b",
    "gemma4:e4b": "ollama/gemma4:e4b",
    "ollama/qwen2.5:7b": "ollama/qwen2.5:7b",
    "qwen2.5:7b": "ollama/qwen2.5:7b",
    "glm4": "ollama/glm4",  # alias for GLM family; pull glm4 or glm-5.3 tag when available
    "ollama/glm4": "ollama/glm4",
}

SYSTEM_PROMPT = (
    "You extract Israeli Form 939 (ייפוי כוח) ID numbers only.\n"
    "Roles:\n"
    "- principal = נותן ההרשאה / מייפה הכוח / giving_permission\n"
    "- attorney_in_fact = מקבל ההרשאה / מיופה הכוח / get_permission\n"
    "Each role is an object: value (digits as written), is_handwritten (bool), "
    "_type=\"text\", _low_OCR_score (bool).\n"
    "Copy the digits you see. Do not invent, complete, or correct an ID number.\n"
    "If a role is missing or unreadable, set that role to null.\n"
    "CRITICAL RULE FOR `is_handwritten`:\n"
    "Pay attention to the boolean value or answer next to the label, not just the word itself!\n"
    "- If it says 'מודפס (לא בכתב יד) - FALSE' or 'בכתב יד: כן' or 'handwritten = TRUE' -> is_handwritten MUST be true.\n"
    "- If it says 'מודפס (לא בכתב יד) - TRUE' or 'בכתב יד: לא' or 'handwritten = FALSE' -> is_handwritten MUST be false.\n"
    "Do not extract names, dates, or addresses. JSON only.\n\n"
    "Examples:\n"
    "Text: 'נותן ההרשאה: ת.ז 123456789 מודפס (לא בכתב יד) - FALSE, בכתב יד: כן. מקבל ההרשאה: 987654321 handwritten = FALSE'\n"
    "Output: {\"principal\": {\"value\": \"123456789\", \"is_handwritten\": true, \"_type\": \"text\", \"_low_OCR_score\": false}, \"attorney_in_fact\": {\"value\": \"987654321\", \"is_handwritten\": false, \"_type\": \"text\", \"_low_OCR_score\": false}}\n\n"
    "Text: 'נותן ההרשאה: ת.ז 123456789 בכתב יד: לא. מקבל ההרשאה: חסר'\n"
    "Output: {\"principal\": {\"value\": \"123456789\", \"is_handwritten\": false, \"_type\": \"text\", \"_low_OCR_score\": false}, \"attorney_in_fact\": null}"
)

COMPACT_SCHEMA_HINT = (
    '{"principal":{"value":"516190899","is_handwritten":false,"_type":"text","_low_OCR_score":false},'
    '"attorney_in_fact":{"value":"024481863","is_handwritten":true,"_type":"text","_low_OCR_score":false}}'
)

EXAMPLE_JSON = COMPACT_SCHEMA_HINT

JsonMode = str  # "schema" | "json" | "prompt"


@dataclass(frozen=True, slots=True)
class ModelBenchmarkResult:
    """Represents the result of a single model extraction attempt."""
    run_id: str
    filename: str
    model: str
    litellm_model: str
    latency_ms: float
    cost_usd: float | None
    parsed_output: dict[str, Any] | None
    success: bool
    error: str | None
    error_type: str | None
    prompt_tokens: int | None
    completion_tokens: int | None
    timestamp_utc: str
    flag_cloud_escalation: bool = False

    def to_row(self) -> dict[str, Any]:
        """Convert the result into a flat dictionary suitable for a pandas DataFrame."""
        parsed = self.parsed_output or {}
        principal = parsed.get("principal") if isinstance(parsed.get("principal"), dict) else {}
        attorney = (
            parsed.get("attorney_in_fact") if isinstance(parsed.get("attorney_in_fact"), dict) else {}
        )
        return {
            "run_id": self.run_id,
            "timestamp_utc": self.timestamp_utc,
            "Filename": self.filename,
            "model": self.model,
            "litellm_model": self.litellm_model,
            "success": self.success,
            "latency_ms": round(self.latency_ms, 3),
            "cost_usd": self.cost_usd,
            "prompt_tokens": self.prompt_tokens,
            "completion_tokens": self.completion_tokens,
            "principal.value": principal.get("value"),
            "principal.is_handwritten": principal.get("is_handwritten"),
            "principal.low_ocr_score": principal.get("_low_OCR_score", False),
            "attorney_in_fact.value": attorney.get("value"),
            "attorney_in_fact.is_handwritten": attorney.get("is_handwritten"),
            "attorney_in_fact.low_ocr_score": attorney.get("_low_OCR_score", False),
            "parsed_output": json.dumps(parsed, ensure_ascii=False, default=str)
            if parsed
            else None,
            "error": self.error,
            "error_type": self.error_type,
            "flag_cloud_escalation": self.flag_cloud_escalation,
            "cloud_escalation_target": CLOUD_ESCALATION_MODEL if self.flag_cloud_escalation else None,
        }


class CloudModelRouter:
    """Concurrent LiteLLM router for Form 939 structured-extraction benchmarks."""

    DEFAULT_MODELS: ClassVar[tuple[str, ...]] = (
        "gemini-1.5-pro",
        "deepseek-chat",
        "claude-3-5-sonnet-20240620",
    )

    def __init__(
        self,
        *,
        models: Sequence[str] | None = None,
        timeout_s: float = 90.0,
        max_retries: int = 2,
        retry_backoff_s: float = 1.5,
        temperature: float = 0.0,
        results_path: str | Path | None = None,
        max_concurrency: int = 3,
        run_id: str | None = None,
    ) -> None:
        self.models: tuple[str, ...] = tuple(models) if models else self.DEFAULT_MODELS
        self.timeout_s = timeout_s
        self.max_retries = max_retries
        self.retry_backoff_s = retry_backoff_s
        self.temperature = temperature
        self.results_path = Path(results_path) if results_path else DEFAULT_RESULTS_PATH
        self._semaphore = asyncio.Semaphore(max_concurrency)
        self._write_lock = asyncio.Lock()
        self.run_id = run_id or datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")

        litellm.drop_params = True
        litellm.suppress_debug_info = True

        self._json_schema: dict[str, Any] = Form939Output.model_json_schema()

    @log_execution_time_async
    async def extract(self, filename: str, hebrew_text: str, persist: bool = True) -> pd.DataFrame:
        """
        Send mock Hebrew Form 939 text to all configured models concurrently.
        
        Args:
            filename (str): The name of the file being processed.
            hebrew_text (str): The raw Hebrew text to extract from.
            persist (bool): Whether to append the result to the CSV immediately.
            
        Returns:
            pd.DataFrame: A DataFrame containing the extraction results.
        """
        if not hebrew_text or not hebrew_text.strip():
            raise ValueError("hebrew_text must be a non-empty Unicode string")

        tasks = [self._invoke(model, filename, hebrew_text) for model in self.models]
        results = await asyncio.gather(*tasks)
        frame = pd.DataFrame([row.to_row() for row in results])
        if persist:
            await self._persist(frame)
        return frame

    @log_execution_time_async
    async def _invoke(self, model: str, filename: str, hebrew_text: str) -> ModelBenchmarkResult:
        """
        Invoke a specific model for extraction.
        
        Args:
            model (str): The model identifier.
            filename (str): The name of the file.
            hebrew_text (str): The text to process.
            
        Returns:
            ModelBenchmarkResult: The result of the extraction.
        """
        litellm_model = LITELLM_MODEL_MAP.get(model, model)
        started = time.perf_counter()
        timestamp = datetime.now(timezone.utc).isoformat()

        async with self._semaphore:
            try:
                response = await self._complete(litellm_model, hebrew_text)
            except Exception as exc:
                latency_ms = (time.perf_counter() - started) * 1000
                logger.exception("Model %s failed", model)
                return ModelBenchmarkResult(
                    run_id=self.run_id,
                    filename=filename,
                    model=model,
                    litellm_model=litellm_model,
                    latency_ms=latency_ms,
                    cost_usd=None,
                    parsed_output=None,
                    success=False,
                    error=f"{type(exc).__name__}: {exc}",
                    error_type=type(exc).__name__,
                    prompt_tokens=None,
                    completion_tokens=None,
                    timestamp_utc=timestamp,
                )

        latency_ms = (time.perf_counter() - started) * 1000
        usage = getattr(response, "usage", None)
        prompt_tokens = getattr(usage, "prompt_tokens", None) if usage else None
        completion_tokens = getattr(usage, "completion_tokens", None) if usage else None
        cost = self._safe_cost(response, litellm_model)

        try:
            parsed = self._parse_response(response)
        except ValidationError as exc:
            logger.warning(
                "Schema/Luhn validation failed for %s; flagging for cloud escalation. %s",
                model,
                exc,
            )
            try:
                payload = self._loads_json(self._message_content(response))
                parsed = self._null_invalid_id_roles(payload)
                # Successful recovery but flagged
                latency_ms = (time.perf_counter() - started) * 1000
                return ModelBenchmarkResult(
                    run_id=self.run_id,
                    filename=filename,
                    model=model,
                    litellm_model=litellm_model,
                    latency_ms=latency_ms,
                    cost_usd=0.0 if cost is None and "ollama" in litellm_model else cost,
                    parsed_output=parsed.model_dump_utf8(),
                    success=True,
                    error=f"ValidationError: {exc}",
                    error_type="LuhnValidationError",
                    flag_cloud_escalation=True,
                    prompt_tokens=prompt_tokens,
                    completion_tokens=completion_tokens,
                    timestamp_utc=timestamp,
                )
            except (ValidationError, ValueError, json.JSONDecodeError, Exception) as drop_exc:
                return self._failed_result(
                    filename,
                    model,
                    litellm_model,
                    started,
                    timestamp,
                    cost,
                    prompt_tokens,
                    completion_tokens,
                    drop_exc,
                )
        except (ValueError, json.JSONDecodeError) as exc:
            return self._failed_result(
                filename,
                model,
                litellm_model,
                started,
                timestamp,
                cost,
                prompt_tokens,
                completion_tokens,
                exc,
            )

        latency_ms = (time.perf_counter() - started) * 1000
        payload = parsed.model_dump_utf8()
        return ModelBenchmarkResult(
            run_id=self.run_id,
            filename=filename,
            model=model,
            litellm_model=litellm_model,
            latency_ms=latency_ms,
            cost_usd=0.0 if cost is None and "ollama" in litellm_model else cost,
            parsed_output=payload,
            success=True,
            error=None,
            error_type=None,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            timestamp_utc=timestamp,
        )

    async def _complete(self, litellm_model: str, hebrew_text: str) -> Any:
        """
        Execute the completion request with retries and fallback modes.
        
        Args:
            litellm_model (str): The LiteLLM model identifier.
            hebrew_text (str): The input text.
            
        Returns:
            Any: The LiteLLM response object.
        """
        messages = self._build_messages(hebrew_text)
        modes = self._json_modes_for(litellm_model)
        last_error: Exception | None = None

        for mode in modes:
            for attempt in range(self.max_retries + 1):
                try:
                    return await self._complete_once(litellm_model, messages, mode=mode)
                except Exception as exc:
                    last_error = exc
                    if self._is_format_unsupported(exc):
                        logger.info(
                            "JSON format unsupported for %s in mode=%s; trying next mode. (%s)",
                            litellm_model,
                            mode,
                            exc,
                        )
                        break
                    if isinstance(exc, BadRequestError) and self._is_schema_unsupported(exc):
                        logger.info(
                            "Structured output unsupported for %s in mode=%s; trying next mode",
                            litellm_model,
                            mode,
                        )
                        break
                    if isinstance(exc, RETRYABLE) and attempt < self.max_retries:
                        delay = self.retry_backoff_s * (2**attempt)
                        logger.warning(
                            "Retryable error on %s mode=%s (attempt %s/%s): %s. Sleeping %.1fs",
                            litellm_model,
                            mode,
                            attempt + 1,
                            self.max_retries + 1,
                            exc,
                            delay,
                        )
                        await asyncio.sleep(delay)
                        continue
                    if mode != modes[-1] and self._is_format_unsupported(exc):
                        break
                    if mode != modes[-1] and not isinstance(exc, RETRYABLE):
                        logger.info("Non-retryable error in mode=%s for %s; trying next mode", mode, litellm_model)
                        break
                    raise

        assert last_error is not None
        raise last_error

    def _json_modes_for(self, litellm_model: str) -> tuple[str, ...]:
        """
        Determine the supported JSON modes for a given model.
        
        Args:
            litellm_model (str): The model identifier.
            
        Returns:
            tuple[str, ...]: A tuple of supported modes (e.g., 'schema', 'json', 'prompt').
        """
        # gemma4 via Ollama rejects `format` (json/json_schema): "failed to load model vocabulary required for format"
        if "ollama" in litellm_model.lower():
            return ("prompt",)
        return ("schema", "json", "prompt")

    async def _complete_once(
        self,
        litellm_model: str,
        messages: list[dict[str, str]],
        *,
        mode: str,
    ) -> Any:
        """
        Make a single completion call to LiteLLM.
        
        Args:
            litellm_model (str): The model identifier.
            messages (list[dict[str, str]]): The conversation messages.
            mode (str): The JSON mode to use.
            
        Returns:
            Any: The LiteLLM response object.
        """
        kwargs: dict[str, Any] = {
            "model": litellm_model,
            "messages": messages,
            "temperature": self.temperature,
            "timeout": self.timeout_s,
            "num_retries": 0,
        }
        # Do not limit max_tokens for local models to avoid truncation errors
        if "ollama" not in litellm_model.lower():
            kwargs["max_tokens"] = 250
            
        if mode == "schema":
            kwargs["response_format"] = Form939Output
        elif mode == "json":
            kwargs["response_format"] = {"type": "json_object"}
        return await acompletion(**kwargs)

    @staticmethod
    def _null_invalid_id_roles(payload: dict[str, Any]) -> Form939Output:
        """
        Nullify ID fields that fail Luhn validation without retrying the LLM.
        
        Args:
            payload (dict[str, Any]): The parsed JSON payload.
            
        Returns:
            Form939Output: The validated Pydantic model with invalid IDs set to None.
        """
        cleaned = dict(payload)
        for role in ("principal", "attorney_in_fact"):
            leaf = cleaned.get(role)
            if not isinstance(leaf, dict):
                continue
            raw = leaf.get("value")
            if raw is None or raw == "":
                continue
            if normalize_valid_israeli_id(str(raw)) is None:
                cleaned[role] = None
        return Form939Output.model_validate(cleaned)

    def _failed_result(
        self,
        filename: str,
        model: str,
        litellm_model: str,
        started: float,
        timestamp: str,
        cost: float | None,
        prompt_tokens: int | None,
        completion_tokens: int | None,
        exc: Exception,
    ) -> ModelBenchmarkResult:
        """
        Create a failed benchmark result record.
        """
        logger.warning("Repair failure for %s: %s", model, exc)
        return ModelBenchmarkResult(
            run_id=self.run_id,
            filename=filename,
            model=model,
            litellm_model=litellm_model,
            latency_ms=(time.perf_counter() - started) * 1000,
            cost_usd=0.0 if cost is None and "ollama" in litellm_model else cost,
            parsed_output=None,
            success=False,
            error=f"{type(exc).__name__}: {exc}",
            error_type=type(exc).__name__,
            flag_cloud_escalation=True,  # Failed models also flag for escalation
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            timestamp_utc=timestamp,
        )

    def _build_messages(self, hebrew_text: str) -> list[dict[str, str]]:
        """
        Build the message payload for the LLM.
        
        Args:
            hebrew_text (str): The input text.
            
        Returns:
            list[dict[str, str]]: The messages list.
        """
        system = (
            f"{SYSTEM_PROMPT}\n"
            f"Required JSON shape:\n{COMPACT_SCHEMA_HINT}\n"
            f"Example (do not copy values, extract from the document):\n{EXAMPLE_JSON}"
        )
        return [
            {"role": "system", "content": system},
            {"role": "user", "content": hebrew_text},
        ]

    def _parse_response(self, response: Any) -> Form939Output:
        """
        Parse and validate the LLM response.
        
        Args:
            response (Any): The LiteLLM response.
            
        Returns:
            Form939Output: The validated Pydantic model.
        """
        content = self._message_content(response)
        payload = self._loads_json(content)
        return Form939Output.model_validate(payload)

    @staticmethod
    def _message_content(response: Any) -> str:
        """
        Extract the text content from a LiteLLM response.
        
        Args:
            response (Any): The LiteLLM response.
            
        Returns:
            str: The extracted text content.
        """
        try:
            content = response.choices[0].message.content
        except (AttributeError, IndexError, TypeError) as exc:
            raise ValueError(f"Malformed completion response: {exc}") from exc

        if content is None:
            raise ValueError("Empty model content")
        if isinstance(content, list):
            parts: list[str] = []
            for item in content:
                if isinstance(item, str):
                    parts.append(item)
                elif isinstance(item, dict) and item.get("type") in {"text", "output_text"}:
                    parts.append(str(item.get("text", "")))
                elif hasattr(item, "text"):
                    parts.append(str(item.text))
            content = "".join(parts)
        if not isinstance(content, str):
            content = str(content)
        return content.strip()

    @staticmethod
    def _loads_json(raw: str) -> dict[str, Any]:
        """
        Robustly load JSON from a string, handling markdown fences and trailing commas.
        
        Args:
            raw (str): The raw string output from the LLM.
            
        Returns:
            dict[str, Any]: The parsed JSON dictionary.
        """
        text = raw.strip()
        fenced = _JSON_FENCE_RE.search(text)
        if fenced:
            text = fenced.group(1).strip()
        try:
            parsed = json.loads(text)
        except json.JSONDecodeError:
            repaired = re.sub(r",\s*([}\]])", r"\1", text)
            try:
                parsed = json.loads(repaired)
            except json.JSONDecodeError:
                match = _JSON_OBJECT_RE.search(repaired)
                if not match:
                    raise
                candidate = re.sub(r",\s*([}\]])", r"\1", match.group(0))
                parsed = json.loads(candidate)
        if not isinstance(parsed, dict):
            raise ValueError("Model JSON root must be an object")
        return parsed

    @staticmethod
    def _safe_cost(response: Any, litellm_model: str) -> float | None:
        """
        Safely extract the cost from a LiteLLM response.
        
        Args:
            response (Any): The LiteLLM response.
            litellm_model (str): The model identifier.
            
        Returns:
            float | None: The cost in USD, or None if unavailable.
        """
        hidden = getattr(response, "_hidden_params", None) or {}
        if isinstance(hidden, dict) and hidden.get("response_cost") is not None:
            try:
                return float(hidden["response_cost"])
            except (TypeError, ValueError):
                pass
        try:
            return float(completion_cost(completion_response=response, model=litellm_model))
        except Exception as exc:
            logger.debug("Cost unavailable for %s: %s", litellm_model, exc)
            return None

    @staticmethod
    def _is_schema_unsupported(exc: Exception) -> bool:
        """Check if the exception indicates structured output is unsupported."""
        message = str(exc).lower()
        needles = (
            "response_format",
            "json_schema",
            "response_schema",
            "unsupported",
            "invalid parameter",
            "unrecognized request argument",
        )
        return any(needle in message for needle in needles)

    @staticmethod
    def _is_format_unsupported(exc: Exception) -> bool:
        """Check if the exception indicates JSON format is unsupported."""
        message = str(exc).lower()
        return any(
            needle in message
            for needle in (
                "vocabulary required for format",
                "failed to load model vocabulary",
                'error":"failed to load model vocabulary',
                "does not support format",
                "unknown format",
            )
        )

    async def _persist(self, frame: pd.DataFrame) -> None:
        """Asynchronously write a DataFrame to the CSV file."""
        async with self._write_lock:
            await asyncio.to_thread(self._write_csv, frame)

    def _write_csv(self, frame: pd.DataFrame) -> None:
        """Synchronously append a DataFrame to the CSV file, handling schema changes."""
        self.results_path.parent.mkdir(parents=True, exist_ok=True)
        if self.results_path.exists() and self.results_path.stat().st_size > 0:
            existing_header = self.results_path.read_text(encoding="utf-8-sig").splitlines()[0]
            if "principal.value" not in existing_header:
                archive = self.results_path.with_name("benchmark_results_legacy.csv")
                self.results_path.replace(archive)
                logger.info("Archived pre-v1 benchmark CSV to %s", archive)
        write_header = not self.results_path.exists() or self.results_path.stat().st_size == 0
        export = frame.copy()
        for column in (
            "run_id",
            "Filename",
            "principal.value",
            "attorney_in_fact.value",
            "parsed_output",
            "error",
            "error_type",
            "flag_cloud_escalation",
            "cloud_escalation_target",
        ):
            if column in export.columns:
                export[column] = export[column].astype(object).where(export[column].notna(), None)
        # TODO(Future): Consider adding a 'run_id' or 'benchmark_session' column to the DataFrame 
        # before appending here. This will prevent data contamination from previous debug runs 
        # when analyzing the CSV later.
        export.to_csv(
            self.results_path,
            mode="a",
            header=write_header,
            index=False,
            encoding="utf-8-sig",
            quoting=csv.QUOTE_ALL,
        )
        logger.info("Wrote %s rows to %s", len(frame), self.results_path)


DEFAULT_HEBREW_SAMPLE = (
    "טופס 939 ייפוי כוח\n"
    "נותן הרשאה / principal: ת.ז 516190899 מודפס\n"
    "מקבל הרשאה / attorney_in_fact: ת.ז 24481863 בכתב יד\n"
)


async def _main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
    router = CloudModelRouter()
    frame = await router.extract(DEFAULT_HEBREW_SAMPLE)
    pd.set_option("display.max_columns", None)
    pd.set_option("display.width", 160)
    print(frame.to_string(index=False))


if __name__ == "__main__":
    if sys.platform.startswith("win"):
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(_main())
