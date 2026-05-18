"""PlebsForumWatcher — cross-phalanx volume reader.

The Plebs (Plebeians) class watches the **Forum** — the pheromone
log — for cross-phalanx volume imbalances. If a single phalanx
contributes more than `DOMINANT_THRESHOLD` of recent pheromones,
that phalanx's domain is in crisis (or experiencing a real burst
of activity that warrants visibility).

This is the cross-phalanx read the bloom does at READ time; the
Plebs do it at SCAN time so the imbalance becomes a pheromone
itself, visible to other citizens (especially Augures).

The Forum is the public space where everything meets. The Plebs
walk it daily.
"""

from __future__ import annotations

from collections import Counter

from monsters.argos.demes.base import (
    Deme, DemeFinding, CIVITAS_PLEBS,
)


DOMINANT_THRESHOLD = 0.50    # one phalanx ≥ 50% of recent deposits = imbalance


class PlebsForumWatcher(Citizen):
    NAME          = "plebs_forum_watcher"
    CIVITAS_CLASS = CIVITAS_PLEBS
    DESCRIPTION   = "Plebs in the Forum: watches for cross-phalanx volume imbalance."

    def observe(self, recent_pheromones: list[dict]) -> list[DemeFinding]:
        findings: list[DemeFinding] = []
        if not recent_pheromones:
            return findings

        # Count deposits per phalanx (from evidence.legio).
        phalanx_counts: Counter[str] = Counter()
        for ph in recent_pheromones:
            ev = ph.get("evidence") or {}
            legio = ev.get("phalanx", "(unattributed)")
            phalanx_counts[legio] += 1

        total = sum(phalanx_counts.values())
        if total < 4:
            # Too few deposits to draw conclusions
            return findings

        for legio, count in phalanx_counts.most_common():
            share = count / total
            if share >= DOMINANT_THRESHOLD:
                findings.append(DemeFinding(
                    node_id=f"forum:{legio}",
                    intensity=round(min(7.0, 3.0 + share * 5.0), 3),
                    kind="info",
                    observation_type="forum_imbalance",
                    evidence={
                        "message": (
                            f"Plebs observation: {legio} contributes "
                            f"{count}/{total} ({share:.0%}) of recent "
                            f"forum deposits — domain may be in crisis "
                            f"or experiencing a genuine activity burst"
                        ),
                        "dominant_phalanx": legio,
                        "share": round(share, 3),
                        "total_deposits": total,
                    },
                    half_life_hours=12.0,    # half-day; fades fast
                ))
                # Only flag the most dominant phalanx; one imbalance
                # finding per pass is enough signal.
                break
        return findings
