from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

_SUPERVISOR = Path(__file__).resolve().parents[1] / "scripts" / "supervisor"
sys.path.insert(0, str(_SUPERVISOR))

from config import SupervisorConfig  # noqa: E402
from health import check_directories, check_disk  # noqa: E402
from watchdog import WeekendSupervisor, _count_csv_rows  # noqa: E402


def test_count_csv_rows(tmp_path: Path) -> None:
    csv_path = tmp_path / "bench.csv"
    csv_path.write_text("a,b\n1,2\n3,4\n", encoding="utf-8")
    assert _count_csv_rows(csv_path) == 2
    assert _count_csv_rows(tmp_path / "missing.csv") == 0


def test_supervisor_config_expected_calls() -> None:
    cfg = SupervisorConfig(models=["ollama/a", "ollama/b"])
    assert cfg.expected_calls_per_iteration >= 0


def test_supervisor_state_roundtrip(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    import config as sup_config
    import watchdog as sup_watchdog

    log_dir = tmp_path / "logs"
    log_dir.mkdir()
    monkeypatch.setattr(sup_config, "LOG_DIR", log_dir)
    monkeypatch.setattr(sup_config, "STATE_PATH", log_dir / "supervisor_state.json")
    monkeypatch.setattr(sup_config, "CSV_PATH", log_dir / "bench.csv")
    monkeypatch.setattr(sup_config, "HEARTBEAT_PATH", log_dir / "heartbeat.txt")
    monkeypatch.setattr(sup_config, "SUPERVISOR_LOG", log_dir / "supervisor.log")
    monkeypatch.setattr(sup_config, "SUMMARY_PATH", log_dir / "summary.txt")
    monkeypatch.setattr(sup_watchdog, "LOG_DIR", log_dir)
    monkeypatch.setattr(sup_watchdog, "STATE_PATH", log_dir / "supervisor_state.json")
    monkeypatch.setattr(sup_watchdog, "CSV_PATH", log_dir / "bench.csv")
    monkeypatch.setattr(sup_watchdog, "HEARTBEAT_PATH", log_dir / "heartbeat.txt")
    monkeypatch.setattr(sup_watchdog, "SUPERVISOR_LOG", log_dir / "supervisor.log")
    monkeypatch.setattr(sup_watchdog, "SUMMARY_PATH", log_dir / "summary.txt")

    sup = WeekendSupervisor(SupervisorConfig(models=["ollama/x"]))
    sup._save_state()
    loaded = json.loads((log_dir / "supervisor_state.json").read_text(encoding="utf-8"))
    assert loaded["status"] in ("initializing", "supervisor_running", "benchmark_running")


def test_health_directories() -> None:
    ok, msg = check_directories()
    assert ok is True
    assert "Directories" in msg


def test_health_disk() -> None:
    ok, msg = check_disk(Path(__file__).resolve().parents[1])
    assert ok is True
    assert "Disk" in msg
