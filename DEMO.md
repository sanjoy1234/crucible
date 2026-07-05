# CRUCIBLE — Demo & Testing Guide

**Audience:** Engineering Managers and CTOs  
**Primary surface:** CLI (dashboard as supporting visual)  
**Model setup:** Run `crucible setup` once — interactive wizard picks the best available model

---

## Part 1 — How to Test What's Been Built Right Now

### Step 0 — First-time setup (run once, stay in terminal)

```bash
crucible setup
```

This interactive wizard will:
- Ask you to choose your AI model provider (Anthropic, OpenRouter, OpenAI, HuggingFace, or Ollama)
- Prompt for your API key and write it to `.env` automatically — no file editing
- Test the connection before finishing
- Set up optional GitHub / Jira / Confluence / Aha! integrations

After setup, verify everything is green:

```bash
crucible doctor
```

**If Ollama shows `Model reachable: ✓` but runs fail with 404:**
The configured model may not be pulled yet. Pull it:
```bash
ollama pull llama3.1:8b    # ~4.7 GB, recommended quality
# or for a lighter option: ollama pull llama3.2:1b
```

---

### Step 1 — Run your first adversarial session (the core feature)

```bash
crucible run --issue examples/demo_issue.md --pretty
```

**What happens:** Builder generates a Flask login endpoint. Breaker simultaneously attacks it. Arbiter scores each attack. ARS score gates the result.

**What to watch for in the output:**
- Vulnerability findings appear FIRST (CWE, severity, description, fix)
- ARS score and PASS/BLOCKED verdict appear LAST
- The whole session completes in ~30–60 seconds locally

---

### Step 2 — View the vulnerability findings in detail

```bash
crucible findings
```

Shows the last run's findings only — no score, no noise. Good for a PR comment view.

```bash
crucible findings --format md
```

Markdown output — exactly what would be posted as a GitHub PR comment.

---

### Step 3 — Open the full HTML report

```bash
crucible report --format html > /tmp/last_report.html
open /tmp/last_report.html
```

The HTML report is executive-ready: findings cards, severity color-coding, remediation panel, compliance table, ARS score at the bottom.

---

### Step 4 — Launch the animated dashboard

```bash
crucible dashboard
```

Open `http://localhost:8080` in a browser.

**What to show:**
- ARS trend sparkline (animates on load)
- Attack outcome donut chart (Mitigated / Partial / Missed)
- Pipeline diagram showing Builder ↔ Breaker concurrent execution
- Run history table — click any row to open the full HTML report
- CLI Quick Start panel at the bottom

---

### Step 5 — Test IDE integration (zero-setup claim)

```bash
crucible integrate --dry-run
```

Shows the exact MCP configs that would be written for Claude Code, Cursor, Windsurf, GitHub Copilot, Codex, and GitHub Actions — without writing anything.

To actually wire it up:

```bash
crucible integrate
```

---

### Step 6 — Run against a public repo (multi-repo test)

Pick any of the repos below. CRUCIBLE walks the folder, extracts source files, and attacks the codebase.

**Python:**
```bash
git clone https://github.com/pallets/flask /tmp/flask-demo
crucible run --issue /tmp/flask-demo --pretty
```

**JavaScript:**
```bash
git clone https://github.com/axios/axios /tmp/axios-demo
crucible run --issue /tmp/axios-demo --pretty
```

**Go:**
```bash
git clone https://github.com/gin-gonic/gin /tmp/gin-demo
crucible run --issue /tmp/gin-demo --pretty
```

**Java:**
```bash
git clone https://github.com/spring-projects/spring-petclinic /tmp/petclinic
crucible run --issue /tmp/petclinic --pretty
```

**TypeScript:**
```bash
git clone https://github.com/microsoft/vscode-extension-samples /tmp/vscode-samples
crucible run --issue /tmp/vscode-samples --pretty
```

---

### Step 7 — Run all tests (regression)

```bash
pytest tests/ -q
```

Expected: **476 passed, 0 failed**.

---

## Part 2 — Exact CLI Demo Script (EM / CTO Audience)

Run these in order. Each command is one talking point.

---

### Scene 1 — The problem (30 seconds, no commands)

*"Security testing today requires security engineers to write tests manually. That's expensive, slow, and doesn't scale. CRUCIBLE eliminates that cost entirely — it generates attacks at the same time it generates code."*

---

### Scene 2 — Zero setup

```bash
crucible doctor
```

*"One command. No YAML to write, no rules to configure, no security expertise required. It just works."*

---

### Scene 3 — Run a session — the core demo

```bash
crucible run --issue examples/demo_issue.md --pretty
```

*"I give it a spec — the same thing I'd give to any AI coding assistant. CRUCIBLE's Builder generates the code. Simultaneously — not after — the Breaker attacks it. In the time it takes to write one story ticket, we've done a full adversarial security review."*

Wait for output. Point out:

- **Vulnerabilities appear first** — "The report leads with what broke, the CWE category, the severity, and exactly how to fix it. Not a score. Not a number. A fix."
- **ARS score appears last** — "The Adversarial Resilience Score is the gate. Above 0.75 — it ships. Below — it's blocked. That's it."

---

### Scene 4 — The business intent angle

*"Most security tools only see the code. CRUCIBLE sees the business intent too."*

```bash
# If JIRA_URL / JIRA_EMAIL / JIRA_TOKEN are set:
crucible run --issue examples/demo_issue.md --intent PROJ-42 --pretty
```

*"A FINRA requirement in Jira plus a payment spec in the code creates a vulnerability surface that neither document creates alone. CRUCIBLE finds it. Sonar doesn't even know Jira exists."*

---

### Scene 5 — Findings view (for developers)

```bash
crucible findings
crucible findings --format md
```

*"The developer gets this in their PR. Not a scan report from 1998. A specific finding, the CWE, the severity, and a one-line fix. No security team review required."*

---

### Scene 6 — Dashboard (for the audience watching)

```bash
crucible dashboard
# open http://localhost:8080
```

*"Every run is tracked. The trend line shows whether your codebase is getting more or less resilient over time. The donut shows your attack outcome breakdown. Click any run to open the full executive report."*

---

### Scene 7 — IDE integration (for the developer in the room)

```bash
crucible integrate --dry-run
```

*"Developers don't change their workflow. They use Claude Code, Cursor, Copilot, whatever they want. CRUCIBLE wires itself in as an MCP server — one command, zero config. The next time they use their AI assistant, CRUCIBLE is already there."*

---

### Scene 8 — CI/CD gate (for the engineering manager)

```bash
crucible integrate --platform github-actions
cat .github/workflows/crucible.yml
```

*"Every pull request hits this gate. If the ARS score drops below threshold, the PR is blocked. No human security review in the loop. The gate is automated, tamper-evident — SHA-256 hash on every report — and auditable."*

---

### Scene 9 — Multi-repo (scale argument)

```bash
crucible run --issue /tmp/flask-demo --pretty
```

*"We just ran the same pipeline against Flask — a real-world Python web framework with 60,000 GitHub stars. No reconfiguration. No language-specific rules. Folder path in, findings out."*

---

## Part 3 — Competitive Comparison (Sonar vs CRUCIBLE)

| | SonarQube | CRUCIBLE |
|---|---|---|
| Test authoring | Manual rules | Zero — generated automatically |
| Attack surface | Code only | Intent (Jira/Confluence/Aha!) + code |
| Output | Rule violations | Exploitable vulnerabilities with fix |
| Speed | Minutes to hours | ~30–60 seconds |
| CI integration | Complex agent setup | `crucible integrate` one command |
| Business context | None | Jira, Confluence, Aha! adapters |
| Score type | Quality gate | Adversarial Resilience Score (ARS) |

---

## Part 4 — Talking Points by Audience

### For the Engineering Manager

- *"It's TDD for security — but without the cost barrier that killed TDD adoption. You don't write the tests. CRUCIBLE does."*
- *"Near-zero overhead. No training, no rules, no security headcount."*
- *"Every PR has an ARS score. You know, in real time, whether your codebase is getting more or less resilient."*

### For the CTO

- *"Builder + Breaker run concurrently via asyncio — adversarial testing starts the moment code generation starts, not after."*
- *"Attack surface = business intent + spec. That's the gap every other tool misses."*
- *"Reports are SHA-256 tamper-evident. SARIF and JUnit output for your existing compliance pipeline."*
- *"MCP server over stdio — works with any AI coding assistant that speaks MCP: Claude Code, Cursor, Windsurf, Copilot."*

---

## Part 5 — Troubleshooting

**`crucible run` hangs or times out**  
→ Ollama isn't running. Start it: `ollama serve`

**`Model reachable: ✗` in doctor**  
→ Pull a model first: `ollama pull llama3`

**`crucible dashboard` command not found after install**  
→ FastAPI and uvicorn are included in the base install. Try reinstalling: `pip install --upgrade crucible-ai`

**Findings are empty / no attacks generated**  
→ The model returned malformed JSON. Try a larger model: `ollama pull llama3:70b`

**GitHub URL input fails**  
→ Set `GITHUB_TOKEN` in your `.env` for private repos. Public repos work without it.

**Intent adapter (Jira) does nothing**  
→ Set `JIRA_URL`, `JIRA_EMAIL`, `JIRA_TOKEN` in `.env`. Without them, CRUCIBLE falls back silently to spec-only mode — no error, no degradation.
