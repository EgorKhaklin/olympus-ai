"""EquesCorrelator — cross-phalanx courier.

The Equites (Equestrians) were Rome's merchant class — they moved
between cities, between provinces, between social strata. In the
swarm, they move INFORMATION between phalanxs that have not
declared formal alliances (auxilia_pool).

The Eques observes when two un-allied phalanxs fire within a short
window on related signals. The classic example: Legio Schema
flags drift AND Legio Substrate flags drift within 6 hours. This
could be a real **dependency-driven schema regression** that
neither phalanx alone would surface.

The Eques deposits a "cross_phalanx_correlation" finding which
Augures (interpreters) can read on the next pass. Information
moves between phalanxs via the Forum, not via direct messages —
this preserves G6 (phalanxs don't talk to each other directly).
"""

from __future__ import annotations

from datetime import datetime, timezone, timedelta

from monsters.argos.demes.base import (
    Deme, DemeFinding, CIVITAS_EQUITES,
)


# Correlation window: deposits from different phalanxs within this
# many hours are candidates for cross-phalanx correlation.
CORRELATION_WINDOW_HOURS = 6.0

# Pairs of phalanxs whose co-firing is structurally interesting.
# These are NOT pre-declared alliances (that's AUXILIA); these are
# generic curiosity correlations the Equites watch for.
INTERESTING_PAIRS = [
    ("phalanx_schema",     "phalanx_substrate"),    # dependency-driven schema drift
    ("phalanx_schema",     "phalanx_security"),     # schema change + security regression
    ("phalanx_cognitive",  "phalanx_mission"),      # cognitive drift + mission drift
    ("phalanx_performance","phalanx_substrate"),    # perf regression + dependency
    ("phalanx_docs",       "phalanx_mission"),      # doc drift + mission drift
    #  (R bundle from the 100-year-architect Delphi): added the
    # dominant-signal pairs the simulation revealed. Trajectory is
    # the limes; ship-burst alone or done-list alone is signal, but
    # together (or co-occurring with cognitive drift) they may
    # indicate scope-creep under pressure.
    ("phalanx_mission",    "phalanx_trajectory"),   # done-list + ship-burst (the heartbeat of the project)
    ("phalanx_cognitive",  "phalanx_trajectory"),   # cognitive drift + scope-creep
]


class EquesCorrelator(Citizen):
    NAME          = "eques_correlator"
    CIVITAS_CLASS = CIVITAS_EQUITES
    DESCRIPTION   = "Eques on horseback: correlates findings across un-allied phalanxs."

    def observe(self, recent_pheromones: list[dict]) -> list[DemeFinding]:
        findings: list[DemeFinding] = []
        if not recent_pheromones:
            return findings

        # Group deposits by phalanx + timestamp.
        per_legio: dict[str, list[datetime]] = {}
        for ph in recent_pheromones:
            ev = ph.get("evidence") or {}
            legio = ev.get("phalanx", "")
            if not legio:
                continue
            ts = ph.get("deposited_at")
            if ts is None:
                continue
            if isinstance(ts, datetime) and ts.tzinfo is None:
                ts = ts.replace(tzinfo=timezone.utc)
            per_phalanx.setdefault(legio, []).append(ts)

        window = timedelta(hours=CORRELATION_WINDOW_HOURS)
        for phalanx_a, phalanx_b in INTERESTING_PAIRS:
            times_a = per_phalanx.get(phalanx_a, [])
            times_b = per_phalanx.get(phalanx_b, [])
            if not times_a or not times_b:
                continue
            # Find any cross-pair within the window.
            correlated = False
            for ta in times_a:
                for tb in times_b:
                    if abs((ta - tb).total_seconds()) <= window.total_seconds():
                        correlated = True
                        break
                if correlated:
                    break
            if correlated:
                findings.append(DemeFinding(
                    node_id=f"correlation:{phalanx_a}+{phalanx_b}",
                    intensity=4.5,
                    kind="drift",
                    observation_type="cross_phalanx_correlation",
                    evidence={
                        "message": (
                            f"Eques observation: {phalanx_a} and {phalanx_b} "
                            f"both fired within {CORRELATION_WINDOW_HOURS}h — "
                            f"may indicate a cross-domain issue neither "
                            f"phalanx alone would surface"
                        ),
                        "phalanx_a": phalanx_a,
                        "phalanx_b": phalanx_b,
                        "deposits_a": len(times_a),
                        "deposits_b": len(times_b),
                        "window_hours": CORRELATION_WINDOW_HOURS,
                    },
                    half_life_hours=24.0,
                ))
        return findings
