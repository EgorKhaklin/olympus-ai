"""Legio Cognitive — Legatus of the cognitive-layer domain.

The project's self-monitoring HUB. Commands the ants that scan
the cognitive substrate's own state: script staleness, pattern
warmth, TODO debt, registry-vs-reality, treasury health, phalanx
doctrine, brain-map freshness.

Cohort grew 2 → 7 in  (Phase E10 acceleration + consciousness
expansion). Doctrine remains TESTUDO for now — all 7 ants scan
every pass. Per the Delphi, the shift to TRIPLEX_ACIES is a
deliberate Phase-2+ decision; TESTUDO at 7 ants is operationally
fine (each ant is cheap; the swarm pays a few seconds for
maximum coverage).

Two of the seven (`ant_self_model_accuracy`,
`ant_phalanx_doctrine_health`) are the first ALERT-capable ants
in the cohort. They surface structural divergence between the
swarm's CLAIMS about itself and its actual state — the consciousness
layer of the swarm.

Authorized by `delphi/2026-05-13-arc-e-acceleration-consciousness-cohort-e10.md`.
"""

from monsters.argos.phalanges.base import Phalanx, Tactic, TacticConfig
from monsters.argos.eyes.ant_stale_script import AntStaleScript
from monsters.argos.eyes.ant_pattern_warmth import AntPatternWarmth
from monsters.argos.eyes.ant_todo_debt import AntTodoDebt
from monsters.argos.eyes.ant_self_model_accuracy import AntSelfModelAccuracy
from monsters.argos.eyes.ant_treasury_health import AntTreasuryHealth
from monsters.argos.eyes.ant_phalanx_doctrine_health import AntPhalanxDoctrineHealth
from monsters.argos.eyes.ant_brain_map_freshness import AntBrainMapFreshness


class LegioCognitive(Phalanx):
    NAME    = "phalanx_cognitive"
    DOMAIN  = "cognitive"
    LEGATUS = "Legatus Cognitive"
    ANTS    = [
        # Original (E2)
        AntStaleScript,
        AntPatternWarmth,
        # E10 acceleration (1)
        AntTodoDebt,
        # E10 consciousness (4)
        AntSelfModelAccuracy,
        AntTreasuryHealth,
        AntPhalanxDoctrineHealth,
        AntBrainMapFreshness,
    ]
    TACTIC  = TacticConfig(tactic=Tactic.TESTUDO)
