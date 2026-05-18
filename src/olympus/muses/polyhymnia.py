"""Polyhymnia — Muse of sacred hymns and meditation.

Polyhymnia inspires hymns to the gods — the reverent, the formal,
the unchanging. In Olympus she serves the constitutional records:
oaths, sacred commitments, the Styx-chain reading.
"""
from __future__ import annotations

from dataclasses import dataclass

from olympus.underworld.styx import styx


@dataclass
class Hymn:
    """A reading of the immutable record. Polyhymnia composes hymns
    by summarizing the Styx oath chain in a fixed liturgical form."""
    total_oaths: int
    intact: bool
    last_oath_ts: str | None
    summary: str


class Polyhymnia:
    """Composer of constitutional readings."""

    def hymn(self) -> Hymn:
        oaths = styx._read_all()
        intact, _ = styx.verify()
        last_ts = oaths[-1]["ts"] if oaths else None
        return Hymn(
            total_oaths=len(oaths),
            intact=intact,
            last_oath_ts=last_ts,
            summary=(
                f"Of {len(oaths)} oath{'s' if len(oaths) != 1 else ''} "
                f"sworn upon Styx, the chain is "
                f"{'intact' if intact else 'broken'}."
            ),
        )


polyhymnia = Polyhymnia()
