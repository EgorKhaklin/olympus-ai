"""Clotho — the Spinner, first of the three Fates.

Clotho spins the thread of life from her spindle. In Olympus she is
the creation primitive: she calls on Eros (primordial generation) to
mint new ids, and records each new thread in Mnemosyne so the lifecycle
is auditable from birth.
"""
from __future__ import annotations

from dataclasses import dataclass

from primordials.eros import Eros
from titans.mnemosyne import mnemosyne


@dataclass
class Thread:
    """A spun thread — one component's lifecycle handle."""
    id: str
    kind: str               # what kind of thing it is
    spun_for: str           # purpose / owner


class Clotho:
    def spin(self, kind: str, spun_for: str, seed: str | None = None) -> Thread:
        """Spin a new thread. If `seed` is given, the id is deterministic."""
        if seed is None:
            tid = Eros.fresh_id(kind)
        else:
            tid = Eros.begotten_id(kind, seed)
        thread = Thread(id=tid, kind=kind, spun_for=spun_for)
        mnemosyne.remember(
            kind="thread.spun",
            actor="clotho",
            summary=f"spun {kind} for {spun_for}",
            thread_id=tid,
        )
        return thread


clotho = Clotho()
spin = clotho.spin
