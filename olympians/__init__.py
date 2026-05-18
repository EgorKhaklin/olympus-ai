"""The Twelve Olympians + Hades and Hestia.

Mount Olympus is home to the twelve principal gods of Greek religion.
Each Olympian holds dominion over a domain; together they govern the
cosmos. In Olympus the project, each Olympian module owns one
cognitive-substrate concern.

  Zeus        operator interface — the authority above the pantheon
  Hera        bindings — what is married to what
  Poseidon    data flow — streams, queues, the moving water
  Demeter     ingestion — harvesting raw observations
  Athena      strategic synthesis — wisdom, the brief
  Apollo      foresight — falsifiable predicates
  Artemis     precision metrics — the hunter's mark
  Ares        adversarial testing — war, chaos
  Aphrodite   aesthetics — beauty in output
  Hephaestus  the Architect — forge, drift surfacing
  Hermes      communication — messengers, CLIs, APIs
  Dionysus    transformation — refactoring, state change

  Hades       (not strictly Olympian, lives in underworld/)
  Hestia      the hearth, sacred boundary (lives below)
"""

from olympians import (
    zeus, hera, poseidon, demeter, athena, apollo,
    artemis, ares, aphrodite, hephaestus, hermes, dionysus, hestia,
)

__all__ = [
    "zeus", "hera", "poseidon", "demeter", "athena", "apollo",
    "artemis", "ares", "aphrodite", "hephaestus", "hermes", "dionysus", "hestia",
]
