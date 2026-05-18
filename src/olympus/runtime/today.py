"""olympus.runtime.today — the single-action oracle.

`invoke today` returns ONE concrete operator action based on the
substrate's current state. The dashboard already shows the digest;
this oracle does not summarize, it *picks*.

The decision tree is intentionally simple and explicit. Each layer
checks one signal; the first layer that fires wins.

Per Delphi 2026-05-18-aegis-arc.md.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from olympus.primordials.nyx import Nyx
from olympus.titans.mnemosyne import mnemosyne


@dataclass
class TodaysAction:
    """The one thing the substrate suggests for today."""
    priority: str            # 'urgent' | 'noteworthy' | 'gentle' | 'calm'
    headline: str            # the one-line directive
    detail: str = ""
    drawn_from: list[str] = field(default_factory=list)  # source kinds
    decided_at: str = ""

    def __post_init__(self) -> None:
        if not self.decided_at:
            self.decided_at = Nyx.now().isoformat()


def today() -> TodaysAction:
    """Walk the substrate's recent state; pick ONE action.

    Priority order (first match wins):
      1. Pan in panic → address panic first
      2. Cassandra has unaddressed vindications → re-raise the
         strongest dismissed warning
      3. Hygieia found an incoherence → fix the cross-module gap
      4. Phoenix has a high-confidence rebirth candidate → consider it
      5. Metis has a HIGH-confidence recommendation → tune
      6. Otherwise → the substrate is calm
    """
    # 1. Pan
    try:
        from olympus.olympians.pan import pan
        state = pan.evaluate()
        if state.panicked:
            return TodaysAction(
                priority="urgent",
                headline="Pan is in panic — address the cause first",
                detail=state.detail,
                drawn_from=["pan.transition"],
            )
    except Exception:  # noqa: BLE001
        pass

    # 2. Cassandra vindications
    try:
        vinds = mnemosyne.recall("cassandra.vindicated")
        if vinds:
            # Pick the most-recurrent vindication
            best = max(
                vinds,
                key=lambda m: int((m.body or {}).get(
                    "recurrences_after_dismissal", 0)),
            )
            body = best.body or {}
            slice_ = body.get("slice", "?")
            kind = body.get("dismissal_kind", "?")
            rec = body.get("recurrences_after_dismissal", 0)
            return TodaysAction(
                priority="noteworthy",
                headline=(f"Re-examine the {kind}-dismissed warning on "
                          f"slice {slice_!r} — it recurred {rec}× "
                          f"after dismissal"),
                detail=("Cassandra has vindication evidence for this "
                        "slice. Either re-raise the original proposal "
                        "or document why dismissal is still correct."),
                drawn_from=["cassandra.vindicated"],
            )
    except Exception:  # noqa: BLE001
        pass

    # 3. Hygieia incoherence
    try:
        # Use the most recent hygieia.check record, if any
        recent_checks = mnemosyne.recall("hygieia.check")
        if recent_checks:
            last = recent_checks[-1]
            body = last.body or {}
            if int(body.get("incoherent", 0)) > 0:
                findings = body.get("findings") or []
                incoherent = [f for f in findings
                              if isinstance(f, dict)
                              and f.get("status") == "incoherent"]
                if incoherent:
                    first = incoherent[0]
                    return TodaysAction(
                        priority="noteworthy",
                        headline=(f"Hygieia reports an incoherence: "
                                  f"{first.get('check', '?')}"),
                        detail=first.get("detail", ""),
                        drawn_from=["hygieia.check"],
                    )
    except Exception:  # noqa: BLE001
        pass

    # 4. Phoenix high-confidence rebirth candidate
    try:
        cands = mnemosyne.recall("phoenix.candidate")
        if cands:
            best = max(
                cands,
                key=lambda m: float((m.body or {}).get("confidence", 0.0)),
            )
            body = best.body or {}
            conf = float(body.get("confidence", 0.0))
            if conf >= 0.7:
                kind_str = (body.get("candidate_kind")
                             or body.get("kind", "?"))
                return TodaysAction(
                    priority="gentle",
                    headline=(f"Phoenix suggests rebirth of "
                              f"{body.get('subject', '?')} "
                              f"({kind_str})"),
                    detail=body.get("proposed_action", body.get("reason", "")),
                    drawn_from=["phoenix.candidate"],
                )
    except Exception:  # noqa: BLE001
        pass

    # 5. Metis high-confidence recommendation
    try:
        recs = mnemosyne.recall("metis.advice")
        if recs:
            last = recs[-1]
            body = last.body or {}
            for r in (body.get("recommendations") or []):
                if isinstance(r, dict) and float(r.get("confidence", 0)) >= 0.85:
                    return TodaysAction(
                        priority="gentle",
                        headline=(f"Consider tuning {r.get('parameter', '?')} "
                                  f"from {r.get('current')} → "
                                  f"{r.get('proposed')}"),
                        detail=r.get("rationale", ""),
                        drawn_from=["metis.advice"],
                    )
    except Exception:  # noqa: BLE001
        pass

    # 6. Default — substrate is calm
    return TodaysAction(
        priority="calm",
        headline="The substrate is healthy. Quiet days are good days.",
        detail=("No panic, no vindications worth re-raising, no "
                "incoherences, no high-confidence rebirth candidates "
                "or tuning recommendations."),
        drawn_from=[],
    )


def record(action: TodaysAction) -> None:
    """Persist the action to Mnemosyne (so operator can see what
    `invoke today` has been pointing at over time)."""
    mnemosyne.remember(
        kind="today.action",
        actor="today-oracle",
        summary=f"[{action.priority}] {action.headline[:100]}",
        priority=action.priority,
        headline=action.headline,
        detail=action.detail,
        drawn_from=action.drawn_from,
    )
