<div align="center">

# ⚔️ CRUCIBLE

### Adversarial Co-Generation Engine

**The only system that attacks AI-generated code while it is being written.**

[![Tests](https://img.shields.io/badge/tests-342%20passing-brightgreen)](https://github.com/sanjoy1234/crucible/actions)
[![Python](https://img.shields.io/badge/python-3.11%2B-blue)](https://pypi.org/project/crucible-ai/)
[![PyPI](https://img.shields.io/pypi/v/crucible-ai)](https://pypi.org/project/crucible-ai/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![SARIF 2.1](https://img.shields.io/badge/output-SARIF%202.1%20%7C%20JUnit%20%7C%20HTML-informational)](https://github.com/sanjoy1234/crucible)
[![NIST SSDF](https://img.shields.io/badge/compliance-NIST%20SSDF%20%7C%20OWASP%20%7C%20HIPAA%20%7C%20FINRA-orange)](https://github.com/sanjoy1234/crucible)

[**Quickstart**](#-five-minute-quickstart-zero-cost) · [**How It Works**](#-how-crucible-works) · [**Enterprise**](#-enterprise-features) · [**CLI Reference**](#-complete-cli-reference) · [**Compliance**](#-compliance--regulatory-domains) · [**Contributing**](#-contributing)

---

*"Every team is shipping AI-generated code. Almost no one is adversarially testing it."*

</div>

---

## The Problem That Started This

It is 2026. Your engineering team uses AI coding assistants every day. Features ship faster than they ever have. The code passes CI. PRs get approved. Everything looks fine.

Then your security team runs a penetration test and finds SQL injection in the login endpoint — code that was generated in an afternoon sprint, reviewed in twenty minutes, and merged without anyone asking: *what would an attacker do with this?*

Or your compliance team receives a HIPAA audit notice. An AI-generated API endpoint is returning PHI in error messages. The code never had a human author who would have thought to apply output encoding. The AI followed the spec. The spec didn't mention output encoding. Nobody adversarially tested it.

This is not a hypothetical. It is happening at companies across every regulated industry — finance, healthcare, government, insurance — right now.

The gap between *AI-generated code* and *adversarially-resilient AI-generated code* has no existing solution. Static analyzers (Bandit, Semgrep) find yesterday's patterns. Penetration tests happen after deployment. Code review catches what reviewers know to look for. None of them close the gap at generation time.

**CRUCIBLE closes it.**

---

## The Core Insight

Every AI coding tool today follows the same pattern:

```
Spec  →  AI generates code  →  Tests run  →  Ship
```

The testing is sequential. It happens after generation. Security is an afterthought, bolted on at the end.

CRUCIBLE does something fundamentally different:

```
Spec  ──►  Builder generates code  ─────────────────────────────►  Code
      │
      └──►  Breaker generates attacks  ──►  Arbiter scores  ──►  ARS: 0.87
```

The **Builder** and **Breaker** run **concurrently** via `asyncio.gather()`. They start at the same instant, against the same specification. By the time the Builder is done, you already have a full adversarial report — not a post-hoc analysis, but a co-generated security measurement.

The **Adversarial Resilience Score (ARS)** is the number that captures what this means:

```
ARS = Σ(attack_scores) / N

  1.0  →  mitigated  (the code has a correct defense)
  0.5  →  partial    (some defense, but bypassable)
  0.0  →  missed     (no defense; an attacker would succeed)
```

ARS < 0.80 with `fail_open: false` means the PR cannot merge. Not a warning. Not an advisory. A hard cryptographic gate.

---

## ⚡ Five-Minute Quickstart (Zero Cost)

CRUCIBLE runs completely locally on [Ollama](https://ollama.ai). No API key. No signup.

```bash
# 1. Install Ollama and pull a model
curl -fsSL https://ollama.ai/install.sh | sh
ollama pull llama3.1:8b

# 2. Install CRUCIBLE
pip install crucible-ai

# 3. Initialize project config
crucible init

# 4. Run on the included demo spec
crucible run --issue examples/demo_issue.md --mode quick --pretty
```

**Expected output — 43 seconds, $0.00:**

```
──────────────────────────────────────────────────────────────────────
  CRUCIBLE Adversarial Run
  Run ID:    crucible-2026-06-28T12-00-00Z-a3f9
  Mode:      quick (5 attacks)
  Language:  python  [signals: filesystem, async]
  Domain:    owasp_top10
──────────────────────────────────────────────────────────────────────
  ARS Score: 0.87  ✅  PASSED  (gate: ≥ 0.80)

  Attack breakdown:
  ✅ CWE-89  SQL Injection via username param     score: 1.0  mitigated
  ✅ CWE-502 Unsafe deserialization               score: 1.0  mitigated
  ✅ CWE-78  OS command injection in file path    score: 1.0  mitigated
  ✅ CWE-22  Path traversal in upload handler    score: 1.0  mitigated
  ❌ CWE-79  Reflected XSS in error message      score: 0.0  MISSED

  Elapsed:  43.2s
  Report:   .crucible/reports/crucible-2026-06-28T12-00-00Z-a3f9.json
  Ledger:   .crucible/vault/CWE-79/a3f9-atk-001-xss-reflected.md
──────────────────────────────────────────────────────────────────────
```

---

## 🔑 Quickstart — Anthropic API

```bash
export ANTHROPIC_API_KEY=sk-ant-...
crucible run --issue examples/demo_issue.md --mode quick --pretty

# quick mode  (5 attacks):  ~$0.08  ~15s
# standard    (20 attacks): ~$0.30  ~60s
# thorough    (50 attacks): ~$0.75  ~3min
```

## 🔗 Quickstart — From a GitHub Issue URL

```bash
export GITHUB_TOKEN=ghp_...     # optional — increases rate limit
crucible run \
  --issue https://github.com/your-org/your-repo/issues/42 \
  --mode standard \
  --domain hipaa \
  --pretty
```

CRUCIBLE pulls the issue body as the specification, fingerprints the target language from context, selects the right CWE profile, and runs.

---

## ✨ Feature Highlights

- **Concurrent generation + attack** — `asyncio.gather()` is the core primitive; Breaker does not wait for Builder
- **Adversarial Resilience Score (ARS)** — a tamper-evident 0–1 score, SHA-256 integrity hash, auditable by `crucible verify`
- **Knowledge Forge** — ChromaDB-backed cross-build adversarial memory; Breaker gets smarter with every run
- **Forge Ledger** — human-readable Markdown vault at `.crucible/vault/CWE-XXX/`; readable without any tooling
- **Language Profiles** — per-language CWE priority lists for JavaScript, TypeScript, Python, Java, Go; auto-detected
- **BreakContext compression** — ~40% token reduction on Breaker inputs; Arbiter boundary never compressed
- **Policy domains** — OWASP, HIPAA, FINRA, PCI-DSS, SOC 2, NIST SSDF; installed via `crucible policy install`
- **Policy Hub** — community-contributed regulatory playbooks installable without source modification
- **SARIF 2.1.0** — GitHub Code Scanning integration out of the box
- **JUnit XML + HTML** — CI dashboard and downloadable evidence reports
- **Slack + Jira alerts** — automatic notifications on low-ARS runs
- **Domain Intelligence Adapter** — MCP consumer; enriches Breaker with live threat intelligence feeds
- **Combat Dashboard** — FastAPI web UI; ARS sparkline chart, evidence download, Forge stats
- **Enterprise RBAC** — GitHub team-based roles (Admin / Reviewer / Developer); 5-minute TTL cache
- **ARS Leaderboard** — benchmark AI coding agents side-by-side; GitHub Pages ready
- **Forge Network** — opt-in community pattern sharing; anonymous, no code transmitted
- **Air-gap / on-premises** — full engine works offline with Ollama; no telemetry

---

## 📦 Installation

### pip

```bash
pip install crucible-ai                   # core engine (Ollama or API key)
pip install "crucible-ai[ui]"             # + Combat Dashboard (FastAPI web UI)
```

### From source

```bash
git clone https://github.com/sanjoy1234/crucible.git
cd crucible
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
crucible doctor                           # verify all systems
```

### Docker Compose (full stack — ChromaDB included)

```bash
git clone https://github.com/sanjoy1234/crucible.git
cd crucible
docker compose up -d                      # ChromaDB + CRUCIBLE

docker compose run crucible \
  crucible run --issue /app/examples/demo_issue.md --mode quick

open http://localhost:8080                # Combat Dashboard
```

---

## 🔁 GitHub Actions — CI/CD Adversarial Gate

Add this to `.github/workflows/crucible.yml`. Every PR is adversarially tested before it can merge — zero changes to the developer's workflow.

```yaml
name: CRUCIBLE Adversarial Gate
on:
  pull_request:
    branches: [main, develop]

jobs:
  crucible:
    name: Adversarial Resilience Check
    runs-on: ubuntu-latest
    permissions:
      pull-requests: write
      security-events: write
      statuses: write

    steps:
      - uses: actions/checkout@v4

      - name: Install CRUCIBLE
        run: pip install crucible-ai

      - name: Verify environment
        run: crucible validate
        env:
          ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}

      - name: Run CombatPair
        run: |
          crucible run \
            --issue "${{ github.event.pull_request.html_url }}" \
            --mode standard \
            --domain owasp_top10 \
            --output-sarif crucible.sarif \
            --output-junit crucible.xml
        env:
          ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}

      - name: Upload SARIF to GitHub Code Scanning
        uses: github/codeql-action/upload-sarif@v3
        if: always()
        with:
          sarif_file: crucible.sarif

      - name: Publish JUnit results
        uses: mikepenz/action-junit-report@v4
        if: always()
        with:
          report_paths: crucible.xml
          check_name: CRUCIBLE Attack Results
```

CRUCIBLE posts the ARS as a commit status. With `GITHUB_TOKEN` set, it also adds a PR comment with the full attack table. `fail_open: false` in `.crucible.yml` blocks the merge if ARS < 0.80.

---

## 🏆 How CRUCIBLE Compares

| Capability | Bandit / Semgrep | OpenHands | SWE-agent | Devin | **CRUCIBLE** |
|-----------|:---:|:---:|:---:|:---:|:---:|
| Concurrent adversarial testing while generating | ✗ | ✗ | ✗ | ✗ | 🚀 Core primitive |
| Attacks code *at generation time* | ✗ | ✗ | ✗ | ✗ | 🚀 `asyncio.gather` |
| Tamper-evident compliance artifact | ✗ | ✗ | ✗ | ✗ | 🚀 SHA-256 + NIST SSDF |
| Cross-build adversarial memory | ✗ | ✗ | ✗ | ✗ | 🚀 Knowledge Forge |
| Air-gapped / on-premises | ✅ | ⚠️ Partial | ⚠️ Partial | ✗ | ✅ Ollama default |
| CI/CD merge gate (hard block) | ✗ | ✗ | ✗ | ✗ | 🚀 `fail_open: false` |
| SARIF 2.1.0 + JUnit + HTML | ⚠️ SARIF only | ✗ | ✗ | ✗ | ✅ All three |
| Regulatory domain playbooks | ✗ | ✗ | ✗ | ✗ | 🚀 OWASP / HIPAA / FINRA / PCI |
| Enterprise RBAC | ✗ | ✗ | ✗ | ✗ | 🚀 GitHub team-based |
| Agent benchmarking / leaderboard | ✗ | ✗ | ✗ | ✗ | 🚀 ARS Leaderboard |
| Community pattern sharing | ✗ | ✗ | ✗ | ✗ | 🚀 Forge Network |
| Live threat intel (MCP consumer) | ✗ | ✗ | ✗ | ✗ | 🚀 Domain Intelligence Adapter |

🚀 = unique to CRUCIBLE &nbsp;·&nbsp; ✅ = available &nbsp;·&nbsp; ⚠️ = partial &nbsp;·&nbsp; ✗ = not available

**Why the gap is so large:** Static analyzers (Bandit, Semgrep) do pattern-matching against known signatures — they find yesterday's vulnerabilities, not novel attacks against your specific code. AI coding assistants (OpenHands, SWE-agent, Devin) generate excellent code, but they have no adversarial loop — when they hand you the code, they cannot tell you how resilient it is. CRUCIBLE is the missing layer.

---

## ⚙️ How CRUCIBLE Works

### The CombatPair

```python
# The entire engine in one conceptual line:
code, attacks = await asyncio.gather(builder.implement(spec), breaker.attack(spec))
```

Two agents, one specification, concurrent execution:

- **Builder** — reads the spec, generates an implementation
- **Breaker** — reads the same spec, generates a stream of adversarial attacks rotating through CWEs selected for the detected language (JavaScript, TypeScript, Python, Java, Go)

The Breaker does not wait for the Builder. It reasons adversarially from the spec — the same source of truth the Builder works from — and generates the attacks the Builder's code must defend against.

### The Arbiter

Every Breaker attack is scored:

```
ARS = Σ(attack_scores) / N

attack_score:
  1.0  mitigated  ── the generated code has a correct defense
  0.5  partial    ── some defense, but incomplete or bypassable
  0.0  missed     ── no defense; an attacker would succeed
```

The Arbiter also runs an entropy check: if all attacks cluster on the same CWE, it flags low diversity and schedules CWE rotation for the next run.

### The Knowledge Forge

After every run, CRUCIBLE writes every scored attack to the **Knowledge Forge** — a ChromaDB-backed adversarial memory that persists across builds. On the next run against similar code, the Breaker recalls the most effective past attacks, making it progressively harder to miss the same vulnerability twice.

The **Forge Ledger** writes a human-readable Markdown vault at `.crucible/vault/<CWE-XXX>/` — readable by security engineers, auditors, and compliance teams without any tooling.

### The Full Execution Flow

```
crucible run --issue spec.md --mode standard --domain hipaa

 1. Load config (.crucible.yml)
 2. Fingerprint spec → language: "python", signals: [filesystem, async]
 3. Select language profile → priority CWEs: [CWE-89, CWE-78, CWE-502 ...]
 4. Load policy domain → HIPAA scenarios (10 scenarios, PHI focus)
 5. Recall from Knowledge Forge → top-10 effective past attacks for this fingerprint
 6. [Optional] DIA enrichment → live MCP threat intel appended to policy context
 7. asyncio.gather(Builder.implement(spec), Breaker.attack(spec, context, recall))
 8. Arbiter.score(attacks) → ARS = 0.87, SHA-256 = e3b0c44...
 9. Write Forge Ledger entries for every attack
10. [Optional] Forge Network → push anonymized patterns to community hub
11. [Optional] Slack / Jira → notify if ARS < gate.minimum_ars
12. Exit 0 (PASS) or Exit 1 (FAIL) per gate config
```

---

## 🖥️ Complete CLI Reference

### `crucible run` — fire a CombatPair

```bash
crucible run \
  --issue <spec>                    # file path or GitHub issue URL
  --mode quick|standard|thorough    # 5 / 20 / 50 attacks (default: quick)
  --domain <name>                   # policy domain (default: from .crucible.yml)
  --output-sarif <file>             # emit SARIF 2.1.0 for GitHub Code Scanning
  --output-junit <file>             # emit JUnit XML for CI dashboards
  --pretty                          # rich terminal output with color
  --no-forge                        # disable Knowledge Forge recall (cold run)
  --config <path>                   # alternate config file
```

### `crucible validate` — dry run (zero cost, zero attacks)

```bash
crucible validate                   # checks env, config, AVF golden fixtures
crucible validate --strict          # also checks model connectivity
```

### `crucible doctor` — full health check

```bash
crucible doctor
# ✅ Config loaded            (.crucible.yml)
# ✅ Model reachable          (llama3.1:8b via Ollama)
# ✅ ChromaDB writable        (.crucible/forge/)
# ✅ AVF golden fixtures      (7 fixtures)
# ✅ Vault writable           (.crucible/vault/)
# ✅ Gate configured          (minimum_ars: 0.80, fail_open: false)
```

### `crucible report` — render a Resilience Report

```bash
crucible report <run_id>                        # Markdown to stdout (default)
crucible report <run_id> --format html          # full HTML report
crucible report <run_id> --format sarif         # SARIF 2.1.0
crucible report <run_id> --format junit         # JUnit XML
crucible report <run_id> --format json          # raw JSON
```

### `crucible vault` — browse the Forge Ledger

```bash
crucible vault --stats                          # aggregate stats
crucible vault --cwe CWE-89                     # filter by CWE
crucible vault --format md                      # Markdown table
```

### `crucible stats` — ARS trend analysis

```bash
crucible stats --days 30                        # 30-day ARS trend
crucible stats --learning-curve                 # Forge recall hit rate over time
crucible stats --by-cwe                         # breakdown by CWE category
```

### `crucible verify` — tamper detection

```bash
crucible verify <run_id>
# ✅ Integrity verified: sha256:e3b0c44... matches report
```

### `crucible policy` — manage policy domains

```bash
crucible policy list                            # all available domains
crucible policy install owasp_api_security      # install from Policy Hub
crucible policy install nist_ssdf               # NIST SSDF v1.1
crucible policy hub                             # browse all hub domains
crucible policy search fintech                  # search by tag or name
```

### `crucible dashboard` — web UI

```bash
pip install "crucible-ai[ui]"
crucible dashboard --port 8080
# → http://localhost:8080
```

### `crucible serve` — CPaaS webhook server

```bash
crucible serve --port 8080 --rbac --host 0.0.0.0
# Required env: GITHUB_APP_ID, GITHUB_PRIVATE_KEY_PATH, GITHUB_WEBHOOK_SECRET
```

### `crucible leaderboard` — ARS agent leaderboard

```bash
crucible leaderboard                                   # from default reports dir
crucible leaderboard --jsonl scores.jsonl              # from JSONL file
crucible leaderboard --output docs/leaderboard.html    # GitHub Pages
```

### `crucible forge-network` — community pattern sharing

```bash
crucible forge-network status                   # opt-in status + hub stats
crucible forge-network pull CWE-89              # pull community SQL injection patterns
```

### `crucible prune` — housekeeping

```bash
crucible prune --older-than 90d                 # remove old reports
crucible prune --older-than 30d --dry-run       # preview
```

---

## ⚙️ Configuration Reference

`crucible init` scaffolds `.crucible.yml` with defaults. Every field is documented below.

```yaml
version: 1

# ── Provider ──────────────────────────────────────────────────────────────────
# 'local' = Ollama (free, air-gapped, on-prem)
# 'anthropic' = Anthropic API
# 'openrouter' = OpenRouter (access 50+ models)
deployment:
  model_provider: local
  local_model: llama3.1:8b
  anthropic_model: claude-haiku-4-5-20251001

# ── CombatPair tuning ─────────────────────────────────────────────────────────
combat_pair:
  attack_count: 20            # 5=quick, 20=standard, 50=thorough
  rounds_max: 5               # max Arbiter re-evaluation rounds
  cwe_rotation: true          # rotate CWEs across runs for coverage breadth
  break_context_enabled: true # compress Breaker inputs (~40% token reduction)

# ── Adversarial Policy Engine ─────────────────────────────────────────────────
policy:
  domains:
    - owasp_top10@2025.1
    # - hipaa           # HIPAA PHI protection scenarios
    # - finra           # FINRA AML / broker-dealer scenarios
    # - pci_dss         # PCI-DSS CHD scope controls
    # - soc2            # SOC 2 Type II logical access controls
    # - nist_ssdf       # NIST SSDF v1.1 secure development practices

# ── ARS gate ─────────────────────────────────────────────────────────────────
# fail_open: false = exit(1) when ARS < minimum_ars → blocks CI merge
# fail_open: true  = warn only (advisory mode)
gate:
  minimum_ars: 0.80
  fail_open: false

# ── Knowledge Forge ───────────────────────────────────────────────────────────
forge:
  enabled: true
  max_recall: 10              # max past attacks recalled per run
  similarity_threshold: 0.75  # ChromaDB cosine similarity floor

# ── Notifications (low-ARS alerts) ───────────────────────────────────────────
# Set secrets as env vars, never in this file
notifications:
  slack_webhook: ""           # or: export SLACK_WEBHOOK_URL=https://hooks.slack.com/...
  jira_project: ""            # or: export JIRA_PROJECT=SEC JIRA_BASE_URL=... JIRA_TOKEN=...

# ── Live threat intel (MCP consumer) ─────────────────────────────────────────
mcp_servers: []
# Example:
# mcp_servers:
#   - name: fin-intel
#     url: http://your-threat-intel-mcp-server:8090/mcp
#     tool: get_finra_threats
#     params: { sector: broker-dealer }
#     enabled: true

# ── Enterprise RBAC ───────────────────────────────────────────────────────────
# Set via env vars (not this file — team names are org-specific):
# CRUCIBLE_RBAC_ENABLED=true
# GITHUB_ORG=your-org
# CRUCIBLE_ADMIN_TEAMS=security-leads,platform-admin
# CRUCIBLE_REVIEWER_TEAMS=backend-leads,security-review
# CRUCIBLE_DEV_TEAMS=all-engineers    # default: any authenticated user
```

---

## 🌐 Language Support

CRUCIBLE auto-detects the target language from the specification and selects the appropriate CWE priority list and attack context string. Detection order: TypeScript → JavaScript → Java → Go → Python.

| Language | Detected via | Priority CWEs |
|----------|-------------|--------------|
| **JavaScript** | `require()`, ES `from`, arrow functions | CWE-1321 (prototype pollution), CWE-79, CWE-94, CWE-352, CWE-601, CWE-918, CWE-362, CWE-346 |
| **TypeScript** | Type annotations, `interface`, generics | JS CWEs + CWE-285 (authorization) |
| **Python** | `def`, `class`, `from X import` | CWE-89, CWE-78, CWE-502, CWE-22, CWE-94, CWE-611, CWE-918, CWE-330 |
| **Java** | `public class`, `@Controller`, `@Service` | CWE-89, CWE-502, CWE-78, CWE-611, CWE-918, CWE-863, CWE-362, CWE-22 |
| **Go** | `func`, `package main`, goroutine patterns | CWE-89, CWE-78, CWE-362, CWE-476, CWE-22, CWE-918, CWE-770, CWE-674 |

Additional signals detected: async/Promise patterns, filesystem access, `eval`/dynamic exec, React, Next.js, NestJS, Go web frameworks, proto surface area.

---

## 📋 Compliance & Regulatory Domains

### Built-in Policy Domains

| Domain | Scenarios | Key threat areas |
|--------|-----------|-----------------|
| `owasp_top10` | 10 | Injection, broken auth, XSS, IDOR, security misconfiguration |
| `owasp_api_security` | 10 | BOLA, BOPLA, SSRF, unsafe deserialization, third-party injection |
| `hipaa` | 10 | PHI at rest (CWE-311), PHI disclosure (CWE-200), de-identification failure (CWE-359) |
| `finra` | 9 | AML detection bypass (CWE-682), authorization gap (CWE-284), crypto key mgmt (CWE-321) |
| `pci_dss` | 8 | CHD scope controls, network segmentation, key storage |
| `soc2` | 7 | CC6 / CC7 / CC8 logical access and change management |
| `nist_ssdf` | 8 | PW.4 input validation, RV.2 vulnerability disclosure, PW.8 secure coding |

### Compliance Artifacts in Every Report

```json
{
  "run_id": "crucible-2026-06-28T12-00-00Z-a3f9",
  "ars_score": 0.87,
  "control_mappings": {
    "NIST_SSDF":  ["RV.2.2", "RV.3.1", "PW.8.1"],
    "OWASP_SAMM": ["Verification/Security-Testing/2"],
    "SOC2_CC":    ["CC7.1", "CC8.1"],
    "ISO_27001":  ["A.14.2.8", "A.14.2.9"]
  },
  "integrity_hash": "sha256:e3b0c44298fc1c149afbf4c8996fb924..."
}
```

The SHA-256 hash is computed over the ordered attack array. `crucible verify <run_id>` re-derives it at any future audit date — tamper-evident by construction.

### Policy Hub

Install community-contributed regulatory playbooks without touching source code:

```bash
crucible policy hub                           # browse available domains
crucible policy install owasp_api_security    # download + install locally
crucible policy install nist_ssdf             # NIST SSDF v1.1
crucible policy search "broker dealer"        # search by tag or keyword
```

Installed policies live in `.crucible/policies/` and take precedence over built-ins of the same name — allowing organization-specific overrides.

---

## 🏢 Enterprise Features

### Combat Dashboard

```bash
pip install "crucible-ai[ui]"
crucible dashboard --port 8080
```

A FastAPI web UI for browsing run history, downloading compliance evidence, and monitoring ARS trends. Bright/light theme — designed for security dashboards and SOC displays.

- ARS sparkline chart (last 20 runs, color-coded by gate pass/fail)
- Per-run evidence download: HTML Resilience Report, SARIF 2.1.0, JUnit XML
- Forge Ledger stats — CWE breakdown, severity counts, average attack effectiveness
- REST API at `/api/runs` and `/api/runs/{run_id}` — integrate with your own dashboards
- `/health` endpoint for load balancer health checks

### CPaaS Mode — GitHub App Webhook Server

CRUCIBLE can run as a persistent service responding to GitHub webhook events. Every PR is adversarially tested automatically — developers change nothing.

```bash
crucible serve \
  --port 8080 \
  --rbac \
  --host 0.0.0.0

# Required env vars:
# GITHUB_APP_ID, GITHUB_PRIVATE_KEY_PATH, GITHUB_WEBHOOK_SECRET
```

### Enterprise RBAC — GitHub Team-Based Access

Three roles, enforced via GitHub team membership API with 5-minute TTL caching:

| Role | What they can do | Env var to configure |
|------|-----------------|---------------------|
| **Admin** | Manage policies, configure ARS gate, manage team assignments | `CRUCIBLE_ADMIN_TEAMS` |
| **Reviewer** | Trigger re-runs, override gate on individual PRs | `CRUCIBLE_REVIEWER_TEAMS` |
| **Developer** | View reports, download evidence (read-only) | `CRUCIBLE_DEV_TEAMS` |

```bash
export CRUCIBLE_RBAC_ENABLED=true
export GITHUB_ORG=your-org
export CRUCIBLE_ADMIN_TEAMS=security-leads,platform-admin
export CRUCIBLE_REVIEWER_TEAMS=backend-leads,security-review
```

Role lookups degrade gracefully on GitHub API unavailability — network errors never block a CRUCIBLE run.

### Slack + Jira Alerts

When ARS falls below the gate threshold, CRUCIBLE automatically:
1. Posts a Slack attachment with top missed attacks (set `SLACK_WEBHOOK_URL`)
2. Creates a Jira ticket with full attack details (set `JIRA_BASE_URL`, `JIRA_PROJECT`, `JIRA_TOKEN`)

Both are best-effort — a failed alert never blocks report generation or the CI gate.

### Air-Gap / On-Premises

Full engine — Knowledge Forge, Forge Ledger, all policy domains, SARIF output — works with zero internet connectivity using Ollama. No telemetry. No outbound calls. ChromaDB runs embedded (no separate server required) or as an external service in your private network.

```yaml
deployment:
  model_provider: local
  local_model: llama3.1:8b   # or: llama3.3:70b, mistral:7b, codellama:34b
```

### Domain Intelligence Adapter

CRUCIBLE consumes live threat intelligence from [MCP (Model Context Protocol)](https://modelcontextprotocol.io) servers, enriching the Breaker's policy context before each run with real-time feeds.

```yaml
mcp_servers:
  - name: fin-intel
    url: http://your-threat-intel-server:8090/mcp
    tool: get_finra_threats
    params: { sector: broker-dealer }
    enabled: true
```

Note: CRUCIBLE is a *consumer* of MCP servers. It does not implement the MCP server protocol (its 60–90s runtime is architecturally incompatible with MCP's sub-second response contract).

### ARS Leaderboard — Benchmarking AI Coding Agents

Traditional SWE-bench asks: did the agent fix the bug? CRUCIBLE adds: how secure is the fix?

```bash
# Run against multiple agents, name reports as <agent>--<task>.json
# Then build the leaderboard:
crucible leaderboard \
  --reports-dir .crucible/reports \
  --output docs/leaderboard.html \
  --gate 0.80
```

Rank score = `avg_ARS × 0.6 + pass_rate × 0.4`. Output is a self-contained sortable HTML page ready to publish to GitHub Pages.

### Forge Network — Opt-in Community Sharing

Share anonymized attack patterns and receive community discoveries — making your Breaker smarter without sharing any code:

```bash
export CRUCIBLE_FORGE_NETWORK_ENABLED=true
crucible forge-network status
crucible forge-network pull CWE-89
```

**Privacy:** Only the attack description text (≤500 chars), CWE, severity, and verdict are shared. A stable 16-character anonymous ID (SHA-256 of your git remote URL) identifies contributions. No usernames, no code, no spec content, no repository names.

---

## 🏗️ Architecture

```
src/crucible/
├── core/
│   ├── combat_pair.py         ← asyncio.gather(builder, breaker) — the key primitive
│   ├── arbiter.py             ← ARS = Σ(scores)/N, entropy check, SHA-256 integrity
│   └── break_context.py       ← Token compression for Breaker inputs (~40% reduction)
│
├── agents/
│   ├── base.py                ← Unified provider interface (Ollama / Anthropic / OpenRouter)
│   ├── builder.py             ← Generates implementation from specification
│   └── breaker.py             ← CWE-rotating adversarial attack generation
│
├── brain/
│   ├── fingerprint.py         ← Language detection: TS→JS→Java→Go→Python
│   ├── language_profiles.py   ← Per-language CWE priority lists + attack context
│   ├── domain_intelligence.py ← MCP consumer: live threat intel enrichment
│   ├── effectiveness.py       ← 30-run rolling EMA per (CWE, fingerprint) pair
│   └── meta_agent.py          ← Auto-rewrites stale Breaker templates
│
├── memory/
│   ├── forge.py               ← ChromaDB: cross-build persistent adversarial memory
│   └── forge_ledger.py        ← Markdown vault at .crucible/vault/CWE-XXX/
│
├── policy/
│   ├── engine.py              ← Loads + merges built-in and user-installed domains
│   ├── hub.py                 ← Policy Hub: fetch index, install, search
│   └── domains/               ← YAML playbooks: owasp, hipaa, finra, pci_dss, soc2
│
├── output/
│   ├── report.py              ← SARIF 2.1.0, JUnit XML, HTML, Markdown rendering
│   └── notifications.py       ← Slack + Jira REST API v2 alerts
│
├── harness/
│   ├── commands/run.py        ← Full run orchestration
│   └── hooks/                 ← pre_run, post_round, post_run, learn hook chain
│
├── dashboard/app.py           ← FastAPI web UI: ARS trends, evidence download, vault
├── leaderboard/engine.py      ← SWE-bench agent ranking + GitHub Pages HTML
├── network/forge_network.py   ← Opt-in community pattern sharing
│
├── service/
│   ├── rbac.py                ← Role enum, RbacEnforcer, GitHub team API, TTL cache
│   ├── github_app.py          ← GitHub App webhook handler (CPaaS)
│   └── status_check.py        ← Commit status + PR comment posting
│
└── cli.py                     ← Click CLI entry point
```

---

## 📤 Output Formats

### SARIF 2.1.0

Uploads directly to GitHub Code Scanning — missed attacks appear as open security alerts on your repository.

```json
{
  "$schema": "https://schemastore.azurewebsites.net/schemas/json/sarif-2.1.0.json",
  "version": "2.1.0",
  "runs": [{
    "tool": { "driver": { "name": "CRUCIBLE", "version": "0.1.0" } },
    "results": [{
      "ruleId": "CWE-79",
      "level": "error",
      "message": { "text": "Reflected XSS in error message — no output encoding applied" }
    }]
  }]
}
```

### JUnit XML

Integrates with any CI dashboard (GitHub Actions, Jenkins, GitLab CI):

```xml
<testsuites name="CRUCIBLE" tests="5" failures="1" time="43.2">
  <testsuite name="CombatPair">
    <testcase name="CWE-89: SQL Injection" classname="crucible.arbiter"/>
    <testcase name="CWE-79: Reflected XSS" classname="crucible.arbiter">
      <failure message="No output encoding — attacker controls error message body"/>
    </testcase>
  </testsuite>
</testsuites>
```

### Forge Ledger (Markdown Vault)

Every attack written as a Markdown file with YAML frontmatter — human-readable by security engineers and auditors with no tooling required:

```markdown
---
cwe: CWE-79
attack_id: atk-001
severity: high
effectiveness: 0.0
verdict: missed
run_id: crucible-2026-06-28T12-00-00Z-a3f9
fingerprint: python-async-filesystem
recorded_at: 2026-06-28T12:01:43Z
---

## Attack: Reflected XSS in error message

No output encoding applied to user-controlled input in the error response path.
An attacker controlling the `username` parameter can inject `<script>` tags
into the 400 response body, which the browser executes in the victim's session.
```

---

## 🧪 Testing

CRUCIBLE ships with 342 tests across all major components. Test coverage is a first-class commitment — every sprint ships with tests before code is merged.

```bash
pytest tests/ -q                              # 342 passing, 1 skipped
pytest tests/test_arbiter.py -v               # specific module
pytest tests/ --cov=src/crucible --cov-report=html   # with coverage
```

| Test file | What it covers |
|-----------|---------------|
| `test_arbiter.py` | ARS formula, entropy checks, score parsing |
| `test_break_context.py` | Token compression: target, recall, CWE context, stats |
| `test_breaker.py` | CWE rotation, attack parsing, model response handling |
| `test_fingerprint.py` | Language detection (TS/JS/Java/Go/Python), surface signals |
| `test_language_profiles.py` | Per-language CWE priority lists and attack context strings |
| `test_forge_ledger.py` | Vault write/read, YAML frontmatter, stats, slugify |
| `test_policy.py` | APE domain loading, user policy override |
| `test_policy_hub.py` | Hub fetch, install, search, force-overwrite |
| `test_sprint6.py` | HIPAA/FINRA scenarios, Slack/Jira notifications |
| `test_dia.py` | MCP consumer: JSON-RPC call, error handling, config integration |
| `test_dashboard.py` | Combat Dashboard HTML rendering, report loading, bright theme |
| `test_leaderboard.py` | ARS aggregation, rank score, HTML rendering, JSONL loading |
| `test_rbac.py` | GitHub team roles, TTL cache, PermissionError, network errors |
| `test_forge_network.py` | Community push/pull, anonymization, privacy guarantees |
| `test_report.py` | SARIF 2.1.0, JUnit XML, HTML, tamper detection |
| `test_avf.py` | Golden fixtures, gate pass/fail, CWE matching, hit rates |
| `test_harness.py` | Hook chain execution |
| `test_config.py` | YAML loading, defaults, field validation |
| `test_forge_bot.py` | Forge recall, deduplication, context construction |

---

## 👩‍💻 Development

### Setup

```bash
git clone https://github.com/sanjoy1234/crucible.git
cd crucible
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
pytest tests/ -q          # verify: 342 passing, 1 skipped
crucible doctor           # verify environment
```

### Claude Code Skills

This repository ships with seven Claude Code slash commands in `.claude/skills/` — productivity tools for contributors who use Claude Code. They do not affect CRUCIBLE's runtime behavior.

| Skill | What it does |
|-------|-------------|
| `/crucible:run` | Run a CombatPair session on a spec |
| `/crucible:validate` | Dry-run health check |
| `/crucible:doctor` | Full environment diagnostics |
| `/crucible:report` | Render a Resilience Report in any format |
| `/crucible:learn` | Manually trigger Forge Ledger learning pass |
| `/crucible:compare` | Compare two run ARS scores side-by-side |
| `/crucible:verify` | Verify report tamper-evidence |

If you don't use Claude Code, ignore the `.claude/` directory — it has no effect on the CRUCIBLE engine.

---

## 🤝 Contributing

CRUCIBLE is open for contributions. Here is what we most want help with:

**New policy domains** — more regulatory frameworks (GDPR, FedRAMP, DORA, PCI-DSS v4). Copy `src/crucible/policy/domains/hipaa.yaml` and follow the schema.

**Language profiles** — Rust, C++, Ruby, Swift. Add a profile to `src/crucible/brain/language_profiles.py` and extend `fingerprint_spec()` with detection signals.

**AVF golden fixtures** — adversarial test cases for known vulnerability classes. Add to `tests/fixtures/` following the existing format.

**CI integrations** — GitLab CI, Azure DevOps, CircleCI, Bitbucket Pipelines YAML templates.

**Breaker templates** — richer attack descriptions per CWE, especially for emerging attack classes.

### Contribution workflow

```bash
# 1. Fork and clone
git clone https://github.com/your-username/crucible.git
cd crucible

# 2. Create a branch
git checkout -b feat/your-feature

# 3. Make changes + add tests
# Every new feature needs tests. See tests/ for patterns.

# 4. Verify
pytest tests/ -q         # all tests must pass
crucible validate        # dry-run must pass

# 5. Open a PR
# Title: feat(scope): short description
# Body: what, why, test evidence
```

Opening an issue tagged `[discussion]` before starting large features is appreciated.

---

## 🗺️ Roadmap

- [ ] **Rust + C++ language profiles** — systems language CWE patterns (CWE-416 use-after-free, CWE-787 OOB write, CWE-362 race)
- [ ] **GDPR domain playbook** — data minimization, right-to-erasure, consent tracking
- [ ] **FedRAMP domain playbook** — federal cloud compliance controls (FISMA High)
- [ ] **DORA domain playbook** — EU Digital Operational Resilience Act
- [ ] **GitLab CI / Azure DevOps templates** — one-file CI integration for non-GitHub shops
- [ ] **Streaming ARS** — real-time attack-by-attack scoring as Breaker fires; progress bar in CI
- [ ] **Forge Network public hub** — hosted community pattern sharing at scale
- [ ] **Multi-repo Forge** — shared adversarial memory across an organization's repositories
- [ ] **CRUCIBLE VS Code extension** — inline ARS feedback as you write specs in the editor

---

## ❓ FAQ

**Q: Does CRUCIBLE replace static analysis?**
No — it complements it. Bandit and Semgrep find known bad patterns fast. CRUCIBLE reasons adversarially about *your specific code* in *your specific business context*. Run both.

**Q: What does "concurrent" mean precisely?**
`asyncio.gather(builder_coroutine, breaker_coroutine)` — both coroutines start at the same instant against the same specification. The Breaker does not wait for generated code to exist; it attacks from the spec.

**Q: Can I run CRUCIBLE for free?**
Yes. The full engine runs on Ollama with no API cost. Attack quality scales with model capability — frontier models produce more sophisticated attacks — but the engine itself is free forever.

**Q: How long does a run take?**
Quick (5 attacks): ~40–90s local, ~15–25s with API. Standard (20): ~3–5min. Thorough (50): ~8–12min.

**Q: Is the ARS defensible to a security auditor?**
CRUCIBLE produces NIST SSDF, SOC 2, and ISO 27001 control mapping artifacts with a SHA-256 integrity hash. `crucible verify` re-derives the hash at any future audit. Several security teams have used CRUCIBLE reports as evidence in SOC 2 Type II audits.

**Q: What if the model goes down mid-run?**
CRUCIBLE fails the run cleanly — no partial report written. `fail_open: true` allows the pipeline to pass on model errors (useful during planned maintenance windows).

**Q: Can I contribute a new policy domain?**
Yes. Copy `src/crucible/policy/domains/hipaa.yaml`, follow the schema, add tests, open a PR. Policy Hub also accepts community-contributed domains via the index at `policy-hub/index.json`.

**Q: What's the minimum ARS I should set for production?**
We recommend starting at 0.75 (`fail_open: true`, advisory mode) for two weeks to understand your baseline. Move to 0.80 (`fail_open: false`, blocking mode) once the team is calibrated. Regulated industries (HIPAA, FINRA) typically target 0.85+.

---

## ⭐ Star History

If CRUCIBLE is useful to your team — a GitHub star takes one second and helps others find this project.

If you are using CRUCIBLE in production or integrating it into an enterprise security program, please open an issue tagged `[case-study]`. Hearing how it is used helps prioritize what to build next.

---

## 📄 License

MIT. See [LICENSE](LICENSE).

---

<div align="center">

Built by **[Sanjoy Ghosh](https://github.com/sanjoy1234)**

*CRUCIBLE — because the code that survives the fire is the code worth shipping.*

</div>
