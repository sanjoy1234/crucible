---
name: crucible:run
description: Run a full CRUCIBLE adversarial session on a spec file or GitHub issue URL. Invokes the CombatPair (Builder + Breaker concurrent) and outputs an Adversarial Resilience Score (ARS) with a Resilience Report.
---

# /crucible:run

Runs a full CombatPair session on a specification or GitHub issue.

## Usage

```
/crucible:run [--issue <url|file>] [--mode quick|standard|thorough] [--domain owasp_top10]
```

## Execution

This skill invokes the installed `crucible` CLI. Run:

```bash
crucible run --issue "$ISSUE" --mode "$MODE" --domain "$DOMAIN"
```

Where:
- `$ISSUE` = the spec file path or GitHub issue URL from the user's message
- `$MODE` = `quick` (default, 5 attacks, <90s), `standard` (20 attacks), `thorough` (50 attacks)
- `$DOMAIN` = policy domain (default `owasp_top10`)

## What It Does

1. Loads `.crucible.yml` from the current working directory (or defaults if not present)
2. Runs Builder and Breaker concurrently via `asyncio.gather()`
3. Arbiter scores each attack: 1.0 (mitigated) / 0.5 (partial) / 0.0 (miss)
4. Emits Resilience Report JSON + Markdown to `.crucible/reports/<run_id>.json`
5. Returns ARS score and a table of attacks

## Output to User

After running, report:
- ARS score (e.g., `ARS: 0.87`)
- Number of attacks attempted and how many were mitigated
- Top 3 unmitigated attacks (if any)
- Report saved to `.crucible/reports/<run_id>.json`
- Whether the gate passed or failed (vs `minimum_ars` in `.crucible.yml`)

## Checking prerequisites

Before running, verify:
1. `crucible doctor` passes (model reachable, ChromaDB writable)
2. `.crucible.yml` exists or inform user defaults will be used

If `crucible` is not installed: `pip install -e <project_root>` or `pip install crucible-ai`
