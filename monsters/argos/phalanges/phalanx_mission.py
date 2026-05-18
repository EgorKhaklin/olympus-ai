"""Legio Mission — Legatus of the mission/done-list domain.

Commands the ants that read MISSION.md and the Delphi corpus:
done-list arithmetic and Delphi §VII cross-ref coverage. Doctrine:
TESTUDO — both ants scan independent slices and aggregate cleanly.
"""

from monsters.argos.phalanges.base import Phalanx, Tactic, TacticConfig
from monsters.argos.eyes.ant_done_list_arithmetic import AntDoneListArithmetic
from monsters.argos.eyes.ant_delphi_outcome import AntDelphiOutcome


class LegioMission(Phalanx):
    NAME    = "phalanx_mission"
    DOMAIN  = "mission"
    LEGATUS = "Legatus Mission"
    ANTS    = [AntDoneListArithmetic, AntDelphiOutcome]
    TACTIC  = TacticConfig(tactic=Tactic.TESTUDO)
