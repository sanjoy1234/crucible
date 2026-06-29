"""
Combat Dashboard — FastAPI web UI for CRUCIBLE.

Optional install: pip install crucible-ai[ui]
Launch:           crucible dashboard --port 8080

Features:
  - ARS trend chart over recent runs
  - Per-run attack breakdown with verdict colors
  - Compliance evidence download (JSON, SARIF, HTML)
  - Forge Ledger vault browser
  - Bright/light theme throughout (#FAFAFA background)
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

# Guard against FastAPI/Uvicorn not being installed
try:
    from fastapi import FastAPI, HTTPException, Request
    from fastapi.responses import HTMLResponse, JSONResponse, Response
    _FASTAPI_AVAILABLE = True
except ImportError:
    _FASTAPI_AVAILABLE = False
    FastAPI = None  # type: ignore

from ..config import CrucibleConfig
from ..output.report import load_report, render_html, render_sarif, render_junit_xml


def _require_fastapi():
    if not _FASTAPI_AVAILABLE:
        raise RuntimeError(
            "Combat Dashboard requires FastAPI and Uvicorn. "
            "Install with: pip install crucible-ai[ui]"
        )


def create_app(config: CrucibleConfig | None = None) -> "FastAPI":
    _require_fastapi()

    cfg = config or CrucibleConfig.load()
    app = FastAPI(title="CRUCIBLE Combat Dashboard", version="0.1.0")

    @app.get("/", response_class=HTMLResponse)
    async def index():
        reports = _load_all_reports(cfg.reports_dir)
        return HTMLResponse(_render_index(reports, cfg))

    @app.get("/api/runs")
    async def list_runs():
        reports = _load_all_reports(cfg.reports_dir)
        return JSONResponse([
            {
                "run_id": r["run_id"],
                "ars_score": r["ars_score"],
                "attack_count": r["attack_count"],
                "miss_count": r["miss_count"],
                "generated_at": r.get("generated_at", ""),
                "passed": r["ars_score"] >= cfg.gate.minimum_ars,
            }
            for r in reports
        ])

    @app.get("/api/runs/{run_id}")
    async def get_run(run_id: str):
        try:
            report = load_report(run_id, cfg.reports_dir)
        except FileNotFoundError:
            raise HTTPException(status_code=404, detail=f"Run '{run_id}' not found")
        return JSONResponse(report)

    @app.get("/api/runs/{run_id}/html")
    async def download_html(run_id: str):
        try:
            report = load_report(run_id, cfg.reports_dir)
        except FileNotFoundError:
            raise HTTPException(status_code=404, detail=f"Run '{run_id}' not found")
        content = render_html(report)
        return Response(
            content=content,
            media_type="text/html",
            headers={"Content-Disposition": f'attachment; filename="{run_id}.html"'},
        )

    @app.get("/api/runs/{run_id}/sarif")
    async def download_sarif(run_id: str):
        try:
            report = load_report(run_id, cfg.reports_dir)
        except FileNotFoundError:
            raise HTTPException(status_code=404, detail=f"Run '{run_id}' not found")
        content = render_sarif(report)
        return Response(
            content=content,
            media_type="application/json",
            headers={"Content-Disposition": f'attachment; filename="{run_id}.sarif"'},
        )

    @app.get("/api/runs/{run_id}/junit")
    async def download_junit(run_id: str):
        try:
            report = load_report(run_id, cfg.reports_dir)
        except FileNotFoundError:
            raise HTTPException(status_code=404, detail=f"Run '{run_id}' not found")
        content = render_junit_xml(report)
        return Response(
            content=content,
            media_type="application/xml",
            headers={"Content-Disposition": f'attachment; filename="{run_id}.xml"'},
        )

    @app.get("/api/vault/stats")
    async def vault_stats():
        from ..memory.forge_ledger import ForgeLedger
        ledger = ForgeLedger()
        return JSONResponse(ledger.stats())

    @app.get("/health")
    async def health():
        return {"status": "ok", "service": "crucible-dashboard"}

    # ── MCP HTTP endpoint (JSON-RPC 2.0) ──────────────────────────────────────
    # Serves CRUCIBLE as an MCP server over HTTP for team/enterprise deployment.
    # Individual developers use stdio transport (`crucible mcp-server`).
    # Team deploy: `crucible serve` exposes POST /mcp alongside the dashboard.
    #
    # Client config (HTTP transport):
    #   { "crucible": { "url": "http://your-server:8080/mcp" } }

    from ..mcp.server import MCPServer as _MCPServer

    _mcp_server = _MCPServer(config=cfg)

    @app.post("/mcp")
    async def mcp_endpoint(request: Request):
        try:
            body = await request.json()
        except Exception:
            return JSONResponse(
                {"jsonrpc": "2.0", "id": None, "error": {"code": -32700, "message": "Parse error"}},
                status_code=400,
            )
        response = await _mcp_server.handle_http_request(body)
        return JSONResponse(response)

    @app.get("/mcp/tools")
    async def mcp_tools_list():
        """Convenience GET — returns the tool list without a JSON-RPC envelope."""
        response = await _mcp_server.handle_message({
            "jsonrpc": "2.0", "id": 1, "method": "tools/list", "params": {},
        })
        return JSONResponse(response.get("result", {}).get("tools", []))

    return app


def _load_all_reports(reports_dir: Path, limit: int = 100) -> list[dict]:
    if not reports_dir.exists():
        return []
    reports = []
    for f in sorted(reports_dir.glob("*.json"), key=lambda p: p.stat().st_mtime, reverse=True):
        try:
            with open(f) as fh:
                reports.append(json.load(fh))
        except Exception:
            continue
        if len(reports) >= limit:
            break
    return reports


def _render_index(reports: list[dict], cfg: CrucibleConfig) -> str:
    """Render the main dashboard HTML page."""
    gate_threshold = cfg.gate.minimum_ars

    # Build summary stats
    total = len(reports)
    passed = sum(1 for r in reports if r["ars_score"] >= gate_threshold)
    avg_ars = sum(r["ars_score"] for r in reports) / total if total else 0.0

    # ARS sparkline data (last 20 runs, chronological)
    chart_data = [{"x": i + 1, "y": round(r["ars_score"], 3)}
                  for i, r in enumerate(reversed(reports[:20]))]
    chart_json = json.dumps(chart_data)

    # Build run rows
    rows = ""
    for r in reports[:50]:
        ars = r["ars_score"]
        passed_run = ars >= gate_threshold
        gate_class = "pass" if passed_run else "fail"
        gate_label = "PASS" if passed_run else "FAIL"
        run_id = r["run_id"]
        short_id = run_id[-16:]
        gen_at = r.get("generated_at", "")[:16].replace("T", " ")
        rows += f"""
        <tr>
          <td><code class="run-id">{short_id}</code></td>
          <td><strong class="ars-val {'ars-pass' if passed_run else 'ars-fail'}">{ars:.3f}</strong></td>
          <td><span class="gate-badge {gate_class}">{gate_label}</span></td>
          <td>{r.get('attack_count', 0)}</td>
          <td class="miss-count">{r.get('miss_count', 0)}</td>
          <td class="ts">{gen_at}</td>
          <td class="actions">
            <a href="/api/runs/{run_id}/html" class="btn-dl">HTML</a>
            <a href="/api/runs/{run_id}/sarif" class="btn-dl">SARIF</a>
            <a href="/api/runs/{run_id}/junit" class="btn-dl">JUnit</a>
          </td>
        </tr>"""

    empty_msg = "" if reports else '<p class="empty">No runs yet. Run <code>crucible run --issue ...</code> to start.</p>'

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>CRUCIBLE Combat Dashboard</title>
<style>
  *{{box-sizing:border-box;margin:0;padding:0}}
  body{{font-family:system-ui,-apple-system,sans-serif;background:#F8FAFC;color:#111827;min-height:100vh}}
  header{{background:#fff;border-bottom:1px solid #E5E7EB;padding:16px 32px;display:flex;align-items:center;gap:16px}}
  header h1{{font-size:18px;font-weight:700;color:#111827}}
  header .badge{{background:#DBEAFE;color:#1E40AF;padding:3px 10px;border-radius:12px;font-size:12px;font-weight:600}}
  .main{{padding:32px;max-width:1200px;margin:0 auto}}
  .stat-row{{display:flex;gap:16px;margin-bottom:28px}}
  .stat{{background:#fff;border:1px solid #E5E7EB;border-radius:8px;padding:20px 24px;flex:1}}
  .stat .label{{font-size:11px;font-weight:600;text-transform:uppercase;letter-spacing:.08em;color:#6B7280;margin-bottom:6px}}
  .stat .value{{font-size:32px;font-weight:800;color:#111827;line-height:1}}
  .stat .value.green{{color:#047857}}
  .stat .value.red{{color:#B91C1C}}
  .section{{background:#fff;border:1px solid #E5E7EB;border-radius:8px;margin-bottom:24px;overflow:hidden}}
  .section-header{{padding:16px 20px;border-bottom:1px solid #F3F4F6;font-size:14px;font-weight:700;color:#374151}}
  .chart-area{{padding:20px;height:120px;position:relative}}
  svg.sparkline{{width:100%;height:100%}}
  table{{width:100%;border-collapse:collapse;font-size:13px}}
  th{{background:#F9FAFB;padding:10px 16px;text-align:left;font-size:11px;font-weight:600;text-transform:uppercase;letter-spacing:.06em;color:#6B7280;border-bottom:1px solid #E5E7EB}}
  td{{padding:10px 16px;border-bottom:1px solid #F9FAFB}}
  tr:last-child td{{border-bottom:none}}
  tr:hover td{{background:#F9FAFB}}
  code.run-id{{font-size:11px;font-family:monospace;color:#374151}}
  .ars-val{{font-weight:700}}
  .ars-pass{{color:#047857}}
  .ars-fail{{color:#B91C1C}}
  .gate-badge{{padding:3px 10px;border-radius:12px;font-size:11px;font-weight:700}}
  .gate-badge.pass{{background:#D1FAE5;color:#065F46}}
  .gate-badge.fail{{background:#FEE2E2;color:#991B1B}}
  .miss-count{{color:#B91C1C;font-weight:600}}
  .ts{{color:#9CA3AF;font-size:12px}}
  .actions{{display:flex;gap:6px}}
  .btn-dl{{text-decoration:none;background:#EFF6FF;color:#1D4ED8;padding:3px 9px;border-radius:4px;font-size:11px;font-weight:600}}
  .btn-dl:hover{{background:#DBEAFE}}
  .empty{{padding:32px;text-align:center;color:#9CA3AF}}
  footer{{margin-top:48px;padding:16px 32px;border-top:1px solid #E5E7EB;font-size:12px;color:#9CA3AF;text-align:center}}
</style>
</head>
<body>
<header>
  <h1>⚔️ CRUCIBLE Combat Dashboard</h1>
  <span class="badge">ARS Gate: {gate_threshold:.2f}</span>
</header>

<div class="main">
  <div class="stat-row">
    <div class="stat">
      <div class="label">Total Runs</div>
      <div class="value">{total}</div>
    </div>
    <div class="stat">
      <div class="label">Gate Passed</div>
      <div class="value green">{passed}</div>
    </div>
    <div class="stat">
      <div class="label">Gate Failed</div>
      <div class="value red">{total - passed}</div>
    </div>
    <div class="stat">
      <div class="label">Avg ARS</div>
      <div class="value {'green' if avg_ars >= gate_threshold else 'red'}">{avg_ars:.3f}</div>
    </div>
  </div>

  <div class="section">
    <div class="section-header">ARS Trend — Last {min(20, total)} Runs</div>
    <div class="chart-area" id="chart-area">
      <svg class="sparkline" id="sparkline" viewBox="0 0 800 100" preserveAspectRatio="none">
        <line x1="0" y1="{int((1 - gate_threshold) * 100)}" x2="800" y2="{int((1 - gate_threshold) * 100)}"
              stroke="#FCA5A5" stroke-width="1" stroke-dasharray="4,4"/>
      </svg>
    </div>
  </div>

  <div class="section">
    <div class="section-header">Runs ({total})</div>
    {empty_msg}
    {'<table><thead><tr><th>Run ID</th><th>ARS</th><th>Gate</th><th>Attacks</th><th>Missed</th><th>Generated</th><th>Download</th></tr></thead><tbody>' + rows + '</tbody></table>' if reports else ''}
  </div>
</div>

<footer>CRUCIBLE Adversarial Co-Generation Engine · Built by Sanjoy Ghosh</footer>

<script>
(function() {{
  var data = {chart_json};
  if (!data.length) return;
  var svg = document.getElementById('sparkline');
  var n = data.length;
  var maxY = 1.0, minY = 0.0;
  var pts = data.map(function(d, i) {{
    var x = (i / Math.max(n - 1, 1)) * 800;
    var y = (1 - d.y) * 100;
    return x + ',' + y;
  }});
  var poly = document.createElementNS('http://www.w3.org/2000/svg', 'polyline');
  poly.setAttribute('points', pts.join(' '));
  poly.setAttribute('fill', 'none');
  poly.setAttribute('stroke', '#3B82F6');
  poly.setAttribute('stroke-width', '2.5');
  poly.setAttribute('stroke-linejoin', 'round');
  svg.appendChild(poly);
  data.forEach(function(d, i) {{
    var x = (i / Math.max(n - 1, 1)) * 800;
    var y = (1 - d.y) * 100;
    var c = document.createElementNS('http://www.w3.org/2000/svg', 'circle');
    c.setAttribute('cx', x); c.setAttribute('cy', y); c.setAttribute('r', '3');
    c.setAttribute('fill', d.y >= {gate_threshold} ? '#047857' : '#B91C1C');
    svg.appendChild(c);
  }});
}})();
</script>
</body>
</html>"""
