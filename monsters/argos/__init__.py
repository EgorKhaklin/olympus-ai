"""Argos Panoptes — the many-eyed giant.

Argos had a hundred eyes set throughout his body. Some slept while
others watched; sleep never closed all his eyes at once. Hera set
him to guard Io.

In Olympus, Argos is the decentralized swarm. Four sub-tiers:

  eyes/         observation specialists — one slice each
  satyrs/       lower-cadence concrete checks
  demes/        civic-class observers (the Greek polis tier)
  phalanges/    battle formations grouping eyes by concern

No Eye imports another Eye. The colony orchestrator dispatches
parallel scans and aggregates pheromones at read time. Synthesis is
emergent (substrate invariant S4).
"""

from monsters.argos.base import Eye, EyeFinding, Pheromone, KIND_INFO, KIND_DRIFT, KIND_ALERT
from monsters.argos.colony import colony, Colony

__all__ = [
    "Eye", "EyeFinding", "Pheromone",
    "KIND_INFO", "KIND_DRIFT", "KIND_ALERT",
    "colony", "Colony",
]
