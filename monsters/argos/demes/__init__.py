"""Argos Civitas — citizens of the swarm.

Parallel to `monsters.argos/phalanxs/` and `monsters.argos/eyes/`.
Where phalanxs command ants (military), citizens are civilians
who observe the swarm itself (the Forum, the census, cross-phalanx
patterns).

The four civic classes:

  - **Plebs** (Plebeians)     — cross-phalanx forum readers
  - **Equites** (Equestrians) — cross-phalanx correlators
  - **Augures** (Augurs)      — pattern interpreters (read auspices)
  - **Censores** (Censors)    — keepers of the census roll

Demes deposit to the same Pheromone table as ants. AoR is
preserved via `deposited_by = citizen.NAME`. Citizen class is in
`evidence.civitas_class`; observation type is in
`evidence.observation_type`.

Authorized by `delphi/2026-05-13-arc-e-civitas-civilian-classes.md`.
"""

from monsters.argos.demes.base import (
    Deme, DemeFinding,
    CIVITAS_PLEBS, CIVITAS_EQUITES, CIVITAS_AUGURES, CIVITAS_CENSORES,
    CIVITAS_QUAESTORES, CIVITAS_TRIBUNI_PLEBIS,
    VALID_CIVITAS_CLASSES,
    propose_new_ant,
)
from monsters.argos.demes.plebs_forum_watcher import PlebsForumWatcher
from monsters.argos.demes.eques_correlator import EquesCorrelator
from monsters.argos.demes.augur_bloom_reader import AugurBloomReader
from monsters.argos.demes.censor_roll_keeper import CensorRollKeeper
from monsters.argos.demes.quaestor_treasurer import QuaestorTreasurer
from monsters.argos.demes.tribuni_plebis_watcher import TribuniPlebisWatcher


ALL_DEMES = [
    PlebsForumWatcher,        # Plebeians
    EquesCorrelator,          # Equestrians
    AugurBloomReader,         # Augurs
    CensorRollKeeper,         # Censors
    QuaestorTreasurer,        # Quaestores — financial magistrates ((legacy arc) / F1 / )
    TribuniPlebisWatcher,     # Tribuni Plebis — usability advocates ((legacy arc) / G1 / )
]


__all__ = [
    "Citizen", "DemeFinding",
    "CIVITAS_PLEBS", "CIVITAS_EQUITES", "CIVITAS_AUGURES", "CIVITAS_CENSORES",
    "CIVITAS_QUAESTORES", "CIVITAS_TRIBUNI_PLEBIS",
    "VALID_CIVITAS_CLASSES",
    "propose_new_ant",
    "PlebsForumWatcher", "EquesCorrelator", "AugurBloomReader",
    "CensorRollKeeper", "QuaestorTreasurer", "TribuniPlebisWatcher",
    "ALL_DEMES",
]
