"""Tests for Resilience Report generation and integrity verification."""

from __future__ import annotations

import json
import tempfile
from pathlib import Path

import pytest

from crucible.agents.breaker import Attack
from crucible.core.combat_pair import CombatResult
from crucible.output.report import (
    build_report,
    generate_run_id,
    render_markdown,
    save_report,
    load_report,
    verify_integrity,
)


def _make_result(scores: list[float]) -> CombatResult:
    attacks = [
        Attack(id=f"atk-{i:03d}", cwe="CWE-89", title="SQL Injection test",
               description="Test", score=s)
        for i, s in enumerate(scores)
    ]
    result = CombatResult()
    result.all_attacks = attacks
    result.final_ars = sum(scores) / len(scores) if scores else 1.0
    return result


def test_run_id_format():
    run_id = generate_run_id()
    assert run_id.startswith("crucible-")
    assert len(run_id) > 20


def test_build_report_structure():
    result = _make_result([1.0, 0.5, 0.0, 1.0, 1.0])
    run_id = generate_run_id()
    report = build_report(result, run_id)

    assert report["schema_version"] == "1.0"
    assert report["run_id"] == run_id
    assert "ars_score" in report
    assert "integrity_hash" in report
    assert report["integrity_hash"].startswith("sha256:")
    assert len(report["attacks"]) == 5
    assert "control_mappings" in report
    assert "NIST_SSDF" in report["control_mappings"]


def test_integrity_hash_tamper_detection():
    result = _make_result([1.0, 0.5])
    report = build_report(result, generate_run_id())
    assert verify_integrity(report) is True

    # Tamper with an attack score
    report["attacks"][0]["score"] = 0.0
    assert verify_integrity(report) is False


def test_save_and_load_report(tmp_path):
    result = _make_result([1.0, 0.8])
    run_id = generate_run_id()
    report = build_report(result, run_id)
    save_report(report, tmp_path)

    loaded = load_report(run_id, tmp_path)
    assert loaded["run_id"] == run_id
    assert loaded["ars_score"] == report["ars_score"]


def test_render_markdown_contains_ars():
    result = _make_result([1.0, 0.5, 0.0])
    report = build_report(result, generate_run_id())
    md = render_markdown(report)
    assert "ARS Score" in md
    assert "CRUCIBLE" in md
    assert "sha256:" in md


def test_mitigated_partial_missed_counts():
    result = _make_result([1.0, 0.5, 0.0, 1.0])
    report = build_report(result, generate_run_id())
    assert report["mitigated_count"] == 2
    assert report["partial_count"] == 1
    assert report["miss_count"] == 1
