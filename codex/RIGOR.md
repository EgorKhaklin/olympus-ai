<div align="center">

# 🏛 RIGOR 🏛

**how Olympus answers the "is this theatrical?" question**

</div>

---

Per Delphi 2026-05-18-akropolis-arc.md.

Zeus's critique was the right one:

> *"The weaker area is likely: rigorous evaluation methodology, measurable agent capability, fault tolerance, scalability, reproducibility, and proving the abstractions correspond to meaningful intelligence gains rather than theatrical structure. A lot of advanced-looking agent systems collapse under scrutiny because: the cognition loop is shallow, modules don't materially improve outcomes, memory isn't grounded, or 'reasoning layers' are mostly wrappers around a single LLM call."*

This document is the per-concern answer with the substrate's actual instrumentation. Numbers come from live runs; commands are the operator's verification path.

---

## The six concerns → six concrete substrate surfaces

| Zeus's concern | Substrate answer | Operator verification |
|---|---|---|
| **rigorous evaluation methodology** | Heracles benchmark harness (deterministic seeds, golden outputs, regression detection) | `invoke bench` |
| **measurable agent capability** | Tiresias ground-truth tracker — Brier-score calibration, hit rate by confidence bucket | `tiresias.calibration(claimant)` |
| **fault tolerance** | Typhon fault injector with reverters — verifies Asclepius/Pan/Hecate/Charon respond correctly | `invoke fault-inject <scenario> --confirm` |
| **scalability** | Atalanta scalability harness — p50/p95/p99 + memory delta per state size | `invoke scale --sizes 10,100,1000` |
| **reproducibility** | Ananke deterministic seed source — SHA-256(name) → fixed seed; no clock-time, no OS entropy without a name | `ananke.seed("anything")` |
| **proving non-theatrical intelligence gains** | Real benchmark recipe with multi-runner comparison; doctor diagnostic that *honestly surfaces* warnings + failures | `invoke bench --runner <name>` + `invoke doctor` |

Plus the operational diagnostic Zeus implied via the OpenClaw reference:

| OpenClaw idea | Olympus surface | Verification |
|---|---|---|
| `openclaw doctor` | `invoke doctor` | one-screen health diagnostic (Hygieia + Pan + Styx + Atlas + Themis + LLM bridge + disk + session errors + today oracle) |

---

## Live measurements (sampled at arc-completion)

### Heracles benchmark — deterministic, all green, sub-millisecond

```
$ invoke bench
╔════════════════════════════════╗
║Heracles — benchmark (heuristic)║
║5/5 pass · 0 regression(s)      ║
╚════════════════════════════════╝
task                   ?  latency  output
count-alerts           ✓  0.00ms   3
extract-slice          ✓  0.17ms   state/argos_pheromones.jsonl
sum-pheromones         ✓  0.01ms   7.0
dedupe-preserve-order  ✓  0.00ms   ['a', 'b', 'c', 'd']
deterministic-shuffle  ✓  0.01ms   [2, 4, 7, 1, 3, 6, 5]
```

Every run produces `[2, 4, 7, 1, 3, 6, 5]` for the deterministic-shuffle task — that is reproducibility made operational via Ananke.

### Atalanta scalability — visible O(n) growth

```
$ invoke scale --sizes 10,100,1000
╔═════════════════════════════════════════╗
║Atalanta — scalability (mnemosyne-recall)║
╚═════════════════════════════════════════╝
size  iters  p50ms  p95ms  p99ms  Δmem
10    10     0.11   0.17   0.20   32KB
100   10     0.48   0.54   0.56   48KB
1000  10     3.91   4.12   4.18   1024KB
```

That's measured O(n) growth on real I/O, with memory delta. Not a theoretical claim.

### Doctor — honestly surfaces real problems

```
$ invoke doctor
╔══════════════════════╗
║doctor — olympus 0.1.0║
║7 ok · 3 warn · 0 fail║
╚══════════════════════╝
check           ?  detail
python+deps     ✓  py3.9.6 · psutil✓ anthropic✗
hygieia         ✓  6 well · 0 warning · 0 incoherent
pan             ✓  calm
styx            ✓  chain intact
atlas           !  58 burdens in flight (high) — investigate hung burdens
themis          ✓  7 schemas · 3 TLA+ specs
llm-bridge      ✓  echo (safe default)
state-disk      ✓  65.9 MB across 996 files
session-errors  !  30/50 recent error rate (60.0%) — investigate
today           !  [noteworthy] Re-examine the silent-dismissed warning...
```

**The diagnostic surfaces three real warnings.** It doesn't paper over them.

### Typhon fault-inject — break-then-verify-then-revert

```
$ invoke fault-inject break-styx-chain --confirm
╔══════════════════════════════════╗
║Typhon — injected break-styx-chain║
╚══════════════════════════════════╝
  detail: bogus self_hash on last line of state/styx.jsonl
🜂  reverted (state restored)
```

While the injection is active, `invoke verify` detects the chain break — proving the integrity check works on real corruption, not just on test mocks.

---

## What's NOT yet measured (honest scope)

- **Tiresias ground-truth tracking on REAL operator decisions.** The infrastructure is in place; running it at scale requires actual production operator-decisions. The unit tests cover the math (Brier score, bucket distribution); the live calibration is bootstrap-only.
- **Agent-vs-baseline LLM comparison on a real-world task.** The mechanism is wired (different runners on the same benchmark task); a meaningful comparison requires the AnthropicBridge configured + a hand-labeled task corpus. The bench harness IS ready for it — `invoke bench --runner agent` already routes through the agent path.
- **Multi-process scalability.** Atalanta measures single-process; cross-process scalability needs a separate harness (future arc).

These are tracked as **honest, open work** — not hidden gaps.

---

## How each Zeus-named failure mode is structurally prevented

> *"the cognition loop is shallow"*

The substrate's loop has nine distinct gods, each with a load-bearing role:

```
Hydra/Argos/Furies (observe)
  → Athena (synthesize)
  → Hephaestus (propose)
  → Momus (contest via AP1-AP8)
  → Delphi (write debate for HIGH-risk)
  → Zeus (ratify via Styx oath)
  → ActionQueue (route by S7 risk class)
  → Prometheus (execute LOW autonomously)
  → Epimetheus (record hindsight)
  → Cassandra (verify dismissed warnings later)
  → Ariadne (causal-chain query)
```

Eleven distinct surfaces, every one queryable from Mnemosyne. Not a single LLM call.

> *"modules don't materially improve outcomes"*

Every Mnemosyne record is dated + bodied + reconstructable. The benchmark harness lets the operator A/B different runners on the same task. The doctor surfaces real warnings. The harmony score (`invoke harmony`) measures live substrate ratios against φ; it doesn't claim improvement — it shows the measurement.

> *"memory isn't grounded"*

S1 + S8 are the constitution: every load-bearing event writes to Mnemosyne; the audit-of-record is reconstructable from substrate records alone. Lineage hashes (Daedalus, Iris) tie derived outputs to source inputs. Ariadne lets you walk back from any event to its causal root.

> *"reasoning layers are wrappers around a single LLM call"*

Olympus runs heuristic Momus first (deterministic Python), then optional LLM-as-Momus (recorded), then operator Zeus ratification. Three distinct decision gates. The LLM is *one* contestable input among many, not the source of truth.

---

## The recipe for verifying any future Olympus claim

```bash
# 1. Baseline: doctor + benchmark
invoke doctor                              # is the substrate healthy?
invoke bench                               # are the canonical tasks correct?

# 2. Reproducibility: same seed → same result
invoke pythagoras fib 10
invoke pythagoras fib 10                   # identical
ananke.seed("anything")                    # always the same number

# 3. Fault tolerance: break it, verify detection, revert
invoke fault-inject break-styx-chain --confirm
invoke verify                              # detects break
# (the inject command auto-reverts unless --no-revert)

# 4. Scalability: actual numbers
invoke scale --sizes 10,100,1000

# 5. Agent calibration (when AnthropicBridge is configured)
OLYMPUS_LLM=anthropic invoke bench --runner agent
invoke calibration                         # per-role hit-rate

# 6. Ground truth: claim → verify
# (in Python)
from olympus.heroes.tiresias import tiresias
cid = tiresias.claim(claimant="my-agent", claim="x will happen",
                       expected="x", confidence=0.7)
# ... later, when truth is known ...
tiresias.verify(cid, observed="x", hit=True)
tiresias.calibration("my-agent")           # real Brier score
```

---

*Per Delphi 2026-05-18-akropolis-arc.md. The akropolis is the highest part of a Greek city; that's where strength had to be measured because the city's survival depended on it. The akropolis is up.*
