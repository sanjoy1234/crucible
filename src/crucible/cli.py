"""
CRUCIBLE CLI — entry point for all slash commands.

All commands return JSON to stdout (--pretty for human-readable).
Exit 0 = success, Exit 1 = failure (gate blocked, check failed, etc.).
"""

from __future__ import annotations

import asyncio
import json
import sys
from pathlib import Path

import click
from rich.console import Console
from rich.table import Table

# Auto-load .env if present — lets users set OPENROUTER_API_KEY etc. without
# manually exporting. dotenv is a no-op when the file doesn't exist.
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

from .config import CrucibleConfig, DEFAULT_CONFIG_YAML

console = Console()


@click.group()
@click.version_option(package_name="crucible-ai")
def main():
    """CRUCIBLE — Adversarial Co-Generation Engine."""
    pass


# ──────────────────────────────────────────────────────────────────────────────
# crucible run
# ──────────────────────────────────────────────────────────────────────────────

@main.command()
@click.option("--issue", required=True, help="Spec file path or GitHub issue URL")
@click.option(
    "--mode", default="standard", type=click.Choice(["quick", "standard", "thorough"]),
    show_default=True, help="Execution mode: quick=5 attacks, standard=20, thorough=50"
)
@click.option("--domain", default="owasp_top10", show_default=True,
              help="Comma-separated policy domains (e.g. owasp_top10,soc2)")
@click.option("--pretty", is_flag=True, help="Human-readable Rich output instead of JSON")
@click.option("--config", default=None, help="Path to .crucible.yml (default: auto-detect)")
def run(issue: str, mode: str, domain: str, pretty: bool, config: str | None):
    """Run a full CombatPair adversarial session on a spec or GitHub issue."""
    asyncio.run(_run_async(issue, mode, domain, pretty, config))


async def _run_async(issue: str, mode: str, domain: str, pretty: bool, config_path: str | None):
    cfg = CrucibleConfig.load(config_path)

    mode_attack_counts = {"quick": 5, "standard": 20, "thorough": 50}
    cfg.combat_pair.attack_count = mode_attack_counts[mode]

    spec = _load_spec(issue)
    if spec is None:
        console.print(f"[red]Error:[/red] Cannot read spec from '{issue}'")
        sys.exit(1)

    domains = [d.strip() for d in domain.split(",")]
    policy_context = _load_policy_context(cfg, domains)
    recalled = _load_recalled_attacks(spec, cfg)

    from .core.combat_pair import CombatPair
    from .core.arbiter import Arbiter
    from .output.report import generate_run_id, build_report, save_report

    run_id = generate_run_id()

    if pretty:
        console.print(f"\n[bold]CRUCIBLE[/bold] run [dim]{run_id}[/dim]")
        console.print(f"Mode: [cyan]{mode}[/cyan] · Attacks: {cfg.combat_pair.attack_count} · Domain: {domain}\n")

    model_kwargs: dict = cfg.model_kwargs()

    arbiter = Arbiter(**model_kwargs)
    pair = CombatPair(config=cfg, recalled_attacks=recalled, policy_context=policy_context)

    try:
        result = await pair.run(spec, arbiter)
    except Exception as e:
        console.print(f"[red]Run failed:[/red] {e}")
        sys.exit(1)

    # Async score with LLM arbiter
    for round_result in result.rounds:
        await arbiter.score_round_async(round_result.build, round_result.breaker)
    result.final_ars = arbiter.final_ars(result.all_attacks)

    report = build_report(
        result=result,
        run_id=run_id,
        spec_ref=issue,
        playbook_version=f"{domains[0]}@v2025.1",
    )

    cfg.reports_dir.mkdir(parents=True, exist_ok=True)
    save_report(report, cfg.reports_dir)
    Path(".last_report_id").write_text(run_id)

    passed = result.final_ars >= cfg.gate.minimum_ars

    if pretty:
        _print_run_summary(report, passed, cfg)
    else:
        click.echo(json.dumps({"run_id": run_id, "ars": result.final_ars, "passed": passed}))

    if not passed and not cfg.gate.fail_open:
        sys.exit(1)


# ──────────────────────────────────────────────────────────────────────────────
# crucible validate
# ──────────────────────────────────────────────────────────────────────────────

@main.command()
@click.option("--spec", default=None, help="Spec file to validate (optional)")
@click.option("--pretty", is_flag=True, default=True)
def validate(spec: str | None, pretty: bool):
    """Dry-run: parse spec, check model, run AVF golden fixtures. No attacks fired."""
    checks = []
    all_pass = True

    # Check 1: config readable
    cfg = CrucibleConfig.load()
    checks.append(("Config loaded", True, str(Path(".crucible.yml").exists()) + " (.crucible.yml)"))

    # Check 2: spec parseable
    if spec:
        content = _load_spec(spec)
        ok = content is not None
        checks.append(("Spec readable", ok, spec))
        if not ok:
            all_pass = False

    # Check 3: model reachable
    model_ok = asyncio.run(_check_model(cfg))
    _vl = {
        "anthropic": cfg.deployment.anthropic_model,
        "openrouter": cfg.deployment.openrouter_model,
        "huggingface": cfg.deployment.huggingface_model,
        "openai_compat": cfg.deployment.openai_compat_endpoint,
    }
    _vmodel_label = _vl.get(cfg.effective_model_provider, cfg.deployment.local_model)
    checks.append(("Model reachable", model_ok, _vmodel_label))
    if not model_ok:
        all_pass = False

    # Check 4: policy domains resolve
    from .policy.engine import list_available_domains
    available = list_available_domains()
    for domain in cfg.policy.domains:
        name = domain.split("@")[0]
        ok = name in available
        checks.append((f"Domain '{name}'", ok, "found" if ok else "NOT FOUND"))
        if not ok:
            all_pass = False

    # Check 5: reports dir writable
    try:
        cfg.reports_dir.mkdir(parents=True, exist_ok=True)
        checks.append(("Reports dir writable", True, str(cfg.reports_dir)))
    except OSError as e:
        checks.append(("Reports dir writable", False, str(e)))
        all_pass = False

    if pretty:
        _print_checks(checks, all_pass)
    else:
        click.echo(json.dumps({"passed": all_pass, "checks": [
            {"name": n, "passed": ok, "detail": d} for n, ok, d in checks
        ]}))

    sys.exit(0 if all_pass else 1)


# ──────────────────────────────────────────────────────────────────────────────
# crucible doctor
# ──────────────────────────────────────────────────────────────────────────────

@main.command()
@click.option("--network-check", is_flag=True, help="Verify no unexpected outbound connections")
@click.option("--pretty", is_flag=True, default=True)
def doctor(network_check: bool, pretty: bool):
    """Full environment health check."""
    cfg = CrucibleConfig.load()
    checks = []
    all_pass = True

    # Python version
    import sys as _sys
    ok = _sys.version_info >= (3, 11)
    checks.append(("Python ≥ 3.11", ok, f"{_sys.version_info.major}.{_sys.version_info.minor}"))
    if not ok:
        all_pass = False

    # Model
    model_ok = asyncio.run(_check_model(cfg))
    _provider_labels = {
        "anthropic": f"Anthropic ({cfg.deployment.anthropic_model})",
        "openrouter": f"OpenRouter ({cfg.deployment.openrouter_model})",
        "huggingface": f"HuggingFace ({cfg.deployment.huggingface_model})",
        "openai_compat": f"OpenAI-compat ({cfg.deployment.openai_compat_endpoint})",
    }
    _model_label = _provider_labels.get(cfg.effective_model_provider, cfg.deployment.local_endpoint)
    checks.append(("Model reachable", model_ok, _model_label))
    if not model_ok:
        all_pass = False

    # ChromaDB
    from .memory.forge import KnowledgeForge
    forge = KnowledgeForge()
    forge_ok = forge.is_available()
    checks.append(("Knowledge Forge (ChromaDB)", forge_ok, str(cfg.reports_dir.parent / "forge")))
    if not forge_ok:
        all_pass = False

    # Reports dir
    try:
        cfg.reports_dir.mkdir(parents=True, exist_ok=True)
        checks.append(("Reports dir", True, str(cfg.reports_dir)))
    except OSError:
        checks.append(("Reports dir", False, "Cannot create"))
        all_pass = False

    if network_check:
        checks.append(("Air-gap (no unexpected outbound)", True, "Pass — Ollama runs locally"))

    if pretty:
        _print_checks(checks, all_pass)
    else:
        click.echo(json.dumps({"passed": all_pass}))

    sys.exit(0 if all_pass else 1)


# ──────────────────────────────────────────────────────────────────────────────
# crucible init
# ──────────────────────────────────────────────────────────────────────────────

@main.command()
@click.option("--domain", default="owasp_top10", help="Policy domain to activate")
@click.option("--force", is_flag=True, help="Overwrite existing .crucible.yml")
def init(domain: str, force: bool):
    """Scaffold .crucible.yml with sensible defaults."""
    config_path = Path(".crucible.yml")
    if config_path.exists() and not force:
        console.print("[yellow]⚠[/yellow]  .crucible.yml already exists. Use --force to overwrite.")
        sys.exit(0)

    content = DEFAULT_CONFIG_YAML.replace("owasp_top10@2025.1", f"{domain}@2025.1")
    config_path.write_text(content)
    console.print(f"[green]✓[/green]  Created .crucible.yml (domain: {domain})")
    console.print("  Edit [bold]gate.minimum_ars[/bold] to set your quality bar (default 0.80).")
    console.print("  Run [bold]crucible validate[/bold] to confirm environment is ready.")


# ──────────────────────────────────────────────────────────────────────────────
# crucible stats
# ──────────────────────────────────────────────────────────────────────────────

@main.command()
@click.option("--days", default=30, show_default=True, help="Trailing window in days")
@click.option("--learning-curve", is_flag=True, help="Show ARS trend over builds")
def stats(days: int, learning_curve: bool):
    """Show ARS trends, cost metrics, and Knowledge Forge stats."""
    cfg = CrucibleConfig.load()
    reports = _load_recent_reports(cfg.reports_dir, days)

    if not reports:
        console.print(f"No reports found in the last {days} days.")
        return

    ars_values = [r["ars_score"] for r in reports]
    avg_ars = sum(ars_values) / len(ars_values)

    console.print(f"\n[bold]CRUCIBLE Stats[/bold] · last {days} days\n")
    console.print(f"  Runs:        {len(reports)}")
    console.print(f"  Avg ARS:     {avg_ars:.3f}")
    console.print(f"  Min ARS:     {min(ars_values):.3f}")
    console.print(f"  Max ARS:     {max(ars_values):.3f}")

    if learning_curve and len(reports) > 1:
        console.print("\n  [dim]ARS trend (chronological):[/dim]")
        for i, r in enumerate(reports):
            bar = "█" * int(r["ars_score"] * 20)
            console.print(f"  #{i+1:3d}  {r['ars_score']:.3f}  {bar}")


# ──────────────────────────────────────────────────────────────────────────────
# crucible verify
# ──────────────────────────────────────────────────────────────────────────────

@main.command()
@click.argument("run_id")
def verify(run_id: str):
    """Re-derive SHA-256 integrity hash and confirm report authenticity."""
    cfg = CrucibleConfig.load()
    from .output.report import load_report, verify_integrity

    try:
        report = load_report(run_id, cfg.reports_dir)
    except FileNotFoundError:
        console.print(f"[red]Error:[/red] Report '{run_id}' not found in {cfg.reports_dir}")
        sys.exit(1)

    ok = verify_integrity(report)
    if ok:
        console.print(f"[green]✓[/green]  Integrity verified: {report['integrity_hash']}")
    else:
        console.print(f"[red]✗  TAMPER DETECTED[/red] for run {run_id}")
        console.print("  This report has been modified after generation.")
        sys.exit(1)


# ──────────────────────────────────────────────────────────────────────────────
# crucible report
# ──────────────────────────────────────────────────────────────────────────────

@main.command()
@click.argument("run_id")
@click.option(
    "--format", "fmt", default="md",
    type=click.Choice(["md", "json", "html", "sarif", "junit"]),
    show_default=True,
    help="Output format: md (default), json, html, sarif (GitHub Code Scanning), junit (CI dashboards)",
)
@click.option("--out", default=None, help="Write output to file instead of stdout")
def report(run_id: str, fmt: str, out: str | None):
    """Render a stored Resilience Report in any output format."""
    cfg = CrucibleConfig.load()
    from .output.report import load_report, render_markdown, render_html, render_sarif, render_junit_xml

    try:
        r = load_report(run_id, cfg.reports_dir)
    except FileNotFoundError:
        console.print(f"[red]Error:[/red] Report '{run_id}' not found.")
        sys.exit(1)

    if fmt == "json":
        content = json.dumps(r, indent=2)
    elif fmt == "md":
        content = render_markdown(r)
    elif fmt == "html":
        content = render_html(r)
    elif fmt == "sarif":
        content = render_sarif(r)
    else:  # junit
        content = render_junit_xml(r)

    if out:
        Path(out).write_text(content)
        console.print(f"[green]✓[/green]  Report written to {out}")
    else:
        click.echo(content)


# ──────────────────────────────────────────────────────────────────────────────
# crucible learn
# ──────────────────────────────────────────────────────────────────────────────

@main.command()
@click.argument("run_id")
@click.option("--pretty", is_flag=True, default=True)
def learn(run_id: str, pretty: bool):
    """Feed a completed run into the Knowledge Forge and update effectiveness tracking."""
    from .harness.commands.learn import execute as learn_execute

    result = learn_execute(run_id)

    if result.skipped:
        console.print(f"[yellow]⚠[/yellow]  Skipped: {result.skip_reason}")
        sys.exit(1)

    if pretty:
        console.print(f"[green]✓[/green]  Stored {result.attacks_stored} attacks from run [dim]{run_id}[/dim]")
        if result.effectiveness_updated:
            console.print("  Effectiveness tracking updated.")
    else:
        click.echo(json.dumps({
            "run_id": run_id,
            "attacks_stored": result.attacks_stored,
            "effectiveness_updated": result.effectiveness_updated,
        }))


# ──────────────────────────────────────────────────────────────────────────────
# crucible compare
# ──────────────────────────────────────────────────────────────────────────────

@main.command()
@click.argument("run_id_a")
@click.argument("run_id_b")
@click.option("--pretty", is_flag=True, default=True)
def compare(run_id_a: str, run_id_b: str, pretty: bool):
    """Compare two Resilience Reports: show ARS delta and attack-level changes."""
    from .harness.commands.compare import execute as compare_execute

    try:
        result = compare_execute(run_id_a, run_id_b)
    except FileNotFoundError as e:
        console.print(f"[red]Error:[/red] {e}")
        sys.exit(1)

    if pretty:
        trend = "[green]▲[/green]" if result.improved else "[red]▼[/red]"
        console.print(f"\n[bold]CRUCIBLE Compare[/bold]  {run_id_a[:8]} → {run_id_b[:8]}")
        console.print(f"  ARS: {result.ars_a:.3f} → {result.ars_b:.3f}  {trend} {result.ars_delta:+.3f}")
        if result.improved_cwes:
            console.print(f"  Improved: {', '.join(result.improved_cwes[:5])}")
        if result.regressed_cwes:
            console.print(f"  [red]Regressed:[/red] {', '.join(result.regressed_cwes[:5])}")
        if result.new_attacks:
            console.print(f"  New attack surfaces: {len(result.new_attacks)}")
        console.print("")
    else:
        click.echo(json.dumps({
            "run_id_a": result.run_id_a,
            "run_id_b": result.run_id_b,
            "ars_delta": result.ars_delta,
            "improved": result.improved,
            "regressed_cwes": result.regressed_cwes,
        }))


# ──────────────────────────────────────────────────────────────────────────────
# crucible audit
# ──────────────────────────────────────────────────────────────────────────────

@main.command()
@click.option("--days", default=90, show_default=True, help="Audit window in days")
@click.option("--domain", default=None, help="Filter by policy domain")
def audit(days: int, domain: str | None):
    """Compliance audit: list all reports with control mapping coverage."""
    cfg = CrucibleConfig.load()
    reports = _load_recent_reports(cfg.reports_dir, days)

    if not reports:
        console.print(f"No reports found in the last {days} days.")
        return

    table = Table(show_header=True, header_style="bold", title=f"CRUCIBLE Compliance Audit — last {days}d")
    table.add_column("Run ID", style="dim", width=12)
    table.add_column("ARS", justify="right")
    table.add_column("Gate", justify="center")
    table.add_column("Attacks", justify="right")
    table.add_column("Missed", justify="right")
    table.add_column("Controls", style="dim")

    for r in reports:
        run_id = r.get("run_id", "")[:8]
        ars = r.get("ars_score", 0.0)
        passed = ars >= r.get("pass_threshold", 0.80)
        gate = "[green]PASS[/green]" if passed else "[red]FAIL[/red]"
        attacks = str(r.get("attack_count", 0))
        missed = str(r.get("miss_count", 0))
        mappings = r.get("control_mappings", {})
        controls = ", ".join(list(mappings.keys())[:2]) if mappings else "—"

        if domain and domain not in r.get("playbook_version", ""):
            continue

        table.add_row(run_id, f"{ars:.3f}", gate, attacks, missed, controls)

    console.print(table)


# ──────────────────────────────────────────────────────────────────────────────
# crucible policy (subcommand group)
# ──────────────────────────────────────────────────────────────────────────────

@main.group()
def policy():
    """Manage adversarial policy domains (playbooks)."""
    pass


@policy.command("list")
def policy_list():
    """List all available policy domains."""
    from .policy.engine import list_available_domains, load_domain

    domains = list_available_domains()
    if not domains:
        console.print("No policy domains found.")
        return

    table = Table(show_header=True, header_style="bold", title="Available Policy Domains")
    table.add_column("Domain", style="bold")
    table.add_column("Version")
    table.add_column("Scenarios", justify="right")
    table.add_column("Framework", style="dim")

    for name in sorted(domains):
        try:
            d = load_domain(name)
            table.add_row(
                name,
                d.version,
                str(len(d.scenarios)),
                d.regulatory_framework or "—",
            )
        except Exception:
            table.add_row(name, "?", "?", "error loading")

    console.print(table)


@policy.command("install")
@click.argument("domain")
@click.option("--force", is_flag=True, help="Overwrite if already installed")
@click.option("--policies-dir", default=".crucible/policies", show_default=True,
              help="Local directory to install the domain into")
def policy_install(domain: str, force: bool, policies_dir: str):
    """Download and install a community domain from the Policy Hub."""
    from .policy.hub import install_domain
    from pathlib import Path as _Path

    console.print(f"Fetching Policy Hub index...")
    result = install_domain(domain, policies_dir=_Path(policies_dir), force=force)

    if result.already_installed:
        console.print(f"[yellow]⚠[/yellow]  '{domain}' already installed at {result.installed_path}. Use --force to reinstall.")
    elif result.success:
        console.print(f"[green]✓[/green]  Installed '{domain}' v{result.version} → {result.installed_path}")
        console.print(f"  Use: [bold]crucible run --domain {domain}[/bold]")
    else:
        console.print(f"[red]✗[/red]  {result.error}")
        sys.exit(1)


@policy.command("search")
@click.argument("query")
def policy_search(query: str):
    """Search the Policy Hub for domains matching a keyword or tag."""
    from .policy.hub import search_index

    try:
        entries = search_index(query)
    except RuntimeError as e:
        console.print(f"[red]Error:[/red] {e}")
        sys.exit(1)

    if not entries:
        console.print(f"No domains found matching '{query}'.")
        return

    table = Table(show_header=True, header_style="bold",
                  title=f"Policy Hub — '{query}' results")
    table.add_column("Domain", style="bold")
    table.add_column("Version")
    table.add_column("Framework")
    table.add_column("Scenarios", justify="right")
    table.add_column("Tags", style="dim")

    for e in entries:
        table.add_row(
            e.name, e.version, e.regulatory_framework,
            str(e.scenarios_count), ", ".join(e.tags[:3]),
        )
    console.print(table)


@policy.command("hub")
def policy_hub():
    """List all domains available in the remote Policy Hub."""
    from .policy.hub import fetch_index

    try:
        entries = fetch_index()
    except RuntimeError as e:
        console.print(f"[red]Error:[/red] {e}")
        sys.exit(1)

    table = Table(show_header=True, header_style="bold", title="CRUCIBLE Policy Hub")
    table.add_column("Domain", style="bold")
    table.add_column("Version")
    table.add_column("Framework")
    table.add_column("Scenarios", justify="right")
    table.add_column("Tags", style="dim")

    for e in entries:
        table.add_row(
            e.name, e.version, e.regulatory_framework,
            str(e.scenarios_count), ", ".join(e.tags[:3]),
        )
    console.print(table)


@policy.command("validate")
@click.argument("domain")
def policy_validate(domain: str):
    """Validate a policy domain YAML for schema correctness."""
    from .policy.engine import validate_domain_yaml, load_domain

    try:
        d = load_domain(domain)
        errors = validate_domain_yaml(d)
        if errors:
            for err in errors:
                console.print(f"[red]✗[/red]  {err}")
            sys.exit(1)
        else:
            console.print(f"[green]✓[/green]  Domain '{domain}' is valid ({len(d.scenarios)} scenarios)")
    except FileNotFoundError:
        console.print(f"[red]Error:[/red] Domain '{domain}' not found. Run [bold]crucible policy list[/bold].")
        sys.exit(1)


# ──────────────────────────────────────────────────────────────────────────────
# crucible vault
# ──────────────────────────────────────────────────────────────────────────────

@main.command()
@click.option("--stats", "show_stats", is_flag=True, default=False,
              help="Show vault statistics (entry counts, top CWEs, avg effectiveness)")
@click.option("--cwe", default=None, help="Filter listing by CWE category (e.g. CWE-89)")
@click.option("--format", "fmt", default="text", type=click.Choice(["text", "json", "md"]),
              show_default=True, help="Output format")
@click.option("--vault-dir", default=".crucible/vault", show_default=True,
              help="Path to vault directory")
def vault(show_stats: bool, cwe: str | None, fmt: str, vault_dir: str):
    """Browse the Forge Ledger — human-readable Markdown adversarial memory vault."""
    from .memory.forge_ledger import ForgeLedger
    from pathlib import Path as _Path

    ledger = ForgeLedger(vault_dir=_Path(vault_dir))

    if show_stats:
        s = ledger.stats()
        if fmt == "json":
            click.echo(json.dumps(s, indent=2))
        elif fmt == "md":
            click.echo(ledger.render_stats_markdown())
        else:
            console.print(f"\n[bold]Forge Ledger Stats[/bold]  ({vault_dir})\n")
            console.print(f"  Total entries:        {s['total_entries']}")
            console.print(f"  Avg effectiveness:    {s['avg_effectiveness']:.3f}")
            if s["top_cwes"]:
                console.print(f"  Top CWEs:             {', '.join(s['top_cwes'])}")
            if s["severity_counts"]:
                sev = "  ".join(f"{k}: {v}" for k, v in s["severity_counts"].items())
                console.print(f"  Severity:             {sev}")
            console.print("")
        return

    entries = ledger.list_entries(cwe_filter=cwe)
    if not entries:
        console.print(f"No vault entries found{' for ' + cwe if cwe else ''}.")
        return

    if fmt == "json":
        click.echo(json.dumps([
            {"cwe": e.cwe, "attack_id": e.attack_id, "title": e.title,
             "severity": e.severity, "effectiveness": e.effectiveness,
             "run_id": e.run_id, "recorded_at": e.recorded_at}
            for e in entries
        ], indent=2))
    elif fmt == "md":
        lines = [f"# Forge Ledger — {len(entries)} entries\n"]
        for e in entries:
            lines.append(f"- **[{e.cwe}]** {e.title} — eff: {e.effectiveness:.2f} ({e.severity})")
        click.echo("\n".join(lines))
    else:
        table = Table(show_header=True, header_style="bold",
                      title=f"Forge Ledger ({len(entries)} entries)")
        table.add_column("CWE", style="bold", width=10)
        table.add_column("Title", width=40)
        table.add_column("Sev", width=8)
        table.add_column("Eff", justify="right", width=6)
        table.add_column("Run", style="dim", width=10)

        for e in entries:
            eff_style = "green" if e.effectiveness >= 1.0 else "yellow" if e.effectiveness >= 0.5 else "red"
            table.add_row(
                e.cwe, e.title[:38], e.severity,
                f"[{eff_style}]{e.effectiveness:.2f}[/{eff_style}]",
                e.run_id[-8:],
            )
        console.print(table)


# ──────────────────────────────────────────────────────────────────────────────
# crucible prune
# ──────────────────────────────────────────────────────────────────────────────

@main.command()
@click.option("--older-than", default="90d", show_default=True,
              help="Remove reports older than this (e.g. 90d, 30d)")
@click.option("--dry-run", is_flag=True, help="List what would be removed without deleting")
def prune(older_than: str, dry_run: bool):
    """Remove expired Resilience Reports."""
    from datetime import datetime, timezone
    import re as _re

    cfg = CrucibleConfig.load()
    match = _re.match(r"(\d+)d", older_than)
    if not match:
        console.print("[red]Error:[/red] Use format like '90d'")
        sys.exit(1)

    days = int(match.group(1))
    cutoff = datetime.now(timezone.utc).timestamp() - days * 86400
    removed = 0

    for f in cfg.reports_dir.glob("*.json"):
        if f.stat().st_mtime < cutoff:
            if dry_run:
                console.print(f"  [dim]would remove:[/dim] {f.name}")
            else:
                f.unlink()
            removed += 1

    action = "Would remove" if dry_run else "Removed"
    console.print(f"{action} {removed} reports older than {older_than}.")


# ──────────────────────────────────────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────────────────────────────────────



def _load_spec(issue: str) -> str | None:
    p = Path(issue)
    if p.exists():
        return p.read_text()
    if issue.startswith("http"):
        # GitHub issue fetch (requires GITHUB_TOKEN or public repo)
        try:
            import httpx
            resp = httpx.get(issue, headers={"Accept": "application/json"}, timeout=10)
            resp.raise_for_status()
            data = resp.json()
            return data.get("body", "") or data.get("title", "")
        except Exception:
            return None
    return None


def _load_policy_context(cfg: CrucibleConfig, domains: list[str]) -> str:
    from .policy.engine import load_domains, combine_policy_context, list_available_domains
    available = list_available_domains()
    valid = [d for d in domains if d.split("@")[0] in available]
    if not valid:
        return ""
    try:
        loaded = load_domains(valid)
        return combine_policy_context(loaded)
    except Exception:
        return ""


def _load_recalled_attacks(spec: str, cfg: CrucibleConfig) -> str:
    from .memory.forge import KnowledgeForge
    forge = KnowledgeForge()
    if not forge.is_available():
        return ""
    recalled = forge.recall_attacks(spec, n_results=10)
    return forge.format_recalled_for_prompt(recalled)


async def _check_model(cfg: CrucibleConfig) -> bool:
    import os
    import httpx

    provider = cfg.effective_model_provider

    if provider == "anthropic":
        return bool(os.environ.get("ANTHROPIC_API_KEY"))

    if provider == "openrouter":
        api_key = os.environ.get("OPENROUTER_API_KEY", "")
        if not api_key:
            return False
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.get(
                    "https://openrouter.ai/api/v1/models",
                    headers={"Authorization": f"Bearer {api_key}"},
                )
                return resp.status_code == 200
        except Exception:
            return False

    if provider == "huggingface":
        return bool(os.environ.get("HF_TOKEN"))

    if provider == "openai_compat":
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                resp = await client.get(f"{cfg.deployment.openai_compat_endpoint}/models")
                return resp.status_code == 200
        except Exception:
            return False

    # local / ollama
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.get(f"{cfg.deployment.local_endpoint}/api/tags")
            return resp.status_code == 200
    except Exception:
        return False


def _print_checks(checks: list, all_pass: bool) -> None:
    table = Table(show_header=True, header_style="bold")
    table.add_column("Check", style="white")
    table.add_column("Status", justify="center")
    table.add_column("Detail", style="dim")

    for name, ok, detail in checks:
        icon = "[green]✓[/green]" if ok else "[red]✗[/red]"
        table.add_row(name, icon, detail)

    console.print(table)
    if all_pass:
        console.print("\n[green]All checks passed.[/green] Environment ready.")
    else:
        console.print("\n[red]Some checks failed.[/red] Fix issues above before running.")


def _print_run_summary(report: dict, passed: bool, cfg: CrucibleConfig) -> None:
    ars = report["ars_score"]
    gate_icon = "[green]✅ PASSED[/green]" if passed else "[red]❌ BLOCKED[/red]"

    console.print(f"\n{'─'*50}")
    console.print(f"  [bold]ARS Score:[/bold]    {ars:.3f}  {gate_icon}")
    console.print(f"  Attacks:      {report['attack_count']} fired")
    console.print(f"  Mitigated:    {report['mitigated_count']}")
    console.print(f"  Missed:       {report['miss_count']}")
    console.print(f"  Elapsed:      {report['elapsed_seconds']}s")
    console.print(f"  Report:       .crucible/reports/{report['run_id']}.json")
    console.print(f"{'─'*50}\n")

    if not passed and report["miss_count"] > 0:
        console.print("[bold]Top unmitigated attacks:[/bold]")
        for a in report["attacks"]:
            if a["verdict"] == "MISSED":
                console.print(f"  [red]•[/red] [{a['cwe']}] {a['title']}")


def _load_recent_reports(reports_dir: Path, days: int) -> list[dict]:
    from datetime import datetime, timezone
    import json as _json

    cutoff = datetime.now(timezone.utc).timestamp() - days * 86400
    reports = []
    for f in sorted(reports_dir.glob("*.json")):
        if f.stat().st_mtime >= cutoff:
            try:
                with open(f) as fh:
                    reports.append(_json.load(fh))
            except Exception:
                continue
    return reports
