"""Legio Praetorian — Legatus Custos Constitutionis.

The first **Imperial phalanx** (added  / (legacy arc)). Where the
nine Republican phalanxs cover project surface area (schema,
cognitive, security, mission, adversary, performance, trajectory,
substrate, docs), the Praetorian guards the **constitution
itself**: MISSION.md, the four cognitive-substrate principles,
the C1-C10 lattice.

Note:  framed this addition as bending the " Hydra-9
commitment." In  the Hydra mythology was relocated from
phalanxs to HYDRA watchers, retroactively unloading that
framing — adding an Imperial phalanx no longer breaks any Hydra
count, only the historical Republican vs Imperial provenance
distinction.

The Roman Praetorian Guard's history was mixed (the Architect
recorded this in §IV of the (legacy arc) Delphi). In the cognitive
substrate, this risk is structurally mitigated by G24: new
phalanxs require a Delphi, and the Delphi that creates a phalanx
specifies its tactic. The Praetorian here observes; it does
not adjudicate or auction the constitution to the highest bidder.

Doctrine: **TESTUDO** — both ants always scan; constitutional
drift is the kind of thing that wants maximum-defense coverage,
not escalation tiers. If MISSION.md changes silently, BOTH ants
should fire on the next pass.

The cohort:
  - `ant_mission_drift` — anchor presence in MISSION.md (the
    document)
  - `ant_principle_invariant` — implementation presence of the
    four principles (the lived structure)

Both ants are ALERT-capable. The Praetorian's gaze produces
the project's third and fourth ALERT-capable ants (after
`ant_self_model_accuracy` and `ant_phalanx_doctrine_health` from
).

Authorized by `delphi/2026-05-13-arc-g-roman-empire-opening.md`.
"""

from monsters.argos.phalanges.base import Phalanx, Tactic, TacticConfig
from monsters.argos.eyes.ant_mission_drift import AntMissionDrift
from monsters.argos.eyes.ant_principle_invariant import AntPrincipleInvariant


class LegioPraetorian(Phalanx):
    NAME    = "phalanx_praetorian"
    DOMAIN  = "constitutional"
    LEGATUS = "Legatus Custos Constitutionis"
    ANTS    = [AntMissionDrift, AntPrincipleInvariant]
    TACTIC  = TacticConfig(tactic=Tactic.TESTUDO)
