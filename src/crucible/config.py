"""CrucibleConfig — loads and validates .crucible.yml."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal

import yaml


@dataclass
class CombatPairConfig:
    attack_count: int = 20
    rounds_max: int = 5
    cwe_rotation: bool = True
    early_exit_threshold: float = 0.95
    early_exit_streak: int = 3


@dataclass
class PolicyConfig:
    domains: list[str] = field(default_factory=lambda: ["owasp_top10@2025.1"])


@dataclass
class GateConfig:
    minimum_ars: float = 0.80
    fail_open: bool = False
    exempt_labels: list[str] = field(default_factory=lambda: ["crucible-exempt", "hotfix"])


@dataclass
class DeploymentConfig:
    model_provider: Literal["local", "anthropic", "openrouter", "huggingface", "openai_compat"] = "local"
    # Ollama (local)
    local_model: str = "llama3.1:8b"
    local_endpoint: str = "http://localhost:11434"
    # Anthropic
    anthropic_model: str = "claude-haiku-4-5-20251001"
    # OpenRouter — free and paid open-source models
    openrouter_model: str = "meta-llama/llama-3.3-70b-instruct:free"
    # HuggingFace Inference API
    huggingface_model: str = "meta-llama/Llama-3.1-70B-Instruct"
    # Generic OpenAI-compatible (vLLM, Together AI, Groq, Azure OpenAI, etc.)
    openai_compat_endpoint: str = "http://localhost:8000/v1"
    openai_compat_model: str = "llama3.1:8b"


@dataclass
class RbacConfig:
    admin_teams: list[str] = field(default_factory=list)
    reviewer_teams: list[str] = field(default_factory=list)


@dataclass
class NotificationsConfig:
    jira_project: str = ""
    slack_webhook: str = ""


@dataclass
class CrucibleConfig:
    version: int = 1
    combat_pair: CombatPairConfig = field(default_factory=CombatPairConfig)
    policy: PolicyConfig = field(default_factory=PolicyConfig)
    gate: GateConfig = field(default_factory=GateConfig)
    deployment: DeploymentConfig = field(default_factory=DeploymentConfig)
    rbac: RbacConfig = field(default_factory=RbacConfig)
    notifications: NotificationsConfig = field(default_factory=NotificationsConfig)
    retention_days: int = 365
    community_brain: bool = False

    # resolved at load time
    reports_dir: Path = field(default_factory=lambda: Path(".crucible/reports"))

    @classmethod
    def load(cls, path: str | Path | None = None) -> "CrucibleConfig":
        """Load config from .crucible.yml, walking up from cwd if path not given."""
        if path is None:
            path = _find_config()
        if path is None or not Path(path).exists():
            return cls()

        with open(path) as f:
            raw = yaml.safe_load(f) or {}

        cfg = cls()
        cfg.version = raw.get("version", 1)

        if cp := raw.get("combat_pair"):
            cfg.combat_pair = CombatPairConfig(
                attack_count=cp.get("attack_count", 20),
                rounds_max=cp.get("rounds_max", 5),
                cwe_rotation=cp.get("cwe_rotation", True),
                early_exit_threshold=cp.get("early_exit_threshold", 0.95),
                early_exit_streak=cp.get("early_exit_streak", 3),
            )

        if p := raw.get("policy"):
            cfg.policy = PolicyConfig(domains=p.get("domains", ["owasp_top10@2025.1"]))

        if g := raw.get("gate"):
            cfg.gate = GateConfig(
                minimum_ars=g.get("minimum_ars", 0.80),
                fail_open=g.get("fail_open", False),
                exempt_labels=g.get("exempt_labels", ["crucible-exempt", "hotfix"]),
            )

        if d := raw.get("deployment"):
            cfg.deployment = DeploymentConfig(
                model_provider=d.get("model_provider", "local"),
                local_model=d.get("local_model", "llama3.1:8b"),
                local_endpoint=d.get("local_endpoint", "http://localhost:11434"),
                anthropic_model=d.get("anthropic_model", "claude-haiku-4-5-20251001"),
                openrouter_model=d.get("openrouter_model", "meta-llama/llama-3.3-70b-instruct:free"),
                huggingface_model=d.get("huggingface_model", "meta-llama/Llama-3.1-70B-Instruct"),
                openai_compat_endpoint=d.get("openai_compat_endpoint", "http://localhost:8000/v1"),
                openai_compat_model=d.get("openai_compat_model", "llama3.1:8b"),
            )

        if r := raw.get("rbac"):
            cfg.rbac = RbacConfig(
                admin_teams=r.get("admin_teams", []),
                reviewer_teams=r.get("reviewer_teams", []),
            )

        if n := raw.get("notifications"):
            cfg.notifications = NotificationsConfig(
                jira_project=n.get("jira_project", ""),
                slack_webhook=n.get("slack_webhook", ""),
            )

        cfg.retention_days = raw.get("retention_days", 365)
        cfg.community_brain = raw.get("community_brain", False)

        # Env var overrides — order matters (most specific wins)
        if os.environ.get("OPENROUTER_API_KEY"):
            cfg.deployment.model_provider = "openrouter"
        elif os.environ.get("ANTHROPIC_API_KEY"):
            cfg.deployment.model_provider = "anthropic"
        elif os.environ.get("HF_TOKEN"):
            cfg.deployment.model_provider = "huggingface"

        # Per-provider model overrides
        if m := os.environ.get("OPENROUTER_MODEL"):
            cfg.deployment.openrouter_model = m
        if m := os.environ.get("HF_MODEL"):
            cfg.deployment.huggingface_model = m
        if m := os.environ.get("OPENAI_COMPAT_MODEL"):
            cfg.deployment.openai_compat_model = m
        if ep := os.environ.get("OPENAI_COMPAT_BASE_URL"):
            cfg.deployment.openai_compat_endpoint = ep

        return cfg

    def model_kwargs(self) -> dict:
        """Return BaseAgent kwargs for the effective provider."""
        p = self.effective_model_provider
        if p == "anthropic":
            return {"provider": "anthropic", "model": self.deployment.anthropic_model}
        if p == "openrouter":
            return {"provider": "openrouter", "model": self.deployment.openrouter_model}
        if p == "huggingface":
            return {"provider": "huggingface", "model": self.deployment.huggingface_model}
        if p == "openai_compat":
            return {
                "provider": "openai_compat",
                "model": self.deployment.openai_compat_model,
                "openai_compat_endpoint": self.deployment.openai_compat_endpoint,
            }
        return {
            "provider": "ollama",
            "model": self.deployment.local_model,
            "ollama_endpoint": self.deployment.local_endpoint,
        }

    @property
    def effective_model_provider(self) -> str:
        if os.environ.get("OPENROUTER_API_KEY"):
            return "openrouter"
        if os.environ.get("ANTHROPIC_API_KEY"):
            return "anthropic"
        if os.environ.get("HF_TOKEN"):
            return "huggingface"
        return self.deployment.model_provider


def _find_config() -> Path | None:
    """Walk up from cwd looking for .crucible.yml."""
    current = Path.cwd()
    for parent in [current, *current.parents]:
        candidate = parent / ".crucible.yml"
        if candidate.exists():
            return candidate
    return None


DEFAULT_CONFIG_YAML = """\
version: 1

combat_pair:
  attack_count: 20
  rounds_max: 5
  cwe_rotation: true

policy:
  domains:
    - owasp_top10@2025.1

gate:
  minimum_ars: 0.80
  fail_open: false
  exempt_labels: [crucible-exempt, hotfix]

# ── Model provider (pick one) ────────────────────────────────────────────────
#
#  local       — Ollama, zero cost, air-gapped (default)
#  openrouter  — set OPENROUTER_API_KEY; free tier available
#  anthropic   — set ANTHROPIC_API_KEY
#  huggingface — set HF_TOKEN
#  openai_compat — any OpenAI-compatible endpoint (vLLM, Together AI, Groq, etc.)
#
# Env vars take precedence: OPENROUTER_API_KEY > ANTHROPIC_API_KEY > HF_TOKEN > config
# ─────────────────────────────────────────────────────────────────────────────
deployment:
  model_provider: local

  # Ollama (local)
  local_model: llama3.1:8b
  local_endpoint: http://localhost:11434

  # OpenRouter — free open-source models, zero-cost tier available
  # Best free models for adversarial security tasks:
  #   meta-llama/llama-3.3-70b-instruct:free    ← recommended (70B, reliable JSON/code)
  #   qwen/qwen3-coder:free                      ← code-specialized, great for CWE analysis
  #   nousresearch/hermes-3-llama-3.1-405b:free  ← most powerful free option (405B)
  #   openai/gpt-oss-120b:free                   ← 120B OSS model
  #   nvidia/nemotron-3-ultra-550b-a55b:free      ← largest free model available
  openrouter_model: meta-llama/llama-3.3-70b-instruct:free

  # Anthropic Claude
  anthropic_model: claude-haiku-4-5-20251001

  # HuggingFace Serverless Inference API (free tier)
  huggingface_model: meta-llama/Llama-3.1-70B-Instruct

  # Generic OpenAI-compatible (vLLM, Together AI, Groq, Azure OpenAI, etc.)
  # Set OPENAI_COMPAT_API_KEY and OPENAI_COMPAT_BASE_URL env vars
  openai_compat_endpoint: http://localhost:8000/v1
  openai_compat_model: llama3.1:8b

notifications:
  jira_project: ""
  slack_webhook: ""

retention_days: 365
community_brain: false
"""
