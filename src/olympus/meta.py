"""olympus.meta — Olympus reasoning about Olympus.

The self-referential surface. When you ask "what is Olympus doing
right now, structurally?", this is where the question is answered.

Built from the existing tiers — Coeus poses the question, Theseus
walks the labyrinth, Urania charts the constellations, Polyhymnia
hymns the oath chain. Meta just composes them.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from olympus.primordials.nyx import Nyx


@dataclass
class SelfPortrait:
    composed_at: str
    tiers: dict[str, int]
    hydra_heads: dict[str, str]   # head_name → "mortal" | "immortal"
    argos_eyes: list[str]
    invariants: list[dict[str, Any]]
    styx_summary: str
    recent_sessions: list[dict[str, Any]] = field(default_factory=list)
    pending_actions: int = 0
    delphi_pending: int = 0
    last_brief: dict[str, Any] | None = None

    def as_text(self) -> str:
        lines: list[str] = []
        lines.append(f"# Olympus self-portrait — {self.composed_at}")
        lines.append("")
        lines.append("## Population")
        for tier, count in self.tiers.items():
            lines.append(f"  - {tier}: {count} modules")
        lines.append("")
        lines.append("## HYDRA heads")
        for name, kind in self.hydra_heads.items():
            lines.append(f"  - {name}  ({kind})")
        lines.append("")
        lines.append(f"## Argos eyes ({len(self.argos_eyes)})")
        for name in self.argos_eyes:
            lines.append(f"  - {name}")
        lines.append("")
        lines.append("## Substrate invariants")
        for inv in self.invariants:
            lines.append(f"  - **{inv['id']}** {inv['name']}")
        lines.append("")
        lines.append(f"## Styx — {self.styx_summary}")
        lines.append("")
        lines.append(f"## Actions: {self.pending_actions} pending · "
                     f"{self.delphi_pending} delphi-pending")
        if self.recent_sessions:
            lines.append("")
            lines.append("## Recent sessions")
            for s in self.recent_sessions[:5]:
                lines.append(f"  - {s.get('remembered_at', '?')[:19]}  {s.get('summary', '')}")
        return "\n".join(lines)


def portrait() -> SelfPortrait:
    """Compose the current self-portrait. Reads from the live substrate;
    every value is derived, never cached."""
    from olympus.titans.coeus import coeus
    from olympus.monsters.hydra.host import hydra
    from olympus.monsters.argos.colony import colony
    from olympus.titans.themis import themis
    from olympus.muses.polyhymnia import polyhymnia
    from olympus.titans.mnemosyne import mnemosyne
    from olympus.action import action_queue

    tiers = coeus.ask("pantheon-population")
    hydra_heads = {
        h.NAME: "immortal" if h.IMMORTAL else "mortal"
        for h in hydra.heads()
    }
    argos_eyes = [e.NAME for e in colony.eyes()]
    invariants = [
        {"id": inv.id, "name": inv.name, "statement": inv.statement}
        for inv in themis.all()
    ]
    hymn = polyhymnia.hymn()

    recent_sessions = [
        {"remembered_at": m.remembered_at, "summary": m.summary}
        for m in reversed(mnemosyne.recall("session.completed"))
    ]

    return SelfPortrait(
        composed_at=Nyx.now().isoformat(),
        tiers=tiers,
        hydra_heads=hydra_heads,
        argos_eyes=argos_eyes,
        invariants=invariants,
        styx_summary=hymn.summary,
        recent_sessions=recent_sessions,
        pending_actions=len(action_queue.pending()),
        delphi_pending=len(action_queue.delphi_pending()),
    )
