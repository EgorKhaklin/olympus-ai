# Delphi — the Tartarus arc 🜍 (Decade #1)

**Risk class:** MEDIUM-COMPOSITE.
**Decided:** Position T — single source-of-truth `is_test_seed()` filter applied to wisdom, doctor, and Asclepius. Production metrics now exclude test residue. `invoke today --resolve` lets the operator close longstanding findings. **No test data is deleted** — only excluded from production-facing aggregates.
**Sworn on Styx at this arc's ratification.**

Zeus's directive (planning artifact): *"Arc 12 — Tartarus: fix the 4 substrate-surfaced gaps."*

---

## Phase 0 — what the investigation actually found

I planned to fix 5 gaps. Investigation showed **all 5 share one root cause**: tests write records that pollute production-facing metrics. The substrate has been crying about its own health based on test residue:

| gap | test-tagged share | what's really there |
|---|---|---|
| G1 — `hydra::fatigue-slice` proposed 150× | **43%** of proposals are test seeds | Hephaestus's rejection-memory works fine; wisdom counts test records |
| G2 — 10.5% session-error rate | **98%** of errors are test-actor | one real failure; the rest are intentional test raises |
| G3 — Hephaestus 28% ratification | (same root) | test proposals never get ratified; production rate is much higher |
| G4 — 22 burdens in flight | **100%** are `*-test` owners | leftover from test runs (charon-test, asclepius-test, test-owner) |
| G5 — `today` warning | 0 `warning.dismissed` records exist | the finding is misclassified — points at a slice with no real record |

**This is the same class of bug as the Hades test-contamination:** tests write residue that the production layer can't distinguish from real signals. The Hades arc fixed it for `state/config.json` (don't let tests write). Tartarus fixes it for Mnemosyne (let tests write; production-facing aggregates filter them out).

---

## What ships

### `src/olympus/runtime/test_seeds.py` — the source of truth

One small module, three predicates. **This is the single place that defines what "test-seed" means.** Production layers (wisdom, doctor, healer, oracles) import from here.

```python
is_test_actor(actor: str) -> bool     # e.g., "charon-test", "test-plutus"
is_test_owner(owner: str) -> bool     # same shape, for Atlas burdens
is_test_proposal(proposal: dict) -> bool  # checks fix/rationale/drift
is_test_record(memory: Memory) -> bool    # union of the above
```

Rules (intentionally conservative — false negatives preferred over false positives):
- actor/owner ends with `-test`, `:test`, contains `test-`, or is exactly `"test"`
- proposal where `proposed_fix` is exactly `"test"` or `"n/a"`
- proposal where `rationale` contains `test` AND drift contains literal `: test` at end
- proposal whose `id` contains `test-` or comes from a test directive

### `src/olympus/wisdom.py` patch

The drift_counter filter — and the ratification denominator. After this patch:
- "Repeated drift proposals" shows only production drift (Hephaestus's true noise level)
- "of N proposals, X% were ratified" uses production-only N/X

The raw counts (with test seeds) remain available via `wisdom.compose(include_test_seeds=True)` for tests + debugging.

### `src/olympus/runtime/doctor.py::_check_session_errors` patch

Filters `session.errored` by `is_test_actor(memory.actor)`. The 24h time-windowed metric (from pause-arc) is preserved; this just removes the synthetic baseline. Combined with the pause-arc fix, the metric now reflects **production reality in the last 24h**.

### `src/olympus/olympians/asclepius.py` extension

New healer: `release-test-burdens`. Calls `atlas.shoulders()`, finds burdens whose owner matches `is_test_owner`, releases them with outcome `"asclepius:test-seed-cleanup"`. Runs as part of `invoke heal`. NOT autonomous — gated to `--release-test` flag on first run, then auto-enabled if the operator confirms it's safe.

### `invoke today --resolve <slice> [--re-raise | --dismiss-as-stale]`

Real new operator action. The `today` oracle today only *surfaces* findings; `--resolve` lets the operator close them:
- `--re-raise` → creates a fresh proposal referencing the original finding; records `warning.re-raised`
- `--dismiss-as-stale` → records `warning.dismissal-reaffirmed` with operator rationale (no Mnemosyne deletion; S1 holds)

The Hephaestus `_check_today` doctor logic learns to suppress findings that have been `dismissal-reaffirmed` within the configured staleness window (default 7d).

### Tests — `tests/test_tartarus.py`

~25 cases:
- `is_test_*` helper: positive and negative cases for each rule
- `wisdom.compose()` exclude-test by default, include-test on flag
- `_check_session_errors` with test seeds returns clean count
- Asclepius release-test-burdens releases only test owners
- `today --resolve` creates the right Mnemosyne records and is idempotent
- A "metrics realism" test that asserts production-facing metrics differ from raw counts when test seeds are present (catches future drift in the filter)

---

## Constitution

| invariant | how Tartarus honors it |
|---|---|
| S1 | **no test records are deleted from Mnemosyne**; only filtered from production-facing aggregates |
| S6 | every filtered count is verifiable: pass `include_test_seeds=True` to see the raw |
| S8 | `is_test_seed()` rules live in source; reproducible |
| AP1 | one new module ~80 LOC + three small patches |
| AP3 | filter rules are class-level (actor patterns, fix value, rationale shape) — not per-record |
| AP7 (ledger-balancing) | the filter is **real** — the doctor metric changes; the wisdom report changes |
| AP8 | the test: after Tartarus, the substrate stops crying about non-existent problems |

---

## What does NOT ship this arc

- **No deletion of historical test records** — they stay; production reports filter.
- **No autonomous burden release** — Asclepius asks before releasing the first time.
- **No new figure** — Tartarus is the *place* (the chasm where bad things go); the *work* is done by existing figures (Asclepius, Hephaestus, today oracle).
- **No conftest tag for new tests** — operator can mark future tests with `actor="<name>-test"` voluntarily; no enforcement.

---

## Authorization

Per the Decade plan approved 2026-05-19. **Tartarus closes the 5 substrate-surfaced gaps by addressing their shared root cause**: tests writing audit-of-record that pollutes production metrics. The substrate stops crying wolf.

*The standard is holy shit, that's done. The chasm holds what doesn't belong above.*
