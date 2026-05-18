"""Legio Schema — Legatus of the schema domain.

Commands the ants that guard the schema layer: AoR table immutability
and the no-FK-CASCADE rule. Doctrine: TESTUDO (every shield raised).
Schema is the load-bearing surface where false positives are
cheaper than missed signals, so the cohort always scans together.
"""

from monsters.argos.phalanges.base import Phalanx, Tactic, TacticConfig
from monsters.argos.eyes.ant_aor_immutability import AntAorImmutability
from monsters.argos.eyes.ant_fk_cascade_guard import AntFkCascadeGuard


class LegioSchema(Phalanx):
    NAME    = "phalanx_schema"
    DOMAIN  = "schema"
    LEGATUS = "Legatus Schema"
    ANTS    = [AntAorImmutability, AntFkCascadeGuard]
    TACTIC  = TacticConfig(tactic=Tactic.TESTUDO)
