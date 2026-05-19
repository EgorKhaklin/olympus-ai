# Delphi — the Plutus arc 💰

**Risk class:** HIGH-COMPOSITE (tenth heavy-production override, batch #2 of 4).
**Decided:** Position P — a new hero figure (Plutus) aggregates `llm.call` records into a cost ledger with per-bridge / per-role / per-model / per-day rollups; pricing table is data, not hardcoded into agents; new errand `invoke spend`; throne can answer cost questions.
**Sworn on Styx at this arc's ratification.**

Zeus's directive (paraphrased): *"Plutus — a budget/cost ledger tracking LLM spend per agent."*

The operator absolutely needs to know how much Claude is costing them. Right now every `llm.call` records `input_tokens` + `output_tokens` + `model` to Mnemosyne (that's been true since the oikoumene arc). **The data has been there all along; nobody has been adding it up.** This arc adds it up.

---

## Phase 0 — what's already there

- 580+ `llm.call` records in `state/mnemosyne/llm.call.jsonl`
- Each record: `bridge`, `role`, `model`, `input_tokens`, `output_tokens`, `elapsed_ms`, `remembered_at`
- No aggregation function exists
- No pricing table exists
- No CLI errand exists
- The throne can't answer "what's costing me money?"

---

## What ships

### `src/olympus/heroes/plutus.py` — new hero

Plutus (Greek: Πλοῦτος) was the god of wealth and abundance — son of Demeter, often shown carrying a cornucopia. In Olympus, **Plutus is the cost accountant**: tracks LLM spend by aggregating audit-of-record entries. He doesn't *create* the records (every bridge already does); he *reads* and *adds up*.

Public API:
```python
plutus.tally(window: str = "all") → CostReport
plutus.estimate_dollars(input_tokens, output_tokens, model) → float
plutus.PRICING  # dict: model_id → (input_$_per_1M, output_$_per_1M)
```

`CostReport` fields (dataclass):
- `total_input_tokens` / `total_output_tokens`
- `total_calls`
- `estimated_usd`
- `by_bridge` — `{bridge: {calls, in, out, usd}}`
- `by_role` — `{role: {calls, in, out, usd}}`
- `by_model` — `{model: {calls, in, out, usd}}`
- `by_day` — `{YYYY-MM-DD: {calls, in, out, usd}}` (last 30 days)
- `unknown_model_calls` — calls against a model not in the pricing table
- `window` — `"all"` | `"today"` | `"7d"` | `"30d"`
- `snapshot_at`

### Pricing table

Sourced from the live model pricing as of arc time (claude-opus-4-7: $5 in / $25 out per 1M; claude-sonnet-4-6: $3 / $15; claude-haiku-4-5: $1 / $5; echo: $0 / $0). Lives as a `PRICING` dict at module level (data, not hardcoded into agents). Unknown models contribute zero-dollar entries to `estimated_usd` but are surfaced via `unknown_model_calls` so the operator knows the estimate excludes them.

### `invoke spend` errand

Prints the cost report as a clean multi-table layout. Flags:
- `invoke spend` — all-time (default)
- `invoke spend --today` — today only
- `invoke spend --7d` / `--30d` — recent windows
- `invoke spend --json` — JSON dump (honors the global `--json` flag too)

### Throne wiring

Add `spend` to `SAFE_ERRANDS` so the Throne can answer:
- "what am I spending on Claude?"
- "how much did Hephaestus cost today?"
- "which model is most expensive?"

### Doctor check

Add one check: `_check_spend()` — reports today's estimated USD if > $0. Doesn't fail (cost is information, not error); informational only.

---

## Constitution

| invariant | how Plutus honors it |
|---|---|
| S1 | Plutus only reads from Mnemosyne; the source records stay sacred |
| S6 | every dollar number cites the model + token counts it was derived from |
| S8 | pricing table is in code (versionable); estimate is reproducible from records |
| C7-equivalent | pricing data is *data*, not hardcoded into bridges |
| AP1 | one new module ~250 LOC; one errand; no parallel accounting system |
| AP3 | aggregation is per-record-driven, not per-question hardcoded |
| AP8 | the test: an operator who looks at `invoke spend` learns something they didn't know |

---

## What does NOT ship this arc

- **No budget alarms.** No Pan integration ("trip if today's spend > $X"). That's a follow-up arc — requires a constitutional debate about whether the substrate gets to *stop* the operator from running expensive calls.
- **No historical pricing.** If Anthropic changes prices tomorrow, the new prices apply going forward; old records get re-estimated with new prices (we don't snapshot price-at-time-of-call).
- **No multi-currency.** USD only. Operator can convert.
- **No per-call drill-down UI.** The aggregate is the deliverable; per-call inspection stays at `invoke ask "show me recent llm calls"` or the raw JSONL.

---

## Tests

`tests/test_plutus.py` — 12+ cases:
- Empty Mnemosyne → zero-dollar report
- Single call with known model → correct dollar math
- Multiple calls aggregate by bridge/role/model/day
- Unknown model → counted but $0
- Window filters: today / 7d / 30d / all
- `estimate_dollars` matches the math for each known pricing entry
- Errand smoke test: `invoke spend` exits 0 and writes a report

---

## Authorization

Zeus invoked the heavy-production override (tenth invocation, batch #2 of 4). **Plutus turns invisible spend into visible spend.** Every model token has always been recorded; the operator now sees the bill.

*The standard is holy shit, that's done. The cornucopia has a price tag.*
