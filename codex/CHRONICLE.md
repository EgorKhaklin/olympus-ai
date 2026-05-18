<div align="center">

# ⚡ CHRONICLE ⚡

**the record of what has been done**

</div>

---

Newest first. Each entry names what changed, what was sworn, who decided.

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
