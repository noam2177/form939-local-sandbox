"""Dependency-injected orchestration for benchmark publishing."""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from domain_models import BenchmarkMetricRow
from file_repository import FileRepository
from writers import DryRunConsoleWriter, MarkdownWriter, ReportWriterProtocol, TsvWriter


@dataclass
class PublishResult:
    rows: list[BenchmarkMetricRow]
    messages: list[str] = field(default_factory=list)


class BenchmarkPublisherOrchestrator:
    def __init__(
        self,
        repository: FileRepository,
        writers: list[ReportWriterProtocol] | None = None,
    ) -> None:
        self.repository = repository
        self.writers = writers or [DryRunConsoleWriter(), MarkdownWriter(), TsvWriter()]

    def run(self, output_dir: Path, *, dry_run: bool = True) -> PublishResult:
        rows = self.repository.load_all()
        messages: list[str] = []
        for writer in self.writers:
            msg = writer.write(rows, output_dir, dry_run=dry_run)
            messages.append(msg)
        return PublishResult(rows=rows, messages=messages)
