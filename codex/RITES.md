<div align="center">

# ⚡ RITES ⚡

**the ceremonies an agent performs to operate Olympus**

</div>

---

This file is the agent runbook. Every session, every ship, every Delphi consultation follows a rite. The rites are short. Read them once at session start; they are how you act.

---

## Rite 1 — Session invocation

At the start of every session, an agent performs the invocation:

```python
from titans.rhea import rhea
from olympians.hestia import hestia
from heroes.odysseus import odysseus

# Ensure the substrate is whole
rhea.bring_forth()

# Confirm the hearth is lit
if not hestia.is_lit():
    raise RuntimeError("Hearth not lit. Kindle before first session.")

# Take bearing — where was the agent when last seen?
bearing = odysseus.take_bearing()
print(f"Resuming. Last memory: {bearing.last_summary}")
```

That is the rite. Three deities, three lines.

---

## Rite 2 — Issuing a directive (Zeus)

When the operator wants the agent to do something high-risk, the directive is sworn:

```python
from olympians.zeus import zeus

directive = zeus.authorize(
    quote="ship the new Apollo predicate",
    risk_class="HIGH",
    scope="olympians/apollo/oracle.py",
)
```

The oath is recorded on Styx; it cannot be revised. The agent now has authority to perform HIGH-risk action within the named scope.

---

## Rite 3 — Surfacing drift (Hephaestus)

When the agent (acting as Hephaestus) observes structural drift, a proposal is recorded:

```python
from olympians.hephaestus import hephaestus

proposal = hephaestus.propose(
    drift_observed="Argos has 33 Eyes; only 28 are registered in PANTHEON.md",
    proposed_fix="Audit the eyes/; add missing 5 to PANTHEON.md",
    risk_class="LOW",
    rationale="docs drift; not constitutional",
)
```

For MEDIUM or HIGH, Momus contests before the proposal can ship:

```python
from heroes.momus import momus

contests = momus.contest(
    proposal_summary=proposal.proposed_fix,
    ap_ids=["AP3"],  # instance-level rule for class-level drift
)
for ap in contests:
    print(f"{ap.id}: {ap.refusal}")
```

---

## Rite 4 — Consulting the oracle (Delphi)

For MEDIUM and HIGH-risk decisions, a Delphi is opened:

```bash
mkdir -p oracles/delphi
cat > oracles/delphi/$(date +%Y-%m-%d)-delphi-{topic}.md <<EOF
# Delphi — {topic}

## Question
What does the operator need decided?

## Hephaestus position
The Architect's proposal, with rationale.

## Momus contest
Which AP1–AP8 anti-patterns apply? Which refusals stand?

## Zeus decision
Position A / B / C — and why.

## Decision sworn at
(commit reference)
EOF
```

The closed Delphi is referenced in the commit message and indexed at `oracles/delphi-index.md`.

---

## Rite 5 — Daily journal (Clio)

At every load-bearing moment, Clio writes:

```python
from muses.clio import clio

clio.inscribe("decision", "kept option A; option B needed schema change")
clio.inscribe("learning", "Hera bindings are append-only — cannot edit a row")
clio.inscribe("observation", "Argos colony deposited 47 pheromones this cycle")
```

Today's file is `chronicle/journal/YYYY-MM-DD.md`. Append; never edit.

---

## Rite 6 — The ship sequence

To ship a change:

1. **Pick risk class** — LOW (autonomous), MEDIUM (proposal), HIGH (Delphi)
2. **For HIGH**: open the Delphi first
3. **Code change** — edit source under the appropriate tier
4. **Tests** — add to `tests/` under a new class
5. **Reference paths** — use `from primordials.gaia import root; root.child('relative/path')` (never absolute)
6. **CHRONICLE entry** — prepend an entry at the top of `CHRONICLE.md`
7. **Journal entry** — append a `decision` line via Clio
8. **Update PANTHEON.md** if a new named module was added
9. **Pre-ship gate** — run `python3 -m tests.test_pantheon_coherence` (must report `OK`)
10. **Commit** — referencing the Delphi if applicable

---

## Rite 7 — When something breaks

A Fury fires:

```
furies.alecto raised invariant.violated:
  S4: 'monsters/argos/eyes/eye_self_model_accuracy.py' imports another Eye
```

Hecate at the crossroads picks the path:

```python
from underworld.hecate import at_crossroads, Crossroads

at_crossroads(
    attempt=lambda: _try_isolated_fix(),
    on=Crossroads(
        retry=None,                              # no retry; the violation is structural
        abandon=lambda: log_refusal(),           # graceful refusal
        descend=lambda x: medusa.gaze("incident", x),  # snapshot the state
        escalate=lambda exc: notify_zeus(exc),    # surface to operator
    ),
)
```

The incident lands in Hades; the operator is notified; the substrate remains in a known state.

---

## Rite 8 — Closing the session

```python
from muses.thalia_muse import thalia_muse
from muses.erato import erato

print(erato.farewell())
print(thalia_muse.blessing())
```

The hearth stays lit. Hestia keeps watch.

---

## Defaults under ambiguity

When the operator's request is ambiguous, the agent's default is **decline-and-surface**:

- New mission scope → DO NOT silently expand. Explain why it crosses the constitutional bound. Name the trigger needed. Wait for Zeus.
- LOW-risk maintenance (drift, doc gaps, soft signals) → ship under standard autonomous rules.
- Hephaestus surfaces drift; he does not surface opportunities.
- The contract is operator-revocable: Zeus may name a trigger or open a new arc at any time. The constraint is on the agent, not on Zeus.

When Zeus explicitly invokes "boil the ocean" or similar heavy-production directive, the steady-state contract is overridden for that session. Ships during such directives are HIGH-composite and the authorization quote is recorded in the Delphi.

---

## Style

Read `codex/style.md`. The constitutional tone is:

- Declarative; no filler
- No em-dashes in human-readable prose
- "Holy shit, that's done" — no workarounds, no tabling
- When drifting toward cosmic-significance framing, name the pattern (Momus AP1) and back off

---

<div align="center">

*"The rite is not a performance. The rite is the operation."*

</div>
