"""Argos — Olympus's swarm intelligence substrate ((legacy arc) / ).

A stigmergic ant-colony pattern that grows underneath HYDRA. Eyes are
tiny deterministic Python modules under `monsters.argos/eyes/`. Each
ant scans one slice of the project and deposits **pheromones** onto
brain-map nodes via the `Pheromone` table (an additional audit-of-record
beyond the canonical 10; has archive+purge framework per ).

No ant imports any other ant. No host calls anything. Synthesis is
emergent: the pattern of pheromone density across brain-map nodes
over time IS the swarm's reasoning. Operators read the heatmap via
`scripts/oly-argos-bloom.sh`.

Authorized by `delphi/2026-05-13-arc-e-swarm-intelligence-opening.md`.

Constraints (per Zeus mission +  G1-G5 + (legacy arc) G6-G9):
  - Decentralization: no ant has global view; no central synthesizer.
  - Local rules: each ant reads only its slice + recent pheromones.
  - Emergence: synthesis is the aggregate pattern, computed at read time.
  - Robustness: removing N ants degrades coverage gracefully.
  - Adaptability: adding a new ant is a single new file under eyes/.
  - AoR: every deposit is an append-only Pheromone row.
  - Replay: every ant carries a seed; identical seeds produce
    identical pheromones (no randomness anywhere in ant code).
  - LLM-free: no ant imports anthropic; oly-argos-bloom is allowed
    one optional LLM call to translate the heatmap into prose,
    but the pheromone log is the truth.
"""

from monsters.argos.base import (
    Pheromone,
    Ant,
    EyeFinding,
    DECAY_HALF_LIFE_HOURS_DEFAULT,
)

__all__ = ["Pheromone", "Ant", "EyeFinding", "DECAY_HALF_LIFE_HOURS_DEFAULT"]
