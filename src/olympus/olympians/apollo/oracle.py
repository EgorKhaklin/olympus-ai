"""Apollo's oracle — registry of falsifiable predictions.

Each Prediction has:
  - a name
  - a horizon (when the prediction is testable)
  - a `verify()` callable that returns True if the prediction held

S5 substrate invariant: every Prediction MUST carry `verify()`.
"""
from __future__ import annotations

import datetime
from dataclasses import dataclass, field
from typing import Callable, Any


@dataclass
class Prediction:
    name: str
    statement: str
    horizon: datetime.date            # when this becomes testable
    verify: Callable[[], bool] | None # MUST be callable for S5 compliance
    issued_at: str = ""
    accepted: bool | None = None      # None until verified
    evidence: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.issued_at:
            from olympus.primordials.nyx import Nyx
            self.issued_at = Nyx.now().isoformat()


class Apollo:
    """Predicate registry."""

    def __init__(self) -> None:
        self._predictions: dict[str, Prediction] = {}

    def predict(self, p: Prediction) -> Prediction:
        """Register a prediction. Refuses if verify() is None (S5)."""
        if p.verify is None:
            raise ValueError(
                f"S5 violation: prediction {p.name!r} has no verify()"
            )
        self._predictions[p.name] = p
        return p

    def predictions(self) -> list[Prediction]:
        return list(self._predictions.values())

    def by_name(self, name: str) -> Prediction | None:
        return self._predictions.get(name)

    def consult(self, name: str) -> bool | None:
        """Run verify() on the named prediction; record the outcome.
        Also writes the outcome to Mnemosyne so it's reconstructible."""
        p = self._predictions.get(name)
        if p is None:
            return None
        if p.verify is None:
            return None
        try:
            outcome = bool(p.verify())
        except Exception as exc:
            p.evidence["verify_error"] = f"{type(exc).__name__}: {exc}"
            self._remember_outcome(p, accepted=None,
                                    error=p.evidence["verify_error"])
            return None
        p.accepted = outcome
        self._remember_outcome(p, accepted=outcome)
        return outcome

    def consult_due(self) -> list[dict[str, Any]]:
        """Auto-verify every prediction whose horizon has passed and
        whose outcome has not yet been recorded. Returns a list of
        per-prediction result dicts. Called at session start so prophecy
        becomes operational, not just declarative."""
        import datetime as _dt
        today = _dt.date.today()
        results: list[dict[str, Any]] = []
        for p in self._predictions.values():
            if p.accepted is not None:
                continue  # already verified
            if p.horizon > today:
                continue  # horizon not yet reached
            outcome = self.consult(p.name)
            results.append({
                "name": p.name,
                "horizon": p.horizon.isoformat(),
                "outcome": outcome,
            })
        return results

    def acceptance_rate(self) -> float | None:
        """Of predictions with a known accepted/rejected outcome, what
        fraction were accepted? Returns None if no predictions have
        been verified yet."""
        verified = [p for p in self._predictions.values() if p.accepted is not None]
        if not verified:
            return None
        return sum(1 for p in verified if p.accepted) / len(verified)

    def trend(self, *, window: int = 10) -> dict[str, Any]:
        """Acceptance-rate trend over the last `window` verified predictions.
        Useful for Hephaestus risk weighting (low-acceptance domain →
        higher proposal risk)."""
        from olympus.titans.mnemosyne import mnemosyne
        outcomes = mnemosyne.recall("prophecy.verified")[-window:]
        if not outcomes:
            return {"window": window, "count": 0, "accepted": 0,
                    "rejected": 0, "rate": None}
        accepted = sum(1 for m in outcomes if m.body.get("accepted") is True)
        rejected = sum(1 for m in outcomes if m.body.get("accepted") is False)
        total = accepted + rejected
        return {
            "window": window,
            "count": len(outcomes),
            "accepted": accepted,
            "rejected": rejected,
            "rate": (accepted / total) if total else None,
        }

    def _remember_outcome(self, p: Prediction, *,
                          accepted: bool | None, error: str | None = None) -> None:
        """Apollo writes verification outcomes to Mnemosyne so the
        agent's prediction history is reconstructible (S8)."""
        from olympus.titans.mnemosyne import mnemosyne
        if accepted is None:
            summary = f"prophecy {p.name!r} verify() raised: {error}"
        else:
            summary = (f"prophecy {p.name!r} verified "
                       f"{'ACCEPTED' if accepted else 'REJECTED'}")
        mnemosyne.remember(
            kind="prophecy.verified",
            actor="apollo",
            summary=summary,
            prediction=p.name,
            statement=p.statement,
            horizon=p.horizon.isoformat(),
            accepted=accepted,
            error=error,
        )


apollo = Apollo()
