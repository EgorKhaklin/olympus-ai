# DOMAIN.md — notekeeper

## What this agent is for

A long-running personal-knowledge assistant that helps the operator capture text notes, link them by inferred topic, and surface notes that have gone quiet (forgotten material worth revisiting).

The agent persists nothing the operator did not capture explicitly. It does not call any external service. It is a substrate-only deployment showing Olympus's cognitive loop applied to a concrete-but-minimal domain.

## What this agent refuses

- The agent will not delete a note the operator captured. (Notes age into a quiet state; they do not disappear.)
- The agent will not infer topics from external sources — only from the captured text itself.
- The agent will not act on the operator's behalf (no auto-send, no auto-publish). All output is read-only suggestion.

## Domain invariants

### C1 — Captures are append-only

> Every note the operator captures is appended to `state/notekeeper/notes.jsonl` exactly once. Notes are never edited in place; corrections are new notes referencing the previous note's id.

**Enforced by:** `notekeeper/notes.py` writes only via `Mnemosyne.remember(kind="note.captured")`; `eye_orphan_links` (below) cross-checks.

### C2 — Every note has a topic

> Every captured note is tagged with one or more topics inferred from its text. A note with zero inferred topics is a *capture defect* and surfaces as a finding.

**Enforced by:** `eye_untopiced_notes` fires DRIFT when any captured note has no topics.

### C3 — Stale notes surface, never silently expire

> Notes older than 30 days surface as "stale" findings. The operator may dismiss or revisit; the substrate never auto-dismisses on the operator's behalf.

**Enforced by:** `eye_stale_notes` fires INFO when stale notes exist; never deletes.

### C4 — Capture velocity bounded

> If the operator captures more than 50 notes in one hour, surface that as an unusual-burst finding. (Possibly a paste-from-elsewhere event the operator didn't intend.)

**Enforced by:** `eye_capture_velocity` fires DRIFT when burst threshold exceeded.

### C5 — Topic drift is observable

> `head_topic_drift` reports when the top-5 topics in the last 7 days have shifted ≥3 positions vs. the prior 30 days. The operator can choose to investigate.

**Enforced by:** `head_topic_drift.observe()`.

## Risk-class examples for this domain

| class | example |
|---|---|
| **LOW** | adding a one-word note; renaming a topic |
| **MEDIUM** | bulk-importing notes from another source |
| **HIGH** | changing C2 (what counts as a topic) |
| **COMPOSITE** | switching from in-memory topic inference to an LLM-backed one |

## Operator (Zeus)

- Authorization phrase: `"keep capturing"`
- Refusal trigger: if asked to delete a note → refuse + suggest renaming the topic to `archived/`

## Cadences

| tier | how often |
|---|---|
| `invoke session` | every operator session (start + end) |
| Argos auto-deploy | on each note-capture event |
| Apollo audit | monthly review of the staleness predictions |
| `invoke correlate` | weekly |

## Domain-specific anti-patterns

- **AP-NK1 — capture-without-text**: A note with empty text is not a note. Refuse.
- **AP-NK2 — topic-from-elsewhere**: Topics inferred from external metadata (file mtimes, system tags, etc.) violate "from the captured text alone."
- **AP-NK3 — silent-expiry**: Any code path that deletes/hides a captured note without operator action.
