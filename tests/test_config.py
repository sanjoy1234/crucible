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


def test_load_from_yaml(tmp_path):
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
