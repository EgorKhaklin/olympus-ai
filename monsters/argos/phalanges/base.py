"""Phalanx base — a named formation of Eyes advancing as one.

A Phalanx holds references to Eye classes (not instances). When the
colony deploys a Phalanx, it instantiates the Eyes and dispatches
their scans."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Type

from monsters.argos.base import Eye, EyeFinding


@dataclass
class Phalanx:
    name: str
    concern: str                       # one-line description
    eye_classes: list[Type[Eye]] = field(default_factory=list)

    def advance(self) -> list[EyeFinding]:
        """Run every Eye in the formation; collect findings."""
        out: list[EyeFinding] = []
        for cls in self.eye_classes:
            try:
                out.extend(cls().scan())
            except Exception as exc:
                out.append(EyeFinding(
                    eye=cls.NAME, slice=cls.SLICE,
                    kind="alert", intensity=10.0,
                    detail=f"phalanx-deploy raised: {type(exc).__name__}: {exc}",
                ))
        return out
