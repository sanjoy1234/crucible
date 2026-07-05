"""Tests for CrucibleConfig loading and defaults."""

from __future__ import annotations

import tempfile
from pathlib import Path

import pytest
import yaml

from crucible.config import CrucibleConfig


def test_defaults():
    cfg = CrucibleConfig()
    assert cfg.gate.minimum_ars == 0.80
    assert cfg.gate.fail_open is False
    assert cfg.deployment.model_provider == "local"
    assert cfg.combat_pair.attack_count == 20
    assert cfg.combat_pair.rounds_max == 5


def test_load_from_yaml(tmp_path, monkeypatch):
    monkeypatch.delenv("OLLAMA_MODEL", raising=False)
    yml = {
        "version": 1,
        "gate": {"minimum_ars": 0.90, "fail_open": True},
        "deployment": {"model_provider": "local", "local_model": "mistral:7b"},
        "combat_pair": {"attack_count": 5},
    }
    config_file = tmp_path / ".crucible.yml"
    config_file.write_text(yaml.dump(yml))

    cfg = CrucibleConfig.load(config_file)
    assert cfg.gate.minimum_ars == 0.90
    assert cfg.gate.fail_open is True
    assert cfg.deployment.local_model == "mistral:7b"
    assert cfg.combat_pair.attack_count == 5


def test_missing_config_returns_defaults(tmp_path):
    cfg = CrucibleConfig.load(tmp_path / "nonexistent.yml")
    assert cfg.gate.minimum_ars == 0.80


def test_reports_dir_anchored_to_project_root_not_invoking_cwd(tmp_path, monkeypatch):
    """`crucible dashboard`/`crucible status` must resolve the same reports_dir as
    `crucible run` regardless of which subdirectory of the project they're invoked
    from — otherwise a dashboard launched from a different terminal/cwd silently
    reads an empty, unrelated .crucible/reports."""
    project_root = tmp_path / "project"
    subdir = project_root / "some" / "nested" / "dir"
    subdir.mkdir(parents=True)
    (project_root / ".crucible.yml").write_text("version: 1\n")

    monkeypatch.chdir(subdir)
    cfg = CrucibleConfig.load()
    assert cfg.reports_dir == project_root / ".crucible" / "reports"


def test_reports_dir_anchored_at_project_root_itself(tmp_path):
    (tmp_path / ".crucible.yml").write_text("version: 1\n")
    cfg = CrucibleConfig.load(tmp_path / ".crucible.yml")
    assert cfg.reports_dir == tmp_path / ".crucible" / "reports"


def test_explicit_deployment_wins_over_stale_api_key(tmp_path, monkeypatch):
    """A user's explicit `model_provider: local` in .crucible.yml must not be
    silently overridden just because an unrelated API key is sitting in the env."""
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-leftover-from-last-week")
    monkeypatch.delenv("MODEL_PROVIDER", raising=False)
    yml = {"deployment": {"model_provider": "local"}}
    config_file = tmp_path / ".crucible.yml"
    config_file.write_text(yaml.dump(yml))

    cfg = CrucibleConfig.load(config_file)
    assert cfg.effective_model_provider == "local"


def test_model_provider_env_wins_over_yaml(tmp_path, monkeypatch):
    """MODEL_PROVIDER (written by `crucible setup`) is the user's most recent
    explicit choice and always takes precedence over .crucible.yml."""
    monkeypatch.setenv("MODEL_PROVIDER", "openrouter")
    yml = {"deployment": {"model_provider": "local"}}
    config_file = tmp_path / ".crucible.yml"
    config_file.write_text(yaml.dump(yml))

    cfg = CrucibleConfig.load(config_file)
    assert cfg.effective_model_provider == "openrouter"


def test_zero_config_still_autodetects_from_api_key(tmp_path, monkeypatch):
    """With no .crucible.yml and no MODEL_PROVIDER, fall back to detecting the
    provider from whichever API key is present (zero-config / CI convenience)."""
    # `crucible.cli` calls load_dotenv() at import time, which can leak this
    # project's own .env into the test process — isolate against that here.
    monkeypatch.delenv("MODEL_PROVIDER", raising=False)
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
    monkeypatch.delenv("HF_TOKEN", raising=False)
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-test")

    cfg = CrucibleConfig.load(tmp_path / "nonexistent.yml")
    assert cfg.effective_model_provider == "anthropic"


# ── config_source ─────────────────────────────────────────────────────────────

def test_config_source_set_when_found(tmp_path):
    config_file = tmp_path / ".crucible.yml"
    config_file.write_text("version: 1\n")
    cfg = CrucibleConfig.load(config_file)
    assert cfg.config_source == config_file.resolve()


def test_config_source_none_when_not_found(tmp_path):
    cfg = CrucibleConfig.load(tmp_path / "nonexistent.yml")
    assert cfg.config_source is None


def test_config_source_none_by_default():
    """A bare CrucibleConfig() (not built via .load()) has no known source —
    callers must not assume a project was found just because reports_dir exists."""
    cfg = CrucibleConfig()
    assert cfg.config_source is None
