"""Tisiphone — avenger of murder, youngest of the Furies.

Tisiphone pursued those who shed kin's blood. In Olympus she enforces
data-integrity: she validates checksums, manifests, and the
Styx-oath chain. When integrity is broken, she names exactly which
record was murdered.
"""
from __future__ import annotations

from dataclasses import dataclass

from underworld.styx import styx


@dataclass
class Verdict:
    intact: bool
    first_bad_seq: int | None
    detail: str


class Tisiphone:
    """Integrity verification."""

    def verify_styx(self) -> Verdict:
        """Re-hash the Styx chain. Returns intact + first bad seq."""
        intact, bad_seq = styx.verify()
        if intact:
            return Verdict(intact=True, first_bad_seq=None,
                           detail="styx chain is intact")
        return Verdict(
            intact=False, first_bad_seq=bad_seq,
            detail=f"styx chain tampered at seq={bad_seq}",
        )


tisiphone = Tisiphone()
