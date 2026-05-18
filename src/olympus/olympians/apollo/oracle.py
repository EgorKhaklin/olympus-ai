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
        """Run verify() on the named prediction; record the outcome."""
        p = self._predictions.get(name)
        if p is None:
            return None
        if p.verify is None:
            return None
        try:
            outcome = bool(p.verify())
        except Exception as exc:
            p.evidence["verify_error"] = f"{type(exc).__name__}: {exc}"
            return None
        p.accepted = outcome
        return outcome

    def acceptance_rate(self) -> float | None:
        """Of predictions with a known accepted/rejected outcome, what
        fraction were accepted? Returns None if no predictions have
        been verified yet."""
        verified = [p for p in self._predictions.values() if p.accepted is not None]
        if not verified:
            return None
        return sum(1 for p in verified if p.accepted) / len(verified)


apollo = Apollo()
