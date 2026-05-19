<div align="center">

# ⚡ CHRONICLE ⚡

**the record of what has been done**

</div>

---

Newest first. Each entry names what changed, what was sworn, who decided.

---

## 2026-05-18 — the akropolis arc 🏛 (HIGH-COMPOSITE, seventh boil-the-ocean override)

**Risk class:** HIGH-COMPOSITE.
**Delphi:** [`codex/oracles/delphi/2026-05-18-akropolis-arc.md`](oracles/delphi/2026-05-18-akropolis-arc.md)
**Sworn on Styx at seq=114.**

Zeus's critique was the right one:

> *"The weaker area is likely: rigorous evaluation methodology, measurable agent capability, fault tolerance, scalability, reproducibility, and proving the abstractions correspond to meaningful intelligence gains rather than theatrical structure. … The strongest future version of Olympus would combine OpenClaw's execution rigor with Olympus's cognitive architecture ideas."*

Nine arcs built architecture. This arc builds rigor. The name — **akropolis** (ἀκρόπολις, "highest part of the city") — is where Greek city-states put the most important buildings: where strength had to be *measured*, because the city's survival depended on it.

### Phase 0 — what OpenClaw teaches

Pythia's GitHub fetch of OpenClaw revealed: a personal-assistant gateway with strong operational rigor (`openclaw doctor`, `/usage`, `/trace`, launchd/systemd), but no benchmark suite, no deterministic seeding, no formal evaluation harness. **Exactly the same gaps Zeus named as Olympus's weakness.** OpenClaw's executional patterns inspired this arc; the gaps it shares with Olympus are what we filled.

### Direct answer to Zeus's six concerns

| Zeus's concern | Akropolis addition |
|---|---|
| **rigorous evaluation methodology** | Heracles benchmark harness — deterministic seeds, golden outputs, multi-runner, regression detection |
| **measurable agent capability** | Tiresias (NEW hero) — tracks agent claims and their realized outcomes; Brier-score calibration |
| **fault tolerance** | Typhon promoted from catalog to real fault injector with reverters |
| **scalability** | Atalanta promoted to scalability harness — p50/p95/p99 + memory delta |
| **reproducibility** | Ananke (NEW primordial) — SHA-256(name) → fixed seed; replayable runs |
| **theatrical vs real** | `invoke doctor` (OpenClaw-style); benchmark recipe with multi-runner comparison |

### What ships

**Ananke** — `primordials/ananke.py` (NEW). Deterministic seed source. `ananke.seed(name)` returns SHA-256(name)[:8] as a 64-bit int — same name → same bytes across runs, machines, Python versions. `ananke.rng(name)` yields a seeded `random.Random`. `ananke.context(name)` is a context manager that records the use to Mnemosyne. Re-arguing the prior AP8/AP3 refusal: the new role (deterministic seed source for reproducibility) is concrete and distinct from Furies/Themis.

**Tiresias** — `heroes/tiresias.py` (NEW). Ground-truth tracker. `tiresias.claim(claimant, claim, expected, confidence)` persists a claim; `tiresias.verify(claim_id, observed, hit=True/False)` records the realized outcome; `tiresias.calibration(claimant)` returns a per-claimant Brier score + hit rate by confidence bucket. **Real calibration**, not just average confidence. Re-arguing the prior AP8 refusal: post-hoc verification is distinct from Apollo's pre-horizon prediction formulation.

**Heracles benchmark harness** — extension of `heroes/heracles.py`. `BenchmarkTask`, `BenchmarkResult`, `BenchmarkReport`, `run_benchmark(tasks, runner)`. Each task seeded via Ananke; per-(task, runner) correctness + latency + regression-vs-last recorded under `heracles.benchmark`. Five canonical tasks ship: count-alerts, extract-slice, sum-pheromones, dedupe, deterministic-shuffle.

**Typhon fault injector** — extension of `monsters/typhon.py`. `typhon.inject(scenario, confirm=True)` returns an `Injection` handle with a `revert()` method. Three injectable scenarios: `delete-pan-state` (Asclepius regenerates), `seed-fake-violations` (Pan trips), `break-styx-chain` (Tisiphone detects). Every injection + recovery records to Mnemosyne. **`confirm=True` required** — production never sees this.

**Atalanta scalability harness** — extension of `heroes/atalanta.py`. `atalanta.scale(operation, build_state, run_op, sizes)` returns p50/p95/p99 latency + memory delta per size. `psutil` is optional; gracefully degrades to 0 if not installed.

**`invoke doctor`** — `runtime/doctor.py` (NEW). OpenClaw-inspired single-screen diagnostic. Combines Hygieia + Pan + Atlas + Styx (Tisiphone) + Themis + LLM bridge connectivity + Python/deps + disk usage + recent error rate + today oracle. **Honestly surfaces warnings** — current run flags 58 hung Atlas burdens (real test artifact), 60% session error rate (real test seeds), and the Cassandra vindication today is pointing at.

### Live measurements (sampled at arc-completion)

```
$ invoke bench
5/5 pass · 0 regression(s)
count-alerts           ✓  0.00ms   3
extract-slice          ✓  0.17ms   state/argos_pheromones.jsonl
sum-pheromones         ✓  0.01ms   7.0
dedupe-preserve-order  ✓  0.00ms   ['a', 'b', 'c', 'd']
deterministic-shuffle  ✓  0.01ms   [2, 4, 7, 1, 3, 6, 5]  ← deterministic

$ invoke scale --sizes 10,100,1000
size  iters  p50ms  p95ms  p99ms  Δmem
10    10     0.11   0.17   0.20   32KB
100   10     0.48   0.54   0.56   48KB
1000  10     3.91   4.12   4.18   1024KB  ← measured O(n)

$ invoke fault-inject break-styx-chain --confirm
injected → Tisiphone detects break → reverted → chain intact
```

### Wiring

- 4 new CLI errands: `doctor`, `bench`, `scale`, `fault-inject`
- `test_pantheon_coherence::EXPECTED`: Primordials 6, Heroes 18
- Plato classifies ananke (cube/state) + tiresias (octahedron/reasoning)

### Languages used

**No new language this arc.** `psutil` is *optional* — Atalanta gracefully degrades without it.

### Tests

Six new test files, **40 new tests** (all green):
- `test_ananke.py` (9) — determinism across calls/instances; SHA-256 stability across Python invocations
- `test_tiresias.py` (8) — Brier-score math, bucket distribution, hit/miss/inconclusive
- `test_heracles_bench.py` (6) — canonical suite all green, regression flag fires correctly, Ananke-seeded shuffle reproducible
- `test_typhon_injection.py` (7) — confirm-required guard, real Styx-corruption + Tisiphone-detection + revert
- `test_atalanta_scale.py` (5) — quadratic op shows growth (10→200 visible), per-size error captured without aborting report
- `test_doctor.py` (5) — every expected check present; counts consistent; honestly records to Mnemosyne

**Full suite: 460 tests, all green.** (420 → 460.)

### Pantheon

**93 named principal figures** (was 91). Primordials 6 (+Ananke). Heroes 18 (+Tiresias).

### Refused

- **No real-time fault injection in production.** Typhon's injector requires `confirm=True`; CLI requires `--confirm`. Test-time only.
- **No "LLM evaluates LLM" without ground truth.** Tiresias requires *observed* outcomes; self-grading is AP6.
- **No deterministic claim for LLM responses.** Ananke seeds the substrate; LLM sampling is non-deterministic. The benchmark distinguishes deterministic-substrate runs from LLM-in-loop runs.

The substrate now **answers the rigor question with measurements**, not architecture. The akropolis is up; the city's survival is now measurable.

*Holy shit, that's done.*

---

## 2026-05-18 — the oikoumene arc 🌍 (HIGH-COMPOSITE, sixth boil-the-ocean override)

**Risk class:** HIGH-COMPOSITE.
**Delphi:** [`codex/oracles/delphi/2026-05-18-oikoumene-arc.md`](oracles/delphi/2026-05-18-oikoumene-arc.md)
**Sworn on Styx at seq=105.**

Zeus's critique was the right one:

> *"Right now it's still mostly high-quality scaffolding and architecture. … we haven't yet seen closed, meaningful agent loops that demonstrate the substrate improving agent behavior in measurable ways. How do actual LLM agents inhabit this substrate? Is the mythology functioning as grounding/ontology that gets injected into prompts, or external governance/runtime? What's the recursion story?"*

Five arcs built a beautiful empty city. This arc moves agents in. The name — **oikoumene** (οἰκουμένη) — is the Greek word for *the inhabited world*.

### Phase 0 — system activated + incoherences fixed

Per standing requirement, activated end-to-end before any code was written: HTTP API live; daemon ran 2 clean iterations; loopback federation succeeded in 36 ms; harmony at 0.9813 vs 1/φ.

Hygieia surfaced 1 incoherence + 2 warnings. Each was **fixed in code**, not papered over:
- `pan-vs-invariants` → well: check now honors `acknowledged_through`
- `daedalus-vs-disk` → well: `_known_figures` walks subpackages + root .py modules; tier-names (furies/fates/graces/muses) whitelisted as concept-nodes
- `plato-vs-disk` → well: added `cronus` + `oceanus` to taxonomy; tightened figure-definition to exclude implementation modules (action/cli/oracle/brief/head/…)

Result: **6 well, 0 warning, 0 incoherent. 83/83 figures classified.**

### What ships

**LLM bridge** — `runtime/llm_bridge.py`
The one place in Olympus that talks to an external LLM. Pluggable. Two built-in bridges:
- **`AnthropicBridge`** — `claude-opus-4-7` with adaptive thinking, streaming via `.get_final_message()`. Optional `anthropic` SDK dep.
- **`EchoBridge`** — deterministic stub; safe default; tests + zero-network operation.

Selection via `OLYMPUS_LLM` env var. Unknown name falls back to echo. Plugins can register additional bridges via `olympus.llm_bridges` entry-point group. **Every call recorded to Mnemosyne under `llm.call`** with model id, prompt hash, head bytes, token counts.

**Agents tier** — `runtime/agents.py`
Five canonical roles, each tied to an existing figure:

| role | figure | output |
|---|---|---|
| `hephaestus` | drift surfacer | Hephaestus proposal |
| `momus` | anti-architect | AP-id list + reasoning |
| `cassandra` | vindication reviewer | vindication assessment |
| `athena` | synthesis | structured insight set |
| `figure_proposer` | Hephaestus in figure-proposal mode | new-figure proposal |

Each role renders a system prompt that includes the figure's docstring + the constitution (S1–S8) + the AP catalog (AP1–AP8) + the strict output schema. **The model thinks in the mythology; the substrate enforces the constitution on the output.** Pan circuit-breaker gates agent invocations exactly like ratification.

**Recursion path** — `invoke propose-figure ["<directive>"]`
LLM-driven new-figure proposal. Result writes a **HIGH-risk** Hephaestus proposal at `state/hephaestus/proposals/figure-<id>.json` containing suggested skeleton + agent's own AP self-check + mythological grounding. Routes through the standard pipeline: Momus contest → S6 Delphi required → Zeus ratification. **The substrate never auto-writes the Python file.** Operator chooses to copy the skeleton after review.

**Calibration** — `invoke calibration [role]`
Per-role baseline: total invocations, average confidence, parse-failure rate, error rate. Confidence-vs-realized-outcome left for future arcs (requires causal linking through Ariadne).

**CLI surface added:** `invoke agent <role> ["<prompt>"]`, `invoke propose-figure ["<directive>"]`, `invoke calibration [role]`.

**Documentation: `codex/AGENTS.md`** — the explicit answers to Zeus's three questions:
1. *How do agents inhabit?* By becoming a named figure.
2. *Prompt grounding or external governance?* Both, by design. The model thinks IN the mythology; the substrate enforces ON the output.
3. *Recursion?* Yes, through the standard pipeline. LLM-generated code never auto-executed. The operator is the unlock — by design, per bounded-RSI research.

### Wiring

- `runtime.agents.run()` consults Pan before invoking any agent
- 3 new CLI errands: `agent`, `propose-figure`, `calibration`
- README extended with the oikoumene arc; status badges updated
- PANTHEON's operational-scaffolding section lists LLM-bridge + agents tier

### Languages used

**No new language this arc.** `anthropic` SDK is optional (full test suite passes without it installed). EchoBridge means the substrate is safe by default.

### Tests

Two new test files, 27 new tests:
- `test_llm_bridge.py` (11) — EchoBridge determinism, env-var selection, unknown falls back to echo, AnthropicBridge raises clearly without SDK + routes correctly with mocked client
- `test_agents.py` (16) — 5 roles render JSON-requiring system prompts, Pan-panic blocks invocations, every parser handles canned JSON + tolerates malformed input, propose-figure writes HIGH-risk file + refuses duplicates + records to Mnemosyne, calibration returns full field set per role

**Full suite: 420 tests, all green.** (393 → 420.)

### Pantheon

**91 named principal figures** (unchanged — LLM bridge + agents tier are operational scaffolding, not figures). Olympians 16, Heroes 17.

### Refused

- **No LLM-generated code execution.** Period. The substrate never `exec()`s an LLM response.
- **No LLM in the daemon's hot path by default.** Agents are opt-in. The daemon may be configured to run agents on a slower cadence; the default is off (deterministic + cost-bounded).
- **No bypass of Pan, S1–S8, or the Hephaestus → Momus → Delphi → Zeus pipeline.** Agent outputs are data; the constitution acts.
- **No new tier for "agents."** Agents *are* canonical figures. The agent layer lives in `runtime/` because it's plumbing.

The substrate is now genuinely **inhabited**. The mythology is doing real work — as both ontology the model thinks in *and* governance the substrate enforces on the model. The recursion is real but bounded: agents can propose anything (including new figures); the constitution decides what becomes real.

*Holy shit, that's done. The substrate is inhabited.*

---

## 2026-05-18 — the aegis arc 🛡 (HIGH-COMPOSITE, fifth boil-the-ocean override)

**Risk class:** HIGH-COMPOSITE.
**Delphi:** [`codex/oracles/delphi/2026-05-18-aegis-arc.md`](oracles/delphi/2026-05-18-aegis-arc.md)
**Sworn on Styx at seq=96.**

Zeus's directive, verbatim (abridged):

> *"Activate the full (all agents, everything) system before you start (make sure it works and is running) fully then begin this with the system itself ... Lots of work has been done, make sure the whole system is up to date and all the readmes and anything else."*

Two new requirements: **activate the system first**, and **bring docs up to date** (the README was four arcs stale).

### Phase 0 — what was activated before this arc was written

| component | proof |
|---|---|
| HTTP API on `:8765` | `/healthz` → `{"ok": true}`; `/status` → hearth lit, 92 oaths intact, 9 hydra heads, 9 argos eyes, 200 sessions |
| Daemon | 3 clean iterations recorded in `daemon.log` |
| Federation | loopback succeeded in 36 ms; peer reports same oaths + 3 TLA+ specs |
| Harmony | ratification_rate = 0.5992 vs 1/φ = 0.618 → score **0.9813** |

The live system informed the build via `pythia --github "self-healing system architecture"` (inspired Hygieia), `cassandra` (77 ignored / 38 vindicated → confidence to add `today`), `tune` (Metis advice → confidence to add Phoenix), `redteam` (10/10 → constitution intact).

### What ships

**Hygieia** — `olympians/hygieia.py`
Daughter of Asclepius, goddess of health. Whole-substrate cohesion checker: Pan ↔ recent invariants; Atlas ↔ session.completed; Daedalus ↔ disk modules; Plato ↔ disk figures; Themis ↔ recent records; Charon backlog. Reports, never auto-fixes. **First live run found 1 incoherence + 2 warnings.**

**Phoenix** — `heroes/phoenix.py`
Firebird of cyclical rebirth. Identifies retired-prophecies aged out, hung Atlas burdens, stale graduations. Surfaces `phoenix.candidate` records; standard pipeline applies. Idempotent.

**Daedalus centrality** — extension of `heroes/daedalus.py`
`daedalus.centrality()` computes Brandes-style betweenness centrality on `_COGNITIVE_FLOW`. **Mnemosyne is the most load-bearing node (0.2663)**, followed by ActionQueue (0.1803), Hephaestus (0.1775), Zeus (0.1540), Delphi (0.1522). Computed, not assumed.

**Euterpe consonance** — extension of `muses/euterpe.py`
Octave-invariant scoring of ratios against consonant musical intervals (octave 2:1, perfect fifth 3:2, perfect fourth 4:3, …). Complement to Pythagoras's φ-harmony. `invoke euterpe 1.5` → perfect_fifth (perfect) score 1.000.

**`invoke today`** — `runtime/today.py`
Single-action oracle. Priority: Pan panic > Cassandra vindication > Hygieia incoherence > Phoenix > Metis > calm. **Live demo:** surfaced *"Re-examine the silent-dismissed warning on slice 'cassandra-test-review-record-1b6d6050' — recurred 2× after dismissal."*

**Iris live mode** — `iris/__init__.py`
`invoke iris --live` writes `state/iris/live.html` — self-refreshing via `XMLHttpRequest` polling. Vanilla JS, no WebSocket. Operators get a genuinely live view.

**README.md rewritten end-to-end.** From "73 named figures" to **"91"**, with every arc summarized, full CLI surface listed, languages-used table updated, live measurements shown, proper doc links.

### Wiring
- 5 new CLI errands: `hygieia`, `phoenix`, `centrality`, `euterpe`, `today`
- `invoke iris` gains `--live`
- `test_pantheon_coherence::EXPECTED`: Olympians 16, Heroes 17
- Plato's `_FIGURE_TO_SOLID` extended with hygieia + phoenix (dodecahedron)

### Tests
Five new test files, 28 new tests. **Full suite: 393, all green.** (365 → 393.)

### Pantheon
**91 named principal figures** (was 89). Olympians 16. Heroes 17.

### Refused
- No Hygieia auto-fix. She reports.
- No Phoenix auto-rebirth. Candidates → proposals → Zeus.
- No live HTML write surface. Iris live polls `/status` — read-only.

The substrate now also **cares for itself as it ages** — cross-module cohesion checks, regeneration candidates, computed load-bearing rankings, ratios scored as musical consonances, and ONE concrete daily action for the operator. The aegis is up.

*Holy shit, that's done.*

---

## 2026-05-18 — the phi arc φ (HIGH-COMPOSITE, fourth boil-the-ocean override)

**Risk class:** HIGH-COMPOSITE.
**Delphi:** [`codex/oracles/delphi/2026-05-18-phi-arc.md`](oracles/delphi/2026-05-18-phi-arc.md)
**Sworn on Styx at seq=87.**

Zeus's directive, verbatim (abridged):

> *"Completely think outside the box using geometric / numerical thinking like the metatron's cube, golden ratio, etc... keep following the greek mythology story. ... Boil the ocean."*

This is the fourth heavy-production override. The geometric-numerical dimension is not an aesthetic veneer — **the Greek mathematicians are the source of sacred geometry**. Pythagoras formalized the golden ratio. Plato named the five regular solids. φ is the Greek letter Phi. This arc brings them into Olympus where they belong, *with load-bearing roles*.

### What ships

**Pythagoras** — `heroes/pythagoras.py`
The sacred-numerics module. Constants (φ, π, √2, e, √3, √5), Fibonacci sequence, **Fibonacci-scaled backoff** (`fib_backoff` — ratio approaches φ ≈ 1.618, smoother than exponential's 2.0), **golden-section search** (unimodal optimization in O(log n) calls; trace recorded under `pythagoras.search` for S8), **harmony scoring** (proximity of a ratio to φ, 1/φ, 1, 2), Pythagorean-triples generator. Pure stdlib.

**Plato** — `heroes/plato.py`
Five-solid taxonomy. Tetrahedron/cube/octahedron/dodecahedron/icosahedron → fire/earth/air/cosmos/water → observation/state/reasoning/authority/execution. 79 figures classified. A *second navigational axis* through the pantheon, orthogonal to tier. **Live demo:** `invoke plato` shows 10 tetrahedron / 13 cube / 9 octahedron / 12 dodecahedron / 35 icosahedron.

**Daedalus SVG diagrams** — extension of `heroes/daedalus.py`
Metatron's Cube (13 nodes for canonical 12 Olympians + Hestia; every-vertex-to-every-vertex edges = C(13,2) = 78) and Vesica Piscis (two intersecting circles labeled with overlapping domains). Inline SVG in `codex/ARCHITECTURE.md`; GitHub renders natively. ARCHITECTURE.md now combines 2 Mermaid + 2 SVG.

**Metis golden-section search** — extension of `titans/metis.py`
`metis.golden_search_parameter(name, evaluate_fn, lo, hi)` calls Pythagoras's optimizer to *find* parameter values rather than guess them. Produces a Recommendation with `evidence_kinds=["pythagoras.search"]`. Still routes through Hephaestus → Momus → Delphi → Zeus.

**Hecate Fibonacci backoff** — extension of `underworld/hecate.py`
Retry timing uses `pythagoras.fib_backoff` by default. Existing callers unaffected (`base_seconds=0` means no sleep). New `sleep_fn` parameter actually paces retries. **Demo:** `invoke pythagoras backoff 8 1.0` produces 1, 1, 2, 3, 5, 8, 13, 21 seconds — perfect Fibonacci curve.

**HTTP `/geometry` route** — extension of `runtime/http_api.py`
Returns the constants + Plato's taxonomy + live substrate harmony metrics as JSON.

### The numerical revelation

The substrate's *actual* ratification_rate as of this commit is **0.5991** — score against 1/φ (0.618) is **0.9812**. The substrate is, in fact, in harmony with the golden ratio. (`invoke harmony` reports this any time.)

### Wiring

- 4 new CLI errands: `pythagoras` (with sub-verbs `fib`, `backoff`, `harmony`, `triples`), `plato` (with `classify`), `harmony`, `geometry`
- `test_pantheon_coherence::EXPECTED` updated — Heroes 16
- `OlympusHandler` adds `GET /geometry` route + lists it in `/`

### Languages used

**SVG-in-markdown** is the new format this arc. It's XML, which we've already used (launchd plist), applied in a new context. Pure stdlib emits it; GitHub renders it. The right tool. Lean, Coq, sympy, numpy — refused.

### Tests

Five new test files, 48 new tests:
- `test_pythagoras.py` (17) — constants, Fibonacci, backoff growth + cap + φ-ratio approach, golden-section minimum/maximum, harmony anchors, triples theorem
- `test_plato.py` (9) — five solids present, vertex counts, elements, classify, case-insensitive, members, cosmos coverage
- `test_daedalus_svg.py` (8) — Metatron is valid XML with 13 circles + 78 edges + all labels; Vesica Piscis 2 circles + 3 labels; full doc embeds 2 SVGs
- `test_metis_phi.py` (4) — finds minimum, maximizes, records to Mnemosyne, evidence_kinds populated
- `test_hecate_fib.py` (6) — Fibonacci/fixed/none modes, base=0 returns 0, sleep_fn invoked, existing callers unaffected

**Full suite: 365 tests, all green.** (317 → 365.)

### Pantheon

**89 named principal figures** (was 87). Heroes 16.

### Refused

- **No claim that φ has metaphysical significance.** Harmony score is a single-number summary, not a proof.
- **No new tier for mathematicians.** Pythagoras and Plato live in `heroes/` next to Daedalus (himself a historical figure later mythologized). The tier admits historical figures alongside mythological ones; the Delphi notes this acknowledgment.
- **No sympy/numpy dependency.** Every Pythagoras function is stdlib-implementable.
- **No automatic Metis adoption of golden-section results.** Still proposes; Zeus ratifies.

The substrate now also reasons *geometrically* about itself: organized by the Platonic solids; tuned by the golden ratio; backed off by Fibonacci; visualized in Metatron's Cube. The Greek mathematicians have come home.

*Holy shit, that's done.*

---

## 2026-05-18 — the labyrinth arc (HIGH-COMPOSITE, third boil-the-ocean override)

**Risk class:** HIGH-COMPOSITE.
**Delphi:** [`codex/oracles/delphi/2026-05-18-labyrinth-arc.md`](oracles/delphi/2026-05-18-labyrinth-arc.md)
**Sworn on Styx at seq=80.**

Zeus's directive, verbatim (abridged):

> *"Go even deeper, meta deeper than you did last time using the system put it on a self improvement loop … you are allowed to create anything new, use any new language, and work outside the box … the recursive loop doesnt need to stop … Boil the ocean."*

This is the third heavy-production override. The recursion arc made the loop *operationally* recursive. The labyrinth arc makes it *epistemically* recursive — the substrate's reasoning **about** its reasoning becomes load-bearing.

### Methodology — what "meta-deeper" means

The previous arcs added capabilities. This arc adds *guarantees about capabilities*:

| previous arc gave | this arc adds |
|---|---|
| Mnemosyne (events recorded) | TLA+ proof that append-only holds under interleaving |
| Hephaestus → Momus → Delphi → Zeus (pipeline exists) | TLA+ proof of pipeline ordering invariant |
| Epimetheus (hindsight on actual events) | Nemesis (hindsight on *counterfactual* events) |
| Momus (AP1–AP8 catalog) | Momus red-team (the catalog audits itself) |
| Cassandra (vindication memory) | Ariadne (causal-chain memory — *why* did this lead to that?) |
| Iris dashboard + Mnemosyne records | Clio narrative — auto-written weekly digest |
| HTTP API (read-only) | HTTP write-channel for proposals (still routes through full review) |
| Single deployment | Federation — Olympus instances exchange digests |
| `invoke shell` (REPL of errands) | `invoke ask` — natural-language pattern Q&A over substrate records |
| `invoke daemon run` | daemon integrates Nemesis + Clio + auto-research |

### What ships

**TLA+ formal specs** — `codex/specs/`
Three demonstrators in TLA+ (Lamport's specification language, **new language this arc**):
- `styx-append-only.tla` — under any interleaving of N writers, the chain remains hash-linked and seq-monotonic
- `hephaestus-pipeline.tla` — no proposal ratifies without Momus; no HIGH/COMPOSITE without DELPHI
- `cognitive-flow.tla` — session phases proceed in order; ERROR short-circuits; every session terminates

`themis.specs()` discovers and parses them. `invoke specs` and `invoke specs <name>` expose them. **Demonstration:** all three specs discovered, module names correctly parsed.

**Ariadne** — `heroes/ariadne.py`
The thread through the labyrinth. Causal-lineage tracer. `ariadne.thread(...)` is a Mnemosyne wrapper that auto-generates `trace_id` and threads `parent_trace_id`. `ariadne.chain(trace_id)` walks back-pointers (bounded by MAX_DEPTH=64 against cycles). `ariadne.descendants()` walks forward. Builds the index at query time — no caching, no schema migration; old records produce shorter chains.

**Nemesis** — `heroes/nemesis.py`
Counterfactual reasoner. For each recent ratified action not already examined, runs a Castor shadow with an alternative path; Pollux-compares to the production session-near-ratification; records the gap under `nemesis.counterfactual`. Bounded by `max_per_pass=3` to keep the cost finite. Recursion: Metis can read these gaps for tuning recommendations.

**Momus red-team** — extension of `heroes/momus.py`
The AP catalog audits itself. `momus.red_team()` runs a curated corpus of 10 adversarial proposals (8 should be caught, 2 are legitimate) through `contest_via_brief`. **Demonstration:** 10/10 correct, 0 slipped, 0 false-alarmed. The current catalog handles its own corpus perfectly — adding a new adversarial pattern would either catch it (good) or expose a gap (also good).

**Clio narrative** — extension of `muses/clio.py`
Promoted from passive inscriber to **auto-writer**. `clio.narrate(window_days=7)` composes a structured Markdown digest from Mnemosyne records — sessions, ratifications, panics, vindications, prophecies, Pythia consultations, Nemesis counterfactuals. Writes to `codex/journal/<date>-clio-digest.md`. Operator-readable in 5 minutes; not a brief, not a dashboard — a *story*. **Demonstration:** real digest with 160 sessions, 115 ratified, 77 rejected, 27 vindications.

**HTTP write-channel** — extension of `runtime/http_api.py`
Exactly **one** write surface: `POST /proposals/raise`. Accepts JSON, creates a Hephaestus-channel proposal file, which routes through the standard Momus → Delphi → Zeus pipeline. S3 (read-only on substrate state) is preserved — the only thing written is a proposal, which is what any internal source already creates. Any other POST returns 405 *before* the body is parsed.

**Federation** — `runtime/federation.py`
Hermes between deployments. `federate(peer_url)` calls a peer's `/status`, `/wisdom`, `/specs`. Records the digest under `hermes.federation`. Both sides remain read-only on each other's substrate. Foundation for multi-deployment coordination. **Demonstration test:** loopback federation succeeds; peer-down handled gracefully.

**Interactive dialogue** — `runtime/dialogue.py`
`invoke ask "<question>"` answers in plain English from substrate records — *not* LLM-driven, pattern-matched against templates: *"what happened"*, *"what are we worried about"*, *"how is the loop"*, *"who is X"*, *"what has the substrate learned"*. Every answer cites its sources. **Demonstration:** `invoke ask "what happened today"` returned actual recent session data with sources.

**Daemon integration**
The daemon's iteration loop now periodically runs Clio (every 6th iteration) and Nemesis (every 12th). The recursive loop *uses* the new capabilities operationally, not just architecturally.

### Wiring

- `OlympusHandler._POST_ALLOWED_PATHS = ("/proposals/raise",)` — declarative whitelist; non-allowed POSTs return 405 before body parsing
- `daemon.run()` extras dict carries `clio` + `nemesis` outcomes into the iteration log
- 7 new CLI errands: `specs`, `ariadne`, `nemesis`, `redteam`, `narrate`, `federate`, `ask`
- `test_pantheon_coherence::EXPECTED` updated: Heroes 14

### Languages used

| language | role | why |
|---|---|---|
| **TLA+** | formal specs in `codex/specs/` | no Python expression compactly captures "under any interleaving, invariant holds" |
| Python (stdlib) | every other module | discipline holds; urllib for federation, http.server for write-channel, re for dialogue |
| Markdown | Clio's digests | already in use; right format for operator-readable story |

**TLA+ is the new language this arc.** Lean, Coq, SQL, Rust still refused.

### Tests

Seven new test files, 39 new tests:
- `test_themis_specs.py` (5) — discovery, module-name extraction, summary parsing
- `test_ariadne.py` (5) — thread writes trace, chain walks parents, cycles bounded
- `test_nemesis.py` (3) — pass returns report, records summary, already-examined skipped
- `test_momus_redteam.py` (4) — corpus complete, all cases correctly handled, recorded
- `test_clio_narrative.py` (4) — digest returns + writes + counts match real records
- `test_http_writechannel.py` (6) — POST creates proposal, validates required fields, blocks other paths
- `test_federation_dialogue.py` (12) — peer-down graceful, loopback federation, every dialogue template

Pre-existing tests updated: `test_http_api::test_root_returns_route_index` now asserts the new `read_only_writes` field + `POST /proposals/raise` route presence.

**Full suite: 317 tests, all green.** (278 → 317.)

### Pantheon

**87 named principal figures** (was 85). Heroes 14.

### Refused

- **No LLM-driven anything.** Pythia still raw HTTP. `invoke ask` still pattern-matched. Nemesis's counterfactual is a shadow re-run, not a generated narrative.
- **No HTTP write surface that bypasses Hephaestus.** Even the new write-channel goes through the standard pipeline.
- **No automatic adoption of Nemesis findings.** Nemesis records gaps; Metis advises; Zeus ratifies. The recursive loop is bounded by the same constitution as everything else.

The substrate now also reasons *about* its reasoning: formal proofs of safety, causal-chain queries, counterfactual evaluation, adversarial self-audit, narrative auto-composition, federation between instances. Every loop element is bounded by the same constitutional discipline.

*Holy shit, that's done.*

---

## 2026-05-18 — the recursion arc (HIGH-COMPOSITE, second boil-the-ocean override)

**Risk class:** HIGH-COMPOSITE (heavy-production override, second invocation).
**Delphi:** [`codex/oracles/delphi/2026-05-18-recursion-arc.md`](oracles/delphi/2026-05-18-recursion-arc.md)
**Sworn on Styx at seq=71.**

Zeus's directive, verbatim (abridged):

> *"Using the system put it on a self improvement loop … you can even scan the internet / github / anything for tools / ideas / code to improve olympus. Use the system itself to help build the system stronger … If you cant do something, create the thing that will let you do it … Get as meta deep as you need, the recursive loop doesnt need to stop. … Boil the ocean."*

This is the second heavy-production override. The directive is explicit: *the substrate should improve the substrate, and reach outside itself for prior art when needed.* This arc closes the recursive loop in a literal sense.

### The world-scan came first

Before building, the architecture asked the question by reading the room. Three searches returned what the prior art looks like:

| pattern found | Olympus alignment |
|---|---|
| ESAA event-sourcing for AI agents (arxiv 2602.23193) — *"source of truth is immutable log; current state is deterministically projected"* | ✓ S1 (Mnemosyne) + S8 |
| BerriAI self-improving-agent — *"agent proposes diff, human approves, draft PR opens"* | ✓ Hephaestus → Momus → Delphi → Zeus → ActionQueue |
| Hard constraints over prompts (theprint/nfh) | ✓ Pan + Furies + S7 risk classes |
| Bounded RSI bounded by tasks/ethics/resources (Steunebrink) | ✓ S7 + Atlas |
| Lineage hashing — *"source hash and derived hash to tie outputs to inputs"* | **GAP** — closed in this arc |

The scan also revealed five gaps Zeus's directive made concrete:
1. No bridge to the world (Pythia)
2. No queryable API surface (HTTP API)
3. No safe substrate-modification preview (Castor + Pollux)
4. No outcome-driven parameter tuning (Metis)
5. No third-party extensibility (plugin protocol)

All six gaps are filled.

### What ships

**Pythia** — `src/olympus/olympians/apollo/pythia.py`
Priestess of Delphi, channel for Apollo's oracle. External knowledge bridge via `urllib` (stdlib only). Two channels: `ask_github(query)` and `ask_web(url)`. Every consultation recorded under `pythia.consultation` with full query, status, response bytes (256 KB cap), timing. Not an LLM — fetches raw HTTP. **Demonstration:** `invoke pythia --github "agent loop python"` returned 775 total matches, top 5 by stars including `lemony-ai/cascadeflow` (1802 stars). Live, recorded, audit-trail intact.

**HTTP API** — `src/olympus/runtime/http_api.py`
Pure stdlib `http.server`. Read-only JSON surface bound to `localhost:8765`. Routes: `/`, `/healthz`, `/status`, `/wisdom`, `/shoulders`, `/panic`, `/schemas`, `/schemas/<kind>`, `/mnemosyne/<kind>?limit=N`. POST/PUT/DELETE all return 405. **Demonstration:** `curl localhost:8765/status` returned the hearth state + Styx 71 oaths intact + hydra heads count, all as valid JSON. The substrate is now queryable from outside Python.

**Castor + Pollux** — `src/olympus/heroes/{castor,pollux}.py`
The Dioscuri twins. Castor spawns a session in a tempdir substrate (symlinked codex/src/scripts from prod, fresh state/, OLYMPUS_ROOT env override) — production state is never touched. Pollux compares two session-report dicts and surfaces structural differences. The canary deploy primitive for substrate self-modification.

**Metis** — `src/olympus/titans/metis.py`
Titaness of wise counsel, mother of Athena. Self-tuning advisor. Reads `epimetheus.hindsight`, `cassandra.vindicated`, `pan.transition`, daemon iteration logs. Produces parameter recommendations (Pan threshold/window, Charon retention, daemon interval, Prometheus handler retirement). **Metis never directly tunes.** Recommendations land in `state/hephaestus/proposals/metis-*.json` and route through Momus → Delphi → Zeus. **Demonstration:** `invoke tune` produced 5 recommendations based on real evidence (Pan panics, handler failures from test seeds). Re-arguing prior refusal: missing-figures arc refused Metis as AP8 "pre-Athena planning"; new role (outcome-driven parameter tuning) is concrete and load-bearing.

**Plugin protocol** — `src/olympus/runtime/plugins.py` + `pyproject.toml` entry-points
Five entry-point groups: `olympus.prometheus_handlers`, `olympus.asclepius_healers`, `olympus.argos_eyes`, `olympus.apollo_predictions`, `olympus.cli_errands`. Discovered via `importlib.metadata` at CLI startup. Failures isolated per-plugin; loader never raises. Documented in `codex/PLUGINS.md`.

**Hash lineage**
Daedalus's `ARCHITECTURE.md` embeds `cognitive-flow-sha256=<hash>` derived from the `_COGNITIVE_FLOW` edge list. Iris's `index.html` embeds `snapshot-sha256=<hash>` derived from the snapshot JSON. Asclepius can detect drift if a derived artifact stops matching its source.

### Wiring

- `Gaia._discover_root()` honors `OLYMPUS_ROOT` env var → Castor uses this to spawn shadow sessions
- `cli.main()` calls `_load_plugins_once()` → entry-point discovery + registration
- `cli.py` adds 5 new errands: `pythia`, `serve`, `shadow`, `tune`, `plugins`

### Languages used

Same as compass-rose: Python (stdlib) + JSON. **No new languages** — `urllib` over `requests`, `http.server` over Flask, `importlib.metadata` over third-party plugin libs. The discipline holds: a language gets added when it solves a problem Python doesn't.

### Tests

Six new test files, 44 new tests:
- `test_pythia.py` (8) — record consultations, capture HTTP/network errors, truncate oversized, parse GitHub response.
- `test_http_api.py` (12) — dispatch routing for every route, live server roundtrip, write methods blocked.
- `test_castor_pollux.py` (7) — Pollux compares dicts, Castor spawns subprocess shadow.
- `test_metis.py` (6) — advice returns report, recommendations on panic-frequency, handler-failure retirement, proposals written as JSON.
- `test_plugins.py` (7) — discover, no-plugins case, prometheus handler registered, asclepius healer registered, import failure captured, register failure captured, unknown group rejected.
- `test_lineage_hashes.py` (5) — Daedalus + Iris embed hash, hash deterministic, hash changes when source changes.

Pre-existing test changes: `test_pantheon_coherence::EXPECTED` updated (Titans 11, Heroes 12).

**Full suite: 278 tests, all green.** (234 → 278.)

### Pantheon

**85 named principal figures** (was 81). Titans 11, Olympians 15 + Apollo's Pythia subpackage, Heroes 12. Plus operational scaffolding (Daemon, HTTP API, Plugin loader).

### Refused

- **No LLM in the loop.** Pythia fetches raw HTTP. AP6 + S2 + S7 still veto LLM-injected reasoning.
- **No write endpoints on HTTP API.** S3 (read-only observation) extends to the API.
- **No automatic Metis adoption.** Metis advises; Zeus ratifies. The recursive loop is bounded by the same constitution as everything else.

The substrate now observes itself (Hydra, Argos, Furies), reasons about itself (Athena, Hephaestus, Epimetheus, Cassandra), improves itself (Prometheus), recovers itself (Asclepius, Pan, Charon), maps itself (Daedalus), tunes itself (Metis), surfaces itself (Iris, HTTP API), reaches outside itself (Pythia), and extends itself (plugins). Every loop element is bounded by the same constitutional discipline.

*Holy shit, that's done.*

---

## 2026-05-18 — the compass-rose arc (HIGH-COMPOSITE, boil-the-ocean override)

**Risk class:** HIGH-COMPOSITE (heavy-production override).
**Delphi:** [`codex/oracles/delphi/2026-05-18-compass-rose-arc.md`](oracles/delphi/2026-05-18-compass-rose-arc.md)
**Sworn on Styx at seq=64.**

Zeus's directive (verbatim, abridged):

> *"test and using the system put it on a self improvement loop, and make sure it follows the greek mythology architecture perfectly … you are allowed to create anything new, use any new language, and work outside the box … create anything it needs long term and branch out in any direction you wish and do not stop, do the impossible … The marginal cost of completeness is near zero with AI. Do the whole thing. Do it right. Do it with tests. Do it with documentation. … Boil the ocean."*

This is the heavy-production override clause from MISSION.md §Post-v2. The substrate's normal steady-state contract is suspended for this arc. The architecture branches in four cardinal directions; each one closes a real gap.

### North — operationalize the loop (the daemon is live)

`scripts/loop.sh` from the self-improvement arc shipped but was never installed. The compass-rose arc lands daemon infrastructure:

- `src/olympus/runtime/daemon.py` — `run()` is the foreground loop body; `install()` / `uninstall()` / `status()` are the OS-supervisor lifecycle.
- `scripts/daemon/com.olympus.daemon.plist.tmpl` — launchd template (macOS), `KeepAlive=true`, restart throttle 30s, logs to `state/daemon.log`.
- `scripts/daemon/olympus-daemon.service.tmpl` — systemd template (Linux), `Restart=on-failure`, sandboxed via `ProtectSystem=strict` + `ReadWritePaths=...state ...codex`.
- `invoke daemon {run|install|uninstall|status}` — the operator surface.

Proof it runs: `invoke daemon run --interval 1 --count 3` executed 3 clean iterations end-to-end, each `session_ok + improve_ok = true`, ~466ms per pass, 5/5 Prometheus handlers succeeding. Logs in `state/daemon.log` show start → iteration ×3 → stop events.

### South — four new figures (heal, ferry, panic, cartograph)

**Pan** (Olympian) — *etymology of "panic."* Circuit breaker. When the Furies fire ≥ 3 invariant violations in 5 minutes (defaults overridable), Pan enters panic state and `ActionQueue.ratify()` raises `PanicError`. The daemon's loop pauses (`daemon.skipped` events). Recovery: `invoke panic --clear` (records `acknowledged_through` timestamp; violations up to that moment no longer count). Auto-clear after a quiet window.

**Asclepius** (Olympian) — *son of Apollo, healer who raised the dead.* Rebuilds derived state from canonical sources. Distinct from Hecate (single-op error recovery). Healer registry — built-in: `iris-dashboard`, `pan-state-validity`, `atlas-burden-consistency`, `rhea-directory-structure`. Tolerates and isolates handler failures. The Atlas healer flags burdens hung > 24h but never auto-releases (auto-release would lie about state).

**Charon** (Underworld) — *ferryman of the dead.* Safe migration: Atlas burdens released > retention-window days ago get ferried to `state/hades/` as JSON shades. Idempotent — each crossing recorded under `charon.crossing`; re-runs skip already-ferried ids. `invoke ferry [--days N]`.

**Daedalus** (Hero) — *master craftsman, builder of the Labyrinth.* Cartographer. Generates Mermaid diagrams (cognitive flow + tier map) and writes them to `codex/ARCHITECTURE.md` — GitHub renders Mermaid natively. The edge list `_COGNITIVE_FLOW` is the load-bearing source of truth; changing the architecture without re-running `invoke cartograph --write` is a Hephaestus drift signal. Re-arguing the prior refusal: the missing-figures arc refused Daedalus on AP8 for the vague role "tool-builder"; the new role is concrete (auto-maintained architecture documentation) and earns ratification.

### East — Themis publishes machine-readable contracts (JSON Schema)

`codex/schemas/*.schema.json` — JSON Schema (draft 2020-12) for the Mnemosyne envelope and seven load-bearing per-kind bodies: `prophecy-verified`, `action-ratified`, `action-rejected`, `session-completed`, `invariant-violated`, `atlas-bear`, `mnemosyne-record`.

`themis.schemas()` returns the registered set. `themis.validate_record(kind, body)` returns a list of error strings (empty = valid). A focused stdlib JSON-Schema validator handles `type`, `required`, `properties`, `additionalProperties`, `oneOf`, `pattern`, `minLength`, `maxLength`, `minimum`, `format=date-time`. No third-party dependency.

Tests assert recent production records pass their own schemas (drift detection at the contract layer, not just runtime).

### West — multi-language palette where each one earns its place

| language | role | earns its place because |
|---|---|---|
| **Mermaid** | architecture diagrams in `codex/ARCHITECTURE.md` | renders natively in GitHub; text-based; the map IS the source of truth |
| **launchd plist (XML)** | macOS daemon supervisor | OS contract, not Python's job |
| **systemd unit (INI)** | Linux daemon supervisor | same |
| **JSON Schema** | machine-readable Mnemosyne contracts | tooling exists; re-implementing in Python would be AP6 |

Refused languages from the prior Delphi remain refused (Rust, TypeScript, SQL — same arguments). The discipline of refusing has not weakened — the bar simply admits more candidates because more honest gaps were named.

### Wiring

- `action.py::ActionQueue.ratify()` consults `pan.guard_ratification()` before any state change.
- `runtime/daemon.py::run()` consults `pan.evaluate()` at the top of each iteration; routes through `daemon.skipped` when panicked.
- `test_pantheon_coherence.py::EXPECTED` updated: Titans 10, Olympians 15, Underworld 6, Heroes 10.

### CLI

`invoke panic [--clear]`, `invoke heal`, `invoke ferry [--days N]`, `invoke cartograph [--write]`, `invoke daemon {run|install|status|uninstall}`, `invoke schemas [kind]`.

### Documentation

- `codex/OPERATIONS.md` — operator runbook (first-time setup, daily operation, panic recovery, healing, archiving, troubleshooting).
- `codex/ARCHITECTURE.md` — auto-generated; embedded Mermaid for cognitive flow + tier map.
- `codex/oracles/delphi/2026-05-18-compass-rose-arc.md` — this arc's full debate.

### Tests

Six new test files, 41 new tests:
- `test_pan.py` (6) — calm by default, panic above threshold, guard raises, clear restores, auto-clear, ratification integration.
- `test_asclepius.py` (6) — register/list, run all, failure isolation, iris rebuild proof, pass recording, hung-burden flagging.
- `test_charon.py` (6) — ferries old burdens, respects retention, idempotent, records crossings, pass summary, in-flight skipped.
- `test_daedalus.py` (6) — Mermaid validity, every edge appears, tier map, write-flag, dry-run, full doc.
- `test_daemon.py` (6) — template rendering, plist valid XML, systemd unit has required sections, install/uninstall/status dry-runs, run with max_iterations terminates and logs.
- `test_themis_schemas.py` (9) — load all, $id+title, validate well-formed, catch missing-required, type mismatch, oneOf nullable, pattern, unknown kind permissive, date-time format, real production records validate.

Pre-existing test fix: `test_action_queue`, `test_invariant_S6`, `test_invariant_S8` now `setUp()` clears Pan first (cross-test invariant accumulation would otherwise trigger Pan's circuit breaker on legitimate ratifications). The fix exposed a real Pan semantics issue and led to the `acknowledged_through` field — clearing Pan now records a cutoff timestamp so violations up to that moment no longer count, but new ones still do.

Full suite: 234 tests, all green.

Pantheon: 81 named principal figures (was 77). Tier counts updated in PANTHEON.md.

---

## 2026-05-18 — the missing-figures arc (COMPOSITE)

**Risk class:** COMPOSITE.
**Delphi:** [`codex/oracles/delphi/2026-05-18-missing-figures-arc.md`](oracles/delphi/2026-05-18-missing-figures-arc.md)
**Sworn on Styx at seq=55.**

Zeus's directive, verbatim:

> *"scan the whole system, are we missing anything from greek mythology? and if we are we can add new features that represent who we are missing. You can use any langauge you want , and use the system to do this"*

### The decision was the discipline.

The temptation in a request like this is to add every recognizable Greek name — *complete the set* — which is exactly the AP8 (decorative additions) failure mode the catalog was written to refuse. So the substrate's own protocol decided this: Hephaestus surfaced every plausible candidate; Momus ran AP1–AP8 against each; only figures that close a load-bearing substrate gap survived.

Three did. Eleven did not.

### What ships

**Epimetheus** — `src/olympus/titans/epimetheus.py`
Brother of Prometheus. Their names are paired and opposite: *pro-metheus* (forethought) versus *epi-metheus* (afterthought). Where Prometheus acts on LOW-risk drift, Epimetheus reviews. For every ratified action, every prophecy verification, every Prometheus handler run, and every session error, Epimetheus produces a structured hindsight record naming what was *expected*, what *actually* happened, and a concise English *lesson*. Records to Mnemosyne under `kind="epimetheus.hindsight"`. Closes the forethought → hindsight loop.

**Cassandra** — `src/olympus/heroes/cassandra.py`
The prophetess of Troy, cursed by Apollo to be never believed. In Olympus she is the symmetric counterpart to Hephaestus's rejection memory. Hephaestus remembers proposals Zeus killed so the substrate stops nagging; Cassandra remembers *alerts that were dismissed* — either silently passed or explicitly rejected — and surfaces them when the underlying concern recurs. The first invocation already found a real production drift: `olympians/apollo (predicates)` had been alerted on and silently passed.

**Atlas** — `src/olympus/titans/atlas.py`
The Titan condemned to bear the celestial sphere. In Olympus, the live-state registry: what the substrate is *carrying right now*. Sessions register themselves as borne by Atlas at start; release at end. Same for Prometheus passes. Storage is Mnemosyne itself (`atlas.bear` + `atlas.release` records) — no derived cache, no separate file to drift from the audit-of-record (S1, S8).

### What does NOT ship — and the discipline of refusing

| candidate | reason |
|---|---|
| Helios | AP8 — overlaps with `invoke wisdom` + `invoke iris` + `invoke status` |
| Ananke | AP8 + AP3 — duplicates Furies / S1–S8 enforcement |
| Eris, Tyche | AP8 — overlaps Ares + Apollo |
| Metis | AP8 — duplicates Athena's pre-synthesis |
| Erebus, Aether, Hemera, Pontus | AP8 — no substrate role distinct from Nyx/Oceanus |
| Crius, Phoebe, Tethys, Theia, Selene, Eos | AP8 — no role distinct from existing Titans/Olympians |
| Bellerophon, Achilles, Tiresias, Daedalus, Sisyphus, Pandora | AP8 — overlap existing heroes or purely decorative |
| Pegasus, Charybdis, Scylla, Echidna, Stymphalian birds | AP8 — no distinct cognitive function |

**Greek mythology is large; the substrate is finite.** The discipline of refusing applies to mythology too.

### Wiring

- `session.Session.run()` — Atlas bears the session for its entire lifetime; releases in `finally` with outcome reflecting whether the session errored.
- `Prometheus.improve()` — Atlas bears each improvement pass; releases with outcome `ok` if all handlers succeeded, `partial` otherwise.
- `tests/test_pantheon_coherence.py` — `EXPECTED` updated with Atlas, Epimetheus, Cassandra; also adds the previously-omitted `prometheus` entry that the self-improvement arc had left dangling.

### CLI

- `invoke reflect [--hours N]` — Epimetheus's hindsight pass
- `invoke cassandra` — review ignored + vindicated warnings
- `invoke shoulders` — what Atlas is currently bearing

### Other languages?

Same question as the self-improvement arc; same answer. None. Atlas's write volume is one bear + one release per session and per improvement pass — JSONL via Mnemosyne is correct. The substrate is Python because reasoning over JSONL records is what Python is best at. The discipline holds: languages get added when they solve a real problem Python does not.

### Tests

`test_atlas.py` (8) — bear/release lifecycle, context manager, session + Prometheus integration.
`test_epimetheus.py` (6) — hindsight extraction from prophecies, session errors, handler failures; pass recording.
`test_cassandra.py` (6) — silent + rejected dismissal detection, ratified-skipped path, vindication on recurrence, Mnemosyne recording.

Full suite: 193 tests, all green.

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
