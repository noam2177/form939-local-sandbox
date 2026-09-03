"""CLI entrypoint — defaults to dry-run (zero disk writes)."""
from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

from file_repository import FileRepository
from orchestrator import BenchmarkPublisherOrchestrator


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Autonomous Benchmark Publisher (read-only sidecar, PII-safe)",
    )
    parser.add_argument(
        "--input-dir",
        type=Path,
        default=Path("logs"),
        help="Directory with benchmark CSV/JSON artifacts (default: logs)",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("logs/published"),
        help="Output directory when --write is passed (default: logs/published)",
    )
    parser.add_argument(
        "--write",
        action="store_true",
        help="Persist Markdown/TSV reports (default: dry-run preview only)",
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Enable debug logging",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(levelname)s %(name)s: %(message)s",
    )
    repo = FileRepository(args.input_dir.resolve())
    orchestrator = BenchmarkPublisherOrchestrator(repository=repo)
    dry_run = not args.write
    result = orchestrator.run(args.output_dir.resolve(), dry_run=dry_run)
    for message in result.messages:
        print(message)
    if not result.rows:
        print("WARNING: No publishable metrics found. Check --input-dir.")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
