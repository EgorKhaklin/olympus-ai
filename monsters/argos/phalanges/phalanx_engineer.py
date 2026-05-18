"""Legio Engineer — Legatus Aedile.

The second **Imperial phalanx** added after (legacy arc). Roman
context: the *aediles* were the magistrates responsible for
public works — roads, aqueducts, granaries, public games. The
Engineer's domain in the cognitive substrate is the *public
works of the codebase*: build artifacts, release cadence,
shipping velocity.

This phalanx is deliberately CUNEUS doctrine — the lead ant
(`ant_build_freshness`) pierces first: if build state looks
healthy, no further investigation is needed. If the lead fires,
the follower (`ant_release_velocity`) deploys to characterize
the cadence implications.

The Engineer **does not duplicate** the  / E10 acceleration
ants under `phalanx_cognitive` / `phalanx_performance` /
`phalanx_trajectory`. Those ants surface source-level debt (TODOs,
test gaps, recent churn, version refs, CHANGELOG gaps); the
Engineer covers the layer ABOVE the source: build artifacts,
vendored assets, release rhythm. The Delphi §III analysis
called out the duplication risk explicitly; the Engineer's
cohort was scoped to address it.

The cohort:
  - `ant_build_freshness` (LEAD / CUNEUS point) — Docker
    artifacts, `__pycache__` orphans, Rust target staleness,
    vendored-asset version drift.
  - `ant_release_velocity` (follower) — long-term cadence:
    stagnation (≥14d no ship); sustained burst (≥3 consecutive
    days with ships); median version-bump gap.

Authorized by `delphi/2026-05-13-arc-g-roman-empire-opening.md`.
"""

from monsters.argos.phalanges.base import Phalanx, Tactic, TacticConfig
from monsters.argos.eyes.ant_build_freshness import AntBuildFreshness
from monsters.argos.eyes.ant_release_velocity import AntReleaseVelocity


class LegioEngineer(Phalanx):
    NAME    = "phalanx_engineer"
    DOMAIN  = "engineering"
    LEGATUS = "Legatus Aedile"
    ANTS    = [AntBuildFreshness, AntReleaseVelocity]
    TACTIC  = TacticConfig(
        tactic=Tactic.CUNEUS,
        lead=AntBuildFreshness,
    )
