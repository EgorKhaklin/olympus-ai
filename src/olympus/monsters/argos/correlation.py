"""olympus.monsters.argos.correlation — cross-eye pattern detection.

Argos's eyes scan independently (S4 decentralization). Patterns emerge
only when something walks the aggregated pheromone log at read time.
That walker is the CorrelationEngine.

The engine produces three kinds of cross-eye signals:

  Cluster      Multiple eyes reporting on the SAME slice in the same window
  Cascade      An eye that frequently fires shortly after another eye
  Quiet        An eye that has stopped depositing pheromones (silent gap)

These are emergent properties of the swarm — no single eye sees them.
"""
from __future__ import annotations

import datetime
from collections import defaultdict, Counter
from dataclasses import dataclass, field
from typing import Any

from olympus.titans.cronus import Cronus


WINDOW_HOURS_DEFAULT = 24.0
CASCADE_MAX_GAP_MINUTES = 15.0
QUIET_THRESHOLD_HOURS = 72.0


@dataclass
class Cluster:
    """≥2 eyes reporting on the same slice in the window."""
    slice: str
    eyes: list[str]
    kinds: list[str]
    intensity_sum: float
    sample_details: list[str] = field(default_factory=list)


@dataclass
class Cascade:
    """Eye A frequently followed within a short gap by Eye B."""
    leader: str
    follower: str
    instances: int
    median_gap_minutes: float


@dataclass
class Quiet:
    """Eye that hasn't deposited in `hours_silent` hours."""
    eye: str
    last_seen_ts: str | None
    hours_silent: float


@dataclass
class CorrelationReport:
    window_hours: float
    pheromones_considered: int
    clusters: list[Cluster] = field(default_factory=list)
    cascades: list[Cascade] = field(default_factory=list)
    quiet: list[Quiet] = field(default_factory=list)


class CorrelationEngine:
    """Reads the pheromone log; produces structured correlations."""

    def correlate(self, *, window_hours: float = WINDOW_HOURS_DEFAULT,
                  known_eyes: list[str] | None = None) -> CorrelationReport:
        from olympus.monsters.argos.colony import colony

        cutoff_age_s = window_hours * 3600.0
        all_phers = colony.read_log()
        recent = [
            p for p in all_phers
            if Cronus.age_seconds(p.deposited_at) <= cutoff_age_s
        ]

        report = CorrelationReport(
            window_hours=window_hours,
            pheromones_considered=len(recent),
        )

        report.clusters = self._clusters(recent)
        report.cascades = self._cascades(recent)
        if known_eyes:
            report.quiet = self._quiet(all_phers, known_eyes)

        return report

    # ─────────────────────────────────────────────────────────

    @staticmethod
    def _clusters(phers: list[Any]) -> list[Cluster]:
        by_slice: dict[str, list[Any]] = defaultdict(list)
        for p in phers:
            by_slice[p.slice].append(p)

        clusters: list[Cluster] = []
        for slice_name, group in by_slice.items():
            eyes = sorted({p.eye for p in group})
            if len(eyes) < 2:
                continue
            clusters.append(Cluster(
                slice=slice_name,
                eyes=eyes,
                kinds=sorted({p.kind for p in group}),
                intensity_sum=sum(p.intensity for p in group),
                sample_details=[p.detail[:80] for p in group[:3] if p.detail],
            ))
        return sorted(clusters, key=lambda c: -c.intensity_sum)

    @staticmethod
    def _cascades(phers: list[Any]) -> list[Cascade]:
        # Sort by deposited_at
        ordered = sorted(phers, key=lambda p: p.deposited_at)
        gaps: dict[tuple[str, str], list[float]] = defaultdict(list)

        for i, leader in enumerate(ordered):
            for j in range(i + 1, len(ordered)):
                follower = ordered[j]
                if follower.eye == leader.eye:
                    continue
                gap_s = Cronus.age_seconds(leader.deposited_at) - \
                        Cronus.age_seconds(follower.deposited_at)
                gap_minutes = gap_s / 60.0
                if gap_minutes < 0:
                    gap_minutes = -gap_minutes
                if gap_minutes > CASCADE_MAX_GAP_MINUTES:
                    break
                gaps[(leader.eye, follower.eye)].append(gap_minutes)

        cascades: list[Cascade] = []
        for (leader, follower), instances in gaps.items():
            if len(instances) < 2:
                continue
            instances.sort()
            median = instances[len(instances) // 2]
            cascades.append(Cascade(
                leader=leader, follower=follower,
                instances=len(instances), median_gap_minutes=median,
            ))
        return sorted(cascades, key=lambda c: -c.instances)

    @staticmethod
    def _quiet(all_phers: list[Any], known_eyes: list[str]) -> list[Quiet]:
        last_seen: dict[str, str] = {}
        for p in all_phers:
            cur = last_seen.get(p.eye, "")
            if p.deposited_at > cur:
                last_seen[p.eye] = p.deposited_at

        quiet: list[Quiet] = []
        for eye in known_eyes:
            last = last_seen.get(eye)
            if last is None:
                quiet.append(Quiet(eye=eye, last_seen_ts=None,
                                    hours_silent=float("inf")))
                continue
            hours = Cronus.age_seconds(last) / 3600.0
            if hours > QUIET_THRESHOLD_HOURS:
                quiet.append(Quiet(eye=eye, last_seen_ts=last,
                                   hours_silent=hours))
        return quiet


correlation = CorrelationEngine()
