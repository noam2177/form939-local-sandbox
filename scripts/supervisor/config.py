"""Weekend supervisor configuration defaults.

Rationale (lean weekend):
  - 20 synthetic files × 3 models = 60 LLM calls per pass.
  - 1 pass  → model comparison (who is fastest / most accurate).
  - 3 passes → consistency + latency variance (same input, stable output?).
  - 5+ passes on identical data → diminishing returns, CSV bloat.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]

DEFAULT_MODELS = [
    "ollama/qwen2.5:7b",
    "ollama/llama3.1",
    "ollama/gemma4:e4b",
]
# Pass 1: full model comparison. Pass 2-3: fast models only (consistency, ~40 calls each).
FAST_MODELS = ["ollama/qwen2.5:7b", "ollama/llama3.1"]

INPUT_DIR = PROJECT_ROOT / "data" / "synthetic_inputs"
LOG_DIR = PROJECT_ROOT / "logs"
CSV_PATH = LOG_DIR / "benchmark_results.csv"
STATE_PATH = LOG_DIR / "supervisor_state.json"
SUPERVISOR_LOG = LOG_DIR / "supervisor.log"
HEARTBEAT_PATH = LOG_DIR / "supervisor_heartbeat.txt"
SUMMARY_PATH = LOG_DIR / "weekend_final_summary.txt"
CHECKPOINT_PATH = LOG_DIR / "run_checkpoint.json"

DEFAULT_TARGET_ITERATIONS = 3
DEFAULT_SLEEP_BETWEEN_PASSES_S = 120
DEFAULT_HEALTH_INTERVAL_S = 120
DEFAULT_STALL_TIMEOUT_S = 1800  # 30 min — Gemma can block >15 min without killing the pass


def models_for_pass(pass_num: int) -> list[str]:
    return list(DEFAULT_MODELS) if pass_num == 1 else list(FAST_MODELS)


@dataclass
class SupervisorConfig:
    models: list[str] = field(default_factory=lambda: list(DEFAULT_MODELS))
    loops_per_child: int = 1
    sleep_between_loops_s: int = DEFAULT_SLEEP_BETWEEN_PASSES_S
    target_iterations: int = DEFAULT_TARGET_ITERATIONS
    health_interval_s: int = DEFAULT_HEALTH_INTERVAL_S
    stall_timeout_s: int = DEFAULT_STALL_TIMEOUT_S
    ollama_retry_s: int = 30
    request_timeout_s: float = 400.0
    restart_cooldown_s: int = 15
    pass_rest_s: int = DEFAULT_SLEEP_BETWEEN_PASSES_S  # supervisor-enforced rest between passes

    @property
    def expected_calls_per_iteration(self) -> int:
        file_count = len(list(INPUT_DIR.glob("*.txt"))) if INPUT_DIR.is_dir() else 0
        return file_count * len(self.models)
