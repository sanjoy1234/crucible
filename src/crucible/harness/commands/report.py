"""Report command — programmatic API for rendering Resilience Reports."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class ReportResult:
    run_id: str
    format: str
    content: str
    path: str


def execute(
    run_id: str,
    fmt: str = "md",
    config_path: str | None = None,
) -> ReportResult:
    """
    Load and render a stored Resilience Report.

    Args:
        run_id: The run_id to render
        fmt: Output format — 'md', 'json', or 'html' (html = future)
        config_path: Path to .crucible.yml

    Returns:
        ReportResult with rendered content string
    """
    import json
    from crucible.config import CrucibleConfig
    from crucible.output.report import load_report, render_markdown

    cfg = CrucibleConfig.load(config_path)
    report = load_report(run_id, cfg.reports_dir)
    report_path = str(cfg.reports_dir / f"{run_id}.json")

    if fmt == "json":
        content = json.dumps(report, indent=2)
    elif fmt == "md":
        content = render_markdown(report)
    elif fmt == "html":
        md = render_markdown(report)
        content = f"<pre>{md}</pre>"
    else:
        raise ValueError(f"Unknown format: {fmt}. Use 'md', 'json', or 'html'.")

    return ReportResult(run_id=run_id, format=fmt, content=content, path=report_path)
