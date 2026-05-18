"""Legio Trajectory — Legatus of the project's temporal dynamics.

Commands the ants that read project rhythm: ship-rate bursts,
journal silence, file churn, CHANGELOG gaps, proposal stagnation.
Doctrine: **TRIPLEX ACIES** — three-line battle order with
deliberate escalation.

Cohort grew 4 → 5 in  (Phase F3): added
`ant_proposal_stagnation` as the first proposal-driven ant —
materialized via the G13 ratification loop (Augur proposed;
Zeus ratified via Delphi-authorized Option B).

The three tiers, post-F3:

  - **Tier 1 (hastati / front line)**: `ant_ship_burst`
      Cheapest: parse CHANGELOG headers, group by date, flag
      bursts. Almost always silent on normal-velocity work;
      fires loudly during sprints. Acts as the gate: if no
      burst is firing, the deeper tiers stay quiet because
      the project isn't moving.

  - **Tier 2 (principes / veterans)**: `ant_journal_silence`,
    `ant_recent_churn`, `ant_proposal_stagnation`
      Time-sensitive and pacing-related; meaningful when work
      IS actively happening (as established by T1) OR when the
      project HAS been stagnant in places (which proposal-
      stagnation catches even at rest). Journal-silence asks
      "is the agent recording?"; recent-churn asks "where is
      the heat?"; proposal-stagnation asks "what did we forget
      to ship?".

  - **Tier 3 (triarii / elite reserves)**: `ant_changelog_gap`
      Deepest: a full mtime walk of the source tree against the
      latest CHANGELOG date. Reserved for the case where T1 + T2
      both fired — work is happening, the project is hot, but
      the ship doc hasn't caught up yet. The classic "did we
      forget to write a CHANGELOG entry" check.

The escalation order is meaningful: T1 establishes that movement
exists, T2 characterizes the movement (including its absence in
forgotten proposals), T3 audits whether the movement has been
narrated.

Authorized by `delphi/2026-05-13-arc-e-acceleration-consciousness-cohort-e10.md`
and extended by `delphi/2026-05-13-arc-f-accelerated-pacing-override.md`.
"""

from monsters.argos.phalanges.base import Phalanx, Tactic, TacticConfig
from monsters.argos.eyes.ant_ship_burst import AntShipBurst
from monsters.argos.eyes.ant_journal_silence import AntJournalSilence
from monsters.argos.eyes.ant_recent_churn import AntRecentChurn
from monsters.argos.eyes.ant_changelog_gap import AntChangelogGap
from monsters.argos.eyes.ant_proposal_stagnation import AntProposalStagnation


class LegioTrajectory(Phalanx):
    NAME    = "phalanx_trajectory"
    DOMAIN  = "trajectory"
    LEGATUS = "Legatus Trajectory"
    ANTS    = [
        AntShipBurst,
        AntJournalSilence,
        AntRecentChurn,
        AntChangelogGap,
        AntProposalStagnation,
    ]
    TACTIC  = TacticConfig(
        tactic=Tactic.TRIPLEX_ACIES,
        tiers=[
            [AntShipBurst],                          # hastati (T1)
            [
                AntJournalSilence,
                AntRecentChurn,
                AntProposalStagnation,
            ],                                        # principes (T2)
            [AntChangelogGap],                       # triarii (T3)
        ],
    )
