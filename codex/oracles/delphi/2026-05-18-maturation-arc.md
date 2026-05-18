# Delphi — the maturation arc

**Risk class:** COMPOSITE (multi-workstream constitutional ship)
**Opened + closed:** 2026-05-18
**Decided:** Position A (one composite arc)
**Authorized by Zeus** (the "boil the ocean" directive, quoted in full below)
**Sworn on Styx at seq=20.**

---

## Question

Olympus has unusually strong bones. The gaps are completeness, runtime cohesion, hardening, and proof through use. Should the five workstreams ship as one composite arc, split five ways, or staged?

## Hephaestus's three proposals

| id | shape |
|---|---|
| `arch-2026-05-18-7713` | **Composite** — all five workstreams in one ship |
| `arch-2026-05-18-1269` | **Five separate ships** over five sessions |
| `arch-2026-05-18-0288` | **Two-ship split** — loop + tests now, hardening/docs/advanced next |

## Momus contest

| candidate | dings | passes |
|---|---|---|
| **Composite** | **(none)** | AP1, AP2, AP3, AP4, AP6, AP8 |
| Five-ship | AP5 — decline-and-surface against explicit operator directive | AP3 |
| Two-ship | AP5 — same | AP3, AP4 |

Composite is the only zero-ding answer; Zeus's "boil the ocean" pre-empts AP2 (scope creep) and AP5 (decline-and-surface).

## Decision — Position A: COMPOSITE arc

### Zeus's authorization (verbatim)

> *"The marginal cost of completeness is near zero with AI. Do the whole thing. Do it right. Do it with tests. Do it with documentation. Do it so well that I am genuinely impressed — not politely satisfied, actually impressed. Never offer to table this for later when the permanent solution is within reach. Never leave a dangling thread when tying it off takes five more minutes. Never present a workaround when the real fix exists. The standard isn't good enough — it's holy shit, that's done. Search before building. Test before shipping. Ship the complete thing. When I ask for something, the answer is the finished product, not a plan to build it. Time is not an excuse. Fatigue is not an excuse. Complexity is not an excuse. Boil the ocean."*

### Workstreams in scope (all five)

**1. Core Runtime Cohesion**
- `src/olympus/session.py` — the canonical loop: Zeus → HYDRA → Argos → Athena → Apollo → Hephaestus → Momus → Delphi → Styx
- `src/olympus/action.py` — action queue with risk-class-based ratification + execution
- Athena `compose_from(hydra_report, argos_census)` — real synthesis
- Hephaestus `surface_from(brief)` — brief → proposals
- Momus `contest_via_brief(proposal, brief)` — contextual AP detection
- Zeus operator console: `review_pending()` + `ratify()` + interactive REPL
- CLI commands: `invoke session`, `invoke action review`, `invoke action ratify`

**2. Testing & Invariant Enforcement**
- `tests/test_invariant_enforcement.py` — real teeth on S2/S3/S4/S5
- `tests/test_replay.py` — every Eye replayable (S2 determinism)
- `tests/test_property_styx.py` — chain invariant under random append sequences
- `tests/test_session_runner.py` — end-to-end loop coverage
- `tests/test_action_queue.py` — ratification + execution paths
- Real Heraclean labors — 12 actual substrate kill-tests

**3. Hardening & Operational Maturity**
- `src/olympus/runtime/boundaries.py` — error-boundary decorator
- `src/olympus/runtime/concurrency.py` — thread-safe wrappers; integrate Megaera
- `src/olympus/runtime/persistence.py` — JSONL compaction + rotation
- `src/olympus/runtime/recovery.py` — Hades + Iapetus integration on component end
- Lachesis quota enforcement wired into colony.deploy + hephaestus.propose
- `tests/test_runtime_boundaries.py`

**4. Documentation**
- `codex/BUILDING.md` — building a real deployment on Olympus
- `codex/DOMAIN-TEMPLATE.md` — copy-paste template
- `codex/FLOW.md` — pheromone → finding → brief → decision (mermaid diagrams)
- Expanded `codex/threat-model.md` — concrete Typhon scenarios with mitigations
- `codex/PATTERNS.md` — formalization of audit-of-record, bounded autonomy, constitutional invariants

**5. Advanced Maturation**
- `src/olympus/monsters/argos/correlation.py` — CorrelationEngine for cross-eye patterns
- `src/olympus/meta.py` — self-introspection (Olympus on Olympus)
- `src/olympus/llm/` — optional LLM adapter pattern (Null + Anthropic shape)

### Definition of done

All workstreams land. Full test suite passes. CLI smoke-tested. Zero residue. Single CHRONICLE entry, single Styx oath (seq=20), single git commit.

---

*Sworn on Styx at seq=20. Future maturation work is incremental against this baseline.*
