"""olympus.runtime.recovery — Hades + Iapetus integration.

When a component reaches the end of its lifecycle (Iapetus.ENDED),
its final state is archived in Hades so it can be inspected later.
This is the canonical "graceful shutdown" pattern.
"""
from __future__ import annotations

from typing import Any

from olympus.titans.iapetus import iapetus, LifecyclePhase
from olympus.underworld.hades import descend
from olympus.titans.mnemosyne import mnemosyne


def retire_component(name: str, final_state: dict[str, Any] | None = None,
                     reason: str = "natural-end") -> None:
    """Move `name` to ENDED, archive `final_state` in Hades, and record
    the retirement in Mnemosyne. Idempotent — safe to call twice on
    a component already ENDED."""
    lc = iapetus.of(name)
    if lc is None:
        lc = iapetus.register(name)
    if lc.phase == LifecyclePhase.ENDED:
        return  # already retired
    if lc.phase == LifecyclePhase.ACTIVE:
        lc.advance_to(LifecyclePhase.QUIESCING)
    lc.advance_to(LifecyclePhase.DORMANT)
    lc.advance_to(LifecyclePhase.ENDED)

    descend(
        name=f"retired--{name}",
        payload={"reason": reason, "final_state": final_state or {}},
    )
    mnemosyne.remember(
        kind="component.retired",
        actor=name,
        summary=f"retired ({reason})",
        component=name, reason=reason,
    )
