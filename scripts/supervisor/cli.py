"""CLI for the weekend supervisor watchdog."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

_SUPERVISOR_DIR = Path(__file__).resolve().parent
if str(_SUPERVISOR_DIR) not in sys.path:
    sys.path.insert(0, str(_SUPERVISOR_DIR))

from config import (
    DEFAULT_HEALTH_INTERVAL_S,
    DEFAULT_MODELS,
    DEFAULT_SLEEP_BETWEEN_PASSES_S,
    DEFAULT_STALL_TIMEOUT_S,
    DEFAULT_TARGET_ITERATIONS,
    SupervisorConfig,
)
from watchdog import WeekendSupervisor


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Weekend supervisor: watch Ollama, restart benchmark on stall, publish results",
    )
    parser.add_argument(
        "--target-iterations",
        type=int,
        default=DEFAULT_TARGET_ITERATIONS,
        choices=[DEFAULT_TARGET_ITERATIONS],
        help=f"Must be exactly {DEFAULT_TARGET_ITERATIONS} passes (weekend plan)",
    )
    parser.add_argument(
        "--health-interval",
        type=int,
        default=DEFAULT_HEALTH_INTERVAL_S,
        help="Seconds between health checks while a pass is running",
    )
    parser.add_argument(
        "--stall-timeout",
        type=int,
        default=DEFAULT_STALL_TIMEOUT_S,
        help="Restart benchmark if no CSV progress for this many seconds",
    )
    parser.add_argument(
        "--sleep-between-loops",
        type=int,
        default=DEFAULT_SLEEP_BETWEEN_PASSES_S,
        help="Cooldown seconds between passes",
    )
    parser.add_argument(
        "--models",
        nargs="+",
        default=DEFAULT_MODELS,
        help="Ollama models to benchmark",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    config = SupervisorConfig(
        models=args.models,
        target_iterations=args.target_iterations,
        health_interval_s=args.health_interval,
        stall_timeout_s=args.stall_timeout,
        pass_rest_s=args.sleep_between_loops,
    )
    return WeekendSupervisor(config).run()


if __name__ == "__main__":
    sys.exit(main())
