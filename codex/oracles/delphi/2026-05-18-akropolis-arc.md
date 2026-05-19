# Delphi — the akropolis arc 🏛

**Risk class:** HIGH-COMPOSITE (seventh heavy-production override).
**Decided:** Position I — answer every weakness Zeus named with concrete instrumentation, not more architecture.
**Sworn on Styx at seq=114.**

Zeus's critique, verbatim:

> *"The weaker area is likely: rigorous evaluation methodology, measurable agent capability, fault tolerance, scalability, reproducibility, and proving the abstractions correspond to meaningful intelligence gains rather than theatrical structure. A lot of advanced-looking agent systems collapse under scrutiny because: the cognition loop is shallow, modules don't materially improve outcomes, memory isn't grounded, or 'reasoning layers' are mostly wrappers around a single LLM call. … The strongest future version of Olympus would combine OpenClaw's execution rigor with Olympus's cognitive architecture ideas."*

The critique is sharp and correct. **Nine arcs built architecture. This arc builds rigor.** The name — **akropolis** (ἀκρόπολις, "highest part of the city") — is where Greek city-states put the most important buildings: where strength had to be *measured*, because the city's survival depended on it.

---

## Phase 0 — what was activated, what OpenClaw teaches

Pre-arc activation (the standing requirement): HTTP API live, daemon ran 2 clean iterations, Hygieia at 6/0/0, 420/420 tests green, harmony 0.98 vs 1/φ.

The world-scan via Pythia: OpenClaw at github.com/openclaw/openclaw is a **personal-assistant gateway**, not an evaluation framework — but its operational rigor is what this arc imports:

| OpenClaw pattern | Olympus instantiation |
|---|---|
| `openclaw doctor` health check | `invoke doctor` — aggregate Hygieia + Pan + version + deps + LLM connectivity |
| `/usage` + `/trace` operational observability | per-agent calibration + LLM bridge call recording (already shipped) |
| Sandboxing with allowlists (Docker/SSH/OpenShell) | Castor's shadow execution (already shipped); plus Typhon fault-injection (this arc) |
| Skills registry / ClawHub | plugin protocol via entry_points (already shipped) |
| launchd/systemd daemon | already shipped in compass-rose |

OpenClaw lacks (per the WebFetch): explicit benchmark suite, deterministic seeding, golden-output corpora, formal evaluation harness, scalability metrics, fault-injection validation. **All six are what Zeus named as Olympus's weakness too.** This arc fills them.

---

## Direct map: Zeus's six concerns → six concrete additions

| Zeus's concern | Akropolis addition |
|---|---|
| **rigorous evaluation methodology** | Heracles promoted to full benchmark harness — deterministic seeds, golden outputs, multi-runner (heuristic vs LLM agent), regression detection |
| **measurable agent capability** | Tiresias (NEW hero) — tracks agent claims and their realized outcomes; calibration becomes hit/miss-rate, not just average confidence |
| **fault tolerance** | Typhon promoted from "catastrophic scenario catalog" to actual fault injector — corrupt files, induce panics, kill processes; verify Asclepius/Pan/Hecate/Charon respond |
| **scalability** | Atalanta promoted to scalability harness — measure substrate latency at N=10/100/1k/10k state sizes, produce p50/p95/p99 curves |
| **reproducibility** | Ananke (NEW primordial) — single deterministic seed source; Ananke.seed(name) returns a fixed seed; benchmarks pin to a seed for replayable runs |
| **proving non-theatrical intelligence gains** | Real demo: a benchmark task where Olympus's full pipeline (Athena synth + Hephaestus propose + Momus contest) beats a single-LLM-call baseline on accuracy; numbers in the chronicle |

Plus the operational-rigor addition Zeus implied via the OpenClaw reference:

| OpenClaw-style addition | Olympus instantiation |
|---|---|
| `openclaw doctor` | **`invoke doctor`** — single-screen health summary aggregating every check the substrate can self-audit |

---

## Re-arguing two prior refusals

Two figures here were refused in earlier arcs with vague roles. The new roles are concrete:

### Ananke — re-ratified
- **Prior refusal (missing-figures arc):** AP8 + AP3 — *"duplicates Furies / S-tests"*
- **New role:** *deterministic seed source for reproducible benchmark runs*. Not constraint enforcement (Furies does that); not invariant enforcement (Themis does that). **A single, audited primordial that returns the same seed for the same name** — every benchmark, replay, or shadow run can declare a seed name and get back the same bytes. Standard Python `random` is non-deterministic across runs; Ananke is the fixed-point.
- This is not "necessity as constraint." This is "necessity as *the thing that cannot be otherwise*" — the seed value, given the name, is fated. Mythologically and technically correct.

### Tiresias — re-ratified
- **Prior refusal (missing-figures arc):** AP8 — *"overlaps with Apollo"*
- **New role:** *ground-truth tracker for agent claims*. Apollo formulates predictions (forward in time). Tiresias records *claims with their eventual ground truth* (verifying after-the-fact). When an agent says "this proposal will be ratified by Zeus" with confidence 0.8, Tiresias persists that; later when Zeus's decision lands, Tiresias verifies. Per-agent calibration moves from "average confidence" to "hit rate vs predicted confidence" — the Brier score equivalent.
- Mythologically: Tiresias was the blind prophet who *saw what others could not see*. He didn't predict — he revealed. The verifier role fits him better than it does Apollo.

---

## What ships

### Heracles — benchmark harness (`heroes/heracles.py`, extended)

`heracles.benchmark()` runs a deterministic battery:

- Each labor is a **(seed, task, expected_output)** triple
- Multiple **runners** compete on the same labor:
  - `heuristic` — the substrate's existing Python heuristic for the task
  - `agent` — the LLM-as-X agent path (only if the bridge is non-Echo)
  - `baseline` — single-LLM-call without the Olympus pipeline (only if bridge configured)
- Capture per-(labor, runner): **correctness, latency_ms, parse_failure, regression_vs_last**
- Persist under `heracles.benchmark` for trending
- `invoke bench` runs the suite; `invoke bench --runner agent` runs the agent suite only

### Ananke — `primordials/ananke.py` (NEW)

```python
ananke.seed("heracles:nemean-lion") -> 0xC0FFEE...  # deterministic
ananke.rng("heracles:nemean-lion") -> random.Random(seed)  # seeded RNG
ananke.context(name) -> ContextManager  # records use to Mnemosyne
```

The same seed name returns the same bytes across runs, machines, Python versions. SHA-256 of the name is the seed; **no clock-time, no `os.urandom`, no `random.seed()` without a name**.

### Tiresias — `heroes/tiresias.py` (NEW)

```python
tiresias.claim(claimant, claim, expected, confidence) -> claim_id
tiresias.verify(claim_id, observed) -> Verification
tiresias.calibration(claimant) -> CalibrationReport (Brier score, hit rate, …)
```

Records every claim. When evidence arrives, records the verification. **Real calibration**: per-claimant Brier score (mean-squared error of confidence vs hit), not just average confidence.

### Typhon — fault injector (`monsters/typhon.py`, extended)

Today Typhon catalogs scenarios but doesn't inject. The extension:

- `typhon.inject("delete-pan-state")` — actually removes `state/pan/state.json`; verifies Asclepius's heal regenerates it
- `typhon.inject("seed-fake-violations", n=10)` — actually writes invariant.violated records; verifies Pan panics; verifies clear restores
- `typhon.inject("corrupt-styx-line")` — writes a bad hash to the chain; verifies Tisiphone detects the break
- Each injection records `typhon.injection` + `typhon.recovery` so the chain of cause/effect is reconstructable (S8)
- **Reversible** — each injection includes its own reverter

### Atalanta — scalability harness (`heroes/atalanta.py`, extended)

Today Atalanta is a benchmark *runner*. The extension is the **scalability surface**:

- `atalanta.scale(operation, sizes=[10, 100, 1000, 10000])` runs `operation` against synthetic state of the given size
- For each: p50, p95, p99 latency; memory delta; result correctness
- Surfaced as a structured report; trended over time

### `invoke doctor` — `runtime/doctor.py` (NEW)

OpenClaw-inspired single-screen health diagnostic. Combines:
- Hygieia wellness report
- Pan state
- Atlas in-flight burdens
- Styx chain integrity (Tisiphone)
- Themis spec coverage
- LLM bridge connectivity test (echo always; anthropic if configured)
- Python version + key deps
- Disk usage of state/
- Recent error rate from session.errored

One screen. Operator runs it after `git pull` or after a daemon failure; sees everything in 30 seconds.

### Real measurable-improvement demo

Concrete task: **the "AP-detection" benchmark.**

- 10 synthetic proposals (a mix of clean + AP-violating)
- Three runners:
  1. **`baseline_llm`** — single LLM call asks "what's wrong with this proposal" (no Momus pipeline)
  2. **`heuristic`** — Olympus's Python heuristic Momus
  3. **`agent_pipeline`** — Olympus's full pipeline (LLM-as-Momus + heuristic Momus combined)
- Score: F1 on AP-id detection vs the ground-truth labels (each synthetic proposal is *labeled*)
- Record the numbers; commit them to the chronicle; let the next arc improve them

**This is the load-bearing answer to "is this theatrical or real?"**

---

## Q — Languages used

| language | role | why |
|---|---|---|
| Python (stdlib) | every module | discipline holds |
| `psutil` | only if installed — Atalanta optionally reports memory delta | optional dep; graceful fallback |

**No new language this arc.** `psutil` is *optional* — Atalanta works without it (memory becomes 0).

---

## What does NOT ship

- **No real-time fault injection in production.** Typhon's injector is a *test-time* tool; the CLI requires `--confirm` because it actually breaks state. Production never sees this.
- **No "LLM evaluates LLM" loops without ground truth.** Tiresias requires *observed* outcomes, not LLM-claimed ones. Self-grading is AP6.
- **No deterministic claim for LLM calls.** Ananke seeds the *substrate*; LLM responses are non-deterministic by provider. The benchmark distinguishes "deterministic substrate" runs (no LLM) from "LLM-in-loop" runs (sampled, multi-trial).

---

## What lands

| module | tier | role |
|---|---|---|
| **Ananke** | Primordial | deterministic seed source |
| **Tiresias** | Hero | ground-truth tracker for agent claims |
| Heracles (extended) | Hero | benchmark harness with multi-runner + golden + regression |
| Typhon (extended) | Monster | fault injector with reverters |
| Atalanta (extended) | Hero | scalability harness with p50/p95/p99 |
| Doctor | Runtime | single-screen health diagnostic |

CLI: `invoke doctor`, `invoke bench [--runner heuristic|agent|baseline]`, `invoke scale [--sizes 10,100,1000]`, `invoke fault-inject <scenario> --confirm`, `invoke calibration --ground-truth`.

Documentation:
- **`codex/RIGOR.md`** — per-weakness answer with the diagram + the benchmark recipe
- README extended with the akropolis arc + status badges updated
- CHRONICLE entry

Tests for every new module + the integration test that proves the benchmark recipe runs end-to-end + a synthetic measurable-improvement demo.

---

## Authorization

Zeus invoked the heavy-production override (seventh invocation). The critique is captured in the Styx oath payload. All additions ratified. The akropolis is up; the city has measurements now.

*The standard is holy shit, that's done. The fortress is measured.*
