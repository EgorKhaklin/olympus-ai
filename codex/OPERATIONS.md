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
invoke pythia            # show recent external consultations
```

## Reaching outside Olympus

Pythia bridges to the world via `urllib`. She is not an LLM — she
fetches raw HTTP and records every consultation.

```bash
invoke pythia --github "cognitive substrate event sourcing"
invoke pythia --web https://example.com/document.json
invoke pythia            # list recent consultations
```

Each consultation produces a `pythia.consultation` Mnemosyne record
with the query, response code, byte count, and head bytes (capped
at 256 KB). Use this to record external knowledge with the same
audit-of-record discipline as internal events.

## Querying from outside Python

The HTTP API exposes a localhost JSON surface (read-only):

```bash
invoke serve                       # foreground, http://127.0.0.1:8765
invoke serve --port 9000           # custom port
invoke serve --host 0.0.0.0        # bind broadly (review CORS/firewall first)

# In another shell:
curl http://127.0.0.1:8765/status
curl http://127.0.0.1:8765/wisdom | jq
curl http://127.0.0.1:8765/mnemosyne/session.completed?limit=5 | jq
```

The API is **read-only by design** — `POST`, `PUT`, `DELETE` all
return 405. Mutations go through `invoke`.

## Shadow execution (canary for substrate self-modification)

Castor + Pollux let you test a proposed substrate change without
touching production state:

```bash
invoke shadow                                  # one shadow session
invoke shadow --mod OLYMPUS_INTERVAL=60        # with env override
invoke shadow --directive "test directive"
```

Castor materializes a tempdir with symlinks to `codex/`, `src/`,
`scripts/`, copies the hearth seal, then spawns `invoke session` with
`OLYMPUS_ROOT` pointing at the tempdir. The shadow run writes only
to the tempdir's `state/`. Production is untouched. The report comes
back as JSON; `Pollux.compare(prod_report, shadow_report)` surfaces
structural diffs.

## Self-tuning advice

Metis observes outcomes (Epimetheus hindsights, Cassandra
vindications, daemon iteration stats) and proposes parameter changes:

```bash
invoke tune                # default lookback: 168h (one week)
invoke tune --hours 24     # last 24 hours of evidence
invoke tune --no-raise     # just show; don't write proposals
```

Metis never directly tunes. Her recommendations land in
`state/hephaestus/proposals/metis-*.json` and go through the standard
Momus → Delphi → Zeus pipeline. The meta-loop is bounded by the same
constitutional discipline as everything else.

## Plugins

Third-party extensions register via `pyproject.toml` entry-points.
See `codex/PLUGINS.md` for the author guide.

```bash
invoke plugins             # show what's loaded + what failed
```

## Asking the substrate questions (interactive)

The substrate can answer common questions in plain English from its
own records — *not* via LLM, just pattern-matched templates. Limited
but honest: every answer cites the Mnemosyne kind(s) it drew from.

```bash
invoke ask "what happened today"
invoke ask "what are we worried about"
invoke ask "how is the loop"
invoke ask "who is pan"
invoke ask "what has the substrate learned"
invoke ask "help"
```

## Causal lineage (Ariadne's thread)

When code uses `ariadne.thread(...)` instead of `mnemosyne.remember(...)`,
each record gets a `trace_id` and an optional `parent_trace_id`.
Then you can walk the causal chain:

```bash
invoke ariadne <trace_id>   # show the chain from leaf to root
```

The chain is bounded by `MAX_DEPTH=64` so cycles or pathological
back-pointers don't loop forever.

## Counterfactual reasoning (Nemesis)

Nemesis asks: "what would have happened if we'd decided differently?"
For each recent ratified action, she runs a Castor shadow with an
alternative choice and Pollux-compares to what production did.

```bash
invoke nemesis              # one pass, max 3 counterfactuals
invoke nemesis --max 1      # smaller pass
invoke nemesis --keep-shadows  # don't clean up shadow dirs
```

Nemesis never tunes — she records gaps. Metis turns those gaps into
proposals.

## Self-audit (Momus red-team)

Momus audits his own AP catalog by running a curated corpus of
adversarial proposals through it. Any case that should have been
caught but wasn't is a constitution gap.

```bash
invoke redteam              # 0 → all correct, non-zero → catalog has gap
```

## Narrative (Clio)

Clio composes a structured weekly digest from Mnemosyne records,
writing to `codex/journal/<date>-clio-digest.md`.

```bash
invoke narrate              # default window: 7 days
invoke narrate --days 1     # today only
invoke narrate --dry-run    # show what would be written
```

The daemon auto-runs `narrate` every 6 iterations.

## Federation (Hermes between deployments)

If two Olympus instances are running, they can exchange digests via
the HTTP API:

```bash
invoke federate http://peer.example:8765      # fetch a peer's digest
invoke federate                               # list known peers
```

Both sides remain read-only on each other's substrate state.

## Formal specs (Themis's deepest layer)

Themis publishes TLA+ specifications of the substrate's safety
properties. See `codex/SPECS.md` for the full discussion.

```bash
invoke specs                       # list all specs
invoke specs hephaestus-pipeline   # show one
```

## Sacred geometry layer (Pythagoras + Plato)

Pythagoras owns the sacred constants and numerical primitives.
Plato organizes the pantheon by function via the five Platonic solids.

```bash
invoke pythagoras                   # show φ, π, √2, e, √3, √5
invoke pythagoras fib 15            # first 15 Fibonacci numbers
invoke pythagoras backoff 8 1.0     # 8 Fibonacci backoff delays
invoke pythagoras harmony 1.618     # score against φ, 1/φ, 1, 2
invoke pythagoras triples 50        # Pythagorean triples below 50

invoke plato                        # five-solid taxonomy of the pantheon
invoke plato classify athena        # which solid does Athena belong to?

invoke harmony                      # substrate ratios vs sacred anchors
invoke geometry                     # combined Plato + Pythagoras view
```

Hecate's retry path now uses Fibonacci backoff by default — smoother
than exponential. Metis can use `golden_section_search` to *find*
optimal parameter values rather than guessing them. See
`codex/GEOMETRY.md`.

## Raising a proposal via HTTP (the only write surface)

The HTTP API has exactly one write route: `POST /proposals/raise`.
A proposal raised this way enters the standard Hephaestus → Momus
→ Delphi → Zeus pipeline.

```bash
curl -X POST http://127.0.0.1:8765/proposals/raise \
  -H "Content-Type: application/json" \
  -d '{
    "summary": "rotate the test slice",
    "proposed_fix": "rotate state/test.jsonl when > 5k lines",
    "rationale": "approaching disk-fill",
    "raised_by": "external-monitor",
    "risk_class": "LOW"
  }'
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

---

## The Decade + Eos errands (Arcs 12–22)

Twelve arcs of operational capability added after the compass-rose
era. Each is its own Delphi note in `codex/oracles/delphi/`.

### 👑 Throne — conversational front door (Arc 12)

```bash
invoke throne                       # interactive REPL
invoke throne "<one-shot question>"
invoke throne --voice               # responses spoken via macOS `say`
```

The Throne calls **SAFE_ERRANDS** on the operator's behalf
(`doctor`, `today`, `wisdom`, `harmony`, `status`, `shoulders`,
`geometry`, `ask`, `agent`, `session`, `blessing`, `spend`, `vault`,
`recall`, `replay`). For GATED operations (`kindle`, `ratify`,
`hephaestus apply`, etc.) it shows the exact CLI command — never
executes them.

### 💧 Hippocrene — semantic recall (Arc 13)

```bash
invoke recall "<query>" [-k N] [--kinds K1,K2]
invoke recall --stats              # what's indexed
invoke recall --rebuild            # force re-index
```

Pure-Python TF-IDF over Mnemosyne kinds (`agent.invocation`,
`llm.call`, `throne.turn`, `demeter.chunk`, etc.). Zero deps.

### 👁️ Argos-Eyes — filesystem watcher (Arc 14)

```bash
invoke argos watches
invoke argos watch add <id> <path> [--glob "*.md"] [--action alert]
invoke argos watch remove <id>
invoke argos scan
```

Action whitelist: `alert`, `errand:today`, `errand:session`,
`errand:recall`, `errand:doctor`.

### ⏰ Chronos — scheduled rituals (Arc 15)

```bash
invoke chronos rituals
invoke chronos ritual add <id> <when> <do>      # e.g. "weekday 09:00" today
invoke chronos ritual remove <id>
invoke chronos tick
invoke chronos check "<when-expr>"
```

Grammar: `daily HH:MM` · `weekday HH:MM` · `weekend HH:MM` ·
`<day> HH:MM` · `monthly <N> [HH:MM]` · `every <N>m` · `every <N>h` ·
`hourly`. Errand whitelist shared with Argos.

### 🔧 Hephaestus-PR — proposals → real git PRs (Arc 16)

```bash
invoke hephaestus pending                                  # ratified-but-unapplied
invoke hephaestus apply <pid>                              # DRY-RUN
invoke hephaestus apply <pid> --really                     # actually mutate
invoke hephaestus apply <pid> --really --skip-pr           # local commit only
```

**Constitutional guarantees (all tested):**
- Never push to `main`/`master`/`trunk`/`production`/`release`
- Never `--force` push (no parameter exists)
- Never `git merge` (no merge function exists)
- Refuse on dirty tree
- Branch name always `prometheus/<pid>` (no operator-chosen paths)
- Throne CANNOT trigger apply (S7-gated)
- Every apply records `prometheus.applied` to Mnemosyne

### 📚 Demeter-Library — knowledge-base ingestion (Arc 17)

```bash
cp ~/docs/onboarding.md state/demeter/library/
invoke demeter ingest                # process new/changed files
invoke demeter ingest --reingest     # force re-process
invoke demeter library               # list ingested docs
invoke demeter forget <document_id>  # mark forgotten (S1: chunks remain)
```

Supports `.md`, `.txt`, `.rst`, `.pdf` (pdf needs `pip install pypdf`).

### 🎙️ Throne-Voice — TTS (Arc 18)

```bash
invoke speak "<text>" [--voice V] [--rate N] [--block]
invoke throne --voice                # chat with speech output
```

macOS `say` only. STT explicitly deferred. `speak` is in
`AUTOMATED_ERRANDS` so Chronos rituals can speak.

### 🪶 Hermes-MCP — Olympus as MCP server (Arc 19)

```bash
invoke mcp           # serve over stdio
invoke mcp --probe   # print server info + tools; exit
```

Wire into `~/.claude/mcp_servers.json`:
```json
{"mcpServers": {"olympus":
    {"command": "/Users/vanta/.local/bin/invoke", "args": ["mcp"]}}}
```

Exposes 14 SAFE_ERRANDS as MCP tools; GATED ops are unreachable.

### 💸 Plutus — spend ledger + budget (Arcs 9 + 20)

```bash
invoke spend                                  # all-time
invoke spend --today | --7d | --30d
invoke spend --budget                         # budget status
invoke spend --acknowledge-budget --reason "..."   # clear breach refusal
```

Opt-in budget enforcement: set `plutus.budget.enabled = true` +
at least one threshold (`daily_usd`/`weekly_usd`/`monthly_usd`).
When over AND not acknowledged, `AnthropicBridge.call` refuses with
a clear error + override command. **Pan is NOT involved** — the
constitutional debate decided cost is a soft enforcement layer, not
a new Pan authority.

### 🗝️ Hades — secrets vault (Arc 10)

```bash
invoke vault status                       # what's stored, where (no values)
invoke vault deposit <name>               # hidden-input → keychain
invoke vault forget <name>
invoke vault migrate                      # plaintext config.json → keychain
```

Uses `keyring`: macOS Keychain · Linux Secret Service · Windows
Credential Manager.

### ⏪ Olympus-Replay — regression harness (Arc 21)

```bash
invoke replay                              # 20 recent, echo bridge (free)
invoke replay --limit 50
invoke replay --role hephaestus
invoke replay --since 24h
invoke replay --use-anthropic              # real LLM (respects budget)
```

Classifications: `stable` · `drift` · `broken` · `skipped` ·
`over-budget`. Schedule via Chronos for nightly sweeps.

### 🌅 Eos — UI + dashboard (Arc 22)

```bash
invoke agora --open
invoke serve --port 8765 &
```

12 pages: 👑 Throne · Dashboard · Today · Doctor · Spend · Library ·
Watches · Rituals · Replay · Proposals · Agents · Setup.

### 🔄 today --resolve — Tartarus discipline (Arc 12)

```bash
invoke today --resolve <slice> --re-raise
invoke today --resolve <slice> --dismiss-as-stale "<reason>"
```

Closes longstanding `today` findings honestly: re-raise as a fresh
proposal OR record an explicit dismissal-reaffirmation (suppresses
for 7d). Per Tartarus: nothing deleted from Mnemosyne; production
metrics filter test seeds.
