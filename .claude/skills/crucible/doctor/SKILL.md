---
name: crucible:doctor
description: Full CRUCIBLE environment health check — model reachable, ChromaDB writable, AVF fixtures pass, no unexpected outbound network (air-gap verification). Use before first run or when debugging failures.
---

# /crucible:doctor

Runs all environment health checks. Use this before the first run or when something is broken.

## Usage

```
/crucible:doctor [--network-check]
```

## Execution

```bash
crucible doctor --network-check
```

## Checks Performed

| Check | What It Tests | Fix If Fails |
|-------|---------------|--------------|
| Ollama reachable | `GET http://localhost:11434/` responds | `ollama serve` |
| Model available | `llama3.1:8b` (or configured model) listed | `ollama pull llama3.1:8b` |
| ChromaDB writable | Can write/read to `.crucible/forge/` | Check disk space + permissions |
| AVF gate | Breaker finds >75% on golden fixtures | Check model quality |
| Network check | No unexpected outbound calls (air-gap) | Disable community_brain |
| reports dir | `.crucible/reports/` writable | `mkdir -p .crucible/reports` |
| Python version | >=3.11 | Install Python 3.11+ |

## Output to User

Show a checklist with ✓/✗ per item. For any ✗, show the specific fix command. End with overall PASS or FAIL.
