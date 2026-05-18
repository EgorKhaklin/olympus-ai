# Delphi — the self-improvement arc

**Risk class:** COMPOSITE
**Decided:** Position A — Prometheus (bounded auto-improver) + Bash cron + Iris dashboard
**Sworn on Styx at seq=46.**

Zeus's question (verbatim):

> *"Use the system now to improve the system itself... so it has more bite, and put it on a cognitive self improvement loop. I noticed we've only used Python, do you need any other language to make this all better"*

---

## Two questions, debated separately through the architecture.

### Q1 — How does Olympus improve itself?

| candidate | dings | passes |
|---|---|---|
| **Prometheus — auto-act on LOW** | **(none)** | AP1, AP3, AP6, AP7, AP8 |
| LLM-driven self-modification | AP6, AP1, S2, S7 | — |
| Manual only | AP5 | AP6 |

**Position A.** Prometheus reads ratified LOW-risk actions and dispatches to a handler registry. The substrate auto-improves only within S7 bounds:

- LOW actions with zero Momus contests → Prometheus may execute
- MEDIUM and above → still require Zeus
- Every execution records before/after state to Mnemosyne (S8 reconstructability)
- Handlers must name what changes visibly (AP8 defense)

**Refused — LLM-driven self-modification.** Same AP6 (understanding-obscuring) + AP1 (no ground-touch) that killed the LLM-injection proposal in the substance arc. Plus S2 (non-determinism) and S7 (autonomous code-edits are HIGH-risk by definition). LLM-coupled self-modification is not Olympus.

**Refused — Manual only.** AP5: declines an explicit Zeus directive for a LOOP.

### Q2 — Other languages?

Honest assessment of each:

| language | verdict | reason |
|---|:---:|---|
| **Bash** | ✅ ship | cron is bash's native habitat; pure orchestration, no logic |
| **HTML + vanilla JS** | ✅ ship | `invoke wisdom` is text; visualization deserves rendering. No build step. No framework. Static files reading `state/*.jsonl`. |
| Rust | ❌ refuse | no current need; AP8 (decorative) at this scale |
| TypeScript | ❌ refuse | vanilla JS suffices; build complexity unjustified |
| SQL | ❌ refuse | JSONL meets every current need; opaque rows would obscure audit trail (AP6) |

The substrate is Python because reasoning over JSONL records is what Python is best at. Languages get added only when they solve a real problem Python doesn't.

---

## What lands

### Prometheus — `src/olympus/heroes/prometheus.py`

- Reads `mnemosyne.recall("action.promoted")` for ratified LOW actions
- Dispatches each to a handler registered for its drift signature
- Records before/after state per slice
- Handler registry includes:
  - `state-rotation` — when a JSONL exceeds 10k lines, rotate it
  - `brief-archive-compaction` — keep only the last N=50 briefs
  - `prophecy-graduation` — accepted ≥5 times → mark graduated
  - `prophecy-retirement` — rejected ≥3 times → mark retired
  - `dead-eye` — eye that emitted no findings for 30+ days → flag for Zeus

### scripts/loop.sh — bash cron loop

```bash
#!/usr/bin/env bash
# Run a session + improvement pass every N minutes.
# Add to crontab: */10 * * * * /path/to/scripts/loop.sh
```

Pure orchestration: cron → loop.sh → `invoke session` + `invoke improve` → logs.

### Iris — `src/olympus/iris/`

- `iris/__init__.py` — Python module that reads state and emits static HTML
- `iris/static/template.html` — the page shell
- `iris/static/iris.js` — vanilla JS, no framework, fetches JSONL files
- `iris/static/iris.css` — gold/wine/marble palette (matches Aphrodite)

`invoke iris` builds the dashboard into `state/iris/index.html`. Operator opens in any browser. No server needed.

### CLI surface

- `invoke improve` — Prometheus runs one improvement pass
- `invoke improve --loop --interval N` — runs continuously
- `invoke iris` — build the dashboard
- `invoke iris --open` — build + auto-open in browser

---

## Authorization

Zeus's quote captured in the Styx oath payload. Sworn at seq=46.

The decision is recorded; the implementation follows. Future arcs may add domain-specific Prometheus handlers; the substrate-level handler set is what this Delphi authorizes.
