"""Argos base — Pheromone + Eye + EyeFinding.

An Eye scans one slice of the substrate and emits EyeFinding records.
The colony serializes findings to Pheromone rows; the colony deposits
those rows; downstream readers aggregate at read time.

Substrate invariants this module supports:
  S2  Eyes are deterministic — given a seed and an immutable substrate,
      the same Eye's scan() always produces the same findings
  S4  Eyes are decentralized — no Eye imports another Eye; no Eye
      reads Pheromone rows other Eyes deposited
"""
from __future__ import annotations

import enum
import hashlib
from dataclasses import dataclass, field, asdict
from typing import Any

from primordials.gaia import root
from primordials.nyx import Nyx


KIND_INFO = "info"
KIND_DRIFT = "drift"
KIND_ALERT = "alert"


@dataclass
class EyeFinding:
    """One emission from one Eye. The colony turns findings into
    Pheromone rows for deposit."""
    eye: str
    slice: str
    kind: str                      # one of KIND_INFO / KIND_DRIFT / KIND_ALERT
    intensity: float = 1.0         # 0.0 .. 10.0; multiplies pheromone weight
    detail: str = ""
    evidence: dict[str, Any] = field(default_factory=dict)


@dataclass
class Pheromone:
    """A deposit on the substrate — what an Eye observed, when. Once
    deposited, pheromones decay; the half-life is read at synthesis
    time."""
    eye: str
    slice: str
    kind: str
    intensity: float
    detail: str
    evidence: dict[str, Any]
    deposited_at: str

    @classmethod
    def from_finding(cls, f: EyeFinding) -> "Pheromone":
        return cls(
            eye=f.eye, slice=f.slice, kind=f.kind,
            intensity=f.intensity, detail=f.detail,
            evidence=dict(f.evidence),
            deposited_at=Nyx.now().isoformat(),
        )

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


class Eye:
    """Base class. Subclasses implement scan() and provide NAME + SLICE.

    The seed is derived deterministically from the class name; if a
    subclass wants reproducible random choices, it can use `self.seed`
    as a Random seed. Eyes that import `random` directly without going
    through self.seed violate S2 and will be caught by the kill test.
    """

    NAME: str = "unnamed-eye"
    SLICE: str = "unspecified"

    @property
    def seed(self) -> int:
        return int(hashlib.sha256(self.NAME.encode("utf-8")).hexdigest()[:8], 16)

    def scan(self) -> list[EyeFinding]:
        """Override. Return a list of findings. Do not modify any state."""
        raise NotImplementedError

    def _read(self, *parts: str) -> str:
        p = root.child(*parts)
        if not p.exists():
            return ""
        return p.read_text(encoding="utf-8")

    def _finding(self, kind: str, detail: str, *,
                 intensity: float = 1.0,
                 **evidence: Any) -> EyeFinding:
        return EyeFinding(
            eye=self.NAME, slice=self.SLICE, kind=kind,
            intensity=intensity, detail=detail, evidence=evidence,
        )
