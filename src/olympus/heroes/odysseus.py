"""Odysseus — hero of the long return.

Odysseus's voyage home took ten years. He survived because he
remembered. In Olympus, Odysseus is the long-session persona — the
agent's facility for picking up an interrupted task across a session
boundary. He reads Mnemosyne to learn where the agent was.
"""
from __future__ import annotations

from dataclasses import dataclass

from olympus.titans.mnemosyne import mnemosyne


@dataclass
class Bearing:
    """Where the agent was when last seen."""
    last_kind: str | None
    last_summary: str | None
    total_memories: int


class Odysseus:
    """Session-resume helper."""

    def take_bearing(self) -> Bearing:
        """Read Mnemosyne; return the most recent memory across all kinds."""
        all_kinds = mnemosyne.kinds()
        latest_kind: str | None = None
        latest_summary: str | None = None
        latest_ts = ""
        total = 0
        for kind in all_kinds:
            memories = mnemosyne.recall(kind)
            total += len(memories)
            if memories:
                last = memories[-1]
                if last.remembered_at > latest_ts:
                    latest_ts = last.remembered_at
                    latest_kind = last.kind
                    latest_summary = last.summary
        return Bearing(
            last_kind=latest_kind,
            last_summary=latest_summary,
            total_memories=total,
        )


odysseus = Odysseus()
