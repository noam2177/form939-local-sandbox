from __future__ import annotations

import csv
from pathlib import Path

from compare import (
    SUMMARY_FILENAME,
    build_summary_rows,
    summarize_compare_rows,
    write_compare_report,
)
from ground_truth import DEFAULT_SYNTHETIC_GT, FORM_939_COMPARE_FIELDS, load_ground_truth_outputs
from schemas import Form939Output


def _read_rows(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def _split(rows: list[dict[str, str]]) -> tuple[list[dict[str, str]], list[dict[str, str]]]:
    details = [row for row in rows if row.get("Filename") != SUMMARY_FILENAME]
    summaries = [row for row in rows if row.get("Filename") == SUMMARY_FILENAME]
    return details, summaries


def test_write_compare_report_covers_production_fields(tmp_path: Path) -> None:
    gold = load_ground_truth_outputs(DEFAULT_SYNTHETIC_GT)
    predicted = {
        stem: Form939Output.model_validate(record.model_dump_utf8())
        for stem, record in gold.items()
    }
    report_path = write_compare_report(
        predicted,
        gold,
        tmp_path / "compare_report.csv",
        model="unit-test",
    )
    rows = _read_rows(report_path)
    details, summaries = _split(rows)
    assert {row["field"] for row in details} == set(FORM_939_COMPARE_FIELDS)
    assert all(row["match"] == "True" for row in details)
    assert rows[-len(summaries) :] == summaries
    assert {row["field"] for row in summaries} == set(FORM_939_COMPARE_FIELDS)
    assert all(row["model"] == "unit-test" for row in summaries)

    summary = summarize_compare_rows(rows)
    assert summary["principal.value"]["success"] == 2
    assert summary["attorney_in_fact.value"]["fail"] == 0


def test_compare_report_appends_and_groups_by_model(tmp_path: Path) -> None:
    gold = load_ground_truth_outputs(DEFAULT_SYNTHETIC_GT)
    predicted = {
        stem: Form939Output.model_validate(record.model_dump_utf8())
        for stem, record in gold.items()
    }
    report_path = tmp_path / "compare_report.csv"
    write_compare_report(predicted, gold, report_path, model="ollama/gemma4:e4b")
    write_compare_report(predicted, gold, report_path, model="gemini/gemini-1.5-pro")

    rows = _read_rows(report_path)
    details, summaries = _split(rows)
    models = [row["model"] for row in details]
    assert models == sorted(models)
    assert set(models) == {"gemini/gemini-1.5-pro", "ollama/gemma4:e4b"}
    assert len(details) == 16
    assert rows[-len(summaries) :] == summaries
    summary_models = [row["model"] for row in summaries]
    assert summary_models == sorted(summary_models)
    assert set(summary_models) == {"gemini/gemini-1.5-pro", "ollama/gemma4:e4b"}
    assert len(summaries) == 8


def test_build_summary_rows_success_fail_counts() -> None:
    details = [
        {"model": "m1", "field": "principal.value", "match": True},
        {"model": "m1", "field": "principal.value", "match": False},
        {"model": "m1", "field": "principal.is_handwritten", "match": True},
        {"model": "m1", "field": "attorney_in_fact.value", "match": True},
        {"model": "m1", "field": "attorney_in_fact.is_handwritten", "match": False},
    ]
    summaries = {row["field"]: row for row in build_summary_rows(details)}
    assert summaries["principal.value"]["predicted"] == 1
    assert summaries["principal.value"]["gold"] == 1
    assert summaries["attorney_in_fact.value"]["predicted"] == 1
    assert summaries["attorney_in_fact.value"]["gold"] == 0
    assert summaries["attorney_in_fact.value"]["match"] is True
    assert summaries["principal.value"]["match"] is False
