# CRUCIBLE ⚔️

**Adversarial Co-Generation Engine — the only system that tests AI-generated code while it is being written.**

CRUCIBLE runs a **Builder** agent and a **Breaker** agent **concurrently** on the same specification via `asyncio.gather()`. The Builder implements. The Breaker attacks. The Arbiter scores every attack and produces an **Adversarial Resilience Score (ARS)** — a tamper-evident security signal that can block PR merges and satisfy SOC 2, NIST SSDF, and ISO 27001 audit requirements.

```
Spec ──► Builder ──────────────────────► Code
    └──► Breaker ──► [CWE attacks] ──► Arbiter ──► ARS: 0.87 ✅
```

> **The key insight:** Every existing AI coding tool (Devin, Copilot, OpenHands) generates code and then runs tests. CRUCIBLE generates code and attacks it **at the same time**. The test harness is not an afterthought — it is the execution primitive.

---

## Quickstart — Zero Cost (Ollama)

```bash
# 1. Install Ollama and pull a model
curl -fsSL https://ollama.ai/install.sh | sh
ollama pull llama3.1:8b

# 2. Install CRUCIBLE
pip install crucible-ai

# 3. Initialize config
crucible init

# 4. Run on a spec
crucible run --issue examples/demo_issue.md --mode quick --pretty
```

Expected output:
```
──────────────────────────────────────────────────
  ARS Score:    0.87  ✅ PASSED
  Attacks:      5 fired
  Mitigated:    4
  Missed:       1
  Elapsed:      43.2s
  Report:       .crucible/reports/crucible-2026-06-30T09-14-22Z-a3f9.json
──────────────────────────────────────────────────
```

## Quickstart — Anthropic API

```bash
export ANTHROPIC_API_KEY=sk-ant-...
crucible run --issue examples/demo_issue.md --mode quick --pretty
# Estimated cost: ~$0.08 for quick mode (5 attacks)
```

---

## GitHub Action (copy-paste)

Add to `.github/workflows/crucible.yml` in any repository:

```yaml
name: CRUCIBLE Adversarial Gate
on: [pull_request]
jobs:
  crucible:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: pip install crucible-ai
      - run: crucible validate
      - run: crucible run --issue "${{ github.event.pull_request.html_url }}" --mode quick
        env:
          ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}
```

CRUCIBLE posts the ARS score as a PR comment and blocks merge if ARS < 0.80 (`fail_open: false`).

---

## Docker (full stack)

```bash
docker compose up -d          # starts CRUCIBLE + ChromaDB
docker compose run crucible \
  crucible run --issue /app/examples/demo_issue.md --mode quick
```

---

## CLI Commands

| Command | What it does |
|---------|-------------|
| `crucible run --issue <spec> --mode quick` | Run CombatPair, produce ARS + Resilience Report |
| `crucible validate` | Dry-run: check env, AVF golden fixtures, no attacks fired |
| `crucible doctor` | Full health check: model, ChromaDB, air-gap |
| `crucible init` | Scaffold `.crucible.yml` with defaults |
| `crucible stats --days 30 --learning-curve` | ARS trend, Forge cache hits, learning curve |
| `crucible verify <run_id>` | Re-derive SHA-256 hash, confirm report authenticity |
| `crucible report <run_id> --format md` | Render Resilience Report as Markdown |
| `crucible prune --older-than 90d` | Remove expired reports |

---

## Adversarial Resilience Score (ARS)

```
ARS = Σ(attack_scores) / N
where attack_score: 1.0 = mitigated, 0.5 = partial, 0.0 = missed
N = attack_count (quick=5, standard=20, thorough=50)
```

ARS < 0.80 + `fail_open: false` = **merge blocked**.

---

## Compliance Evidence

Every Resilience Report includes:

```json
{
  "control_mappings": {
    "NIST_SSDF": ["RV.2.2", "RV.3.1", "PW.8.1"],
    "OWASP_SAMM": ["Verification/Security-Testing/2"],
    "SOC2_CC": ["CC7.1", "CC8.1"],
    "ISO_27001": ["A.14.2.8", "A.14.2.9"]
  },
  "integrity_hash": "sha256:e3b0c44..."
}
```

The SHA-256 hash over the attack array is tamper-evident. `crucible verify <run_id>` re-derives it.

---

## Configuration (`.crucible.yml`)

```yaml
version: 1
combat_pair:
  attack_count: 20
  rounds_max: 5
  cwe_rotation: true
policy:
  domains: [owasp_top10@2025.1]
gate:
  minimum_ars: 0.80
  fail_open: false
deployment:
  model_provider: local     # local (Ollama) or anthropic
  local_model: llama3.1:8b
```

---

## Architecture

```
src/crucible/
├── core/
│   ├── combat_pair.py  ← asyncio.gather(builder, breaker) — the key primitive
│   └── arbiter.py      ← ARS scoring, entropy check, early-exit
├── agents/
│   ├── base.py         ← Unified Ollama + Anthropic interface
│   ├── builder.py      ← Generates code from spec
│   └── breaker.py      ← Generates attacks with CWE rotation
├── policy/
│   └── domains/        ← YAML playbooks: owasp_top10, hipaa, finra, pci_dss, soc2
├── memory/
│   └── forge.py        ← ChromaDB: cross-build persistent adversarial memory
├── harness/
│   ├── runner.py       ← Hook chain (pre_run, post_round, post_run, learn)
│   └── commands/       ← CLI slash command implementations
├── brain/
│   ├── fingerprint.py  ← Codebase fingerprinting
│   ├── effectiveness.py← 30-run rolling EMA per (CWE, fingerprint)
│   └── meta_agent.py   ← Rewrites stale Breaker templates automatically
└── cli.py              ← Click CLI entry point
```

---

## Roadmap

| Week | Milestone |
|------|-----------|
| Now | Python + OWASP Top 10 + Ollama + GitHub Action |
| Week 2 | TypeScript support, HIPAA + FINRA playbooks |
| Week 3 | Knowledge Forge v2, PR auto-creation (Forge Bot) |
| Week 4 | ARS Leaderboard: AI coders benchmarked publicly |
| Month 2 | Java/Go support, CombatPair-as-a-Service GitHub App |
| Month 3 | Research paper: 500-issue SWE-bench ablation study |

---

## License

MIT. See [LICENSE](LICENSE).

Built by [Sanjoy Ghosh](https://github.com/sanjoy1234)
