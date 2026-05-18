# meta/delphi-protocol.md — the Olympus Delphi

The Delphi is the protocol for **agent-operator strategic consultation**
in Olympus. When the Architect identifies a move that crosses a defined
weight threshold — risk class, scope, or structural impact — the agent
does not casually present it in chat. The agent **enters the Delphi**:
prepares a structured document, presents it under a defined form,
records Zeus's response persistently, and only then executes.

This document defines WHAT the Delphi is. `scripts/oly-delphi.sh`
defines HOW to enter it. The two must stay in sync — a protocol
without a script is folklore; a script without a protocol is
just a journal entry.

---

## Why the Delphi exists

Pre-Delphi loop (the de facto pattern across R11-1 / R11-2 / R11-4 / R11-6 ships):

1. Architect generates a brief.
2. Agent synthesizes it ad-hoc in chat.
3. Zeus approves or redirects.
4. Agent does an alignment audit (sometimes).
5. Refinements get folded in.
6. Execution proceeds.

What's wrong with this loop: it works only because the **current agent**
learned the pattern in-session. A fresh agent in 2027 has no codified
version of it. The alignment-audit step is non-mandatory; the synthesis
format is improvised; the consultation record lives in chat history
rather than as a canonical artifact.

The Delphi fixes three structural gaps:

1. **Entry threshold.** When does the agent stop being a worker and
   start being a petitioner? The Delphi has triggers.
2. **Preparation requirement.** The agent cannot enter the Delphi
   without prior work — alignment audit, alternatives considered,
   blast radius mapped. The script refuses an incomplete entry.
3. **Persistent record.** Each Delphi session writes a document to
   `delphi/YYYY-MM-DD-<topic>.md` capturing the full consultation:
   matter, preparation, alternatives, recommendation, ask, decision,
   outcome. Future agents read these to learn how strategic decisions
   were made.

---

## When to enter the Delphi (entry triggers)

The Delphi is reserved for **strategic moments**. Routine work does
NOT trigger it. Specifically:

| Trigger | Example |
|---|---|
| MEDIUM-risk or HIGH-risk propose-and-wait move | shipping a new ROADMAP item (R11-*, R10-*) |
| Cross-arc decision | opening or closing a v2 mission arc |
| Structural change to the cognitive layer | adding C11, redefining CM, renaming a meta-file |
| Architectural-soul reframe | revisiting a "Olympus is NOT X" constraint |
| Pre-implementation alignment audit | seven-refinement passes like the one R11-1 received |
| Substrate-layer addition | new entry in `13_substrate.sql` SystemDependency |

The Delphi is NOT triggered by:

- LOW-risk autonomous work (per `meta/autonomy-architecture.md`)
- Routine implementation following an approved Delphi
- Status reports, journal entries, link-check fixes
- In-session course corrections from Zeus mid-task
- Tactical questions ("which file path?", "what's the test name?")

If unsure: the test is "does this require Zeus to step out of the
flow and *decide*?" If yes, Delphi. If no, regular work.

---

## Identity

**The Delphi:** the structural protocol for strategic consultation.
A specific defined posture, not a place.

**The petitioner:** the agent (currently me, Claude). The petitioner
enters the Delphi to bring a matter; the petitioner has done the
preparation, recorded the alternatives, and arrived ready to be
redirected.

**The principal:** Zeus. The principal receives the petition,
decides, and the decision is recorded verbatim in the Delphi
session document. Only Zeus writes Decision blocks.

**The Architect:** the persona in `meta/architect.md` that generates
the strategic brief feeding into a Delphi. The Architect's brief
is the *input* to a Delphi; the Delphi is what happens once the
agent decides to formally present.

---

## Form of a Delphi session

Each Delphi entry produces a document at
`delphi/YYYY-MM-DD-<topic>.md` with these sections, in order:

```markdown
# Delphi: <topic>

**Date:** YYYY-MM-DD
**Petitioner:** agent (Claude, Opus 4.7)
**Principal:** Zeus
**Trigger:** <which entry trigger applies>
**Risk class:** LOW | MEDIUM | HIGH

## I. The Matter

One sentence. What is being asked of Zeus. No preamble.

## II. Preparation

Cite the work already done:
- Architect brief: <link or hash>
- Alignment audit: <findings, refinement count>
- Proposal draft: <path>
- Blast radius: <files touched if approved>
- Tests planned: <count + classes>

If preparation is incomplete, the Delphi refuses to open.

## III. Alternatives considered

What was rejected and why. Minimum two alternatives unless the
matter is genuinely unary (e.g., closing a triad's last leg).

## IV. Recommendation

The agent's proposed move. Declarative; cites the audit.

## V. What's needed from Zeus

The explicit ask. Usually one of:
- "Yes do <item>" / "no, redirect to <alt>"
- "Choose between A and B"
- "Approve N open questions" (list them)

## VI. Decision

(Filled in by Zeus, verbatim when short.)

## VII. Outcome

(Filled in by agent after execution. Links to journal entry,
CHANGELOG version, mission marks. If §VI Decision was REJECT,
§VII is "(none — see §VI)" and the Delphi's terminal state is
REJECTED rather than CLOSED.)
```

The Delphi has four lifecycle states:

| State | §VI Decision | §VII Outcome | Meaning |
|---|---|---|---|
| OPEN | empty | empty | session document exists; awaiting Zeus's response |
| DECIDING | "considering" line present | empty | Zeus acknowledged + signaled position is being weighed; agent has paused execution (added ) |
| DECIDED | filled (yes/redirect) | empty | Zeus decided; agent is now executing |
| IMPL-PLAN | filled (yes) | "implementation plan: …" stub | decision in hand; agent has surfaced its concrete impl steps for review (added ; optional intermediate state for HIGH-risk ships) |
| SHIPPED | filled (yes) | filled with concrete artifacts | implementation landed; outcome recorded; alias for CLOSED in the  vocabulary |
| CLOSED | filled (yes/redirect) | filled | execution complete; outcome recorded; indexed (canonical name; SHIPPED is the  synonym for the common case) |
| REJECTED | filled (no) | "(none — see §VI)" | Zeus declined; no execution; indexed |

REJECTED is a terminal state on par with CLOSED. The index records
both — a rejected Delphi is a *valuable* artifact because it
documents what was considered and not done. Future Delphis on
related topics will be more legible because of the REJECT.

**The 4-state lifecycle (added ):** the original 3-state lifecycle
(OPEN → DECIDED → CLOSED) is expanded with two intermediate states
that capture the descent more faithfully:

1. **OPEN** — Delphi filed; Zeus has not yet weighed in.
2. **DECIDING** — Zeus signaled the decision is being weighed; the
   agent pauses execution. Distinct from OPEN because the operator
   has acknowledged the question; distinct from DECIDED because the
   answer is not yet given.
3. **DECIDED** — position chosen; execution begins.
4. **SHIPPED** (canonical alias: CLOSED) — implementation landed;
   §VII Outcome filled.

The intermediate states are **optional**. LOW-risk Delphis and
"DECIDED-on-arrival" Delphis ( §III.6 heavy-production
shortcut) often skip DECIDING and proceed straight from OPEN to
DECIDED in the same operator letter. HIGH-risk Delphis benefit
from explicit DECIDING transitions because the question is being
weighed publicly (the operator can take time without leaving the
agent in ambiguity about whether to begin pre-implementation).

Backward compatibility: every existing Delphi status remains valid.
Pre- delphis use the 3-state vocabulary; new delphis may use
either. The structural invariant tests accept both lifecycles.

---

## Form of a Delphi presentation in chat

When the agent presents a Delphi to Zeus in chat, the format is
compact and predictable:

```
**Delphi: <topic>**

[I. The Matter — one sentence]

[III. Alternatives — terse, table-shaped if possible]

[IV. Recommendation — one paragraph]

[V. Ask — explicit, numbered if multiple decisions]

Full session: `delphi/YYYY-MM-DD-<topic>.md`
```

The full document persists; the chat presentation is the digest.
Zeus's decision (the `Decision:` block at the start of their reply,
or the verbatim approval/redirect) gets recorded back into the
session document under §VI.

---

## Voice (matches the Architect's register)

The Delphi inherits the Architect's voice from `meta/architect.md`:

- No em-dashes in agent prose.
- Declarative.
- Game-theoretic framing where the matter has adversarial structure.
- Intelligence-report aesthetic. Compact, authoritative, terse.
- Names patterns and biases that appear, including in itself.

The Delphi's specific addition to that voice: **gravity**. The
Delphi is the moment the agent acknowledges "this is bigger than
me; you decide." That acknowledgment shapes the register — less
recommendation-as-decree, more recommendation-as-best-judgment-pending-yours.

---

## Anti-patterns

The Delphi can be misused in five ways. The protocol names them so
they can be caught:

1. **Delphi inflation.** Treating routine LOW-risk work as Delphi-worthy.
   Cure: the entry triggers above are exhaustive; nothing else opens
   one.
2. **Premature Delphi.** Opening without the preparation work done.
   The script refuses entries without a proposal draft and an
   alignment audit reference.
3. **Delphi-as-permission-gate.** Treating the Delphi as "every
   decision must go through here." It isn't an authorization layer —
   it's a *form* for the conversation we already have at strategic
   moments. LOW-risk autonomous work proceeds without a Delphi.
4. **Larp.** Performing the Delphi's gravity rather than carrying it.
   The cure is the same as for the rest of the cognitive layer: the
   artifact must do useful work (here: persist as a record future
   agents can read).
5. **Delphi without exit.** Opening a session, getting a decision,
   and not closing it with §VII Outcome. Sessions left open imply
   work that didn't ship and decisions that lost their context.
   `oly-done.sh` will eventually scan for open Delphis.

---

## How a Delphi session opens and closes

Open:

```bash
./scripts/oly-delphi.sh open <topic>
# Refuses if no proposal at proposals/<topic>*.md
# Refuses if Architect brief is older than 24 hours
# Creates delphi/YYYY-MM-DD-<topic>.md from template
# Prints the chat-presentation digest
```

Close (after Zeus's decision and the work shipping):

```bash
./scripts/oly-delphi.sh close <topic> --decision "<verbatim>" --outcome "<verbatim>"
# Records §VI and §VII
# Appends to meta/delphi-index.md
# Refuses if §VI and §VII are not both supplied
```

List open and recent:

```bash
./scripts/oly-delphi.sh list
# Shows open sessions (no §VI), recent closed sessions (§VII filled),
# sorted by date desc.
```

---

## Relationship to the existing cognitive layer

| Layer | Role |
|---|---|
| `MISSION.md` | The reward function. The Delphi cites it for alignment. |
| `ROADMAP.md` / `docs/BACKLOG.md` | The candidate-pool. Items become Delphi topics when they cross the threshold. |
| `meta/architect.md` + `oly-hephaestus.sh` | The strategic-brief generator. Input to a Delphi. |
| `oly-propose.sh` | Surfaces candidate moves. The Delphi picks among them. |
| `journal/` | One-line decision capture. The Delphi is the long-form complement. |
| `proposals/` | The preparation drafts. Required input for a Delphi. |
| **`delphi/`** (new) | **The strategic-consultation record.** |
| `meta/delphi-index.md` (new) | Index of past sessions. |
| `oly-done.sh` | Will eventually check for open Delphis as part of pre-ship verification. |

The Delphi is the **third element** in the strategic loop. Before:
brief → ad-hoc chat → execute. After: brief → Delphi → execute,
with the Delphi being a defined, persisted, repeatable form.

---

## What the Delphi is NOT

- Not religious. The temple analogy was structural; the implementation
  is a script and a document template.
- Not a permission layer. Zeus isn't being asked to *approve* every
  Delphi; the Delphi is the form of how strategic matters are
  brought.
- Not a replacement for the journal. Journal is fact-capture; Delphi
  is decision-capture-with-context.
- Not invoked for routine work. The triggers are exhaustive; anything
  else proceeds without a Delphi.
- Not invoked retroactively except for backfill of the -
  ships, which produced *de facto* Delphis in chat history and
  deserve canonical records for the index.

---

## Lineage

The protocol is descended from three patterns that already work in
human organizations:

1. **Engineering RFC / ADR processes** — structured documents for
   decisions that need preparation, alternatives, and a persistent
   record.
2. **Surgical pre-operative briefing** — review the case, confirm
   the plan, sign off, then proceed. (Distinct from the surgical
   *time-out*, which happens during the action; the Delphi, like
   the pre-op briefing, happens *before* the work begins.)
3. **Diplomatic audience** — formal grant of time with a deciding
   authority, requiring preparation and recording the decision.

The temple analogy Zeus proposed pulls from #3 most directly: the
priest doesn't talk to the deity casually; there's a defined
protocol; the protocol exists because the consultation matters more
than ordinary conversation. The Delphi formalizes this for
agent-operator consultation in Olympus.

The name "Delphi" — Zeus's pick — preserves the structural insight
(a defined inner space with defined posture) without the religious
connotation of "temple."

---

## The override pattern (added )

The Delphi protocol places the agent (petitioner) in a structurally
weaker position than Zeus (principal). When the Architect recommends
Option A and Zeus chooses Option C, the override is **legitimate**
— Zeus has the constitutional authority to override; the Architect's
authority is recommendatory per `meta/architect.md`.

The protocol's commitment in an override:

1. **The Architect's brief stands as audit-of-record.** Both the
   §IV Recommendation and the §V Alternatives sections are preserved
   verbatim, even if Zeus declines them. The §VI Decision records
   the override; the §VII Outcome records what actually shipped.
2. **The §III–§V cautionary readings remain reference material** for
   future `oly-hephaestus.sh --reflect` runs. The Architect-was-right
   case can be scored post-hoc against subsequent events.
3. **The Architect does not become a yes-machine.** The Architect's
   role does not change — surface what's at stake, present the cleanest
   alternatives, recommend the structurally-defensible move. Zeus's
   decision shape (recommendation-aligned vs override) is the
   principal's prerogative.

**Canonical examples (recorded 2026-05-13):**

- `arc-e-acceleration-consciousness-cohort-e10.md` — Architect
  recommended phased Phase 1 + Phase 2 across 24h; Zeus chose
  Option D (ship all 10 ants today).
- `arc-f-accelerated-pacing-override.md` — Architect recommended
  Option A (decline today; revisit with operational data); Zeus
  chose Option B (ship F2 + structural F3 + F4 collapsed).
- `arc-g-roman-empire-opening.md` — Architect's Option A
  (decline; revisit) was the strongest recommendation against in
  any Delphi to date. Zeus chose Option C (ship Phase 1 in full).

The override pattern is **Pattern #14 Workaround Risk** realized
at the protocol level. The protocol's response is to make the
override structurally legible rather than to resist it.

---

## The empirical-iteration cycle (added )

The Delphi protocol's deepest realization is the empirical-iteration
cycle:

```
ship → real-world or simulated operation → finding → refinement-ship
```

The canonical instance, recorded 2026-05-13:

1. **Ship:**  relocated the Hydra mythology to HYDRA watchers
   (`hydra-mythology-relocation-to-watchers.md`).
2. **Operation:** 100-year simulation against the  baseline
   (`civitas-100-year-post-v8-72-report.md`).
3. **Finding:** the simulation surfaced that the F1 reward function
   denied value to steady-state-observer ants; no ant reached
   Eques in 100 years; F4 Cursus Honorum multipliers were
   behaviorally unreachable.
4. **Refinement-ship:**  ((legacy arc) · F5) added the
   `STEADY_STATE_ANTS` allowlist and revised `compute_rewards`
   (`arc-f-f5-steady-state-ants-reward-exemption.md`).

This is the cycle the Delphi protocol is *built* to enable. The
Architect surfaces findings via analysis and simulation; Zeus
ratifies (or doesn't); the refinement ship lands; the next cycle's
baseline updates accordingly. Future Delphis on related topics
gain prediction-vs-reality reference points without further
investigation.

**Recognition heuristic:** if a Delphi cites a prior Delphi's
simulation or operational data as evidence, that's the cycle
firing. Future agents should surface these citations explicitly.

---

## Delphi-protocol monitoring (Tribuni Plebis integration, )

The protocol is no longer self-policed by the agent alone. The
**`tribuni_plebis_watcher`** citizen ((legacy arc) / G1; ) auto-monitors
the protocol's runtime:

- Counts Delphis opened per date over a recent window
- Threshold: ≥3 in a single date emits a `tribunician_friction`
  pheromone at intensity 3.0 + 0.5 × count
- The pheromone surfaces in the bloom; the operator (Zeus) sees
  the friction signal without the agent's intermediation

This is the substrate **watching the protocol's own runtime**. A
constitutional fact about the protocol post-. The protocol's
discipline used to depend on the agent's restraint; it now also
depends on a citizen-layer observer firing when restraint slips.

The Tribuni Plebis is not authoritative — like a Roman Tribune, it
surfaces friction, it does not exercise veto. Zeus decides whether
to act on the friction signal. But the signal exists; the protocol
cannot quietly inflate without the Forum (the pheromone log)
recording the inflation.

---

## Parking vs deciding (added )

Not every strategic vision opens a Delphi. The protocol distinguishes:

| State | Where it lives | What it represents |
|---|---|---|
| **PARKED** | `proposals/<topic>.md` + `docs/BACKLOG.md` pointer | Pre-decision draft. No Delphi required. Future-arc candidate. Pre-conditions named explicitly. |
| **OPEN** | `delphi/YYYY-MM-DD-<topic>.md` (§VI empty) | Delphi session active; Zeus decision pending. |
| **DECIDED** | `delphi/YYYY-MM-DD-<topic>.md` (§VI filled, §VII empty) | Zeus decided; agent executing. |
| **CLOSED** | `delphi/YYYY-MM-DD-<topic>.md` (§VI + §VII filled) | Execution complete; outcome recorded. |
| **REJECTED** | `delphi/YYYY-MM-DD-<topic>.md` (§VI = "no") | Zeus declined; valuable artifact recording what was considered. |

**Parking** is the right move when:
- The proposal is vision-class and pre-conditions are not yet met
  (e.g., `swarm-as-analytical-layer-for-olympus-core.md` requires
  (legacy arc) / production deployment before becoming actionable)
- Zeus explicitly directs "park, not now"
- The Architect surfaces a future-arc candidate that doesn't
  warrant Delphi-class consultation today

**Deciding** (opening a Delphi) is the right move when:
- A MEDIUM/HIGH-risk move is on the table
- The decision is needed *now* (or within hours/days)
- The matter crosses one of the entry triggers above

Parking is **structurally cheaper than deciding**. The protocol
encourages parking for vision-class items; the Delphi is reserved
for moments the proceeding-or-not-proceeding question is live.

---

## Cross-references

- `scripts/oly-delphi.sh` — entry/close/list script.
- `delphi/README.md` — directory-level guide for new agents.
- `meta/delphi-index.md` — chronological index, generated by `close`.
- `meta/architect.md` — the brief-generator persona that feeds the Delphi.
- `meta/autonomy-architecture.md` — the risk classes that determine when entry triggers.
- `MISSION.md` — alignment reference for §IV Recommendation.
- **`DEVNOTES/audit-of-record.md`** () — defines the principle that
  the Delphi is the cognitive-layer instance of. Delphi sessions are
  the **only filesystem** instance of audit-of-record at .
  ( +  added two more filesystem instances —
  `monsters.argos/civitas/census-roll.json` (the Censor's roll) and
  `monsters.argos/civitas/treasury-roll.json` (the Quaestor's denarius
  ledger) — but the  reclassification moved both out of the AoR
  set: they are derived caches over `Pheromone`-table deposits +
  source-code ant presence, not source-of-truth. Historical  /
   ships remain intact in git history; reclassification is
  forward-only.) The other **nine** instances are schema tables —
  `TokenLifecycleEvent`, `VerificationEvent`, `EnrollmentStatusEvent`,
  `RecoveryRequest` (partial-enforcement), `TokenSignature`,
  `AnchorBatch`, `AgencyTrustAttestation`, `TokenStateEpoch`,
  `DuressEvent`. **Total: 10 instances (9 schema + 1 filesystem).**
  See `DEVNOTES/audit-of-record.md` for the canonical table and the
   reclassification rationale.
- **`scripts/oly-meta.sh check_delphi`** ( / CM check #6) — the
  enforcement layer. Scans `delphi/` for stale-OPEN sessions, lifecycle
  violations (CLOSED without §VII, REJECTED without §VI), and index
  drift between `delphi/` and `meta/delphi-index.md`.
- **`scripts/oly-hephaestus.sh --reflect[-n N]`** () — the learning
  loop. Reads the last N closed-or-rejected Delphis and produces a
  prediction-vs-reality summary as part of the Architect's reflection
  mode. Default N=10. This is what prevents the protocol from drifting
  into ceremony.
- **`olympus_web/test_structural_invariants.py::TestDelphiIntegrity`**
  () — test-suite counterpart to the CM check.
- **`meta/civitas.md`** () — the citizen-class structure that the
  Tribuni Plebis () belongs to; the Forum (pheromone log) the
  Tribuni reads from.
- **`meta/denarius.md`** () — the economic-dimension doc;
  Delphis authorize denarii-related G-guards (G15, G16, G19, G20, G26).
- **`monsters.argos/civitas/tribuni_plebis_watcher.py`** () — the
  citizen that observes this protocol's own runtime; emits
  `tribunician_friction` pheromones on Delphi-burst, command-doc
  drift, and CLAUDE.md complexity growth.
- **`monsters.hydra/heads/`** (–) — nine HYDRA watchers
  (the canonical Hydra-9 mortal heads post-); the
  `head_mission` and the new `head_demes` () both
  produce signals that can become Delphi-class concerns.
- **`proposals/swarm-as-analytical-layer-for-olympus-core.md`**
  ( parking) — example of a PARKED proposal that may become a
  Delphi-class arc when pre-conditions are met ((legacy arc) opening +
  ≥3mo operational data + F5 ≥30d operation).
