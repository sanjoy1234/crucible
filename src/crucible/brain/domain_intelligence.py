"""
Domain Intelligence Adapter (DIA) — MCP consumer for live threat intelligence.

CRUCIBLE is NOT an MCP server (incompatible 60-90s runtime with MCP's sub-second
contract). Instead, DIA CONSUMES external MCP servers that provide real-time:
  - Financial threat intel (active CVEs in banking software)
  - Regulatory guidance (current FINRA/SEC enforcement priorities)
  - Vulnerability feeds (NVD enriched with domain context)

DIA is configured under mcp_servers: in .crucible.yml.
Each MCP server is called pre_run, and its response enriches the Breaker's
policy context with live threat data for the current run.

If an MCP server is unreachable, DIA fails silently — the run continues
with the standard playbook context.
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from typing import Any

logger = logging.getLogger(__name__)

_REQUEST_TIMEOUT = 10.0


@dataclass
class McpServerConfig:
    name: str
    url: str
    tool: str            # MCP tool name to invoke
    params: dict = field(default_factory=dict)
    enabled: bool = True


@dataclass
class DiaResult:
    server: str
    tool: str
    enrichment: str    # formatted text appended to Breaker policy context
    raw_response: Any = None
    error: str = ""

    @property
    def success(self) -> bool:
        return not self.error


def call_mcp_tool(server: McpServerConfig) -> DiaResult:
    """
    Call a single MCP server tool and return enrichment text.

    The MCP JSON-RPC protocol:
      POST /mcp
      {"jsonrpc": "2.0", "id": 1, "method": "tools/call",
       "params": {"name": <tool>, "arguments": <params>}}
    """
    if not server.enabled:
        return DiaResult(server=server.name, tool=server.tool,
                         enrichment="", error="disabled")

    payload = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "tools/call",
        "params": {
            "name": server.tool,
            "arguments": server.params,
        },
    }

    try:
        import httpx
        resp = httpx.post(
            server.url,
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=_REQUEST_TIMEOUT,
        )
        resp.raise_for_status()
        data = resp.json()
    except Exception as e:
        msg = str(e)
        logger.debug("DIA: MCP server '%s' unreachable: %s", server.name, msg)
        return DiaResult(server=server.name, tool=server.tool, enrichment="", error=msg)

    if "error" in data:
        err = data["error"].get("message", "MCP error")
        return DiaResult(server=server.name, tool=server.tool, enrichment="", error=err)

    raw = data.get("result", {})
    enrichment = _format_mcp_result(server.name, server.tool, raw)
    return DiaResult(server=server.name, tool=server.tool, enrichment=enrichment, raw_response=raw)


def _format_mcp_result(server: str, tool: str, result: Any) -> str:
    """Convert an MCP tool result into a Breaker policy context addition."""
    if isinstance(result, str):
        content = result
    elif isinstance(result, dict):
        # MCP content array format
        if "content" in result:
            parts = result["content"]
            content = "\n".join(
                p.get("text", "") for p in parts
                if isinstance(p, dict) and p.get("type") == "text"
            )
        else:
            content = json.dumps(result, indent=2)
    else:
        content = str(result)

    if not content.strip():
        return ""

    return (
        f"\n--- Live threat intelligence from '{server}' ({tool}) ---\n"
        f"{content[:2000]}\n"
        f"--- End DIA enrichment ---\n"
    )


class DomainIntelligenceAdapter:
    """
    Orchestrates MCP server calls and combines enrichment into policy context.

    Usage (called by pre_run hook or run.py):
        dia = DomainIntelligenceAdapter(servers)
        enriched_context = dia.enrich(base_policy_context)
    """

    def __init__(self, servers: list[McpServerConfig]):
        self._servers = servers

    @classmethod
    def from_config(cls, config: "CrucibleConfig") -> "DomainIntelligenceAdapter":  # noqa: F821
        """Build DIA from the mcp_servers block in .crucible.yml."""
        from ..config import CrucibleConfig
        raw_servers = getattr(config, "mcp_servers", [])
        servers = [
            McpServerConfig(
                name=s.get("name", "unknown"),
                url=s.get("url", ""),
                tool=s.get("tool", ""),
                params=s.get("params", {}),
                enabled=s.get("enabled", True),
            )
            for s in (raw_servers or [])
            if s.get("url") and s.get("tool")
        ]
        return cls(servers)

    def enrich(self, base_context: str) -> tuple[str, list[DiaResult]]:
        """
        Call all configured MCP servers and append enrichment to base_context.

        Returns:
            (enriched_context, list_of_dia_results)
        """
        if not self._servers:
            return base_context, []

        results: list[DiaResult] = []
        enrichments: list[str] = []

        for server in self._servers:
            result = call_mcp_tool(server)
            results.append(result)
            if result.success and result.enrichment:
                enrichments.append(result.enrichment)
                logger.debug("DIA: enriched from '%s' (%d chars)", server.name, len(result.enrichment))

        if not enrichments:
            return base_context, results

        combined = base_context
        if combined:
            combined += "\n\n"
        combined += "\n".join(enrichments)
        return combined, results

    def available_servers(self) -> list[str]:
        return [s.name for s in self._servers if s.enabled]


def parse_mcp_servers_from_yaml(raw: list[dict]) -> list[McpServerConfig]:
    """Parse the mcp_servers YAML block into McpServerConfig objects."""
    return [
        McpServerConfig(
            name=s.get("name", f"server-{i}"),
            url=s.get("url", ""),
            tool=s.get("tool", ""),
            params=s.get("params", {}),
            enabled=s.get("enabled", True),
        )
        for i, s in enumerate(raw or [])
    ]
