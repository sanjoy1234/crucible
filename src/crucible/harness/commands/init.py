"""Init command — scaffold .crucible.yml with sensible defaults."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass
class InitResult:
    path: str
    created: bool
    skipped: bool = False
    skip_reason: str = ""


def execute(domain: str = "owasp_top10", force: bool = False) -> InitResult:
    """
    Scaffold .crucible.yml with sensible defaults for the given domain.

    Args:
        domain: Policy domain to activate (default: owasp_top10)
        force: Overwrite existing .crucible.yml

    Returns:
        InitResult indicating if file was created or skipped
    """
    from crucible.config import DEFAULT_CONFIG_YAML

    config_path = Path(".crucible.yml")
    if config_path.exists() and not force:
        return InitResult(
            path=str(config_path),
            created=False,
            skipped=True,
            skip_reason="File already exists. Use force=True to overwrite.",
        )

    content = DEFAULT_CONFIG_YAML.replace("owasp_top10@2025.1", f"{domain}@2025.1")
    config_path.write_text(content)
    return InitResult(path=str(config_path), created=True)
