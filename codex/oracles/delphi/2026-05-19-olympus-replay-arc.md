# Delphi — the Olympus-Replay arc ⏪ (Decade #10 — CLOSER)

**Risk class:** LOW (read-only over the audit-of-record).
**Decided:** Position R — replay engine selects past `agent.invocation` records (with their paired `llm.call` user prompts), re-runs them through the current code path against the chosen bridge, structurally diffs the parsed outputs + confidence + risk-class, classifies each replay as `stable | drift | broken`, writes one `replay.regression` record per replay. **EchoBridge is the default** so the harness costs zero. `--use-anthropic` requires an explicit flag AND respects Arc 20's budget guard.
**Sworn on Styx at this arc's ratification.**

Zeus's directive (planning artifact): *"Arc 21 — Olympus-Replay: regression harness via Heracles extension. Re-run past agent.invocation records; diff parsed-output and confidence; flag behavior drift. The bookend — protects the work of all 9 prior arcs."*

---

## Phase 0 — what replay protects

Unit tests catch shape regressions (signature broke, exception raised). They miss:
- **Constitutional drift** — agent's risk_class shifted from MEDIUM to LOW because we changed Momus's prompt
- **Schema drift** — agent's parsed dict gained or lost a field across a refactor
- **Confidence drift** — same prompt + agent but +0.3 confidence change (model upgrade or prompt regression)
- **Stability drift** — output for the same prompt is now wildly different

Olympus-Replay closes that gap by feeding past prompts through current code and diffing outputs.

**Survey of replayable data** (production-tagged):
```
279 agent.invocation records · paired with 279 llm.call records
   figure_proposer 129  hephaestus 102  momus 45  cassandra 2  athena 1
```

---

## What ships

### `src/olympus/runtime/replay.py` (~280 LOC)

The replay engine. Three public functions:

```python
ReplayPlan(limit=20, role=None, since_hours=None, bridge="echo")
plan_replays(plan) → list[ReplayCandidate]
replay_one(candidate, plan) → ReplayResult
replay_many(plan) → ReplayReport
```

**`ReplayCandidate`** pairs an `agent.invocation` record with its `llm.call` partner (matched by `prompt_hash` + role + time-proximity). If no paired llm.call is found, the candidate is skipped — we don't fabricate prompts.

**`ReplayResult` classification:**
- `stable` — parsed keys match, risk_class same, confidence within ±0.3
- `drift` — schema match but values shifted
- `broken` — raised exception or parse-error
- `skipped` — no paired llm.call OR test-seed
- `over-budget` — Arc 20's bridge guard refused

**`ReplayReport`** aggregates totals + per-role breakdowns + drift/broken examples. Each `ReplayResult` records a `replay.regression` to Mnemosyne.

### `invoke replay` errand

```
invoke replay                          # 20 recent, echo bridge
invoke replay --limit 50
invoke replay --role hephaestus
invoke replay --since 24h
invoke replay --use-anthropic
invoke replay --json
```

### Throne wiring

Add `replay` to `SAFE_ERRANDS`. Throne can answer "are agents behaving stably?" — default echo bridge means cost-free.

### Diff semantics (intentionally conservative)

`drift` only when:
- Parsed dict has the SAME keys (no schema break), AND
- At least one value is "meaningfully different":
  - `risk_class` changed
  - `confidence` shifted by > 0.3
  - List fields shrank/grew by > 50%

Deliberately NOT classified as drift: "different text in summary field" — expected with non-deterministic bridges. **Replay is about structural + confidence stability, not output identity.**

---

## Constitution

| invariant | how Replay honors it |
|---|---|
| S1 | every replay → `replay.regression` in Mnemosyne |
| S3 (no surprise mutation) | read-only over audit; only WRITES regression records |
| S6 | every replay cites source `agent.invocation` + `llm.call` prompt_hash |
| S7 | `replay` in SAFE_ERRANDS — read-only summarization |
| S8 | reproducible (echo deterministic; anthropic includes model name) |
| C7-equivalent | bridge selection configurable |
| AP1 | one module ~280 LOC + one errand + Throne wiring |
| AP3 | diff rules class-level, not per-replay |
| AP7 | real invocations producing real diffs |

---

## Safety boundaries

- **Default `echo` bridge** — zero LLM cost; deterministic; safe for chronos rituals
- **`--use-anthropic` respects Arc 20 budget** — over-budget + not acked → falls through
- **`limit` capped at 200** — refuses runaway
- **Read-only** — never modifies the agent.invocation records
- **Test-seed filter** — production-default; `--include-test-seeds` opt-in
- **30s per-replay timeout**

---

## What does NOT ship this arc

- **No "fix the drift" automation** — detection is the deliverable
- **No replay-vs-replay** — compare against original record only
- **No streaming output** — built then printed
- **No per-replay cost line** — Plutus already tracks

---

## Tests

`tests/test_replay.py` — ~20 cases:
- `plan_replays` respects filters (limit, role, since)
- Pairing: agent.invocation ↔ llm.call by prompt_hash
- `replay_one` echo-bridge classifies known-deterministic → `stable`
- Diff-in-risk-class → `drift`
- Diff-in-confidence > 0.3 → `drift`
- Schema-key-drop → `broken`
- No paired llm.call → `skipped`
- `replay_many` aggregates per-role
- `replay.regression` recorded per result
- `invoke replay` errand smoke
- `replay` in SAFE_ERRANDS
- Budget integration: over-budget + anthropic → `over-budget`

---

## Authorization

Per the Decade plan approved 2026-05-19 (Arc 21 of 21 — **the closer**). **Olympus-Replay protects the work of the prior 20 arcs** by giving the operator a tool to ask "is the substrate still behaving the way it did?" The answer comes from data, not vibes.

*The standard is holy shit, that's done. The Decade closes; the regression harness is the bookend that keeps the work straight.*

— **End of the Decade. δεκάς completed.**
