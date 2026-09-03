"""CLI for the weekend supervisor watchdog."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

_SUPERVISOR_DIR = Path(__file__).resolve().parent
if str(_SUPERVISOR_DIR) not in sys.path:
    sys.path.insert(0, str(_SUPERVISOR_DIR))

from config import DEFAULT_MODELS, SupervisorConfig
from watchdog import WeekendSupervisor


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Weekend supervisor: watch Ollama, restart benchmark on stall, publish results",
    )
    parser.add_argument(
        "--target-iterations",
        type=int,
        default=0,
        help="Stop after N full benchmark iterations (0 = run until Ctrl+C)",
    )
    parser.add_argument(
        "--health-interval",
        type=int,
        default=60,
        help="Seconds between supervisor health checks",
    )
    parser.add_argument(
        "--stall-timeout",
        type=int,
        default=600,
        help="Restart benchmark if no CSV progress for this many seconds",
    )
    parser.add_argument(
        "--sleep-between-loops",
        type=int,
        default=300,
        help="Pause between benchmark iterations (passed to run.py)",
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
        sleep_between_loops_s=args.sleep_between_loops,
    )
    return WeekendSupervisor(config).run()


if __name__ == "__main__":
    sys.exit(main())
