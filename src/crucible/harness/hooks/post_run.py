"""post_run hook — fired once after all CombatPair rounds complete."""

from __future__ import annotations

from ..runner import RunContext


def emit_report(ctx: RunContext) -> None:
    """
    Build and save the Resilience Report after a completed run.

    Writes JSON to .crucible/reports/<run_id>.json.
    Stores path in ctx.metadata["report_path"].
    """
    if ctx.result is None:
        return

    from pathlib import Path
    from ...output.report import build_report, save_report

    report = build_report(
        result=ctx.result,
        run_id=ctx.run_id,
        spec_ref=ctx.metadata.get("spec_ref", ""),
        commit_sha=ctx.metadata.get("commit_sha", ""),
        playbook_version=ctx.metadata.get("playbook_version", "owasp_top10@v2025.1"),
    )

    reports_dir = ctx.config.reports_dir
    path = save_report(report, reports_dir)
    ctx.metadata["report_path"] = str(path)
    ctx.metadata["report"] = report
