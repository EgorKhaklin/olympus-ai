# Delphi — closing the honest-gap arc

**Risk class:** COMPOSITE
**Opened + closed:** 2026-05-18
**Decided:** Position A — composite ship
**Sworn on Styx at seq=26.**

---

## Question

Zeus surfaced an honest-gap assessment: five items between the current Olympus and "the very best." Each one shipped, the standard is genuinely impressed.

| priority | gap | why it matters |
|---|---|---|
| HIGH | Full end-to-end session loop feels cohesive | currently feels like individual components rather than one flowing system |
| HIGH | Deep test coverage for S1–S8 | many invariants are declared but not yet rigorously enforced |
| MEDIUM | Real usage examples / demo domain | hard to feel the value without seeing it run |
| MEDIUM | More mature CLI surface | the CLI exists but still feels thin |
| LOWER | Correlation + action promotion polish | good direction, needs more integration |

Composite vs. priority-cut vs. demo-first?

## Decision — Composite (zero Momus dings)

All five gaps ship in one commit. The substrate gets genuinely-impressive in one move rather than across five.

### Scope

**Workstream 1 — Session cohesion**
- `Session.run_with_callback(on_phase=fn)` — observability hook
- `Session.run_verbose()` — streams each phase with rich detail
- `SessionReport.render(verbose=True|False)` — show the brief, the proposals, the contests
- `invoke session --verbose` + `invoke session --json`
- `invoke loop --interval N` — run sessions on a cadence

**Workstream 2 — Correlation × Action integration**
- `hephaestus.surface_from(brief, correlation=...)` — proposals weighted by cluster strength
- Quiet eyes generate proposals (an eye that stopped is itself a finding)
- Cascade patterns reweight risk class upward

**Workstream 3 — Deep S1–S8 test suite**
- `tests/test_invariant_S1.py` through `tests/test_invariant_S8.py` — one file per invariant, 5–10 tests each, covering positive AND negative cases

**Workstream 4 — Mature CLI**
- `invoke status` — one-line health snapshot
- `invoke list [tier]` — show all gods + their roles
- `invoke describe <god>` — full module docstring + interface
- `invoke history [N]` — last N sessions with outcomes
- `invoke version`
- `invoke loop --interval N` — auto-session cadence
- `invoke shell` — interactive multi-command REPL
- `--json`, `--quiet`, `--no-color` global flags
- Better `--help` output per command
- Aliases (`ls` → `list`, etc.)

**Workstream 5 — Notekeeper demo**
- `examples/notekeeper/` — a complete working deployment
  - `DOMAIN.md` — vocation, anti-mission, C1–C5 invariants
  - 3 custom Eyes (stale_notes, orphan_links, capture_velocity)
  - 1 custom Head (topic_drift)
  - 2 Apollo predictions
  - `notekeeper/` application code (capture, link, recall)
  - `README.md` — clone, kindle, run-in-90-seconds walkthrough
  - Tests

## What this Delphi authorizes

Single commit. All five workstreams. Full test pass required. End-to-end demo runs cleanly.

## Authorization quote (Zeus, verbatim)

> *"Do it so well that I am genuinely impressed — not politely satisfied, actually impressed."*

---

*Sworn on Styx at seq=26. The commit closing this Delphi is the final ship of the v0.1 era.*
