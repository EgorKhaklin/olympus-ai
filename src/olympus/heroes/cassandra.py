"""Cassandra — the prophetess of Troy.

In myth: Apollo gave her the gift of prophecy. When she refused him,
he cursed her so that no one would believe her warnings. She told the
Trojans the wooden horse was a trap; she was dismissed; Troy fell. Her
tragedy is that she was right.

In Olympus: Cassandra is the symmetric counterpart to Hephaestus's
rejection memory. Hephaestus remembers proposals Zeus killed so the
substrate stops nagging. Cassandra remembers *alerts that were
dismissed* — alerts where no action was raised, or the proposal raised
was rejected — and tracks whether the underlying concern recurs.

When a slice was warned about and the warning was ignored, and the
slice alerts again in subsequent sessions, the warning is *vindicated*.
The substrate now knows what it shrugged off that came back.

Read-only. Records to Mnemosyne. Sources:
  - state/argos_pheromones.jsonl  (canonical alert log, via colony)
  - action.ratified / action.rejected in Mnemosyne
  - state/hephaestus/proposals/*.json (for drift signature recovery)

Per Delphi 2026-05-18-missing-figures-arc.md (zero Momus dings).
"""
from __future__ import annotations

import json
from collections import defaultdict
from dataclasses import dataclass, field, asdict
from typing import Any

from olympus.primordials.gaia import root
from olympus.primordials.nyx import Nyx
from olympus.titans.mnemosyne import mnemosyne


@dataclass
class IgnoredWarning:
    """An ALERT-bearing slice that was dismissed — either explicitly
    rejected or silently passed (no proposal ever raised)."""
    slice: str
    first_alerted_at: str
    last_alerted_at: str
    alert_count: int
    dismissal_kind: str       # 'rejected' | 'silent'


@dataclass
class Vindication:
    """An ignored warning whose underlying concern recurred — Cassandra
    was right."""
    slice: str
    first_alerted_at: str
    dismissed_at: str
    dismissal_kind: str
    recurrences_after_dismissal: int
    last_recurrence_at: str
    recorded_at: str = ""

    def __post_init__(self) -> None:
        if not self.recorded_at:
            self.recorded_at = Nyx.now().isoformat()


@dataclass
class CassandraReport:
    started_at: str
    ended_at: str = ""
    ignored: list[IgnoredWarning] = field(default_factory=list)
    vindicated: list[Vindication] = field(default_factory=list)

    @property
    def total_ignored(self) -> int: return len(self.ignored)

    @property
    def total_vindicated(self) -> int: return len(self.vindicated)


# ─────────────────────────────────────────────────────────
# Sources — read the canonical stores directly
# ─────────────────────────────────────────────────────────


_PHEROMONE_LOG = "state/argos_pheromones.jsonl"
_PROPOSALS_DIR = "state/hephaestus/proposals"


def _slice_alerts() -> dict[str, list[str]]:
    """For each slice, the timestamps of every ALERT pheromone.
    Read from the canonical Argos pheromone log."""
    by_slice: dict[str, list[str]] = defaultdict(list)
    path = root.child(_PHEROMONE_LOG)
    if not path.exists():
        return {}
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                row = json.loads(line)
            except json.JSONDecodeError:
                continue
            if row.get("kind") != "alert":
                continue
            sl = row.get("slice")
            ts = row.get("deposited_at", "")
            if sl and ts:
                by_slice[sl].append(ts)
    for sl in by_slice:
        by_slice[sl].sort()
    return by_slice


def _slice_to_proposals() -> dict[str, list[dict[str, Any]]]:
    """slice → [{proposal_id, action_id, status}] across all proposals
    on disk. Status comes from action.ratified / action.rejected in
    Mnemosyne; absence means queued or never promoted."""
    proposals_dir = root.child(_PROPOSALS_DIR)
    if not proposals_dir.exists():
        return {}

    # Build slice → proposal_id map by parsing each proposal's drift text.
    import re
    pattern = re.compile(r"slice\s+['\"]([^'\"]+)['\"]")
    out: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for pf in proposals_dir.glob("*.json"):
        try:
            data = json.loads(pf.read_text(encoding="utf-8"))
        except Exception:  # noqa: BLE001
            continue
        drift = data.get("drift_observed", "")
        match = pattern.search(drift)
        if not match:
            continue
        sl = match.group(1)
        out[sl].append({
            "proposal_id": data.get("id") or pf.stem,
            "action_id": f"act-{data.get('id') or pf.stem}",
        })
    return out


def _action_status() -> dict[str, tuple[str, str]]:
    """action_id → (status, ts) where status ∈ {ratified, rejected}.
    The latest record wins per action_id."""
    out: dict[str, tuple[str, str]] = {}
    for m in mnemosyne.recall("action.ratified"):
        aid = (m.body or {}).get("action_id", "")
        if aid:
            out[aid] = ("ratified", m.remembered_at)
    for m in mnemosyne.recall("action.rejected"):
        aid = (m.body or {}).get("action_id", "")
        if aid:
            out[aid] = ("rejected", m.remembered_at)
    return out


# ─────────────────────────────────────────────────────────
# Cassandra
# ─────────────────────────────────────────────────────────


class Cassandra:
    """The unbelieved prophetess. Tracks dismissed warnings and their
    subsequent vindication."""

    # Vindication requires at least N alerts AFTER the dismissal moment
    VINDICATION_THRESHOLD = 2

    def ignored_warnings(self) -> list[IgnoredWarning]:
        """Every ALERT-bearing slice whose warning was either rejected
        or silently passed."""
        alerts = _slice_alerts()
        proposals = _slice_to_proposals()
        status = _action_status()

        ignored: list[IgnoredWarning] = []
        for sl, ts_list in alerts.items():
            if not ts_list:
                continue
            slice_props = proposals.get(sl, [])
            if not slice_props:
                # Never had a proposal — silent dismissal
                ignored.append(IgnoredWarning(
                    slice=sl,
                    first_alerted_at=ts_list[0],
                    last_alerted_at=ts_list[-1],
                    alert_count=len(ts_list),
                    dismissal_kind="silent",
                ))
                continue
            # Had proposals — check if any were ratified
            statuses = [status.get(p["action_id"], (None, None))
                        for p in slice_props]
            if any(s[0] == "ratified" for s in statuses):
                continue  # heeded — not ignored
            if any(s[0] == "rejected" for s in statuses):
                ignored.append(IgnoredWarning(
                    slice=sl,
                    first_alerted_at=ts_list[0],
                    last_alerted_at=ts_list[-1],
                    alert_count=len(ts_list),
                    dismissal_kind="rejected",
                ))
                continue
            # Queued but never decided — count as silent for now
            ignored.append(IgnoredWarning(
                slice=sl,
                first_alerted_at=ts_list[0],
                last_alerted_at=ts_list[-1],
                alert_count=len(ts_list),
                dismissal_kind="silent",
            ))
        return ignored

    def vindicated(self) -> list[Vindication]:
        """Ignored warnings whose slice has alerted ≥ threshold times
        AFTER the dismissal moment. For silent dismissals the moment is
        the first alert; for rejected dismissals the moment is the
        latest rejection timestamp."""
        alerts = _slice_alerts()
        ignored = self.ignored_warnings()
        status = _action_status()
        proposals = _slice_to_proposals()

        out: list[Vindication] = []
        for w in ignored:
            ts_list = alerts.get(w.slice, [])
            if w.dismissal_kind == "rejected":
                # Find the latest rejection across this slice's proposals
                slice_props = proposals.get(w.slice, [])
                rej_ts = ""
                for p in slice_props:
                    s, t = status.get(p["action_id"], (None, None))
                    if s == "rejected" and t and t > rej_ts:
                        rej_ts = t
                dismissed_at = rej_ts or w.first_alerted_at
            else:
                dismissed_at = w.first_alerted_at
            after = [t for t in ts_list if t > dismissed_at]
            if len(after) >= self.VINDICATION_THRESHOLD:
                out.append(Vindication(
                    slice=w.slice,
                    first_alerted_at=w.first_alerted_at,
                    dismissed_at=dismissed_at,
                    dismissal_kind=w.dismissal_kind,
                    recurrences_after_dismissal=len(after),
                    last_recurrence_at=after[-1],
                ))
        return out

    def review(self) -> CassandraReport:
        """Full review: ignored + vindicated. New vindications append
        to Mnemosyne; duplicates (same slice) skip."""
        report = CassandraReport(started_at=Nyx.now().isoformat())
        report.ignored = self.ignored_warnings()
        report.vindicated = self.vindicated()

        already_recorded = {
            (m.body or {}).get("slice")
            for m in mnemosyne.recall("cassandra.vindicated")
            if (m.body or {}).get("slice")
        }
        for v in report.vindicated:
            if v.slice in already_recorded:
                continue
            mnemosyne.remember(
                kind="cassandra.vindicated",
                actor="cassandra",
                summary=(f"slice {v.slice!r} dismissed ({v.dismissal_kind}); "
                         f"recurred {v.recurrences_after_dismissal} time(s)"),
                **asdict(v),
            )

        mnemosyne.remember(
            kind="cassandra.review",
            actor="cassandra",
            summary=(f"review: {report.total_ignored} ignored, "
                     f"{report.total_vindicated} vindicated"),
            ignored=report.total_ignored,
            vindicated=report.total_vindicated,
        )
        report.ended_at = Nyx.now().isoformat()
        return report


cassandra = Cassandra()
