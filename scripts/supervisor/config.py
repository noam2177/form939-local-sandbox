"""Weekend supervisor configuration defaults."""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]

DEFAULT_MODELS = [
    "ollama/qwen2.5:7b",
    "ollama/llama3.1",
    "ollama/gemma4:e4b",
]

INPUT_DIR = PROJECT_ROOT / "data" / "synthetic_inputs"
LOG_DIR = PROJECT_ROOT / "logs"
CSV_PATH = LOG_DIR / "benchmark_results.csv"
STATE_PATH = LOG_DIR / "supervisor_state.json"
SUPERVISOR_LOG = LOG_DIR / "supervisor.log"
HEARTBEAT_PATH = LOG_DIR / "supervisor_heartbeat.txt"
SUMMARY_PATH = LOG_DIR / "weekend_final_summary.txt"


@dataclass
class SupervisorConfig:
    models: list[str] = field(default_factory=lambda: list(DEFAULT_MODELS))
    loops_per_child: int = 1
    sleep_between_loops_s: int = 300
    target_iterations: int = 0  # 0 = run until manual stop
    health_interval_s: int = 60
    stall_timeout_s: int = 600
    ollama_retry_s: int = 30
    request_timeout_s: float = 400.0
    restart_cooldown_s: int = 15

    @property
    def expected_calls_per_iteration(self) -> int:
        file_count = len(list(INPUT_DIR.glob("*.txt"))) if INPUT_DIR.is_dir() else 0
        return file_count * len(self.models)
