"""Charon — ferryman of the dead.

In myth: Charon ferried the souls of the recently dead across the
rivers Styx and Acheron into Hades's realm, in exchange for an obol
placed on the corpse's tongue. He carried no one without payment,
and he carried no one twice.

In Olympus, Charon performs **safe migration between active and
archive**. Atlas burdens released longer ago than the retention window
get ferried to Hades. Released-burden Mnemosyne records older than the
cutoff also get archived (the originals stay — Charon does not destroy
the audit-of-record; he copies-then-marks).

Idempotent by construction:
  - Each passage records `kind="charon.crossing"` with the burden id.
  - On re-run, Charon reads the crossing log and skips anything
    already ferried.

Charon never edits source, never amends the constitution. He moves
shades; he does not invent them.

Per Delphi 2026-05-18-compass-rose-arc.md.
"""
from __future__ import annotations

import datetime
from dataclasses import dataclass, field
from typing import Any

from olympus.primordials.nyx import Nyx
from olympus.titans.mnemosyne import mnemosyne
from olympus.underworld.hades import hades


@dataclass
class Crossing:
    """One ferrying — a burden moved from active to archive."""
    burden_id: str
    op: str
    age_days: float
    archived_to: str
    crossed_at: str = ""

    def __post_init__(self) -> None:
        if not self.crossed_at:
            self.crossed_at = Nyx.now().isoformat()


@dataclass
class FerryReport:
    started_at: str
    ended_at: str = ""
    retention_days: float = 30.0
    crossings: list[Crossing] = field(default_factory=list)
    skipped_already_ferried: int = 0
    candidates_considered: int = 0

    @property
    def total_ferried(self) -> int:
        return len(self.crossings)


class Charon:
    """The ferryman. Idempotent archive migration of released burdens."""

    DEFAULT_RETENTION_DAYS = 30.0

    def __init__(self,
                 retention_days: float | None = None) -> None:
        self.retention_days = (retention_days if retention_days is not None
                               else self.DEFAULT_RETENTION_DAYS)

    def _already_ferried(self) -> set[str]:
        """Set of burden ids already ferried, from `charon.crossing`."""
        out: set[str] = set()
        for m in mnemosyne.recall("charon.crossing"):
            bid = (m.body or {}).get("burden_id", "")
            if bid:
                out.add(bid)
        return out

    def _released_burdens_payload(self) -> list[dict[str, Any]]:
        """Each released-burden snapshot suitable for archiving."""
        bears = mnemosyne.recall("atlas.bear")
        releases = mnemosyne.recall("atlas.release")
        release_by_id: dict[str, dict[str, Any]] = {}
        for r in releases:
            body = r.body or {}
            rid = body.get("id")
            if rid:
                release_by_id[rid] = {
                    "released_at": body.get("released_at", r.remembered_at),
                    "outcome": body.get("outcome", "ok"),
                }

        out: list[dict[str, Any]] = []
        for b in bears:
            body = b.body or {}
            bid = body.get("id", "")
            rel = release_by_id.get(bid)
            if rel is None:
                continue  # still in flight — leave alone
            out.append({
                "id": bid,
                "op": body.get("op", ""),
                "owner": body.get("owner", ""),
                "started_at": body.get("started_at", b.remembered_at),
                "released_at": rel["released_at"],
                "outcome": rel["outcome"],
                "payload": body.get("payload", {}),
            })
        return out

    def ferry(self, retention_days: float | None = None) -> FerryReport:
        """Ferry burdens released longer than retention_days to Hades.
        Idempotent."""
        if retention_days is None:
            retention_days = self.retention_days
        now = Nyx.now()
        cutoff = now - datetime.timedelta(days=retention_days)
        report = FerryReport(
            started_at=now.isoformat(),
            retention_days=retention_days,
        )
        already = self._already_ferried()

        for snap in self._released_burdens_payload():
            report.candidates_considered += 1
            try:
                released = datetime.datetime.fromisoformat(snap["released_at"])
            except (ValueError, TypeError):
                continue
            if released > cutoff:
                continue  # too fresh; leave it
            if snap["id"] in already:
                report.skipped_already_ferried += 1
                continue

            age = (now - released).total_seconds() / 86400.0
            target = hades.descend(
                name=f"atlas-burden--{snap['op']}--{snap['id']}",
                payload=snap,
            )
            crossing = Crossing(
                burden_id=snap["id"],
                op=snap["op"],
                age_days=age,
                archived_to=target.as_posix(),
            )
            report.crossings.append(crossing)
            mnemosyne.remember(
                kind="charon.crossing",
                actor="charon",
                summary=(f"ferried {snap['op']!r} burden {snap['id'][:12]} "
                         f"(aged {age:.1f}d) → Hades"),
                burden_id=crossing.burden_id,
                op=crossing.op,
                age_days=crossing.age_days,
                archived_to=crossing.archived_to,
            )

        report.ended_at = Nyx.now().isoformat()
        mnemosyne.remember(
            kind="charon.ferry-pass",
            actor="charon",
            summary=(f"ferry pass: {report.total_ferried} crossing(s), "
                     f"{report.skipped_already_ferried} already-ferried "
                     f"skipped (retention {retention_days}d)"),
            ferried=report.total_ferried,
            considered=report.candidates_considered,
            retention_days=retention_days,
        )
        return report


charon = Charon()
