# Delphi — the Chronos arc ⏰ (Decade #4)

**Risk class:** LOW.
**Decided:** Position C — new `primordials/chronos.py` scheduler. Operator declares rituals in `state/config.json::chronos.rituals[]`. Daemon iteration evaluates rituals each tick. Pure-Python time matching (no `croniter` dep). Shares the automated-errand whitelist with Argos-Eyes (refactored to one source of truth). New errand surface `invoke chronos`. Last-fired times persist; `min_interval_seconds` prevents tight-loop double-fire.
**Sworn on Styx at this arc's ratification.**

Zeus's directive (planning artifact): *"Arc 15 — Chronos: scheduled rituals... operator declares rituals; daemon checks ritual triggers each iteration."*

---

## Phase 0 — what time means in Olympus today

Existing time primitives:
- **Nyx** (`primordials/nyx.py`) — clock + "background processes" (was *meant* to handle cron per the docstring; never operationalized)
- **Daemon** (`runtime/daemon.py`) — runs every `interval_seconds` (default 600s = 10min)
- **Argos-Eyes** (just shipped) — fires on filesystem change; not time-based

Gap: no way to say "every weekday at 9am run `today`" or "monthly run `spend --30d`." The daemon's fixed 10-min cadence is too coarse for time-of-day rituals.

Chronos closes this gap as a sibling primordial to Nyx — **the figure of structured time** vs Nyx's "while-no-one-is-watching" time.

---

## What ships

### `src/olympus/primordials/chronos.py` (~250 LOC)

Chronos (Χρόνος) was the personification of time itself — distinct from Cronus the Titan. In Olympus, Chronos is the scheduler.

Public API:
```python
from olympus.primordials.chronos import (
    chronos, Chronos, RitualSpec, parse_when, matches_now,
)

specs = chronos.load_rituals()        # from config
chronos.tick(now=None)                # evaluate + fire matching rituals
chronos.next_due(spec, now=None)      # when will this fire next?
```

### `when` grammar (intentionally simple)

```
daily HH:MM              # every day at HH:MM (e.g., "daily 09:00")
weekday HH:MM            # every Mon-Fri at HH:MM
weekend HH:MM            # every Sat-Sun at HH:MM
<day> HH:MM              # specific day: monday/tuesday/.../sunday
monthly <N>              # 1..28 of each month at 00:00
monthly <N> HH:MM        # 1..28 at HH:MM
every <N>m               # every N minutes (5..1440)
every <N>h               # every N hours (1..24)
hourly                   # every hour on the hour
```

Anything else → `parse_when` returns `WhenSpec(valid=False, error="...")` and the ritual is skipped at load with a clear message.

### `RitualSpec` dataclass + JSON shape

```json
{
  "id": "morning-briefing",
  "when": "weekday 09:00",
  "do": "today",
  "enabled": true
}
```

The `do` field is a whitelisted errand name (see below). Arguments are NOT supported in this arc — keep the surface small. Future arc may add `do: "today --resolve ..."` style with argv parsing.

### Shared `runtime/errand_whitelist.py` — refactor

Argos-Eyes shipped with `ERRAND_WHITELIST = {today, session, recall, doctor}` in its own module. Chronos needs the same. To honor Tartarus discipline ("don't introduce indirection without need" — but DRY when shared use is real), extract into `runtime/errand_whitelist.py`:

```python
AUTOMATED_ERRANDS: frozenset[str] = frozenset({
    "today", "session", "recall", "doctor",
    # Chronos additions:
    "ferry", "spend", "heal", "blessing",
})
```

Both Argos and Chronos import from here. Argos's `ERRAND_WHITELIST` becomes a compatibility alias.

### Persistence

Last-fired times per ritual: `state/chronos/rituals_state.json` (atomic write). Read at tick-start; updated when a ritual fires. The `min_interval_seconds` (default 60s) prevents tight-loop double-fire — even if the time-matcher says yes twice in the same minute.

### Daemon integration

In `runtime/daemon.py::run()`, between the Pan check and the session call, add:
```python
fired = chronos.tick()
# fired: list of {ritual_id, errand, output_head, elapsed_ms}
```
Each fire is recorded to Mnemosyne under `chronos.fired`. No daemon-blocking; chronos uses the same Lachesis-style quota machinery as Argos to cap excess.

### CLI errand `invoke chronos`

```
invoke chronos rituals               # list configured + next-due
invoke chronos ritual add <id> <when> <do>
invoke chronos ritual remove <id>
invoke chronos tick                  # manual one-shot evaluation
invoke chronos check "<when-expr>"   # would this expression fire now? + next-3
```

---

## Constitution

| invariant | how Chronos honors it |
|---|---|
| S1 | every fire → Mnemosyne (`chronos.fired`) with output_head + elapsed_ms |
| S3 (no surprise mutation) | rituals only run whitelisted errands; cannot trigger ratify/kindle |
| S6 | `next_due(spec)` answers the verifiable question "when will this fire" |
| S7 | errand whitelist excludes all GATED operations |
| AP1 | one primordial ~250 LOC + one CLI errand + shared whitelist module |
| AP3 | grammar rules are class-level; not per-ritual hardcoded |
| AP7 (ledger-balancing) | the rituals actually fire — verified end-to-end with `chronos tick` |

---

## Safety boundaries

- **`min_interval_seconds = 60`** default — prevents tight-loop double-fire (operator-configurable per ritual).
- **`max_fires_per_tick = 3`** — if 5 rituals all match the same minute, only 3 fire that tick; the rest fire next tick.
- **Errand whitelist** prevents arbitrary command execution.
- **Wall-clock-only** — Chronos uses `Nyx.now()` (real time). No "virtual time" / fast-forward modes (use `chronos.tick(now=...)` for tests).
- **Crash-safe** — if a ritual fires and the daemon crashes mid-execution, `last_fired_at` is written BEFORE execution; a partial run won't be re-attempted on restart (operator gets a `chronos.fired` record marking the half-state).

---

## What does NOT ship this arc

- **No full cron grammar** (e.g., `*/15 9-17 * * 1-5`). The named grammar is sufficient for the use cases. Full cron later if demanded.
- **No timezone support** — local time only. Operator's machine timezone applies.
- **No `do` arguments** — `do: "today"` works; `do: "today --resolve ..."` doesn't. Future arc.
- **No retry on failure** — if an errand errors, the failure is recorded; ritual fires on its next schedule.
- **No catchup on missed fires** — if the daemon was down at 09:00 and starts at 09:35, the 09:00 fire is SKIPPED (not back-filled). Documented; predictable.

---

## Tests

`tests/test_chronos.py` — ~25 cases:
- `parse_when`: each grammar variant + invalid input
- `matches_now(spec, now)` for daily/weekday/specific-day/monthly/every/hourly
- `RitualSpec.validate` rejects unwhitelisted errands
- `Chronos.tick`: fires once when match, doesn't fire twice in same minute
- `Chronos.tick`: respects `min_interval_seconds`
- `Chronos.tick`: max_fires_per_tick ceiling
- Last-fired persistence round-trip
- `next_due` computes correct upcoming time for each grammar
- `invoke chronos ritual add/remove` round-trip via monkey-patched config path
- `invoke chronos check` returns sensible output
- Errand whitelist enforcement at config-load AND at fire-time
- The Argos `ERRAND_WHITELIST` alias still works (compatibility)

---

## Authorization

Per the Decade plan approved 2026-05-19 (Arc 15 of 21). **Chronos gives the substrate a clock that does things.** Combined with Argos-Eyes (events) and the daemon (cadence), Olympus now responds to time, files, AND its own internal signals.

*The standard is holy shit, that's done. The substrate keeps the hours.*
