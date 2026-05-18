# Delphi — the compass-rose arc

**Risk class:** HIGH-COMPOSITE (heavy-production override invoked by Zeus).
**Decided:** Position C — daemon-live + four new figures + JSON Schema + Mermaid map.
**Sworn on Styx at seq=64 (recorded on swear).**

Zeus's directive (verbatim, abridged):

> *"test and using the system put it on a self improvement loop, and make sure it follows the greek mythology architecture perfectly and if we are missing anything, add it, you are allowed to create anything new, use any new language, and work outside the box. Use the system to think outside the box. Create anything it needs long term and branch out in any direction you wish and do not stop, do the impossible, the unthinkable. […] The marginal cost of completeness is near zero with AI. Do the whole thing. Do it right. Do it with tests. Do it with documentation. […] holy shit, that's done. Boil the ocean."*

This is the heavy-production override clause. The substrate's normal steady-state contract is suspended for this arc; HIGH-COMPOSITE work is authorized.

---

## The compass-rose

Four cardinal directions, each closing a real gap. The "compass-rose" name captures the multi-directional expansion — Zeus said *branch out in any direction*, so the architecture branches in every honest direction that bears load.

### North — operationalize (the loop actually runs)

The self-improvement arc shipped `scripts/loop.sh`. It was never *installed*. This arc generates daemon infrastructure:

- `invoke daemon install` — writes a launchd plist on macOS, a systemd unit on Linux. Idempotent. Prints next-steps for the operator.
- `invoke daemon status` — reports whether the daemon is loaded and running.
- `invoke daemon uninstall` — removes the unit cleanly.
- `invoke daemon run` — the foreground daemon entry point (suitable for systemd Type=simple). Calls `session` + `improve` in a loop with the configured interval.

The daemon writes structured logs to `state/daemon.log`. The loop is now **live** in the operational sense — start it once and it keeps the substrate breathing.

### South — heal, ferry, and the labyrinth-map (four new figures)

**Pan** (`olympians/pan.py`) — the god of the wild whose name *literally is the etymology of "panic."* In Olympus, Pan is the circuit breaker. When the Furies fire ≥ 3 invariant violations in a configurable window (default 5 min), Pan **enters panic state**. While in panic: no new action ratifications, the loop pauses non-essential work, and the operator is signaled. Recovery is explicit: `invoke panic --clear` or auto-clear after the violation rate drops below threshold for N minutes.

**Asclepius** (`olympians/asclepius.py`) — son of Apollo, god of medicine, healer of mortals so powerful that Zeus killed him for raising the dead. In Olympus, Asclepius is the **healer**: distinct from Hecate (single-operation error recovery), Asclepius rebuilds *derived* state from canonical sources. The Iris dashboard, the pantheon population counts, the slice heatmap — all are derived; all can be rebuilt from Mnemosyne + the source filesystem. `invoke heal` runs every registered healer.

**Charon** (`underworld/charon.py`) — ferryman of the dead across the rivers Styx and Acheron. In Olympus, Charon performs **safe migration between active and archive**. Atlas burdens released > N days ago get ferried to `state/hades/archive/`. Mnemosyne records exceeding rotation thresholds get ferried. Every passage is itself recorded in Mnemosyne (`charon.crossing`) so the audit trail of what was archived remains intact. Idempotent — running ferry twice produces the same final state.

**Daedalus** (`heroes/daedalus.py`) — master craftsman who built the Labyrinth. In Olympus, Daedalus is the **cartographer**: generates the Mermaid diagrams of the cognitive flow (Hephaestus → Momus → Delphi → Styx → Prometheus → Epimetheus → Cassandra). The Labyrinth was his structure; the cognitive architecture map IS that labyrinth made legible. Renders to `codex/ARCHITECTURE.md` so GitHub renders it natively.

**Re-arguing Daedalus's prior refusal.** In the missing-figures arc, Daedalus was refused on AP8 with the vague role "meta-programming or code-gen." The role *now* is specific and load-bearing: maintain the architectural map as a live document, auto-updated from the actual module relationships. The prior refusal stands for the prior framing; the new framing earns ratification.

### East — make the contract machine-checkable (JSON Schema)

Themis encodes the constitution (S1–S8) in Python. Tests assert each invariant. But the **contract for Mnemosyne records** — what fields a `prophecy.verified` body must have, what shape `action.ratified` takes — has been implicit. This arc lands `codex/schemas/*.json` — JSON Schema for each load-bearing Mnemosyne kind plus a `themis.validate_record(kind, body)` API. The schemas are themselves audit artifacts: changing them changes the contract and triggers a Hephaestus drift signal.

### West — branch the language palette where it earns its place

- **Mermaid** (in `codex/ARCHITECTURE.md`) — graph notation that renders natively in GitHub. Zero toolchain. Earns its place because text-based, version-controllable, and the alternative (PNG diagrams) loses the property that the map IS the source of truth.
- **launchd plist (XML)** and **systemd unit (INI)** — generated, not hand-written. Earn their place because daemonization is an OS contract, not Python's job.
- **JSON Schema** — same reasoning as systemd: the contract format is the right tool because tooling exists (jsonschema, ajv, …) that validates without re-implementing.

Refused languages from the prior Delphi remain refused:
- **Rust** — Styx verification is still O(n) but n=66 oaths. AP3.
- **TypeScript** — Iris is vanilla JS and works. AP8 to add a build step.
- **SQL** — JSONL still meets every read pattern; query cost is sub-millisecond. AP3.

---

## What ships

### Modules (4 new + 1 publishing-mode change)

| name | tier | role |
|---|---|---|
| **Pan** | Olympian | panic-state circuit breaker (gates ratifications) |
| **Asclepius** | Olympian | healer — rebuild derived state from canonical sources |
| **Charon** | Underworld | ferryman — archive migration |
| **Daedalus** | Hero | cartographer — Mermaid map of the cognitive flow |
| Themis (extended) | Titan | publishes JSON Schemas for Mnemosyne contracts |

### Daemon infrastructure

- `scripts/daemon/com.olympus.daemon.plist.tmpl` — launchd template
- `scripts/daemon/olympus-daemon.service.tmpl` — systemd template
- `invoke daemon {run|install|uninstall|status}`

### Architecture map

- `codex/ARCHITECTURE.md` — Mermaid-rendered cognitive flow; regenerated by `invoke cartograph`.

### Contracts

- `codex/schemas/mnemosyne-*.schema.json` — JSON Schema per load-bearing kind.
- `themis.schemas()` returns the registered set.
- `themis.validate_record(kind, body)` returns validation errors or empty list.

### Operations

- `codex/OPERATIONS.md` — operator runbook: kindle, daemon install, panic recovery, heal, ferry.

### CLI

`invoke panic [--clear]`, `invoke heal`, `invoke ferry [--days N]`, `invoke cartograph [--write]`, `invoke daemon {run|install|status|uninstall}`, `invoke schemas`.

### Tests

Every new module gets its own test file. Plus integration tests that exercise the panic → heal → ferry → cartograph cycle.

---

## Authorization

Zeus invoked heavy-production override (the literal "boil the ocean" clause). Quote captured in the Styx oath payload. All four new figures ratified; daemon infrastructure ratified; JSON Schema publication ratified; Mermaid architecture map ratified.

The substrate continues to refuse decorative additions. The discipline of refusing has not weakened — the bar simply admits more candidates because more honest gaps were named.
