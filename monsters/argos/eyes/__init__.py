"""Argos ants — independent scanner modules.

Each ant under this package is a self-contained module that subclasses
`monsters.argos.base.Ant`. The colony runner discovers ants by walking
the phalanx modules; this `__init__.py` exposes a flat ALL_EYES list
for partition-correctness checks (G10).

CONTRACT (enforced by structural-invariant `test_no_ant_imports_another_ant`):
  NO ant module may import any other ant module. Period. The shared
  base.py is the only common ground.

Cohort (33 ants as of  / G1 ✅ — (legacy arc) Phase 1; first Imperial phalanxs):

  Phase 1 (E1 / ):
    1. ant_delphi_outcome           (phalanx_mission)
    2. ant_api_doc_coverage          (phalanx_performance)
    3. ant_journal_silence           (phalanx_trajectory)

  Phase 2 (E2 / ):
    4. ant_aor_immutability          (phalanx_schema)
    5. ant_fk_cascade_guard          (phalanx_schema)
    6. ant_stale_script              (phalanx_cognitive)
    7. ant_pattern_warmth            (phalanx_cognitive)
    8. ant_csp_health                (phalanx_security)
    9. ant_done_list_arithmetic      (phalanx_mission)
   10. ant_adversary_walk_complete   (phalanx_adversary)
   11. ant_atlas_endpoint_health     (phalanx_performance)
   12. ant_ship_burst                (phalanx_trajectory)

  Phase 7 (E7 / ) — hydra nine-heads completion:
   13. ant_substrate_catalog         (phalanx_substrate, CUNEUS lead)
   14. ant_dependency_in_use         (phalanx_substrate, follower)
   15. ant_rust_toolchain            (phalanx_substrate, follower)
   16. ant_docs_structure            (phalanx_docs, T1 hastati)
   17. ant_readme_counts             (phalanx_docs, T2 principes)
   18. ant_devnotes_ships_coverage   (phalanx_docs, T3 triarii)

  Phase E10 () — acceleration + consciousness expansion:
   19. ant_todo_debt                 (phalanx_cognitive)
   20. ant_test_gap                  (phalanx_performance)
   21. ant_recent_churn              (phalanx_trajectory, T2 principes)
   22. ant_self_model_accuracy       (phalanx_cognitive — first ALERT-capable)
   23. ant_swarm_inventory_drift     (phalanx_docs, T2 principes)
   24. ant_treasury_health           (phalanx_cognitive)
   25. ant_unbumped_version          (phalanx_docs, T3 triarii)
   26. ant_changelog_gap             (phalanx_trajectory, T3 triarii)
   27. ant_phalanx_doctrine_health    (phalanx_cognitive — second ALERT-capable)
   28. ant_brain_map_freshness       (phalanx_cognitive)

  Phase F3 () — first proposal-driven ant via G13 ratification:
   29. ant_proposal_stagnation       (phalanx_trajectory, T2 principes)
       Proposed by AugurBloomReader on observation of zero coverage
       for proposals/*.md. Ratified by Zeus via Delphi-authorized
       Option B.

  Phase G1 () — (legacy arc) Phase 1, first Imperial phalanxs:
   30. ant_mission_drift             (phalanx_praetorian) — ALERT-capable
   31. ant_principle_invariant       (phalanx_praetorian) — ALERT-capable
   32. ant_build_freshness           (phalanx_engineer, CUNEUS lead)
   33. ant_release_velocity          (phalanx_engineer, CUNEUS follower)
       Praetorian + Engineer are the first two Imperial phalanxs
       (added  / (legacy arc)). Republican phalanxs = 9; Imperial
       phalanxs = 2. **Phalanges are NOT Hydra heads** — that
       mythology was relocated to HYDRA watchers in  (see
       `delphi/2026-05-13-hydra-mythology-relocation-to-watchers.md`).
"""

# Phase 1 ants
from monsters.argos.eyes.ant_delphi_outcome import AntDelphiOutcome
from monsters.argos.eyes.ant_api_doc_coverage import AntApiDocCoverage
from monsters.argos.eyes.ant_journal_silence import AntJournalSilence

# Phase 2 ants
from monsters.argos.eyes.ant_aor_immutability import AntAorImmutability
from monsters.argos.eyes.ant_fk_cascade_guard import AntFkCascadeGuard
from monsters.argos.eyes.ant_stale_script import AntStaleScript
from monsters.argos.eyes.ant_pattern_warmth import AntPatternWarmth
from monsters.argos.eyes.ant_csp_health import AntCspHealth
from monsters.argos.eyes.ant_done_list_arithmetic import AntDoneListArithmetic
from monsters.argos.eyes.ant_adversary_walk_complete import AntAdversaryWalkComplete
from monsters.argos.eyes.ant_atlas_endpoint_health import AntAtlasEndpointHealth
from monsters.argos.eyes.ant_ship_burst import AntShipBurst

# Phase 7 ants ( — hydra nine-heads completion)
from monsters.argos.eyes.ant_substrate_catalog import AntSubstrateCatalog
from monsters.argos.eyes.ant_dependency_in_use import AntDependencyInUse
from monsters.argos.eyes.ant_rust_toolchain import AntRustToolchain
from monsters.argos.eyes.ant_docs_structure import AntDocsStructure
from monsters.argos.eyes.ant_readme_counts import AntReadmeCounts
from monsters.argos.eyes.ant_devnotes_ships_coverage import AntDevnotesShipsCoverage

# Phase E10 ants ( — acceleration + consciousness expansion)
from monsters.argos.eyes.ant_todo_debt import AntTodoDebt
from monsters.argos.eyes.ant_test_gap import AntTestGap
from monsters.argos.eyes.ant_recent_churn import AntRecentChurn
from monsters.argos.eyes.ant_self_model_accuracy import AntSelfModelAccuracy
from monsters.argos.eyes.ant_swarm_inventory_drift import AntSwarmInventoryDrift
from monsters.argos.eyes.ant_treasury_health import AntTreasuryHealth
from monsters.argos.eyes.ant_unbumped_version import AntUnbumpedVersion
from monsters.argos.eyes.ant_changelog_gap import AntChangelogGap
from monsters.argos.eyes.ant_phalanx_doctrine_health import AntPhalanxDoctrineHealth
from monsters.argos.eyes.ant_brain_map_freshness import AntBrainMapFreshness

# Phase F3 ants ( — proposal-driven autogenesis)
from monsters.argos.eyes.ant_proposal_stagnation import AntProposalStagnation

# Phase G1 ants ( — first Imperial phalanxs)
from monsters.argos.eyes.ant_mission_drift import AntMissionDrift
from monsters.argos.eyes.ant_principle_invariant import AntPrincipleInvariant
from monsters.argos.eyes.ant_build_freshness import AntBuildFreshness
from monsters.argos.eyes.ant_release_velocity import AntReleaseVelocity


ALL_EYES = [
    # Phase 1
    AntDelphiOutcome,
    AntApiDocCoverage,
    AntJournalSilence,
    # Phase 2
    AntAorImmutability,
    AntFkCascadeGuard,
    AntStaleScript,
    AntPatternWarmth,
    AntCspHealth,
    AntDoneListArithmetic,
    AntAdversaryWalkComplete,
    AntAtlasEndpointHealth,
    AntShipBurst,
    # Phase 7 ()
    AntSubstrateCatalog,
    AntDependencyInUse,
    AntRustToolchain,
    AntDocsStructure,
    AntReadmeCounts,
    AntDevnotesShipsCoverage,
    # Phase E10 ()
    AntTodoDebt,
    AntTestGap,
    AntRecentChurn,
    AntSelfModelAccuracy,
    AntSwarmInventoryDrift,
    AntTreasuryHealth,
    AntUnbumpedVersion,
    AntChangelogGap,
    AntPhalanxDoctrineHealth,
    AntBrainMapFreshness,
    # Phase F3 ()
    AntProposalStagnation,
    # Phase G1 ( — Imperial phalanxs)
    AntMissionDrift,
    AntPrincipleInvariant,
    AntBuildFreshness,
    AntReleaseVelocity,
]


__all__ = [
    # Phase 1
    "AntDelphiOutcome", "AntApiDocCoverage", "AntJournalSilence",
    # Phase 2
    "AntAorImmutability", "AntFkCascadeGuard", "AntStaleScript",
    "AntPatternWarmth", "AntCspHealth", "AntDoneListArithmetic",
    "AntAdversaryWalkComplete", "AntAtlasEndpointHealth", "AntShipBurst",
    # Phase 7
    "AntSubstrateCatalog", "AntDependencyInUse", "AntRustToolchain",
    "AntDocsStructure", "AntReadmeCounts", "AntDevnotesShipsCoverage",
    # Phase E10
    "AntTodoDebt", "AntTestGap", "AntRecentChurn",
    "AntSelfModelAccuracy", "AntSwarmInventoryDrift", "AntTreasuryHealth",
    "AntUnbumpedVersion", "AntChangelogGap", "AntPhalanxDoctrineHealth",
    "AntBrainMapFreshness",
    # Phase F3
    "AntProposalStagnation",
    # Phase G1
    "AntMissionDrift", "AntPrincipleInvariant",
    "AntBuildFreshness", "AntReleaseVelocity",
    "ALL_EYES",
]
