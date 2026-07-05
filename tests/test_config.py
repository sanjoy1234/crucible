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
