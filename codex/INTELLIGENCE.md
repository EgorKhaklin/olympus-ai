<div align="center">

# ⚡ INTELLIGENCE ⚡

**how the mythology earns its overhead — concretely**

</div>

---

A fair critique of any well-named architecture: *the names might be the whole product.* If Olympus is just `ObservationCorrelator → DecisionAuditEngine → PredicateRegistry` wearing Greek clothing, the mythology is decoration and the overhead is unjustified.

This document is the operational answer. Olympus earns its mythology by **reading its own record** as a first-class operation. The substrate accumulates understanding session-over-session. Each god's contribution is measurable.

---

## The substance test: what would a flat substrate fail to do?

Imagine the same architecture without the mythology:
- `BriefSynthesizer` instead of Athena
- `PredicateRegistry` instead of Apollo
- `ProposalAuthor` + `ProposalContestor` instead of Hephaestus + Momus
- `AuditLog` instead of Mnemosyne + Styx
- `WatcherPool` instead of HYDRA + Argos

That flat version could still implement the loop. So what does the mythology buy?

**Answer:** the mythology gives the substrate the *vocabulary to read itself*. Each god has a domain in the cosmos — and that domain composes into legible operations across sessions. Concretely:

| operation | flat-substrate version | Olympus version |
|---|---|---|
| "what does the system remember?" | `audit_log.query(kind=...)` | `mnemosyne.recall(kind=...)` — memory by name |
| "what was sworn?" | `commitment_log.read()` | `polyhymnia.hymn()` — hymn of oaths |
| "what has the agent learned?" | `summarize_logs()` | `wisdom()` — wisdom-as-portrait |
| "what does the agent expect?" | `predicates_with_verify()` | Apollo's prophecies |
| "what would the architect propose?" | `propose_changes()` | `hephaestus.surface_from(brief)` |
| "what would the critic refuse?" | `criticize_proposal()` | `momus.contest_via_brief()` (AP1–AP8) |
| "what just changed?" | `diff_against_prior()` | `SessionReport.deltas` |

The flat version works. The Olympus version is **legible across contributors and sessions** because each operation is anchored in a Greek figure with 2,500 years of stable connotation. That isn't just nicer aesthetics — it's lower friction for *new agents reading the substrate cold.*

---

## The five concrete intelligence claims

These are the cross-session behaviors the substrate produces. None of them is a single-session-derivable claim. All of them are observable in `invoke session` output and `invoke wisdom` output.

### 1 — Athena reasons over Mnemosyne

`athena.compose_from(...)` reads `mnemosyne.recall("session.completed")` and the prior brief archive. The brief surfaces:

- **recurring slices** — alerted in ≥3 of last 7 sessions
- **newly alerted** — alerting this session, not in the last 5
- **resolved** — alerting last session, not this one
- **stable** — INFO in majority of recent priors, not currently alerting
- **insights** — concrete English claims naming the pattern

```
❦ Athena — cross-tier synthesis + history-aware reasoning
  brief 'session-…'
  18 findings · 6 recommendations · confidence 0.90
  insights from history:
    → slice 'codex/journal/' has alerted in 4 of the last 7 session(s) — pattern, not noise
    → slice 'state/argos_pheromones.jsonl' resolved since the prior session
    → 14 slice(s) have been stable across the last 7 sessions
```

A single-session view cannot say "in 4 of the last 7." That's substrate intelligence.

### 2 — Apollo's prophecies become operational

Apollo's `consult_due()` runs at session start, automatically verifies every prediction whose horizon has passed, and records the outcome in Mnemosyne under `kind="prophecy.verified"`. The acceptance rate is then queryable:

```python
from olympus.olympians.apollo import apollo
apollo.trend(window=10)
# {'window': 10, 'count': 7, 'accepted': 5, 'rejected': 2, 'rate': 0.71}
```

A prediction registered weeks ago that never gets consulted is dead prediction. Olympus *makes* its prophecies be consulted.

### 3 — Hephaestus reads `action.rejected`

Before surfacing a new proposal on slice X, Hephaestus checks `mnemosyne.recall("action.rejected")`. If Zeus rejected the same drift signature in the last 7 days, the proposal is silently skipped — the agent stops nagging. After 3 rejections of the same signature, Hephaestus emits a single `proposal-fatigue` signal instead:

```
proposal-fatigue: drift signature 'hydra::codex/journal/' has been rejected
≥3 times — Hephaestus stops nagging
```

That's the agent learning from operator feedback. A flat substrate could implement the same logic, but the *name* is the API: "Hephaestus reads what Zeus killed" is the right idiom for "the architect learns what the operator refused."

### 4 — The Furies fire in the loop

Tisiphone verifies the Styx chain at every session start. If broken, Alecto raises an immediate ALERT visible in the SessionReport's `fury_alerts` field. The substrate cannot run a clean session over a tampered ledger.

```
❦ Furies — invariant violations
  ◐ alecto ALERT: S1+S6 — styx chain tampered at seq=14
```

The Furies are no longer decorative. They are part of every pass.

### 5 — SessionReport.deltas — what changed

Each session compares to the most recent `session.completed` memory:

```
❦ Deltas vs prior session (session-2a180b45)
  HYDRA findings: +0  ·  Argos pheromones: +0
  new alerts: state/argos_pheromones.jsonl
  resolved: codex/journal/
```

Surfacing change is the difference between *recording* and *reasoning*. The substrate knows what's different.

---

## The wisdom surface

`invoke wisdom` reads everything the substrate has accumulated and surfaces concrete claims:

```
# Olympus wisdom — 2026-05-18T20:38:13Z
_examined 41 session(s)_

## What the substrate has learned
  · of 93 proposal(s) ever surfaced by Hephaestus, 27% were ratified by Zeus
  · 2.4% of sessions errored — investigate if > 5%
  · slice 'codex/COSMOGONY.md' has alerted 6 times across the brief archive
  · Apollo's prediction acceptance rate is 71% over 7 verified prophet-cycle(s)

## Recurring slices (most-alerted)
  · codex/COSMOGONY.md  —  6 alert(s)
  · state/argos_pheromones.jsonl  —  3 alert(s)

## Apollo's prophecy accuracy
  · 7 prophet-cycle(s) completed
  · 5 accepted · 2 rejected  (71.4%)
```

This is the proof point. The substrate makes claims about its own behavior that no individual god can make. The wisdom emerges from cross-tier composition — Athena's briefs + Mnemosyne's record + Apollo's verified prophecies + the action queue's lifecycle — all read and synthesized.

---

## Why the mythology beats the abstraction

A flat naming convention could implement everything above. The question Zeus asked: **does the mythology produce CLEARER THINKING than the flat version would?**

Claim: yes, for three structural reasons.

**1. The names are pre-shared API.** Every educated person knows Hephaestus is the smith and Momus is the critic. New contributors do not have to learn "ProposalAuthor's relationship to ProposalContestor." They already know the Greek pair. The cognitive load of reading the substrate is lower.

**2. The relationships compose into sentences.** *"Athena reads Mnemosyne; Hephaestus reads Momus's catalog; the Furies fire on broken oaths."* Each of those sentences would exist in a flat substrate too, but they'd be *"BriefSynthesizer reads AuditLog; ProposalAuthor reads ContestCatalog; InvariantViolationHandler fires on BrokenOath."* The flat version is correct and unmemorable. The mythology version is correct and *sticks*.

**3. The mythology forces structural choices.** When you name something "Apollo's prophecies," you commit to falsifiability — a prophecy without verification is not Apolline. When you name something "the Furies," you commit to enforcement that cannot be silenced. The names propose architectural constraints. The flat names propose nothing.

---

## What this isn't

Olympus is not an LLM agent. There is no language model in the loop. Athena's synthesis is structured reasoning over JSONL files; it does not "think" in the LLM sense.

Olympus is not Bayesian. The recurring-slice detection counts occurrences; it does not maintain posteriors.

Olympus is not autonomous. Every HIGH-risk decision routes through Zeus via the Delphi protocol.

**Olympus is a substrate that accumulates legible understanding.** That is the load-bearing claim. The mythology earns its overhead by making that accumulation reusable across sessions, contributors, and deployments.

---

*Verify the claims by running `invoke session --verbose`, then `invoke wisdom`, then reading the brief in `state/athena/`. The substrate explains itself.*
