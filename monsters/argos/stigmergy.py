"""monsters.argos/stigmergy.py — recurrence-weighted scan ordering.

 / BIG MISSION Tier 1 #4. Closes the stigmergic loop: deposits
from one colony pass now bias the *next* pass to investigate the
recurring nodes first.

Pre-, the colony scheduler deployed phalanxs in fixed lexicographic
order. Pheromone deposits were written but the next pass did not read
them. The "swarm" word in code+docs was vocabulary larping (AP8) — no
emergent ordering, just a periodic batch job.

This module provides one function: `recurrence_weighted_ordering()`
that reads the most-recent Pheromone deposits and returns a sorted
list of `(phalanx_name, node_id)` tuples that the next colony pass
should investigate first.

**Vocabulary discipline (per Momus contest in  Delphi):**
- Use "recurrence-weighted" — NOT "emergent" or "swarm intelligence."
- The mechanism is mechanical (count + recency), not magical.

**Recurrence definition (per the  Delphi joint resolution):**
- A node_id is *recurring* if ≥2 distinct commander ants emit findings
  with that node_id within the last `window_hours` (default 24).
- A node_id is *decayed-but-returning* if it was emitted in
  [now - decay_hours, now - window_hours] then NOT in [now - window_hours, now]
  AND then re-emitted within the last 2 hours (returned after silence).

Both classes get prioritized in the next pass, with recurring weighted
higher than decayed-but-returning.

**Deterministic + G1-preserving.** Same DB state → same ordering. The
priority is a sort key, not a stochastic process.
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Optional


@dataclass(frozen=True)
class StigmergyPriority:
    """A single prioritization decision for the next scan.

    `phalanx_name` is the phalanx that should run first.
    `node_id` is the surface the ants should examine.
    `weight` is the priority score (higher = run sooner).
    `reason` is one-line operator-readable text.
    """
    phalanx_name: str
    node_id: str
    weight: float
    reason: str


def recurrence_weighted_ordering(
    recent_pheromones: list[dict],
    window_hours: float = 24.0,
    decay_hours: float = 72.0,
) -> list[StigmergyPriority]:
    """Read recent Pheromone deposits; emit prioritized scan list.

    `recent_pheromones` is a list of dicts with at minimum:
        - 'deposited_by' (ant name string)
        - 'deposited_at' (datetime or ISO string)
        - 'evidence' (dict with possibly 'node_id', 'phalanx_name')
        - OR top-level 'node_id' / 'phalanx_name'

    Returns a list of StigmergyPriority sorted by weight DESCENDING.
    The colony scheduler iterates this list when deciding which
    phalanxs to deploy first on the next pass.

    Empty input returns empty list. Caller-side: if empty list,
    scheduler falls back to lexicographic order (G1 preserved —
    same input → same output, including the empty-input case).
    """
    if not recent_pheromones:
        return []

    now = datetime.now(timezone.utc)
    window_cutoff = now - timedelta(hours=window_hours)
    decay_cutoff = now - timedelta(hours=decay_hours)
    return_window_cutoff = now - timedelta(hours=2.0)

    # Group deposits by node_id; track per-ant emissions + most recent emission
    per_node = defaultdict(lambda: {
        "distinct_ants": set(),
        "phalanxs": set(),
        "recent_emissions": [],
        "all_emissions": [],
    })

    for row in recent_pheromones:
        node_id = _extract_node_id(row)
        if not node_id:
            continue
        phalanx = _extract_phalanx_name(row)
        ant = row.get("deposited_by") or row.get("ant_name") or "unknown"
        ts = _parse_ts(row.get("deposited_at"))
        if ts is None:
            continue

        per_node[node_id]["distinct_ants"].add(ant)
        if phalanx:
            per_node[node_id]["phalanxs"].add(phalanx)
        per_node[node_id]["all_emissions"].append(ts)
        if ts >= window_cutoff:
            per_node[node_id]["recent_emissions"].append(ts)

    out: list[StigmergyPriority] = []

    for node_id, info in per_node.items():
        phalanx = sorted(info["phalanxs"])[0] if info["phalanxs"] else "unknown"
        n_ants = len(info["distinct_ants"])
        n_recent = len(info["recent_emissions"])
        all_emissions = sorted(info["all_emissions"], reverse=True)

        # Class 1: recurring within window — ≥2 distinct ants
        if n_ants >= 2 and n_recent >= 2:
            weight = 10.0 + n_ants + (n_recent * 0.5)
            reason = (f"recurring: {n_ants} distinct ants emitted in last "
                      f"{int(window_hours)}h ({n_recent} emissions)")
            out.append(StigmergyPriority(
                phalanx_name=phalanx,
                node_id=node_id,
                weight=weight,
                reason=reason,
            ))
            continue

        # Class 2: decayed-but-returning — old emissions exist + new one in last 2h
        old_emissions = [t for t in all_emissions if t < window_cutoff
                          and t >= decay_cutoff]
        very_recent = [t for t in all_emissions if t >= return_window_cutoff]
        # Was silent in window EXCEPT for the very-recent return
        silent_in_middle = (n_recent <= len(very_recent)) and (n_recent > 0)
        if old_emissions and very_recent and silent_in_middle:
            weight = 5.0 + len(old_emissions) * 0.3
            reason = (f"decayed-but-returning: emitted {len(old_emissions)}x "
                      f"in [{int(decay_hours)}h..{int(window_hours)}h] window, "
                      f"silent in between, returned in last 2h")
            out.append(StigmergyPriority(
                phalanx_name=phalanx,
                node_id=node_id,
                weight=weight,
                reason=reason,
            ))
            continue

        # Class 3 (low priority): emitted at least once recently
        if n_recent >= 1:
            weight = 1.0
            reason = f"single-emission in last {int(window_hours)}h"
            out.append(StigmergyPriority(
                phalanx_name=phalanx,
                node_id=node_id,
                weight=weight,
                reason=reason,
            ))

    out.sort(key=lambda p: (-p.weight, p.phalanx_name, p.node_id))
    return out


def phalanx_priority_order(
    priorities: list[StigmergyPriority],
    all_phalanx_names: list[str],
) -> list[str]:
    """Translate the per-node priority list into a phalanx-deploy order.

    The colony's deploy loop iterates phalanxs, not nodes — this is the
    glue. Phalanges with high-weight nodes get deployed first; phalanxs
    with no priorities go last in lexicographic order.

    G1 (deterministic): same priorities + same all_phalanx_names →
    same output order.
    """
    # Per-phalanx best weight
    per_phalanx: dict[str, float] = {}
    for p in priorities:
        existing = per_phalanx.get(p.phalanx_name, 0.0)
        if p.weight > existing:
            per_phalanx[p.phalanx_name] = p.weight

    # Order: by weight desc, then lex; phalanxs with no weight go after
    weighted = [(name, per_phalanx.get(name, 0.0)) for name in all_phalanx_names]
    weighted.sort(key=lambda x: (-x[1], x[0]))
    return [name for name, _ in weighted]


def _extract_node_id(row: dict) -> Optional[str]:
    """node_id may be at top level OR inside evidence sub-dict."""
    nid = row.get("node_id")
    if nid:
        return str(nid)
    ev = row.get("evidence", {}) or {}
    if isinstance(ev, dict):
        return ev.get("node_id")
    return None


def _extract_phalanx_name(row: dict) -> Optional[str]:
    """phalanx_name may be at top level OR inside evidence."""
    ln = row.get("phalanx_name") or row.get("phalanx")
    if ln:
        return str(ln)
    ev = row.get("evidence", {}) or {}
    if isinstance(ev, dict):
        return ev.get("phalanx_name") or ev.get("phalanx")
    return None


def _parse_ts(value) -> Optional[datetime]:
    """Parse deposited_at as datetime; accepts datetime or ISO string."""
    if value is None:
        return None
    if isinstance(value, datetime):
        return value if value.tzinfo else value.replace(tzinfo=timezone.utc)
    if isinstance(value, str):
        try:
            dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
            return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)
        except ValueError:
            return None
    return None
