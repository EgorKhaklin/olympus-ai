# monsters.argos/phalanxs/ — domain groupings of commander ants

11 phalanxs group the 33 commander ants by domain. Each phalanx is a
Python module that declares its `ALL_EYES` list and registers any
phalanx-level discipline.

For the individual ants see [`../eyes/`](../eyes/).

---

## What's here

13 files: `__init__.py` + `base.py` + 11 phalanx modules.

### Republican phalanxs (9)

| Phalanx | Domain | Ant count |
|---|---|---|
| [`phalanx_schema.py`](phalanx_schema.py) | Schema invariants | 2 |
| [`phalanx_cognitive.py`](phalanx_cognitive.py) | Cognitive layer hygiene | 3 |
| [`phalanx_security.py`](phalanx_security.py) | Security surface | 1 |
| [`phalanx_mission.py`](phalanx_mission.py) | MISSION discipline | 2 |
| [`phalanx_adversary.py`](phalanx_adversary.py) | Adversary walks | 1 |
| [`phalanx_performance.py`](phalanx_performance.py) | Atlas + scaling | 2 |
| [`phalanx_trajectory.py`](phalanx_trajectory.py) | Shipping cadence | 3 |
| [`phalanx_substrate.py`](phalanx_substrate.py) | Primitive dependencies | 4 |
| [`phalanx_docs.py`](phalanx_docs.py) | Documentation discipline | 6 |

### Imperial phalanxs (2 — added )

| Phalanx | Domain | Ant count |
|---|---|---|
| [`phalanx_praetorian.py`](phalanx_praetorian.py) | Palace guard observability | 3 |
| [`phalanx_engineer.py`](phalanx_engineer.py) | Process hygiene | 5 |

**Total: 33 commander ants in 11 phalanxs.**

---

## What a phalanx is

A phalanx is **a domain plus the ants that observe it**. Each phalanx
module exports:

- `LEGION_NAME` — short identifier (e.g., `"phalanx_schema"`)
- `LEGION_DESCRIPTION` — one-line purpose
- `ALL_EYES` — the list of Eye subclasses this phalanx contains
- `LEGION_DOCTRINE` — optional `PhalanxDoctrine` dataclass naming
  the tactic + tier structure (added )

The phalanx is the discovery unit: [`../colony.py`](../colony.py)
walks phalanxs to find ants, not the ants directory directly.

---

## What a phalanx is NOT

- Not a Hydra head (that mythology was relocated to HYDRA watchers
  in ; phalanxs are now purely organizational)
- Not constitutional (phalanxs can be added/removed; the swarm
  invariants are at C/G level)
- Not citizen-aware (citizens live in [`../civitas/`](../civitas/);
  phalanxs are commander-only)

`monsters.argos/phalanxs/` is **how 33 ants are organized into 11
coherent domains** — the equivalent of "teams" in a software org,
sized so each team has 1-6 specialists.

---

## Constitutional contract

- **G6 (no inter-tier imports)**: phalanxs do not import from
  HYDRA or olympus_web; they're pure swarm.
- **G16 (deterministic)**: phalanx `ALL_EYES` lists are static;
  the swarm composition is reproducible across runs.
- Adding/removing a phalanx requires updating the relevant ant
  inventory + structural-invariants count tests.

---

## Adding a new phalanx

1. Create `phalanx_<name>.py` matching the existing template
2. Define `LEGION_NAME`, `LEGION_DESCRIPTION`, `ALL_EYES`,
   optionally `LEGION_DOCTRINE`
3. Add phalanx module to `__init__.py`'s `ALL_PHALANGES`
4. Update CLAUDE.md state-map's swarm topology line
5. Run structural invariants — counts will need updating
6. Delphi if the phalanx crosses an arc boundary
   (e.g., the  Imperial-phalanxs ship had a Delphi)
