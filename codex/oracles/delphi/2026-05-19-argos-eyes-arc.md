# Delphi — the Argos-Eyes arc 👁️ (Decade #3)

**Risk class:** LOW-MEDIUM.
**Decided:** Position A — extend the existing Argos colony with a new `FilesystemEye` class parameterized by a `WatchSpec`. Operator declares watches in `state/config.json::argos.watches[]`. Eyes register with the colony at runtime; the daemon's existing scan loop picks them up. **Pure Python polling** (no `watchdog` / `fsevents` dep). Two action types this arc: `alert` (raise pheromone) and `errand` (run a whitelisted errand). `summarize` deferred to future arc when LLM action is needed.
**Sworn on Styx at this arc's ratification.**

Zeus's directive (planning artifact): *"Arc 14 — Argos-Eyes: filesystem watcher; on change fire sessions or raise pheromones; e.g. watch state/config.json → alert on change (would have caught my Hades bug at runtime not session-end)."*

---

## Phase 0 — what Argos already is

Argos in mythology was the all-seeing giant with 100 eyes (some sleeping, some watching at all times). When Hermes killed Argos, Hera placed his eyes on the peacock's tail.

In Olympus, Argos is already operationalized:
- **`monsters/argos/colony.py`** orchestrates dispatch + pheromone aggregation
- **`monsters/argos/base.py`** defines `Eye`, `EyeFinding`, `Pheromone`
- **9 existing Eyes** under `monsters/argos/eyes/` watching substrate slices (apollo coverage, chronicle gap, oath freshness, pantheon completeness, styx chain, etc.)
- Each daemon iteration runs `colony.scan()` which calls every Eye

**Arc 14 reuses this architecture for filesystem changes** rather than building a parallel watcher subsystem.

---

## What ships

### `src/olympus/runtime/fs_watcher.py` (~110 LOC)

Pure-Python file snapshotter:
- `FsSnapshot.take(path, glob="*", max_files=500) → dict[str, FileState]` — walks the path (or single file), computes sha256 + mtime for each match, returns a snapshot dict
- `diff(old, new) → list[FsChange]` — produces `(path, change_type)` for each added/modified/deleted file
- Persists per-watch snapshots at `state/argos/fs_snapshots/<watch_id>.json`
- Safety: `max_files` ceiling; refuses to descend into `.git`, `__pycache__`, `node_modules`, `state/mnemosyne` (the substrate's own audit log)

### `src/olympus/monsters/argos/eyes/eye_filesystem.py` (~150 LOC)

`FilesystemEye(spec: WatchSpec)` — one Eye instance per configured watch. Each scan compares current snapshot against the persisted baseline; emits an `EyeFinding` per change. Pheromones land in the normal colony bucket so Hephaestus + the today oracle pick them up.

```python
@dataclass
class WatchSpec:
    id: str                   # operator-chosen, e.g. "journal-folder"
    path: str                 # absolute or ~-prefixed
    glob: str = "*"           # narrow what's watched
    action: str = "alert"     # "alert" | "errand:<name>"
    enabled: bool = True
    max_files: int = 500
```

### Config schema extension

`runtime/config.py` gains an `argos` section:
```json
{
  "argos": {
    "watches": [
      {"id": "config-file", "path": "state/config.json",
       "glob": "*", "action": "alert"},
      {"id": "journal", "path": "~/Documents/journal",
       "glob": "*.md", "action": "errand:today"}
    ]
  }
}
```

Watches are loaded at colony-init time and registered as Eyes. Re-loading happens on each `invoke argos scan` (config can change without daemon restart).

### CLI errand extensions

Current `invoke argos` runs the colony once. New subcommands:
- `invoke argos watches` — list configured watches + their last-scan status
- `invoke argos scan` — explicit colony pass (same as existing, but named for discoverability)
- `invoke argos watch add <id> <path> [--glob G] [--action A]` — convenience adder
- `invoke argos watch remove <id>` — convenience remover

### Errand whitelist (for `action: "errand:<name>"`)

Filesystem changes triggering arbitrary errand execution is dangerous. The whitelist is a small set:
- `today` — surface the change in the daily oracle
- `session` — kick off a cognitive cycle
- `recall` — pre-warm the Hippocrene index
- `doctor` — run a health check

Anything outside the whitelist is rejected at config-load time with a clear error.

### Daemon integration

The existing daemon loop already calls `colony.scan()` each iteration. Filesystem Eyes register with the colony automatically; no daemon changes required. The first iteration after enabling a watch establishes the baseline; subsequent iterations report diffs.

---

## Constitution

| invariant | how Argos-Eyes honors it |
|---|---|
| S1 | every pheromone + every fs change → Mnemosyne (`argos.fs_change`) |
| S2 (decentralized) | each FilesystemEye is independent; no cross-Eye reads |
| S3 (no surprise mutation) | Eyes only READ the filesystem; never write to watched paths |
| S6 | each pheromone cites the sha-before + sha-after + path |
| S7 (HIGH-risk gated) | errand whitelist excludes all GATED operations |
| AP1 | one new module + one new Eye class; reuses colony machinery |
| AP3 | watches are class-level (paths, globs); not per-file rules |
| AP7 | the test: change `state/config.json` → next scan emits pheromone |

---

## Safety boundaries (named explicitly)

- **`max_files` per watch** prevents accidental tree-walks of huge directories (default 500; configurable).
- **Skip-list** never descends into `.git`, `__pycache__`, `node_modules`, `state/mnemosyne` (the substrate's own JSONL audit log — watching it would create feedback).
- **Errand whitelist** prevents arbitrary command execution.
- **Path resolution** uses `pathlib.Path.expanduser().resolve()`; no shell expansion.
- **No write actions** — `FilesystemEye` is read-only.

---

## What does NOT ship this arc

- **No `summarize` action** — needs the LLM bridge and a clean way to pass file content to Athena. Deferred to a follow-up if useful.
- **No `watchdog` / `fsevents` dep** — pure Python polling at the daemon's existing 10-minute cadence is sufficient for the named use cases.
- **No sub-minute reactivity** — operator can lower daemon interval or run `invoke argos scan` manually.
- **No recursive symlink resolution** — symlinks are read as their target's sha, not followed for descent.
- **No remote/cloud paths** — local filesystem only.

---

## Tests

`tests/test_argos_eyes.py` — ~20 cases using `tmp_path`:
- `FsSnapshot.take` with a single file and a directory glob
- `diff()` detects added / modified / deleted
- `WatchSpec` defaults + validation
- `FilesystemEye.scan()` emits no findings on baseline; emits findings after a change
- Skip-list excludes `.git` etc.
- `max_files` ceiling honored
- Errand whitelist rejects unknown actions
- `invoke argos watches` lists configured
- `invoke argos watch add/remove` round-trip
- Persisted snapshot survives across runs

---

## Authorization

Per the Decade plan approved 2026-05-19 (Arc 14 of 21). **Argos-Eyes gives the substrate eyes on the filesystem.** Operator can watch their config (real-time alert on Hades-style contamination), their journal (auto-pulse the today oracle), or any project tree.

*The standard is holy shit, that's done. The giant's eyes now see the world outside.*
