"""Legio Performance — Legatus of the runtime/route surface domain.

Commands the ants that verify routes exist, their docs match, and
the modules backing them have test coverage. Doctrine: TESTUDO —
all ants run independent slices and aggregate.

Cohort grew 2 → 3 in  (Phase E10): added `ant_test_gap`, the
acceleration ant that surfaces modules under `olympus_web/` /
`monsters.hydra/` without colocated `test_*.py` files. Test
coverage is the precondition for trusting performance metrics —
hence its natural home in this phalanx.

Authorized by `delphi/2026-05-13-arc-e-acceleration-consciousness-cohort-e10.md`.
"""

from monsters.argos.phalanges.base import Phalanx, Tactic, TacticConfig
from monsters.argos.eyes.ant_atlas_endpoint_health import AntAtlasEndpointHealth
from monsters.argos.eyes.ant_api_doc_coverage import AntApiDocCoverage
from monsters.argos.eyes.ant_test_gap import AntTestGap


class LegioPerformance(Phalanx):
    NAME    = "phalanx_performance"
    DOMAIN  = "performance"
    LEGATUS = "Legatus Performance"
    ANTS    = [AntAtlasEndpointHealth, AntApiDocCoverage, AntTestGap]
    TACTIC  = TacticConfig(tactic=Tactic.TESTUDO)
