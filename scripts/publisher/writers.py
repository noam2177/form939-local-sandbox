"""Strategy-pattern report writers."""
from __future__ import annotations

from pathlib import Path
from typing import Protocol, runtime_checkable

from rich.console import Console
from rich.table import Table

from domain_models import BenchmarkMetricRow


@runtime_checkable
class ReportWriterProtocol(Protocol):
    def write(
        self,
        rows: list[BenchmarkMetricRow],
        output_dir: Path,
        *,
        dry_run: bool,
    ) -> str:
        """Render or persist report. Returns human-readable status line."""
        ...


class DryRunConsoleWriter:
    """Rich preview table — default mode, zero disk writes."""

    def __init__(self, console: Console | None = None) -> None:
        self._console = console or Console()

    def write(
        self,
        rows: list[BenchmarkMetricRow],
        output_dir: Path,
        *,
        dry_run: bool,
    ) -> str:
        table = Table(title="Autonomous Benchmark Publisher — Preview", show_lines=False)
        for col in ("Model", "Resolution", "Accuracy (%)", "Latency (s)", "Total Cost ($)", "Calls", "CPVE"):
            table.add_column(col, justify="right" if col not in ("Model", "Resolution") else "left")
        for row in rows:
            table.add_row(
                row.model,
                row.resolution,
                f"{row.accuracy_pct:.1f}",
                f"{row.latency_s:.2f}",
                f"${row.total_cost_usd:.4f}",
                str(row.calls),
                f"${row.cpve:.4f}",
            )
        if not rows:
            table.add_row("(no data)", "-", "-", "-", "-", "-", "-")
        self._console.print(table)
        mode = "DRY-RUN" if dry_run else "PREVIEW"
        return f"{mode}: displayed {len(rows)} row(s); no files written by console writer."


class MarkdownWriter:
    """Writes benchmark_report.md when dry_run=False."""

    filename = "benchmark_report.md"

    def write(
        self,
        rows: list[BenchmarkMetricRow],
        output_dir: Path,
        *,
        dry_run: bool,
    ) -> str:
        body = ["# Form 939 Benchmark Publisher Report\n", BenchmarkMetricRow.markdown_header()]
        body.extend(row.to_markdown_row() for row in rows)
        content = "\n".join(body) + "\n"
        if dry_run:
            return f"DRY-RUN: would write {output_dir / self.filename} ({len(rows)} rows)"
        output_dir.mkdir(parents=True, exist_ok=True)
        path = output_dir / self.filename
        path.write_text(content, encoding="utf-8")
        return f"Wrote {path} ({len(rows)} rows)"


class TsvWriter:
    """Writes benchmark_report.tsv when dry_run=False."""

    filename = "benchmark_report.tsv"

    def write(
        self,
        rows: list[BenchmarkMetricRow],
        output_dir: Path,
        *,
        dry_run: bool,
    ) -> str:
        lines = [BenchmarkMetricRow.tsv_header(), *(row.to_tsv_row() for row in rows)]
        content = "\n".join(lines) + "\n"
        if dry_run:
            return f"DRY-RUN: would write {output_dir / self.filename} ({len(rows)} rows)"
        output_dir.mkdir(parents=True, exist_ok=True)
        path = output_dir / self.filename
        path.write_text(content, encoding="utf-8")
        return f"Wrote {path} ({len(rows)} rows)"
