"""Atlas — titan condemned to bear the heavens.

In myth: Atlas fought against the Olympians in the Titanomachy. His
punishment was to hold up the celestial sphere on his shoulders for
eternity. He is the embodiment of *carrying load*.

In Olympus he is the **live-state registry**. The substrate has rich
history (Mnemosyne) and rich invariants (Furies, HYDRA, Argos) but no
answer to *"what is in flight right now?"* Sessions register themselves
as borne by Atlas at start; release at end. So do Prometheus passes,
loop iterations, and any long-lived operation.

Storage is Mnemosyne itself — `atlas.bear` and `atlas.release` records.
The live "shoulders" view is computed at read time: any bear without a
matching release is current load. No derived cache, no separate file
to drift from the audit-of-record (S1, S8).

Per Delphi 2026-05-18-missing-figures-arc.md (zero Momus dings).
"""
from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from typing import Any

from olympus.primordials.nyx import Nyx
from olympus.titans.mnemosyne import mnemosyne


@dataclass
class Burden:
    """One operation being carried by Atlas."""
    id: str
    op: str                    # 'session' | 'improvement-pass' | ...
    owner: str                 # the identifier of who initiated it
    started_at: str
    payload: dict[str, Any] = field(default_factory=dict)
    released_at: str = ""      # empty while in flight
    outcome: str = ""          # 'ok' | 'error' | ... after release


@dataclass
class ShoulderReport:
    snapshot_at: str
    current: list[Burden] = field(default_factory=list)
    recently_released: list[Burden] = field(default_factory=list)

    @property
    def current_count(self) -> int: return len(self.current)


# ─────────────────────────────────────────────────────────
# Atlas
# ─────────────────────────────────────────────────────────


class Atlas:
    """The load-bearer. bear() registers a burden; release() marks it
    complete; shoulders() reports current load."""

    def bear(self, op: str, owner: str,
             **payload: Any) -> Burden:
        """Register a new operation as being carried. Returns the
        Burden with a unique id; caller must pass that id to release()."""
        burden_id = uuid.uuid4().hex
        started_at = Nyx.now().isoformat()
        b = Burden(
            id=burden_id, op=op, owner=owner,
            started_at=started_at, payload=dict(payload),
        )
        mnemosyne.remember(
            kind="atlas.bear",
            actor=f"atlas:{op}",
            summary=f"atlas began bearing {op!r} for {owner!r}",
            id=burden_id, op=op, owner=owner,
            started_at=started_at, payload=dict(payload),
        )
        return b

    def release(self, burden_id: str, outcome: str = "ok") -> None:
        """Mark a burden as complete. Atlas no longer carries it.
        Idempotent — releasing an unknown id is a no-op (recorded)."""
        released_at = Nyx.now().isoformat()
        mnemosyne.remember(
            kind="atlas.release",
            actor="atlas",
            summary=f"atlas released burden {burden_id[:12]} ({outcome})",
            id=burden_id, outcome=outcome, released_at=released_at,
        )

    def shoulders(self, recent_releases: int = 5) -> ShoulderReport:
        """What Atlas is currently carrying. Computed at read time:
        any bear without a matching release is in flight."""
        bears = mnemosyne.recall("atlas.bear")
        releases = mnemosyne.recall("atlas.release")

        # Build map of released ids and their final state
        release_by_id: dict[str, dict[str, Any]] = {}
        for r in releases:
            body = r.body or {}
            rid = body.get("id")
            if rid:
                release_by_id[rid] = {
                    "released_at": body.get("released_at",
                                            r.remembered_at),
                    "outcome": body.get("outcome", "ok"),
                }

        report = ShoulderReport(snapshot_at=Nyx.now().isoformat())
        all_burdens: list[Burden] = []
        for m in bears:
            body = m.body or {}
            bid = body.get("id", "")
            b = Burden(
                id=bid,
                op=body.get("op", ""),
                owner=body.get("owner", ""),
                started_at=body.get("started_at", m.remembered_at),
                payload=body.get("payload", {}) or {},
            )
            rel = release_by_id.get(bid)
            if rel is not None:
                b.released_at = rel["released_at"]
                b.outcome = rel["outcome"]
            all_burdens.append(b)

        # Partition: current (no release) vs recently released
        current = [b for b in all_burdens if not b.released_at]
        released = [b for b in all_burdens if b.released_at]
        released.sort(key=lambda x: x.released_at, reverse=True)

        report.current = sorted(current, key=lambda x: x.started_at)
        report.recently_released = released[:recent_releases]
        return report

    # ─────────────────────────────────────────────────────────
    # Context-manager sugar — `with atlas.bearing(...) as b: ...`
    # auto-releases even on exception (records outcome="error").
    # ─────────────────────────────────────────────────────────

    def bearing(self, op: str, owner: str, **payload: Any) -> "_BearingCtx":
        return _BearingCtx(self, op, owner, payload)


class _BearingCtx:
    def __init__(self, atlas: Atlas, op: str, owner: str,
                 payload: dict[str, Any]) -> None:
        self._atlas = atlas
        self._op = op
        self._owner = owner
        self._payload = payload
        self.burden: Burden | None = None

    def __enter__(self) -> Burden:
        self.burden = self._atlas.bear(self._op, self._owner,
                                        **self._payload)
        return self.burden

    def __exit__(self, exc_type, exc, tb) -> None:
        if self.burden is None:
            return
        outcome = "ok" if exc is None else f"error:{exc_type.__name__}"
        self._atlas.release(self.burden.id, outcome=outcome)


atlas = Atlas()
