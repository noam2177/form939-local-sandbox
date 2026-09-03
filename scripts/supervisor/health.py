"""Health probes for the weekend supervisor."""
from __future__ import annotations

import json
import logging
import shutil
import urllib.error
import urllib.request
from pathlib import Path

from config import LOG_DIR, PROJECT_ROOT

logger = logging.getLogger(__name__)

OLLAMA_TAGS_URL = "http://127.0.0.1:11434/api/tags"
MIN_FREE_DISK_GB = 1.0


def check_ollama(timeout_s: float = 10.0) -> tuple[bool, str]:
    try:
        with urllib.request.urlopen(OLLAMA_TAGS_URL, timeout=timeout_s) as resp:
            payload = json.loads(resp.read().decode("utf-8"))
        models = [m.get("name", "") for m in payload.get("models", [])]
        if not models:
            return False, "Ollama up but no models pulled"
        return True, f"Ollama OK ({len(models)} models)"
    except urllib.error.URLError as exc:
        return False, f"Ollama unreachable: {exc.reason}"
    except (TimeoutError, json.JSONDecodeError, OSError) as exc:
        return False, f"Ollama check failed: {exc}"


def check_disk(path: Path = PROJECT_ROOT) -> tuple[bool, str]:
    try:
        usage = shutil.disk_usage(path)
        free_gb = usage.free / (1024**3)
        if free_gb < MIN_FREE_DISK_GB:
            return False, f"Low disk: {free_gb:.2f} GB free"
        return True, f"Disk OK ({free_gb:.1f} GB free)"
    except OSError as exc:
        return False, f"Disk check failed: {exc}"


def check_directories() -> tuple[bool, str]:
    required = [
        PROJECT_ROOT / "data" / "synthetic_inputs",
        PROJECT_ROOT / "src",
        LOG_DIR,
    ]
    missing = [str(p) for p in required if not p.exists()]
    if missing:
        return False, f"Missing paths: {', '.join(missing)}"
    return True, "Directories OK"


def run_health_suite() -> dict[str, tuple[bool, str]]:
    return {
        "ollama": check_ollama(),
        "disk": check_disk(),
        "directories": check_directories(),
    }
