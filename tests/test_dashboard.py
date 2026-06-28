"""Tests for Combat Dashboard — Sprint 10."""

from __future__ import annotations

import json
from pathlib import Path

from crucible.dashboard.app import (
    _load_all_reports,
    _render_index,
    create_app,
)
from crucible.config import CrucibleConfig


# ── _load_all_reports ──────────────────────────────────────────────────────────

def test_load_all_reports_empty_dir(tmp_path):
    reports = _load_all_reports(tmp_path / "nonexistent")
    assert reports == []


def test_load_all_reports_reads_json(tmp_path):
    report = {
        "run_id": "crucible-test-001", "ars_score": 0.85,
        "attack_count": 5, "miss_count": 1, "generated_at": "2026-06-28T12:00:00Z",
    }
    (tmp_path / "crucible-test-001.json").write_text(json.dumps(report))
    reports = _load_all_reports(tmp_path)
    assert len(reports) == 1
    assert reports[0]["run_id"] == "crucible-test-001"


def test_load_all_reports_skips_corrupt_json(tmp_path):
    (tmp_path / "good.json").write_text('{"run_id": "good", "ars_score": 0.9, "attack_count": 3, "miss_count": 0}')
    (tmp_path / "bad.json").write_text("NOT JSON {{{")
    reports = _load_all_reports(tmp_path)
    assert len(reports) == 1
    assert reports[0]["run_id"] == "good"


def test_load_all_reports_respects_limit(tmp_path):
    for i in range(10):
        (tmp_path / f"run-{i:03d}.json").write_text(
            json.dumps({"run_id": f"run-{i:03d}", "ars_score": 0.8, "attack_count": 5, "miss_count": 0})
        )
    reports = _load_all_reports(tmp_path, limit=5)
    assert len(reports) == 5


# ── _render_index ──────────────────────────────────────────────────────────────

def _make_report(run_id: str, ars: float, attacks: int = 5, missed: int = 1) -> dict:
    return {
        "run_id": run_id,
        "ars_score": ars,
        "attack_count": attacks,
        "miss_count": missed,
        "generated_at": "2026-06-28T12:00:00Z",
    }


def test_render_index_is_html():
    cfg = CrucibleConfig()
    html = _render_index([], cfg)
    assert "<!DOCTYPE html>" in html
    assert "</html>" in html


def test_render_index_shows_total_runs():
    cfg = CrucibleConfig()
    reports = [_make_report(f"run-{i}", 0.85) for i in range(3)]
    html = _render_index(reports, cfg)
    assert "3" in html


def test_render_index_shows_gate_threshold():
    cfg = CrucibleConfig()
    cfg.gate.minimum_ars = 0.80
    html = _render_index([], cfg)
    assert "0.80" in html


def test_render_index_shows_pass_fail_badges():
    cfg = CrucibleConfig()
    reports = [
        _make_report("pass-run", 0.90),
        _make_report("fail-run", 0.50),
    ]
    html = _render_index(reports, cfg)
    assert "PASS" in html
    assert "FAIL" in html


def test_render_index_download_links_present():
    cfg = CrucibleConfig()
    reports = [_make_report("my-run-id-12345", 0.85)]
    html = _render_index(reports, cfg)
    assert "/html" in html
    assert "/sarif" in html
    assert "/junit" in html


def test_render_index_empty_shows_empty_message():
    cfg = CrucibleConfig()
    html = _render_index([], cfg)
    assert "No runs yet" in html


def test_render_index_has_bright_background():
    cfg = CrucibleConfig()
    html = _render_index([], cfg)
    # Light theme — no dark background colors
    assert "#F8FAFC" in html or "#FAFAFA" in html
    assert "#1a1a1a" not in html  # not dark mode


def test_render_index_has_ars_trend_section():
    cfg = CrucibleConfig()
    reports = [_make_report(f"run-{i}", 0.85) for i in range(5)]
    html = _render_index(reports, cfg)
    assert "ARS Trend" in html
    assert "sparkline" in html or "svg" in html.lower()


def test_render_index_chart_data_is_valid_json():
    cfg = CrucibleConfig()
    reports = [_make_report(f"run-{i}", 0.8 + i * 0.01) for i in range(3)]
    html = _render_index(reports, cfg)
    # Extract the chart JSON from the rendered HTML
    import re
    match = re.search(r"var data = (\[.*?\]);", html, re.DOTALL)
    assert match is not None
    data = json.loads(match.group(1))
    assert len(data) == 3
    assert all("x" in d and "y" in d for d in data)


# ── create_app (structure only — no live server) ───────────────────────────────

def test_create_app_requires_fastapi(monkeypatch):
    """If FastAPI is not installed, create_app should raise RuntimeError."""
    import crucible.dashboard.app as dash_module
    monkeypatch.setattr(dash_module, "_FASTAPI_AVAILABLE", False)
    try:
        create_app()
        assert False, "expected RuntimeError"
    except RuntimeError as e:
        assert "pip install crucible-ai[ui]" in str(e)


def test_create_app_returns_fastapi_instance():
    """If FastAPI is available, create_app() returns a FastAPI app."""
    import pytest
    try:
        from fastapi import FastAPI  # noqa: F401
    except ImportError:
        pytest.skip("fastapi not installed — skipping live app test")

    app = create_app()
    assert app is not None
    # FastAPI app has routes
    routes = [r.path for r in app.routes]
    assert "/" in routes
    assert "/api/runs" in routes
    assert "/health" in routes


# ── pyproject.toml [ui] extra ──────────────────────────────────────────────────

def test_pyproject_has_ui_optional_dependency():
    import tomllib
    from pathlib import Path as P
    pyproject = P(__file__).parent.parent / "pyproject.toml"
    with open(pyproject, "rb") as f:
        data = tomllib.load(f)
    ui_deps = data["project"]["optional-dependencies"].get("ui", [])
    assert any("fastapi" in d for d in ui_deps)
    assert any("uvicorn" in d for d in ui_deps)
