<div align="center">

# ⚡ PATTERNS ⚡

**the reusable architectural patterns Olympus formalizes**

</div>

---

The cognitive-substrate concepts named in this document are not specific to Greek mythology. The mythology is the API; the patterns are the underlying contribution. Anyone building a long-running agent — with or without Olympus — should know these.

Each pattern has: the **shape** (what it is, abstractly), the **Olympus instance** (how Olympus implements it), and the **invariant it preserves** (why you need it).

---

## P1 — Append-only audit-of-record

**Shape.** Every load-bearing event is recorded in an append-only log. Old entries are never edited. The current state of any thing is a function of the log up to now.

**Olympus instance.** `titans/mnemosyne.py` — per-kind JSONL files under `state/mnemosyne/`. `underworld/styx.py` extends this with cryptographic chain-hashing for constitutional commitments.

**Invariant it preserves.** *Reconstructability.* After the fact, an operator can answer "why did this happen?" from the log alone.

**Anti-pattern this defends against.** *Silent state mutation.* The version of code that runs today is not necessarily the version that ran last week; the log records what actually happened.

---

## P2 — Bounded autonomy by risk class

**Shape.** Every action the agent takes is classified by reversibility cost. LOW reverses easily; HIGH does not. The agent acts autonomously on LOW, proposes on MEDIUM, refuses HIGH without explicit operator authorization.

**Olympus instance.** `LOW` / `MEDIUM` / `HIGH` / `COMPOSITE` risk classes defined in `codex/COSMOGONY.md` and enforced by `zeus.can_perform()` reading Styx oaths.

**Invariant it preserves.** *Operator control proportional to consequence.* The cheaper the mistake, the more freedom the agent has; the more expensive, the more the operator owns it.

**Anti-pattern this defends against.** *Autonomy creep.* An agent that auto-ratifies its way into structural changes the operator never approved.

---

## P3 — Adversarial-pair persona protocol

**Shape.** Two personas, deliberately opposed, both consulted on every significant decision. One proposes; one contests. Neither rules. The operator decides.

**Olympus instance.** Hephaestus (the Architect — `src/olympus/olympians/hephaestus.py`) proposes; Momus (the Anti-Architect — `src/olympus/heroes/momus.py`) contests via an eight-pattern catalog (AP1–AP8). Decision records (Delphi) capture both voices.

**Invariant it preserves.** *Symmetric scrutiny.* Every proposal that ships had to survive its strongest critic.

**Anti-pattern this defends against.** *Single-advisor capture.* An agent whose "thinking" is one well-trained voice talking to itself.

---

## P4 — Decentralized observation with emergent synthesis

**Shape.** Many independent observers each scan one slice. No observer imports another. Aggregation happens at read time, not write time.

**Olympus instance.** Argos's Eyes (`src/olympus/monsters/argos/eyes/`) — each Eye is one module, deterministic, isolated. Synthesis comes from `CorrelationEngine` walking the aggregated pheromone log.

**Invariant it preserves.** *Resilience under partial failure.* Removing N observers degrades coverage gracefully; no observer's bug breaks the others.

**Anti-pattern this defends against.** *Central-synthesis brittleness.* A single observer-correlator pipeline whose failure modes are global.

---

## P5 — Read-only watcher tier with one immortal

**Shape.** Read-only observers watch slices of the substrate. Observers can be replaced (their replacement may take a different form), but the slice coverage is structural. One immortal observer watches whether the others are still observing.

**Olympus instance.** HYDRA (`src/olympus/monsters/hydra/`) — eight mortal heads, one immortal. The immortal head fires ALERT when any mortal head emits zero findings.

**Invariant it preserves.** *Coverage is a structural property, not a runtime check.* Even if every individual watcher is rewritten, the slices remain covered.

**Anti-pattern this defends against.** *Silent watcher death.* A watcher hangs / crashes / gets rewritten with a bug; coverage drops; no one notices until the thing it was watching breaks.

---

## P6 — Falsifiable predicate registry

**Shape.** Predictions about the future are first-class objects with a `verify()` callable that can be checked when the predicted moment arrives. Unfalsifiable predictions are refused at register-time.

**Olympus instance.** Apollo (`src/olympus/olympians/apollo/oracle.py`) — `Apollo.predict()` raises `ValueError` if a Prediction's `verify` is None. Acceptance rate is reported by `apollo.acceptance_rate()`.

**Invariant it preserves.** *Predictions you actually grade.* A prediction that cannot be graded is a wish.

**Anti-pattern this defends against.** *Prophet-talk.* An agent that produces confident statements about the future that no one ever checks.

---

## P7 — Substrate-vocation slot

**Shape.** The substrate prescribes the *shape* of operation (record everything, route by risk, debate hard decisions) but takes NO stance on *what the deployment is for*. Each deployment writes its own one-sentence vocation; the substrate then enforces it.

**Olympus instance.** Hestia's `kindle(name, vocation)` records a one-sentence vocation in a byte-frozen hearth-seal. The substrate refuses to operate without one. The vocation's *content* is per-deployment.

**Invariant it preserves.** *Substrate neutrality.* A surveillance tool, a research assistant, a personal AI, and a trading agent can all adopt the substrate without ideological contradiction.

**Anti-pattern this defends against.** *Frameworks that pretend to be neutral but bake in a worldview.* The substrate has S8 (Continuity of Understanding); it does NOT have an opinion on surveillance, centralization, or retention — those are deployment choices.

---

## P8 — Constitutional invariant tier

**Shape.** A small, named, numbered set of substrate-level claims (S1, S2, …) that all deployments share. They are enforced *structurally*, not aspirationally — each one has a runtime check or a test that fails when it's violated.

**Olympus instance.** S1–S8 in `codex/COSMOGONY.md`, enumerated in `src/olympus/titans/themis.py`, tested in `tests/test_invariant_enforcement.py`. The constitution is also a Python module: `from olympus.titans.themis import themis; themis.all()`.

**Invariant it preserves.** *Architectural claims that cannot drift.* A substrate "promise" with no enforcement decays to a hope; a substrate promise with an enforcing test stays true or the test fails.

**Anti-pattern this defends against.** *README-as-constitution.* Architectural claims that exist only in prose, which the code can quietly violate.

---

## P9 — Hecate-at-crossroads error handling

**Shape.** When an operation fails, the framework offers four named paths: retry, abandon, descend (archive the failure state), escalate. The caller chooses *which* at the call site; the runtime handles the mechanics.

**Olympus instance.** `src/olympus/underworld/hecate.py` — `at_crossroads(attempt, on=Crossroads(retry=..., abandon=..., descend=..., escalate=...))`. Quarantines the failure to Tartarus and records in Mnemosyne.

**Invariant it preserves.** *Failure semantics are explicit.* You can't tell at the call site whether a try/except is "should retry" or "should crash" by reading. With Hecate, the four roads are named.

**Anti-pattern this defends against.** *Bare except: pass.* Silent failure absorption that loses both the error and the question of what should happen next.

---

## P10 — Lifecycle as a state machine

**Shape.** Components don't just exist or not — they pass through phases (unborn / nascent / active / quiescing / dormant / ended). Phase transitions are explicit, append-only, and refuse regression.

**Olympus instance.** `src/olympus/titans/iapetus.py` — `Lifecycle.advance_to(phase)` validates the transition is forward. `src/olympus/runtime/recovery.py::retire_component()` runs the canonical end-of-life sequence and archives final state to Hades.

**Invariant it preserves.** *Components have endings.* "How does this thing shut down?" is answerable for every Olympus component.

**Anti-pattern this defends against.** *Components that get installed but never get retired.* The dead-but-still-imported module problem.

---

## Composition

These ten patterns compose. Olympus is not "P1 plus P2 plus ..."; the patterns reference each other:

- The audit-of-record (P1) is what makes adversarial-pair (P3) meaningful — both voices land in the same log.
- Bounded autonomy (P2) needs the falsifiable predicate registry (P6) so the operator can hold the agent to its predictions.
- Decentralized observation (P4) needs the immortal head (P5) so silent failures surface.
- The constitutional invariant tier (P8) is what gives the vocation slot (P7) its structural meaning — S1–S8 enforce HOW; the slot fills in WHAT.

The patterns are useful individually. They are powerful together.

---

*The mythology is the API. The patterns are the contribution. Use them with or without Olympus.*
