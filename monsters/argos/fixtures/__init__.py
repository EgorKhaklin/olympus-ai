"""monsters.argos/fixtures/ — ground-truth fixtures for swarm validation.

 / BIG MISSION Tier 2 #10.

A fixture is a deliberately-broken (or deliberately-healthy) system
state plus a manifest of *which* commander ants the operator expects
to fire on this state. The validation harness runs the swarm against
each fixture, compares fired-ants against expected-ants, and reports
precision + recall per ant.

An ant with precision < 0.5 OR recall < 0.5 fails Tier 1 #2's
falsifiability requirement retroactively — it either fires on healthy
states (false positives reduce precision) or misses obvious broken
states (false negatives reduce recall). The Delphi scope:
sub-threshold ants get PREDICATE_PENDING flag in meta/ant-predicates.md.

**Fixture shape** (each fixture is a Python dict at module level):

    FIXTURE = {
        "name": "schema-c3-violated",
        "description": "Two ACTIVE tokens for the same individual",
        "setup": ["SQL statement", "SQL statement", ...],
        "teardown": ["SQL to undo"],
        "expected_firing_ants": ["ant_aor_immutability", ...],
        "expected_silent_ants": ["ant_csp_health", ...],
    }

 ships three demonstrator fixtures (one per major class). The
operator adds more per `meta/fixture-catalog.md`. Sub-threshold ant
detection ships as `scripts/oly-argos-validate.sh`.
"""

# Re-export fixtures for the validator's discoverability
from monsters.argos.fixtures import (
    fx_healthy_baseline,
    fx_schema_c3_violated,
    fx_changelog_drift,
)

ALL_FIXTURES = [
    fx_healthy_baseline.FIXTURE,
    fx_schema_c3_violated.FIXTURE,
    fx_changelog_drift.FIXTURE,
]
