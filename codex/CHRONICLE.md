<div align="center">

# ⚡ CHRONICLE ⚡

**the record of what has been done**

</div>

---

Newest first. Each entry names what changed, what was sworn, who decided.

---

## 2026-05-18 — the self-improvement arc (COMPOSITE)

**Risk class:** COMPOSITE.
**Delphi:** [`codex/oracles/delphi/2026-05-18-self-improvement-arc.md`](oracles/delphi/2026-05-18-self-improvement-arc.md)
**Sworn on Styx at seq=46.**

Zeus's directive, verbatim:

> *"Use the system now to improve the system itself... so it has more bite, and put it on a cognitive self improvement loop. I noticed we've only used Python, do you need any other language to make this all better"*

The architecture reached two decisions in parallel: **how** Olympus improves itself, and **what** languages it needs.

### Q1 — Prometheus (the bounded auto-improver)

Hephaestus surfaced three candidates: Prometheus (handler-registry, bounded to LOW-risk + zero Momus contests), LLM-driven self-modification, and manual-only. Momus dinged LLM-self-modification on AP6 (understanding-obscuring) + AP1 (no ground-touch) + S2 (non-determinism) + S7 (autonomous code edits are HIGH-risk). Manual-only dinged AP5 (declines explicit Zeus directive). **Prometheus took zero dings — it ratified.**

`src/olympus/heroes/prometheus.py` — a Titan of forethought. Each pass dispatches a handler registry; each handler returns `(before, after)` state recorded to Mnemosyne (S8 reconstructability). Five built-in handlers ship:

- **state-rotation** — rotate JSONL files > 10k lines
- **brief-archive-compact** — keep last 50 briefs in `state/athena/`, archive older
- **prophecy-graduate** — mark predictions accepted 5+ consecutive times
- **prophecy-retire** — mark predictions rejected 3+ times
- **dead-eye-flag** — surface eyes silent for 30+ days for Zeus review

Prometheus does not edit source code, modify the constitution, or take any action without a recorded drift signature. Domain deployments register additional handlers via `prometheus.register(name, fn)`.

### Q2 — Bash for cron, vanilla JS + HTML for visualization. No Rust, TypeScript, or SQL.

Honest assessment per language:

| language | verdict | reason |
|---|:---:|---|
| **Bash** | ✅ ship | cron is bash's native habitat — pure orchestration |
| **HTML + vanilla JS** | ✅ ship | dashboards need rendering; no build step required |
| Rust | ❌ refuse | AP8 (decorative) — no current need |
| TypeScript | ❌ refuse | vanilla JS suffices; build complexity unjustified |
| SQL | ❌ refuse | JSONL meets every current need; rows would obscure audit (AP6) |

Languages get added when they solve a real problem Python doesn't. Currently: nothing else does.

### scripts/loop.sh

Pure-bash orchestration. `./scripts/loop.sh` runs one pass (cron-safe). `./scripts/loop.sh --loop --interval 600` runs continuously. `--dry-run` reports without invoking. Crontab example documented in the script's `--help`.

### Iris — the rainbow-messenger

`src/olympus/iris/` reads `state/*.jsonl` and renders a single self-contained HTML file (CSS + JS + JSON-data island inlined). No server. No framework. No fetch. Open `state/iris/index.html` in any browser. Palette echoes Aphrodite (gold / wine / marble / sea / laurel). Seven panels:

- **session timeline** — last 15 cognitive passes with hydra/argos/proposals/furies counts
- **slice heatmap** — where Hydra's heads have looked, ranked by alert intensity
- **Apollo prophecies** — verifications with acceptance rate
- **Hephaestus proposals** — ratified and rejected, with drift signatures
- **Prometheus passes + per-handler outcomes** — the substrate improving itself
- **Styx chain status** — total oaths, last seq, last hash, last sworn

### CLI

- `invoke improve` — Prometheus runs one pass
- `invoke improve --loop --interval N` — runs continuously
- `invoke iris` — build the dashboard
- `invoke iris --open` — build + open in browser

### Tests

`test_prometheus.py` (7) — handler registration, dispatch, before/after recording, failure isolation, built-in handler resilience.
`test_iris_build.py` (7) — snapshot purity, render produces self-contained HTML, no external refs, all panel mounts present, `</script>` breakout neutralized.
`test_loop_invocation.py` (5) — script exists/executable, bash shebang, dry-run wiring, --help documents crontab, unknown flags rejected.

Full suite: 173 tests, all green.

---

## 2026-05-18 — the substance arc (COMPOSITE)

**Risk class:** COMPOSITE.
**Delphi:** [`codex/oracles/delphi/2026-05-18-substance-arc.md`](oracles/delphi/2026-05-18-substance-arc.md)
**Sworn on Styx at seq=37.**

Zeus's critique, verbatim:

> *"Right now it reads as a very well-designed constitutional framework more than a running cognitive engine. … The mythology has to justify its overhead by producing clearer thinking and better behavior than simpler named components would."*

Reached through the architecture: Hephaestus surfaced three candidates (history-aware reasoning across all gods, LLM-injected synthesis, more eyes + heads). Momus contested via AP1–AP8; history-aware reasoning was the only zero-ding answer. LLM-injection dinged AP6 (understanding-obscuring) + AP1 (no ground-touch). More-observers dinged AP8 (decorative) + AP3 (instance-vs-class).

### Athena reads Mnemosyne

`athena.compose_from(...)` now pulls the last 7 session.completed memories and the prior brief archive. The Brief gains five new fields:

- **insights** — concrete English claims from cross-session reasoning
- **recurring_slices** — alerted in ≥3 of last 7 sessions
- **newly_alerted_slices** — alerting now, not in last 5
- **resolved_slices** — alerted last session, not this one
- **stable_slices** — INFO in majority of recent priors

The brief now says things like *"slice 'codex/journal/' has alerted in 4 of the last 7 session(s) — pattern, not noise."* A single-session view cannot make that claim.

### Apollo's prophecies become operational

`apollo.consult_due()` auto-verifies every prediction whose horizon has passed. Outcomes are recorded in Mnemosyne under `kind="prophecy.verified"`. `apollo.trend(window=10)` returns the rolling acceptance rate. The session calls `consult_due()` at start — prophecies that drift past their horizon are no longer dead weight, they get graded automatically.

### Hephaestus reads `action.rejected`

Before surfacing a proposal, Hephaestus computes a drift signature (`{source}::{slice}`) and checks two sets:

- **recently_rejected** (last 7 days) — silent skip
- **chronic** (≥3 rejections ever) — emit a single `proposal-fatigue` signal instead

The agent stops nagging on drifts Zeus has already killed.

### The Furies fire in the loop

Each session now starts with a Tisiphone Styx-verify pass. If the chain is broken, Alecto raises an immediate ALERT visible in `SessionReport.fury_alerts`. The Furies are no longer decorative — they are part of every pass.

### SessionReport.deltas

Each session compares to the most recent prior `session.completed` memory:

- `delta_prior_session_id` — what we're comparing to
- `delta_hydra_change` / `delta_argos_change` — count trend
- `delta_new_alerts` — slices alerting now that weren't before
- `delta_resolved_alerts` — slices that resolved since last pass

The verbose render surfaces deltas at the TOP of the session output — *what changed* is the first thing the operator sees.

### `invoke wisdom`

New CLI command. Reads Mnemosyne, the Brief archive, Styx, and the action queue. Surfaces concrete cross-session claims: ratification rate, error rate, recurring slices, prophecy accuracy, repeated drifts, oath frequency by actor. The substrate explains what it has learned, quantitatively.

### codex/INTELLIGENCE.md

A new top-level doc that addresses Zeus's critique directly: *how does mythology-organized substrate produce clearer thinking than flat naming?* Names the five concrete intelligence claims and explains why the mythology earns its overhead. The substance argument made in operator-readable prose.

### Verification

- 154/154 tests pass (was 147, +7 new for history-aware reasoning + prophecy cycle + rejection memory + session deltas + wisdom)
- End-to-end `invoke session` now surfaces insights: *"14 slice(s) have been stable across the last 7 sessions"*
- `invoke wisdom` surfaces quantitative claims: *"of 93 proposal(s) ever surfaced by Hephaestus, 27% were ratified by Zeus"*
- Styx chain intact across 38+ oaths

Zeus's critique is closed. The mythology earns its overhead by accumulating legible understanding session-over-session — a flat substrate could implement the same logic, but the *names* compress the API in a way that survives across contributors.

---

## 2026-05-18 — honest-gap closure (COMPOSITE)

**Risk class:** COMPOSITE.
**Delphi:** [`codex/oracles/delphi/2026-05-18-honest-gap-closure.md`](oracles/delphi/2026-05-18-honest-gap-closure.md)
**Sworn on Styx at seq=26.**

Zeus surfaced five remaining gaps to reach "the very best." All five shipped in one ship. The substrate now feels like one flowing system, the invariants are rigorously enforced, the CLI is mature, a real demo exists, and correlation is wired into action promotion.

### Session cohesion (HIGH)

- **`SessionReport.render(verbose=True|False)`** — rich phase-by-phase display showing the brief text, the proposals with their drifts/fixes/Momus dings, the correlation summary, and the action routing. The loop now reads as one flow.
- **`Session.run_with_callback(on_phase=fn)`** — observability hook fired at every phase boundary; callbacks must not raise (loop continues regardless).
- **Phase-by-phase wiring** — `_observe_hydra`, `_observe_argos`, `_synthesize`, `_correlate` (new), `_propose_and_contest`, `_promote`, `_record` — each phase fires a callback, populates report fields, never silently swallows state.
- **`SessionReport.duration_ms`** — every session times itself.
- **`hydra_alert_details` + `argos_alert_details` + `brief_recommendation_text` + `correlation_summary`** — actual content surfaces in the verbose render rather than just counts.

### Correlation × action integration (LOWER)

- **`hephaestus.surface_from(brief, correlation=...)`** — proposals now incorporate the CorrelationEngine's report.
- **Cluster strength upgrades risk** — a slice corroborated by ≥3 eyes upgrades LOW → MEDIUM and MEDIUM → HIGH.
- **Quiet eyes generate proposals** — an eye that has stopped depositing is itself a finding; surfaces as a MEDIUM proposal.
- **Cascade patterns annotate rationale** — proposals reference cascade frequency where relevant.

### Deep S1–S8 test suite (HIGH)

One dedicated file per invariant, 5–10 tests each. **+59 new tests.** Total substrate suite now 135/135 passing.

| invariant | file | what's covered |
|---|---|---|
| **S1** | `tests/test_invariant_S1.py` | append-only writes, recall order, per-kind isolation, actor filter, immutability under appends, kinds listing, body fields round-trip, kind-filename sanitization |
| **S2** | `tests/test_invariant_S2.py` | replay determinism, seed stability across instances, seed uniqueness across classes, no `random` imports, Eros determinism on edge cases, 1000-distinct-id uniqueness, colony.deploy signature stability |
| **S3** | `tests/test_invariant_S3.py` | AST-scan for forbidden writes, AST-scan for `open(mode='w')`, observe returns HeadFinding list, observe stability under repeat, no head imports action/session |
| **S4** | `tests/test_invariant_S4.py` | no Eye imports sibling Eye, no Eye imports colony, no Eye reads pheromone log, every Eye runs in isolation, synthesis lives outside Eyes |
| **S5** | `tests/test_invariant_S5.py` | Apollo refuses no-verify, accepts callable, consult records outcome, handles false return, handles verify raising, acceptance rate counts only verified, unverified returns None, predictions listing |
| **S6** | `tests/test_invariant_S6.py` | delphi dir exists, at-least-one recorded, every delphi has Decision section, every delphi names Position, every delphi references Styx, action queue routes HIGH → delphi-pending, HIGH ratify swears on Styx |
| **S7** | `tests/test_invariant_S7.py` | LOW auto-ratifies, LOW + contests queues, MEDIUM always queues, HIGH/COMPOSITE always delphi-pending, Zeus.can_perform('LOW') always True, HIGH requires oath, unknown risk class returns False, execute refuses unratified |
| **S8** | `tests/test_invariant_S8.py` | Themis names S8, COSMOGONY mentions S8, Momus AP6 enforces understanding, eye_understanding_gap registered, no anonymous load-bearing memories, every session has session_id, every oath has sworn_by, Styx chain intact, action lifecycle reconstructible |

### Mature CLI (MEDIUM)

The `invoke` surface now has 19 errands plus three global flags:

- **`invoke status`** — one-line health snapshot (hearth, styx, hydra, argos, actions, sessions)
- **`invoke list [tier]`** — tree of named modules per tier
- **`invoke describe <tier.god>`** — full docstring + public-interface listing for any god module
- **`invoke history [N]`** — last N sessions from Mnemosyne
- **`invoke version`** — show olympus version
- **`invoke loop --interval N [--count K]`** — auto-session cadence; Ctrl-C to stop
- **`invoke shell`** — interactive multi-errand REPL
- **`invoke help <errand>`** — per-errand detail with global-flag reference
- **`invoke session --verbose`** — rich render mode showing brief + proposals + contests
- **`invoke session --json`** — machine-readable session report
- **`--json` / `--quiet` / `--no-color`** — global flags consumed before dispatch, honored across errands

### Notekeeper demo deployment (MEDIUM)

`examples/notekeeper/` — a complete working deployment in ~350 lines of domain code:

- **`DOMAIN.md`** — vocation, anti-mission, C1–C5 invariants with enforcement points, risk-class examples, three domain anti-patterns (AP-NK1..3)
- **`notekeeper/notes.py`** — capture + topic inference + recall (stopword-aware, pure-function topic ranker)
- **`notekeeper/eyes.py`** — three custom Eyes: `EyeUntopicedNotes` (C2), `EyeStaleNotes` (C3), `EyeCaptureVelocity` (C4)
- **`notekeeper/heads.py`** — `HeadTopicDrift` for C5
- **`notekeeper/predictions.py`** — two Apollo predictions with verify() callables
- **`notekeeper/cli.py`** — `python3 -m notekeeper capture | list | topic | recent | stale | session | setup`
- **`tests/test_notekeeper.py`** — 12 tests covering pure functions, capture, eyes, head, end-to-end integration with a real session run
- **`README.md`** — 90-second walkthrough from clone to running deployment

End-to-end demo: after `python3 -m notekeeper setup` + a few captures, `python3 -m notekeeper session` runs Olympus's full loop with **10 HYDRA heads** (9 substrate + notekeeper's `topic_drift`) and **12 Argos eyes** (9 substrate + 3 notekeeper). Athena's brief now incorporates the notekeeper data. The whole cognitive loop is alive against a real domain.

### Verification

- 135/135 substrate tests pass
- 12/12 notekeeper tests pass
- End-to-end notekeeper demo runs clean
- Styx chain intact across 35+ oaths
- Heracles 12/12 labors survive
- `invoke status` returns clean snapshot
- `invoke session --verbose` produces operator-readable flow with every phase showing its work

The five gaps Zeus named are closed. Olympus is now genuinely-impressive-on-arrival.

---

## 2026-05-18 — the maturation arc (COMPOSITE)

**Risk class:** COMPOSITE (multi-workstream constitutional ship).
**Delphi:** [`codex/oracles/delphi/2026-05-18-maturation-arc.md`](oracles/delphi/2026-05-18-maturation-arc.md)
**Sworn on Styx at seq=20.**
**Authorized by Zeus** (the "boil the ocean" directive, verbatim in the Delphi).

Olympus was a beautiful set of parts. This arc made it a running cognitive substrate. All five workstreams Zeus named — runtime cohesion, invariant enforcement, hardening, documentation, advanced maturation — landed in one ship.

### 1 — Core Runtime Cohesion

The canonical loop now exists in `src/olympus/session.py`. One `Session` is one full pass: Zeus → Rhea → HYDRA → Argos → Athena (real synthesis from both observation tiers) → Hephaestus (surfaces proposals from the brief) → Momus (contests via AP1–AP8 heuristics) → action queue (risk-class-routed promotion) → Mnemosyne → Polyhymnia. Every link is wired; every link records.

- **`src/olympus/session.py`** — `Session`, `SessionReport`, `run_session()`. Wraps every phase in error boundaries; captures errors without crashing the loop.
- **`src/olympus/action.py`** — `ActionQueue` with append-only log at `state/action_queue.jsonl`. LOW + no contests auto-ratifies; MEDIUM and contested LOW queue for Zeus; HIGH/COMPOSITE land in `delphi-pending` and require a Styx-sworn ratification.
- **Athena enhancement** — `compose_from(hydra_report, argos_census, label, directive)` reads both observation tiers, surfaces cross-tier corroborations, computes confidence proportional to overlap.
- **Hephaestus enhancement** — `surface_from(brief)` walks the brief's findings + recommendations and emits proposals (capped by a Lachesis quota).
- **Momus enhancement** — `contest_via_brief(proposal, brief)` runs eight AP heuristics over the proposal's text and context, returning the AP ids that fire.
- **Zeus enhancement** — `review_pending()`, `review_delphi()`, `ratify()`, `reject()`, `console()` (interactive REPL).

### 2 — Testing & Invariant Enforcement

The substrate now has 76 tests covering every load-bearing claim.

- **`tests/test_invariant_enforcement.py`** — real teeth on S2 (replay every Eye twice; assert identical), S3 (AST-scan HYDRA heads for forbidden write calls), S4 (AST-scan for sibling-Eye imports), S5 (Apollo rejects predictions without verify()), S8 (no load-bearing memory may be anonymous).
- **`tests/test_property_styx.py`** — three property tests on Styx: append-only (snapshots are prefixes), chain integrity (prev_hash linking), tamper detection (corrupt one byte → first_bad_seq surfaces).
- **`tests/test_session_runner.py`** — end-to-end loop coverage including cross-tier confidence assertion.
- **`tests/test_action_queue.py`** — LOW auto-ratifies, MEDIUM queues, HIGH delphi-pending, contested LOW queues, execution failure quarantines to Hades.
- **`tests/test_runtime.py`** — boundary decorator behavior, atomic_append under 8 concurrent writers (160 rows; all parse), JSONL integrity detection, compaction.
- **`tests/test_correlation.py`** — cluster + cascade + quiet detection.
- **`tests/test_meta_and_llm.py`** — self-portrait shape, NullAdapter behavior, adapter factories raise cleanly when optional SDKs missing.
- **`tests/test_heracles_labors.py`** — all twelve canonical labors are now real substrate kill-tests. Each labor is a specific assertion about HYDRA, Argos, Artemis, Ares, Lethe, Poseidon, Atropos, Hera, Demeter, Apollo, Cerberus, or the cosmogony itself.

### 3 — Hardening & Operational Maturity

- **`src/olympus/runtime/boundaries.py`** — `@bounded(name=...)` decorator: catches any exception, returns `BoundaryResult(ok=False, error=...)`, optionally quarantines + records.
- **`src/olympus/runtime/concurrency.py`** — `with_lock(name)` (Megaera-watched named lock); `atomic_append(path, line)` using fcntl LOCK_EX so concurrent appends never interleave bytes. Wired into colony pheromone writes.
- **`src/olympus/runtime/persistence.py`** — `integrity_check()`, `rotate_jsonl(max_lines=N)`, `compact_jsonl(keep_predicate=fn)`. Tmp-file-then-rename for crash-safe rewrites.
- **`src/olympus/runtime/recovery.py`** — `retire_component(name, final_state, reason)` runs the canonical Iapetus phase progression and archives final state to Hades.
- **Lachesis enforcement wired** into `colony.deploy()` (per-eye-per-deploy cap of 50 pheromones) and `hephaestus.surface_from()` (per-pass cap of 5 proposals).

### 4 — Documentation

- **`codex/BUILDING.md`** — a 10-step walkthrough from clone to a working domain-specific deployment with a real Eye, a real Head, and a real Apollo prediction.
- **`codex/DOMAIN-TEMPLATE.md`** — the copy-paste template for `DOMAIN.md`, with sections for vocation, anti-mission, C1–CN invariants, risk-class examples, operator info, cadences, and domain anti-patterns.
- **`codex/FLOW.md`** — the cognitive loop end-to-end as a Mermaid diagram, plus a single-pheromone's journey through twelve numbered steps.
- **`codex/threat-model.md`** — expanded with concrete recovery runbooks for all seven Typhon scenarios (T1–T7).
- **`codex/PATTERNS.md`** — formalization of the ten reusable patterns (P1–P10) underlying Olympus. Each pattern has shape, Olympus instance, invariant preserved, anti-pattern defended against. Usable with or without Olympus.

### 5 — Advanced Maturation

- **`src/olympus/monsters/argos/correlation.py`** — `CorrelationEngine` that walks the pheromone log and produces three kinds of cross-eye signals: clusters (multiple eyes on same slice), cascades (eye A frequently followed by eye B within minutes), quiet eyes (eyes that have stopped depositing). Cross-eye patterns are emergent — no single Eye sees them.
- **`src/olympus/meta.py`** — Olympus reasoning about Olympus. `portrait()` composes a `SelfPortrait` from Coeus, Themis, HYDRA, Argos, Polyhymnia, Mnemosyne, and the action queue. Readable text rendering via `.as_text()`.
- **`src/olympus/llm/`** — optional LLM adapter pattern. `NullAdapter` (default; preserves LLM-free claim), plus factory functions `anthropic_adapter()` and `openai_adapter()` that lazy-import vendor SDKs. Olympus does NOT depend on any LLM vendor.

### CLI surface

`invoke` now dispatches 13 errands: `prime`, `bring-forth`, `kindle`, `remember`, `swear`, `verify`, `labors`, `consult` (chart/population/hymn/brief), `pantheon`, `blessing`, `session`, `action` (review/delphi/ratify/reject), `meta`, `correlate`, `console`.

### Verification

- 76/76 tests pass
- End-to-end `invoke session "..."` runs the full loop in < 1s
- `invoke correlate 24` finds 72 cascade patterns across recent test pheromones
- `invoke meta` produces a full self-portrait
- Styx now holds 26 oaths; chain intact
- Heracles's 12 labors all survive (real substrate kill-tests)

---

**Risk class:** HIGH (filesystem restructure — every import touched).
**Delphi:** [`codex/oracles/delphi/2026-05-18-namespaced-src-layout.md`](oracles/delphi/2026-05-18-namespaced-src-layout.md)
**Sworn on Styx at seq=16.**

GitHub landing showed 14+ top-level directories — visually scattered for a project this thin in actual file count. Reached through the architecture: Hephaestus surfaced three candidates (Flat `src/`, Namespaced `src/olympus/`, Namespaced + codex→docs); Momus contested via AP1–AP8; **Namespaced `src/olympus/`** was the only candidate with zero AP-violations.

**Layout changes shipped:**

- All ten tier directories moved to `src/olympus/<tier>/` — `primordials`, `titans`, `olympians`, `underworld`, `fates`, `furies`, `graces`, `muses`, `heroes`, `monsters`.
- `src/olympus/__init__.py` added (package marker, declares `__version__`).
- `oracles/` folded into `codex/oracles/` (decision records are prose).
- Runtime state moved from inside-package paths to root `state/` (gitignored):
  - `underworld/styx.jsonl` → `state/styx.jsonl`
  - `underworld/hades/` → `state/hades/`
  - `titans/mnemosyne/` → `state/mnemosyne/`
  - `olympians/{athena_briefs, hephaestus_proposals, hera_bindings, dionysus_transitions, hestia_hearth}` → `state/{athena, hephaestus, hera_bindings, dionysus_transitions, hestia_hearth}`
  - `monsters/argos/pheromones.jsonl` → `state/argos_pheromones.jsonl`
- `pyproject.toml` added — `pip install -e .` works; `[project.scripts] invoke = olympus.cli:main` exposes the CLI.
- `src/olympus/cli.py` created (Hermes-dispatch entry point).
- `scripts/invoke` reduced to a thin wrapper around `olympus.cli:main`.
- Every Python import rewritten: `from titans.X import Y` → `from olympus.titans.X import Y` (and the same for nine other tiers, top-level + indented).
- `tests/conftest.py` added to put `src/` on `sys.path` for direct test runs.
- Rhea's `REQUIRED_DIRS` rewritten — source tiers live in the package by construction; Rhea now creates only the runtime state tree (`state/...`) and the prose directories (`codex/journal/`, `codex/postmortems/`, `codex/oracles/delphi/`).
- README + PANTHEON layout sections rewritten.

**State preserved**: the Styx oath chain carried over (`state/styx.jsonl` now holds all 16+ prior oaths). The S8 amendment from earlier today remains the canonical decision; this move is structural, not constitutional.

**GitHub landing now shows:** 5 files (README, LICENSE, NOTICE, SECURITY, pyproject.toml) + 4 directories (codex, src, scripts, tests). 9 visible items. Down from 18.

44/44 tests pass.

---

**Risk class:** HIGH (constitutional amendment).
**Delphi:** [`oracles/delphi/2026-05-18-replace-S8-with-continuity-of-understanding.md`](../oracles/delphi/2026-05-18-replace-S8-with-continuity-of-understanding.md)
**Authorized by Zeus** (quoted in the Delphi). **Sworn on Styx at seq=11.**

The original S8 (Anti-coercion vocation) prescribed a specific stance: refuse changes that strengthen surveillance, centralization, or unbounded retention. Strong principle, but it baked Olympus to one worldview — a surveillance-monitoring deployment, an enterprise-compliance agent, or any tool whose honest job is to surveil or centralize could not adopt Olympus without contradicting its own constitution.

S8 is now:

> Every load-bearing action the agent takes must be reconstructible — what was done, why, and on whose authority — from the substrate's own records alone. The substrate refuses changes that obscure its own decision-making from the operator.

Reached through the cognitive architecture itself: Hephaestus surfaced three candidates (Continuity of Understanding, Operator Optionality, Vocational Fidelity); Momus contested each via the AP1–AP8 catalog; Continuity of Understanding was the only candidate with zero AP-violations.

**Knock-on changes shipped in this commit:**

- `titans/themis.py` — S8 entry rewritten
- `heroes/momus.py` — AP6 reframed from "vocation-adjacent silent strengthening" to "understanding-obscuring"
- `codex/COSMOGONY.md` — §III S8 + §V Vocation rewritten (vocation is now a slot, not a stance)
- `README.md` — S8 row updated
- `monsters/argos/eyes/eye_understanding_gap.py` — new structural enforcement
- `tests/test_substrate_invariants.py` — `test_S8_continuity_AP6_exists` replaces `test_S8_anticoercion_AP6_exists`
- Leftover prose stubs (`titans/mnemosyne.md`, `heroes/momus.md`, `titans/urania/`, `monsters/argos/atlas/`) deleted

**What's preserved:**

- Hestia's vocation slot — deployments still name their own purpose.
- The Hephaestus + Momus + Delphi debate protocol — unchanged.
- All seven other substrate invariants — unchanged.

**What's removed:**

- The substrate's ideological stance. Surveillance, centralization, retention are now **deployment-level** choices, not substrate-level constraints.

---

## The kindling — present epoch

**Olympus exists.** The pantheon is complete: seventy-three named figures plus the swarm tier of Argos's hundred eyes. Every tier of Greek cosmogony is mapped to a structural concern in the substrate.

### What was kindled

- **Five primordials** — Chaos, Gaia, Nyx, Eros, Tartarus
- **Eight Titans** — Mnemosyne, Themis, Cronus, Hyperion, Rhea, Oceanus, Iapetus, Coeus
- **Thirteen Olympians** — the canonical twelve plus Hestia
- **Five underworld figures** — Hades, Persephone, Hecate, Styx, Lethe
- **Three Fates** — Clotho, Lachesis, Atropos
- **Three Furies** — Alecto, Megaera, Tisiphone
- **Three Graces** — Aglaia, Euphrosyne, Thalia
- **Nine Muses** — Calliope, Clio, Erato, Euterpe, Melpomene, Polyhymnia, Terpsichore, Thalia (Muse), Urania
- **Seven heroes** — Heracles, Perseus, Theseus, Odysseus, Orpheus, Atalanta, Momus
- **Eight monsters** — HYDRA, Argos, Cerberus, Sphinx, Medusa, Chimera, Minotaur, Typhon

### What HYDRA carries

Eight mortal heads (cosmogony, pantheon, styx, journal, oaths, lifecycle, substrate, apollo) plus the immortal head — the watcher that watches the watchers.

### What Argos carries

The swarm tier: **Eyes** (8 observation specialists), **Satyrs** (4 concrete checks), **Demes** (6 civic-class observers: mantis, demarchos, hippeus, demos, tamias, ephoros), **Phalanges** (4 battle formations grouping Eyes by concern).

### The substrate invariants — S1 through S8

Sworn on Styx at the moment of kindling:

- **S1** Mnemosyne — append-only audit-of-record
- **S2** Argos — deterministic substrate
- **S3** HYDRA — read-only observation
- **S4** Argos — decentralization
- **S5** Apollo — falsifiability
- **S6** Delphi — strategic-decision discipline
- **S7** bounded autonomy
- **S8** Continuity of Understanding

### Authorization

The kindling was authorized by Zeus, in the exact words:

> *"The marginal cost of completeness is near zero with AI. Do the whole thing. Do it right. Do it with tests. Do it with documentation. Do it so well that I am genuinely impressed."*

Olympus was kindled accordingly.

---

## How to read this file

Every future entry follows this format:

```markdown
## {YYYY-MM-DD} — {one-line summary}

### What changed
- Concrete diff at the file level

### What was sworn
- Reference to Styx oath(s) recorded

### Who decided
- Zeus directive quote / Delphi reference

### Risk class
- LOW / MEDIUM / HIGH / COMPOSITE
```

Older entries roll into `chronicle/archive.md` once this file exceeds ten ships.

---

<div align="center">

*"The chronicle is the substrate's own memory. To delete an entry is to commit a crime against Mnemosyne, who never forgets."*

</div>
