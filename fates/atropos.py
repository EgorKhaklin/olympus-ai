"""Atropos — the Inevitable, third of the three Fates.

Atropos cuts the thread when its time has come. Her name means
"unturnable" — her decisions are final. In Olympus she is the
termination primitive: she cleanly ends a component's life and
records the cut in Mnemosyne, so endings are auditable.
"""
from __future__ import annotations

from typing import Callable

from titans.mnemosyne import mnemosyne


class Atropos:
    """Termination primitive. Calls the cleanup callback, then records
    the cut."""

    def cut(self, thread_id: str, cleanup: Callable[[], None] | None = None,
            reason: str = "natural") -> None:
        """End the thread. Calls `cleanup()` first (if provided), then
        records the termination."""
        if cleanup is not None:
            cleanup()
        mnemosyne.remember(
            kind="thread.cut",
            actor="atropos",
            summary=f"cut {thread_id} ({reason})",
            thread_id=thread_id,
            reason=reason,
        )


atropos = Atropos()
cut = atropos.cut
