"""PII-safe aggregate benchmark metrics (Pydantic V2)."""
from __future__ import annotations

from pydantic import BaseModel, Field, computed_field


class BenchmarkMetricRow(BaseModel):
    """One aggregated model row for publishing. Extra/PII fields are dropped."""

    model_config = {"extra": "ignore", "populate_by_name": True}

    model: str = Field(description="Model identifier")
    resolution: str = Field(description="Dataset scope label (e.g. doc count)")
    accuracy_pct: float = Field(ge=0.0, le=100.0, alias="Accuracy (%)")
    latency_s: float = Field(ge=0.0, alias="Latency (s)")
    total_cost_usd: float = Field(ge=0.0, alias="Total Cost ($)")
    calls: int = Field(ge=0, alias="Calls")
    cpve: float = Field(ge=0.0, alias="CPVE")

    @computed_field  # type: ignore[prop-decorator]
    @property
    def model_label(self) -> str:
        return self.model

    def to_markdown_row(self) -> str:
        return (
            f"| {self.model} | {self.resolution} | {self.accuracy_pct:.1f}% | "
            f"{self.latency_s:.2f}s | ${self.total_cost_usd:.4f} | {self.calls} | ${self.cpve:.4f} |"
        )

    def to_tsv_row(self) -> str:
        return (
            f"{self.model}\t{self.resolution}\t{self.accuracy_pct:.2f}\t"
            f"{self.latency_s:.3f}\t{self.total_cost_usd:.6f}\t{self.calls}\t{self.cpve:.6f}"
        )

    @classmethod
    def markdown_header(cls) -> str:
        return (
            "| Model | Resolution | Accuracy (%) | Latency (s) | Total Cost ($) | Calls | CPVE |\n"
            "|---|---|---|---|---|---|---|"
        )

    @classmethod
    def tsv_header(cls) -> str:
        return "Model\tResolution\tAccuracy (%)\tLatency (s)\tTotal Cost ($)\tCalls\tCPVE"
