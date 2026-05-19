"""Zeus's Throne (Διὸς θρόνος) — the unified conversational front door.

In Greek antiquity: the seat from which Zeus governed Olympus. Every
petition was heard here, every decision rendered here. Operationally:
one place to ask, one place to act.

Per Delphi 2026-05-19-throne-arc.md.

Public API:

    from olympus.throne import Throne, throne, ThroneResponse, Turn

    t = throne()                       # singleton (uses default bridge)
    r = t.respond("how's it going?")   # one turn
    print(r.answer)                    # plain-English synthesis
    print(r.actions_taken)             # ["doctor"]
    print(r.suggested_command)         # None (or "invoke action ratify X")

Constitutional posture:
  - S1: every turn → mnemosyne.remember("throne.turn", ...)
  - S6: every answer cites the errand(s) invoked
  - S7: HIGH-risk actions REFUSED; Throne returns suggested_command instead
  - AP1/AP3/AP7/AP8: Throne is glue (~400 LOC), not a new figure
"""
from __future__ import annotations

from olympus.throne.throne import (
    Throne, ThroneResponse, Turn, throne,
)
from olympus.throne.router import (
    SAFE_ERRANDS, GATED_ERRANDS, Action,
    DirectAnswer, RunErrands, RequiresOperator,
)

__all__ = [
    "Throne", "ThroneResponse", "Turn", "throne",
    "SAFE_ERRANDS", "GATED_ERRANDS",
    "Action", "DirectAnswer", "RunErrands", "RequiresOperator",
]
