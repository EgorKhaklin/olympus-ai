# notekeeper — an example deployment built on Olympus

A working demo. Capture notes, infer topics, surface forgotten material. Every load-bearing event is recorded; every claim about the domain is structurally enforced; every session runs the full cognitive loop.

This is what an Olympus deployment *looks like* — about 350 lines of domain code, leveraging ~5,000 lines of substrate.

---

## Run it in 90 seconds

From the Olympus repo root:

```bash
# 1. Install Olympus (editable mode exposes the `invoke` console script)
pip install -e .

# 2. Add the notekeeper package to your PYTHONPATH for this session
cd examples/notekeeper
export PYTHONPATH="$PWD:$PYTHONPATH"

# 3. Light the hearth for this deployment
invoke kindle "notekeeper" "capture personal notes; surface forgotten material; never auto-delete"

# 4. Register notekeeper's eyes + head + predictions with Olympus
python3 -m notekeeper setup

# 5. Capture a few notes
python3 -m notekeeper capture "Olympus is the substrate; notekeeper is a deployment built on it"
python3 -m notekeeper capture "Argos sees with many eyes; HYDRA watches with eight heads plus one immortal"
python3 -m notekeeper capture "Athena synthesizes briefs from HYDRA findings and Argos pheromones"

# 6. Run the cognitive loop with the notekeeper extensions active
python3 -m notekeeper session
```

The session output now shows:

- **HYDRA** reporting from 10 heads (9 substrate + 1 notekeeper `topic_drift`)
- **Argos** depositing pheromones from 12 eyes (9 substrate + 3 notekeeper)
- **Athena** synthesizing across all of them
- **Hephaestus** surfacing proposals if any of the notekeeper invariants are firing
- **Styx** chain still intact

---

## What this deployment adds to Olympus

| component | file | role |
|---|---|---|
| `infer_topics` + `capture` | `notekeeper/notes.py` | domain logic; pure functions + Mnemosyne writes |
| `EyeUntopicedNotes` | `notekeeper/eyes.py` | enforces C2 (every note has a topic) |
| `EyeStaleNotes` | `notekeeper/eyes.py` | enforces C3 (stale notes surface, never delete) |
| `EyeCaptureVelocity` | `notekeeper/eyes.py` | enforces C4 (capture-burst detection) |
| `HeadTopicDrift` | `notekeeper/heads.py` | enforces C5 (topic distribution drift) |
| `stale-under-50` prediction | `notekeeper/predictions.py` | Apollo forecast on staleness |
| `topic-diversity-growing` prediction | `notekeeper/predictions.py` | Apollo forecast on topic spread |

## What this deployment did NOT need to build

- An audit log (Mnemosyne)
- An immutable decision record (Styx)
- A read-only observation tier (HYDRA)
- A decentralized scan substrate (Argos)
- A predicate validation surface (Apollo)
- A strategic-decision protocol (Delphi)
- An architectural-review persona pair (Hephaestus / Momus)
- Quotas, lifecycle, snapshots, error boundaries, atomic appends, ...

That's the point of the substrate. The notekeeper is **~350 lines** of domain logic; everything else is structural primitive provided by Olympus.

## DOMAIN.md

The full constitutional spec for this deployment is in [`DOMAIN.md`](DOMAIN.md). It names:

- **Vocation** — capture personal notes, surface forgotten material, never auto-delete
- **Anti-mission** — what notekeeper refuses
- **C1–C5** — domain invariants with their enforcement points
- **Risk-class examples** — what LOW/MEDIUM/HIGH/COMPOSITE look like here
- **AP-NK1, AP-NK2, AP-NK3** — domain-specific Momus anti-patterns

## Tests

```bash
cd examples/notekeeper
python3 -m unittest discover -s tests
```

Should report `OK` across:

- `TestInferTopics` (pure-function tests)
- `TestCapture` (capture refuses empty, captures appear in recall)
- `TestEyes` (each eye scans cleanly)
- `TestHead` (`head_topic_drift` observes cleanly)
- `TestIntegration` (full session runs with notekeeper components attached)

## What this demonstrates

Olympus is not abstract. With ~350 lines of domain code you can:

- capture data structurally (Mnemosyne)
- surface observations from the data (Argos eyes)
- synthesize across observations (Athena)
- predict on the data (Apollo predictions with verify)
- detect drift in distribution (HYDRA head)
- enforce domain invariants (the C1–C5 surface)
- record every load-bearing event (the audit-of-record discipline)
- have an actual agent loop you can run end-to-end (`python3 -m notekeeper session`)

All of that "for free," provided by the substrate.

---

*Per Olympus v0.1 — this is what "building on Olympus" looks like.*
