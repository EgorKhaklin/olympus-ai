"""Argos phalanxs — Republican + Imperial cohorts commanding the swarm.

**Phalanges are NOT Hydra heads** (as of ). They are
organizational units of the Argos swarm, named in the Roman
military tradition. The Hydra-9 mythology was relocated from
phalanxs to HYDRA watchers in  — see
`delphi/2026-05-13-hydra-mythology-relocation-to-watchers.md`.

**Republican phalanxs (9):** the original Argos phalanxs
established during (legacy arc) (–): schema, cognitive,
security, mission, adversary, performance, trajectory, substrate,
docs. The count of 9 was historically anchored to the Hydra-9
mythology but is now retained as ship-time provenance — the 
cohort that emerged from the Hydra-nine-heads-completion ship.

**Imperial phalanxs (added +):** phalanxs created after (legacy arc)
via `delphi/2026-05-13-arc-g-roman-empire-opening.md`. Phase 1
adds two:

  - **Legio Praetorian** (constitutional guard, TESTUDO)
  - **Legio Engineer** (development acceleration, CUNEUS)

Future phalanxs can only be added via a Delphi that explicitly
authorizes them (G24).

The Pheromone log records `deposited_by = ant.NAME` for
audit-of-record preservation; the phalanx identity travels in the
evidence JSONB (`evidence["phalanx"]`).

**On CM and the immortal head.** CM remains constitutional. Prior
to  it was framed as "the immortal 10th head" of the
Hydra-on-phalanxs mythology. With the mythology relocated to
watchers, CM is now the immortal head of the Hydra-on-watchers
mythology — the watcher that cannot be cut without losing the
substrate's ability to verify its own claims. CM lives in
`MISSION.md`'s cognitive-substrate section; it does not appear
as a watcher in `monsters.hydra/`. Substitutability per 
applies to every other element of the substrate but not to CM.

Authorized by:
  - : `delphi/2026-05-13-arc-e-swarm-intelligence-opening.md`
  - : `delphi/2026-05-13-arc-e-phalanx-structure-with-tactics.md`
  - : `delphi/2026-05-13-arc-e-hydra-nine-heads-completion.md`
    (the phalanx-Hydra mythology that was later relocated)
  - : `delphi/2026-05-13-arc-g-roman-empire-opening.md` (Hydra-9 amended)
  - : `delphi/2026-05-13-hydra-mythology-relocation-to-watchers.md`
    (mythology moved off phalanxs onto HYDRA watchers; phalanxs are
    organizationally Roman but mythologically just phalanxs)
"""

from monsters.argos.phalanges.base import Phalanx, Tactic, TacticConfig
# Republican phalanxs ((legacy arc) / -)
from monsters.argos.phalanges.phalanx_schema import LegioSchema
from monsters.argos.phalanges.phalanx_cognitive import LegioCognitive
from monsters.argos.phalanges.phalanx_security import LegioSecurity
from monsters.argos.phalanges.phalanx_mission import LegioMission
from monsters.argos.phalanges.phalanx_adversary import LegioAdversary
from monsters.argos.phalanges.phalanx_performance import LegioPerformance
from monsters.argos.phalanges.phalanx_trajectory import LegioTrajectory
from monsters.argos.phalanges.phalanx_substrate import LegioSubstrate
from monsters.argos.phalanges.phalanx_docs import LegioDocs
# Imperial phalanxs ((legacy arc) / +)
from monsters.argos.phalanges.phalanx_praetorian import LegioPraetorian
from monsters.argos.phalanges.phalanx_engineer import LegioEngineer


# Republican phalanxs (Hydra's nine mortal heads, per  commitment)
REPUBLICAN_LEGIONS = [
    LegioSchema,         # head 1
    LegioCognitive,      # head 2
    LegioSecurity,       # head 3
    LegioMission,        # head 4
    LegioAdversary,      # head 5
    LegioPerformance,    # head 6
    LegioTrajectory,     # head 7
    LegioSubstrate,      # head 8  ()
    LegioDocs,           # head 9  ()
]

# Imperial phalanxs (added after (legacy arc) amended Hydra-9 via  Delphi)
IMPERIAL_LEGIONS = [
    LegioPraetorian,     #  — constitutional guard
    LegioEngineer,       #  — development acceleration
]

# Full registry — Republican first (mythologically primary),
# Imperial after. CM is the immortal 10th head; lives in
# MISSION.md as a principle, not in this registry.
ALL_PHALANGES = REPUBLICAN_LEGIONS + IMPERIAL_LEGIONS


#  — the twelfth phalanx, held in reserve.
#
# The current phalanx count is 11 (9 Republican + 2 Imperial). Eleven
# is structurally unstable in tiling-geometry (cannot be evenly divided;
# Republican-Imperial split 9+2 is asymmetric). Twelve is the natural
# completion (matches astrological houses, dodecagon, the Twelve
# Tables of Roman law).
#
# Rather than create a twelfth phalanx preemptively (which would be
# a solution looking for a problem),  documents the twelfth
# slot as DELIBERATELY RESERVED. When a future operational need
# surfaces that genuinely demands a new phalanx, this slot exists to
# receive it. Until then, the gap is a feature: the system holds
# space for what it does not yet know it needs.
#
# Naming convention: when manifested, the twelfth phalanx takes its
# name from the operational need that justifies it (e.g., LegioFiscalia
# for treasury-specific governance, LegioPraetoriaSecunda for a
# second constitutional guard, etc.). The name is NOT pre-assigned;
# pre-naming would constrain the manifestation.
#
# Structural invariant (TestWave11V911) pins:
#   - len(ALL_PHALANGES) == 11 (current; the eleventh + twelfth-reserved)
#   - RESERVED_TWELFTH_LEGION_SLOT is named (this constant)
#   - meta/twelfth-phalanx.md exists and documents the reserve
RESERVED_TWELFTH_LEGION_SLOT: dict = {
    "manifested": False,
    "reserved_at": "",
    "rationale": (
        "Twelve is the natural completion of the phalanx count "
        "(matches dodecagon, twelve houses, twelve tables). The "
        "twelfth slot is held in deliberate reserve until an "
        "operational need surfaces that justifies a new phalanx. "
        "Pre-naming would constrain the manifestation; the slot "
        "exists as a held silence."
    ),
    "manifestation_protocol": (
        "When the twelfth phalanx's need surfaces (operator-identified "
        "or surfaced by HYDRA), open a Delphi proposing it. The "
        "Delphi's §I documents the operational need; §II proposes the "
        "phalanx's name + scope; §V (decision) authorizes addition to "
        "ALL_PHALANGES. RESERVED_TWELFTH_LEGION_SLOT[\"manifested\"] flips "
        "to True; the structural invariant updates."
    ),
}


__all__ = [
    "Phalanx", "Tactic", "TacticConfig",
    # Republican
    "LegioSchema", "LegioCognitive", "LegioSecurity", "LegioMission",
    "LegioAdversary", "LegioPerformance", "LegioTrajectory",
    "LegioSubstrate", "LegioDocs",
    # Imperial
    "LegioPraetorian", "LegioEngineer",
    # Groupings
    "REPUBLICAN_LEGIONS", "IMPERIAL_LEGIONS", "ALL_PHALANGES",
    #  — held silence
    "RESERVED_TWELFTH_LEGION_SLOT",
]
