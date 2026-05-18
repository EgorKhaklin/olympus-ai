"""Alecto — the unceasing, eldest of the Furies.

Alecto's anger never tires. In Olympus she is the invariant-failure
alerter: when a Themis-defined substrate invariant breaks, Alecto
emits an alert that cannot be silently dropped. The alert is recorded
in Mnemosyne and shouted on Poseidon's "furies.alecto" stream.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from olympus.olympians.poseidon import poseidon
from olympus.titans.mnemosyne import mnemosyne


@dataclass
class Alert:
    invariant_id: str
    detail: str
    evidence: Any
    raised_at: str


class Alecto:
    """Invariant-violation alerter."""

    STREAM = "furies.alecto"

    def raise_alert(self, invariant_id: str, detail: str, evidence: Any = None) -> Alert:
        """Sound the unceasing alarm. Recorded forever; broadcast now."""
        from olympus.primordials.nyx import Nyx
        a = Alert(
            invariant_id=invariant_id,
            detail=detail,
            evidence=evidence,
            raised_at=Nyx.now().isoformat(),
        )
        mnemosyne.remember(
            kind="invariant.violated",
            actor="alecto",
            summary=f"{invariant_id}: {detail}",
            invariant_id=invariant_id,
            evidence=evidence,
        )
        poseidon.publish(self.STREAM, a)
        return a


alecto = Alecto()
