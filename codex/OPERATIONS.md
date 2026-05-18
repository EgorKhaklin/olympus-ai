<div align="center">

# ⚙ OPERATIONS ⚙

**the operator runbook**

</div>

---

This document is for the human running Olympus. It assumes you have the
repo cloned and Python 3.9+ available. If you are reading this from a
fresh `git clone`, start with **First-time setup**; otherwise jump to
the section matching what you need to do.

---

## First-time setup

```bash
# 1. Optional: install via pip so `invoke` is on $PATH
pip install -e .

# 2. Kindle the hearth (deployment identity-seal)
invoke kindle my-olympus-deployment "production cognitive substrate"

# 3. Bring forth the substrate (ensures all dirs exist)
invoke bring-forth

# 4. Run one session to confirm everything wires together
invoke session

# 5. Look at what just happened
invoke status
invoke wisdom
```

If you skipped `pip install -e .`, replace `invoke` with `./scripts/invoke` in every command below.

---

## Daily / continuous operation

### Option A — run the daemon (recommended)

The daemon runs `session + improve` on a cadence, indefinitely. It uses
the OS supervisor (`launchd` on macOS, `systemd` on Linux) so it
restarts on crash and survives reboot.

```bash
# Install — generates the unit and loads it. Default interval: 600s.
invoke daemon install
invoke daemon install --interval 300   # custom interval (seconds)

# Confirm it's running
invoke daemon status

# Tail logs
tail -F state/daemon.log

# Stop and remove
invoke daemon uninstall
```

On macOS the unit lands at `~/Library/LaunchAgents/com.olympus.daemon.plist`.
On Linux it lands at `~/.config/systemd/user/olympus-daemon.service`.

### Option B — bash cron loop

If you prefer cron over a long-running daemon, the bash loop from the
self-improvement arc still works:

```bash
# Add to crontab — runs one session + one improve pass every 10 minutes
*/10 * * * * /absolute/path/to/Olympus/scripts/loop.sh
```

### Option C — manual invocation

```bash
invoke session         # one cognitive pass
invoke improve         # one Prometheus self-improvement pass
invoke iris --open     # rebuild dashboard + open in browser
invoke wisdom          # what the substrate has learned
```

---

## Reading the substrate

```bash
invoke status            # one-line health snapshot
invoke history           # last 10 sessions
invoke shoulders         # what Atlas is currently carrying
invoke reflect           # Epimetheus's hindsights from last 24h
invoke cassandra         # warnings dismissed + later vindicated
invoke meta              # Olympus's self-portrait
invoke iris              # rebuild dashboard → state/iris/index.html
invoke cartograph        # show architecture diagram (Mermaid)
invoke schemas           # list all JSON Schemas Themis publishes
invoke schemas prophecy.verified   # show one specific schema
```

---

## Panic and recovery

Pan is the circuit breaker. He enters **panic state** when the Furies
fire more than 3 invariant violations in 5 minutes. While panicked,
new action ratifications are refused — `action_queue.ratify()` raises
`PanicError`. The daemon's loop skips its `session + improve` cycles
and waits.

```bash
# Check whether Pan is panicked
invoke panic

# Clear the panic (acknowledges current violations; future ones
# still count)
invoke panic --clear

# Inspect what triggered it
tail -20 state/mnemosyne/invariantviolated.jsonl
```

### Why was Pan panicked?

A real panic means the Furies caught something. **Read the violations
before clearing.** Common causes:

- **Styx chain broken** (S1) — investigate `invoke verify`; if a
  manual JSONL edit happened, restore from `state/hades/` or git.
- **Pantheon drift** (S4) — a module exists on disk but is not in
  `PANTHEON.md` (or vice versa). Fix the list and re-run.
- **Apollo predicates missing verify()** (S5) — a new prediction was
  added without a verify callable.

After fixing the cause, `invoke panic --clear` and the daemon resumes.

---

## Healing derived state

Asclepius rebuilds anything **derived** — the Iris dashboard, Pan's
state file, Rhea's directory structure. Useful when:

- The Iris HTML is stale or got truncated
- A `state/` subdir was accidentally deleted
- Pan's state file got corrupted

```bash
invoke heal
```

Asclepius **never** modifies canonical state (Mnemosyne records, Styx
oaths). It only rebuilds what can be reconstructed from canonical
sources.

---

## Archiving (Charon's ferry)

Atlas's burdens accumulate over time. Charon ferries released burdens
older than the retention window (default 30 days) into Hades's archive.

```bash
invoke ferry                 # default retention: 30 days
invoke ferry --days 7        # ferry anything released > 7 days ago
```

Charon is idempotent — running twice produces the same final state.
Every ferry passage is itself recorded as `charon.crossing`, so the
audit trail of what was archived survives.

Archived burdens live in `state/hades/` as JSON files named
`<ts>--atlas-burden--<op>--<id>.json` (see `invoke describe underworld.hades`).

---

## Verifying invariants on demand

```bash
invoke verify    # Tisiphone walks the Styx chain; reports intact / broken
invoke labors    # Heracles runs the twelve canonical labors
invoke meta      # full substrate self-portrait
```

If any of these report failure, the cause is usually a manual edit to
`state/` files. Restore from git or from `state/hades/` archives.

---

## Adding a new domain

Olympus is generic; domain deployments add domain-specific gods, eyes,
predictions, and handlers. The pattern is:

1. Read `codex/BUILDING.md` for the deployment recipe.
2. Add gods under your domain's namespace; register them with
   Hephaestus, Argos, Apollo, Prometheus as needed.
3. Update `codex/DOMAIN.md` (deployment-side document) with C1..CN
   invariants that augment S1..S8.
4. Run `invoke labors` to confirm the substrate still holds.

---

## Troubleshooting checklist

| symptom | first thing to check |
|---|---|
| `invoke session` fails with "hearth unlit" | `invoke kindle <name> <vocation>` |
| Iris dashboard is blank | `invoke heal` (Asclepius rebuilds it) |
| Daemon installed but not running | `invoke daemon status`; check `state/daemon.log` |
| Pan panicked unexpectedly | Read `state/mnemosyne/invariantviolated.jsonl`; fix cause; `invoke panic --clear` |
| Cassandra reports many vindications | Review them; consider ratifying the underlying proposals |
| `state/` is huge | `invoke ferry --days 7`; consider `invoke improve` for JSONL rotation |
| Architecture map looks stale | `invoke cartograph --write` regenerates it |
| `tests/test_pantheon_coherence` fails | A module was added/removed without updating PANTHEON.md or the EXPECTED dict |

---

## Where the audit trail lives

Every load-bearing decision is reconstructable from:

- `state/mnemosyne/*.jsonl` — append-only per-kind records
- `state/styx.jsonl` — cryptographic oath chain
- `state/argos_pheromones.jsonl` — every observation deposited
- `state/action_queue.jsonl` — every action and its lifecycle
- `state/hades/*.json` — archived shades (via Charon or direct descend)
- `state/daemon.log` — daemon iteration log

Burn the source code, keep `state/` + `codex/`, and a future operator
can rebuild what was decided and why. That is S8 (Continuity of
Understanding) operationalized.

---

*Per Delphi 2026-05-18-compass-rose-arc.md. Maintained by the operator
and by Asclepius when derivable, never by an LLM auto-edit (AP1 + AP6
would fire).*
