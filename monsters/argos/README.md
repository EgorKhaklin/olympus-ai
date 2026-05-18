# monsters.argos/ — (legacy arc) · the Argos swarm

This directory is **(legacy arc)** (Argos / genuine swarm intelligence),
opened 2026-05-13 by Delphi
`delphi/2026-05-13-arc-e-swarm-intelligence-opening.md`. Subsequent
arcs (F · the Denarius; G · Roman Empire) live partially under
`monsters.argos/civitas/` and `monsters.argos/phalanxs/`.

Where `monsters.hydra/` ((legacy arc)) is the **centralized synthesis** layer
(N watchers → 1 host → 1 voice for Zeus), Argos is the
**decentralized substrate**: tiny ants depositing pheromones onto
brain-map nodes via the append-only `Pheromone` table. Synthesis
emerges from pheromone density; no host calls; no LLM in the
substrate. Operators read the heatmap via
`scripts/oly-argos-bloom.sh`.

For the strategic record (E1–E10 done-list narratives, phalanx +
Civitas + Cursus Honorum mechanics, the Architect's 100-year
simulation findings), see **`meta/arc-e-argos.md`**. For the
deeper Olympus-as-Civitas concept mapping, see `meta/civitas.md`.
For the Denarius economy ((legacy arc)), see `meta/arc-f-denarius.md`
+ `meta/denarius.md`.

---

## Directory layout

```
monsters.argos/
├── base.py                     # Pheromone, Eye, EyeFinding base classes
├── colony.py                   # run_swarm(): Phase 1 phalanxs → Phase 2 citizens
├── chaos.py                    # F2 chaos-test harness (deterministic failure injection)
├── eyes/                       # 33 ants in 11 phalanxs (post-)
│   ├── __init__.py             # ALL_EYES registry
│   ├── ant_*.py                # one file per ant; each <120 LOC
│   └── ...
├── phalanxs/                    # 11 phalanxs (9 Republican + 2 Imperial)
│   ├── base.py                 # Phalanx + TacticConfig + 5 tactics
│   ├── phalanx_*.py              # one file per phalanx; declares ANTS + TACTIC
│   └── ...
└── civitas/                    # 6 citizens + Denarius treasury
    ├── base.py                 # Citizen + DemeFinding + propose_new_ant
    ├── plebs_forum_watcher.py
    ├── eques_correlator.py
    ├── augur_bloom_reader.py
    ├── censor_roll_keeper.py
    ├── quaestor_treasurer.py   # 5th citizen ((legacy arc) · F1)
    ├── tribuni_plebis_watcher.py  # 6th citizen ((legacy arc) · G1)
    ├── treasury.py             # Denarius reward function (compute_rewards)
    ├── census-roll.json        # Filesystem-AoR (G14)
    └── treasury-roll.json      # Filesystem-AoR (G15)
```

---

## Three layers (read top-down)

### 1. Substrate — `Pheromone` table + `base.py`

The Pheromone table (in `olympus_sql/01_schema.sql`) is the 11th
audit-of-record instance. Append-only via
`trg_pheromone_append_only`. Every ant's deposit becomes one row;
the row carries `(deposited_by, node_id, intensity, kind,
half_life_hours, evidence)`. Decay is deterministic per `G7` (pure
function in `base.py::effective_intensity`).

Ants subclass `Eye`, return a list of `EyeFinding` from `scan()`,
and never deposit directly — the colony runner serializes findings
to Pheromone rows.

### 2. Organization — `phalanxs/`

Eyes are organized into Phalanges for tactical dispatch. Each Phalanx
has:
- `NAME` — module name (e.g., `phalanx_cognitive`)
- `DOMAIN` — high-level area
- `LEGATUS` — display name
- `ANTS` — list of Eye subclasses
- `TACTIC` — `TacticConfig` declaring deployment doctrine

Five tactics (Roman military doctrine):
- **TESTUDO** — all ants scan; aggregate
- **TRIPLEX_ACIES** — tiered escalation (hastati → principes → triarii)
- **CUNEUS** — lead ant fires first; followers only if lead detects
- **VEXILLATIO** — operator-directed focused mission
- **AUXILIA** — borrow ants from allied phalanxs

11 phalanxs today: 9 **Republican** (the original Argos cohort —
schema, cognitive, security, mission, adversary, performance,
trajectory, substrate, docs) + 2 **Imperial** (added (legacy arc) — Praetorian,
Engineer). The Hydra-9 mythology was relocated from Argos phalanxs
to HYDRA watchers in  — see
`delphi/2026-05-13-hydra-mythology-relocation-to-watchers.md`.

### 3. Civic layer — `civitas/`

Six citizen classes, parallel to phalanxs:
- **Plebs** (Plebeians) — cross-phalanx forum readers
- **Equites** (Equestrians) — cross-phalanx correlators
- **Augures** (Augurs) — pattern interpreters
- **Censores** (Censors) — keepers of the census-roll (G14 FS-AoR)
- **Quaestores** (Quaestors) — financial magistrates; Denarius reward
  function via `treasury.py` (G15 FS-AoR + G16 determinism)
- **Tribuni Plebis** — usability advocates; observe Delphi-protocol
  entropy ((legacy arc) addition)

Demes observe the swarm itself (cross-phalanx patterns + civic
state); they do NOT subclass Ant (G12); they cannot literally spawn
ants (G13 — proposal-driven autogenesis only).

---

## G-guards (the contract)

| Guard | Rule |
|---|---|
| G6 | No ant imports another ant (decentralization) |
| G7 | Pheromone decay is deterministic (replay) |
| G8 | No ant imports an LLM client (substrate determinism) |
| G9 | Pheromone table is append-only (AoR) |
| G10 | Every ant belongs to exactly one Phalanx (partition) |
| G11 | Eyes don't import from `monsters.argos.phalanges` (one-way knowledge) |
| G12 | Demes don't subclass Ant (parallel hierarchy) |
| G13 | No literal autogenesis (proposal-pheromone-driven only) |
| G14 | `census-roll.json` is filesystem-AoR (append-only) |
| G15 | `treasury-roll.json` is filesystem-AoR (append-only) |
| G16 | Reward function is deterministic (replay-safe) |
| G17 | Acceleration ants are read-only with respect to source files |
| G18 | Consciousness ants observe SWARM SELF-STATE (registries, meta docs, FS-AoR rolls) |
| G19 | Cursus Honorum multipliers are monotonic non-decreasing in balance |
| G20 | Delphi-chair eligibility derives ONLY from denarii balance (C10 pomerium) |
| G22 | Tribuni Plebis observes usability surface only (no identity-layer) |
| G23 | Via Appia is a property of EyeFinding, not a parallel routing layer |
| G24 | New phalanxs require Delphi authorization |
| G25 | Cohort growth >50% per ship requires explicit Delphi acknowledgment |
| G26 | Additions to `STEADY_STATE_ANTS` allowlist require Delphi authorization |

(G21 belongs to `monsters.hydra/` — Praetorian observability constraint
on the Praetorian ants under `monsters.argos/eyes/`.)

---

## Running the swarm

```bash
# Single colony pass (--dry: no DB writes)
python3 -m monsters.argos.colony --dry

# Full two-phase swarm (phalanxs then citizens)
python3 -m monsters.argos.colony --swarm --dry

# Read the bloom (operator-facing heatmap)
./scripts/oly-argos-bloom.sh

# Run F2 chaos test
python3 -c "
from monsters.argos.chaos import run_chaos_pass, FailureMode
from monsters.argos.eyes import AntTodoDebt
import pathlib
result = run_chaos_pass({AntTodoDebt: FailureMode.RAISE_EXCEPTION},
                        root=pathlib.Path('.').resolve())
print(result.detected_failures)
"
```

---

## Where to learn more

| Question | Read |
|---|---|
| Strategic record (E1-E10 narratives) | `meta/arc-e-argos.md` |
| Civitas concept (Senatus, Forum, Pomerium, Mos Maiorum) | `meta/civitas.md` |
| Denarius economy + Cursus Honorum | `meta/arc-f-denarius.md`, `meta/denarius.md` |
| Roman Empire expansion (Imperial phalanxs, Tribuni Plebis) | `meta/arc-g-empire.md` |
| HYDRA's relationship to Argos | `monsters.hydra/README.md` |
| Pheromone schema | `olympus_sql/01_schema.sql` (search `Pheromone`) |
| Ant contract | `monsters.argos/base.py::Ant` |
| Citizen contract | `monsters.argos/civitas/base.py::Citizen` |
| Tactical doctrine details | `monsters.argos/phalanxs/base.py` |
| Authorizing Delphis | `delphi/2026-05-13-arc-e-*` + `arc-f-*` + `arc-g-*` |
