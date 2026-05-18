"""Satyr base — the wild-companion observer pattern.

A Satyr is like an Eye but lower-cadence and tied to a concrete check.
Where an Eye returns structured findings for the colony, a Satyr
answers yes/no plus a brief reason.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass
class Sighting:
    satyr: str
    ok: bool
    detail: str


class Satyr:
    NAME: str = "unnamed-satyr"

    def look(self) -> Sighting:
        raise NotImplementedError
