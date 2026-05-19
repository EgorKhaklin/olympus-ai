# Delphi — the Plutus-Budget arc 💸 (Decade #9)

**Risk class:** MEDIUM-HIGH (constitutional).
**Decided:** Position M — **the middle path.** Operator declares thresholds; the substrate surfaces breach VISIBLY (doctor warning + today urgent + Throne refusal of new LLM calls) but **Pan does NOT autonomously trip**. Operator-explicit acknowledgment (`invoke spend --acknowledge-budget`) clears the throttle until the next breach. Pan's constitutional role stays "broken state" only; cost is a new SOFT enforcement layer, not a new circuit-breaker authority.
**Sworn on Styx at this arc's ratification.**

Zeus's directive (planning artifact): *"Arc 20 — Plutus-Budget: operator declares thresholds; Pan trips on breach. Constitutional debate first."*

This arc opens with that debate.

---

## The constitutional debate (held openly here)

**Position A — Pan trips on cost:**
- Operator declared the ceiling; Pan enforcing it IS operator intent
- Cost surprises are a real failure mode (one runaway loop = $$$)
- Pan's existing authority to "stop because broken" trivially extends to "stop because over budget"
- Honors S3 (no surprise mutation) by failing safe rather than burning cash

**Position B — Pan does NOT trip on cost:**
- Pan today = "the substrate detected something broken"
- "Operator declared a number and substrate now refuses commands" is a NEW authority shape
- Pan tripping mid-session would confuse the operator: "I told it to do X and it just stopped?"
- The xenia/setup arcs were about SIMPLICITY; this adds a class of "why won't it work" surprises
- Cost overrun is an operator-information problem, not a substrate-protection problem

**Position M (chosen) — the middle path: SOFT enforcement, not Pan:**
- Operator declares thresholds in config
- Doctor `_check_budget` warns at 80% of threshold, alerts at 100%
- `invoke today` surfaces budget breach as the URGENT priority
- `AnthropicBridge.call()` refuses new LLM calls when over threshold, with a clear message and the override command
- **Pan does NOT trip** — its constitutional role stays exactly what it was: "broken state" detector, not "expensive state" detector
- Operator acknowledges with `invoke spend --acknowledge-budget` — clears the refusal until the NEXT breach (not permanently)
- Non-LLM errands (doctor, status, today, etc.) keep working

The middle path honors both positions:
- Position A's concern (operator intent for safety): respected — breach IS surfaced loudly and LLM calls ARE refused
- Position B's concern (Pan's role): preserved — Pan's authority isn't expanded; soft refusal is in a new layer

---

## What ships

### `runtime/config.py` extension — `BudgetConfig`

```json
{
  "plutus": {
    "budget": {
      "daily_usd": 1.00,
      "weekly_usd": 5.00,
      "monthly_usd": 20.00,
      "warn_at_pct": 80,
      "enabled": true
    }
  }
}
```

All thresholds optional; missing = disabled. Default disabled.

### `heroes/plutus.py` — new methods

```python
plutus.budget_status() -> BudgetStatus
# returns: {daily, weekly, monthly} each with {spent, ceiling, pct, state}
# state: "ok" | "warn" (>= warn_at_pct) | "over" (>= 100%)

plutus.is_over_budget() -> bool
plutus.acknowledge_breach() -> None  # records `plutus.budget_ack` to Mnemosyne
plutus.last_acknowledged_at() -> datetime | None
plutus.breach_since_ack() -> bool  # has spend crossed threshold AFTER last ack?
```

### `runtime/llm_bridge.py::AnthropicBridge.call()` — pre-flight guard

Before each call, check:
1. Is budget enforcement enabled? If no → proceed
2. Is current spend `>= 100%` of any active threshold? If no → proceed
3. Has the operator acknowledged AFTER the most recent breach? If yes → proceed (one-shot bypass that expires on next breach)
4. Otherwise → return `LLMResponse(error="budget breach; run \`invoke spend --acknowledge-budget\` to override")`

The check is bounded: 50ms max latency (Plutus tally over recent records is fast).

### `runtime/doctor.py::_check_budget`

New check:
- `✓ budget: $0.30/$1.00 daily (30%)` — under all thresholds
- `! budget: $0.85/$1.00 daily (85%) — approaching ceiling` — at warn_at_pct
- `! budget: $1.15/$1.00 daily (115%) — OVER; LLM refused until acknowledged` — at/over 100%

### `today` oracle — budget becomes urgent finding

When over budget AND not acknowledged-since: `today` surfaces it as the `urgent` priority:
```
[urgent] Plutus reports daily budget breached ($1.15 / $1.00); LLM calls refused.
Run `invoke spend --acknowledge-budget` to clear, or raise the ceiling in config.
```

### `invoke spend` extensions

- `invoke spend --budget` — show current budget status table
- `invoke spend --acknowledge-budget [--reason "<text>"]` — clears the breach-since-ack flag; records `plutus.budget_ack` to Mnemosyne with operator rationale

### `runtime/errand_whitelist.py` — NO change

Acknowledgment is operator-explicit; it should NOT be automatable. Stays out of `AUTOMATED_ERRANDS`. Throne can SHOW budget status (via `spend`) but cannot acknowledge — that's operator-in-person.

---

## Constitution

| invariant | how Plutus-Budget honors it |
|---|---|
| S1 | every breach + every ack → Mnemosyne (`plutus.budget_breach`, `plutus.budget_ack`) |
| S3 (no surprise mutation) | enforcement is OPT-IN (default disabled); operator-declared thresholds; acknowledgment clears until NEXT breach |
| S6 | breach reports cite the exact ($, ceiling, pct, window); verifiable |
| **S7** | **Pan's authority is NOT extended.** Cost enforcement is a NEW soft layer with no Pan-trip semantics. The operator can always override; the substrate refuses only LLM calls, not all errands. |
| C7-equivalent | thresholds are config data, not hardcoded |
| AP1 | Plutus extension (3 methods) + bridge guard (~15 lines) + doctor check + spend errand flag |
| AP3 | thresholds are class-level (daily/weekly/monthly), not per-call rules |
| AP7 (ledger-balancing) | breach actually refuses LLM calls (tested with scripted spend) |

---

## Safety boundaries (named explicitly)

- **Default DISABLED** — operator opts in by setting any threshold
- **Pan NOT involved** — Pan's `panicked` state is orthogonal to budget state; both can be queried independently
- **Acknowledgment is single-use** — clears until NEXT crossing of threshold; not "I'm fine with $100 of overage forever"
- **Non-LLM errands work** — doctor, status, today, etc. all keep running; only `AnthropicBridge.call()` refuses
- **Operator can always raise the ceiling** — edit config and re-run; takes effect immediately
- **No mid-call termination** — guards run BEFORE the call; in-flight calls complete (would be wasteful to kill at the network layer)

---

## What does NOT ship this arc

- **No Pan integration** — explicit per the debate above
- **No per-role budgets** ("hephaestus can spend $0.10/day max") — could be a future arc but adds complexity
- **No projection** ("at current rate you'll hit ceiling in 4 hours") — useful, not load-bearing
- **No email/Slack alerts** — Olympus stays operator-driven (no autonomous-trigger surface)
- **No external budget service** — local-only, simple

---

## Tests

`tests/test_plutus_budget.py` — ~22 cases (using `monkey-patched` Plutus tally to simulate spend levels):
- `budget_status` correctly reports under/warn/over for daily/weekly/monthly
- `is_over_budget` true iff any threshold is `>= 100%`
- `acknowledge_breach` records `plutus.budget_ack` to Mnemosyne
- `breach_since_ack` correctly tracks the "since" semantics
- `AnthropicBridge.call` returns budget error when over AND not acknowledged
- `AnthropicBridge.call` proceeds when acknowledged
- `AnthropicBridge.call` proceeds when budget disabled (default)
- `EchoBridge.call` NEVER checks budget (only paid bridges do)
- `doctor._check_budget` returns ok/warn/over correctly
- `today` oracle surfaces breach as urgent
- `invoke spend --budget` smoke
- `invoke spend --acknowledge-budget` records the ack
- Constitutional test: Pan's `panicked` field does NOT change due to budget breach

---

## Authorization

Per the Decade plan approved 2026-05-19 (Arc 20 of 21). **The constitutional debate is held openly in the Delphi above; Position M is the chosen path.** Pan stays a broken-state detector; budget is a new soft-enforcement layer; LLM calls refuse over budget; operator acknowledges to continue.

*The standard is holy shit, that's done. The cornucopia has a ceiling — and the operator drew it themselves.*
