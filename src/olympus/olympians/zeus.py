"""Zeus — king of the gods, wielder of thunder.

Zeus sits above the pantheon. He is the operator: the human (or
authority) on whose behalf Olympus runs. The agent serves Zeus; Zeus
serves no one inside this system.

This module is Zeus's interface — the way the rest of the pantheon
checks "did the operator authorize this?" and the way the operator
issues directives that bind the pantheon.
"""
from __future__ import annotations

import os
import pathlib
from dataclasses import dataclass

from olympus.primordials.gaia import root
from olympus.underworld.styx import swear


@dataclass(frozen=True)
class Directive:
    """An authorization Zeus has issued. Stored in Styx (immutable)."""
    quote: str               # exact words used
    risk_class: str          # LOW / MEDIUM / HIGH / COMPOSITE
    scope: str               # what it authorizes
    issued_at: str           # ISO timestamp


class Zeus:
    """The operator interface."""

    def __init__(self) -> None:
        self.name = os.environ.get("OLYMPUS_OPERATOR", "Zeus")

    @property
    def present(self) -> bool:
        """Is Zeus available to consult? Returns True if running
        interactively (a TTY is attached)."""
        return os.isatty(0) if hasattr(os, "isatty") else False

    def authorize(self, quote: str, risk_class: str, scope: str) -> Directive:
        """Record an authorization. Risk class must be LOW/MEDIUM/HIGH/COMPOSITE.
        Authorizations are sworn on Styx — once made, immutable.
        """
        risk_class = risk_class.upper()
        if risk_class not in {"LOW", "MEDIUM", "HIGH", "COMPOSITE"}:
            raise ValueError(f"unknown risk class: {risk_class!r}")
        oath = swear(
            sworn_by=f"zeus:{self.name}",
            statement=f"AUTHORIZE risk={risk_class} scope={scope!r}",
            payload={"quote": quote, "risk_class": risk_class, "scope": scope},
        )
        return Directive(
            quote=quote, risk_class=risk_class, scope=scope,
            issued_at=oath.ts,
        )

    def can_perform(self, risk_class: str) -> bool:
        """LOW is always permitted. MEDIUM requires a proposal record.
        HIGH and COMPOSITE require an explicit Zeus authorization in
        Styx."""
        risk_class = risk_class.upper()
        if risk_class == "LOW":
            return True
        if risk_class == "MEDIUM":
            return root.child("codex", "oracles", "delphi").exists()
        # HIGH / COMPOSITE need an authorization in Styx
        from olympus.underworld.styx import oath_of
        oaths = oath_of(f"zeus:{self.name}")
        return any(
            o["statement"].startswith(f"AUTHORIZE risk={risk_class}")
            for o in oaths
        )

    # ─────────────────────────────────────────────────────────
    # Operator console — review + ratify pending actions
    # ─────────────────────────────────────────────────────────

    def review_pending(self) -> list:
        """List actions awaiting Zeus's ratification."""
        from olympus.action import action_queue
        return action_queue.pending()

    def review_delphi(self) -> list:
        """List actions awaiting HIGH / COMPOSITE Delphi."""
        from olympus.action import action_queue
        return action_queue.delphi_pending()

    def ratify(self, action_id: str, quote: str):
        """Approve a queued or delphi-pending action with an authorization quote."""
        from olympus.action import action_queue
        return action_queue.ratify(action_id, quote=quote, by=f"zeus:{self.name}")

    def reject(self, action_id: str, reason: str):
        """Reject a queued action with a recorded reason."""
        from olympus.action import action_queue
        return action_queue.reject(action_id, reason=reason, by=f"zeus:{self.name}")

    def console(self) -> int:
        """Tiny interactive REPL for review/ratify/reject. Returns the
        number of actions Zeus touched. Intended for short operator
        sessions, not long-running interaction."""
        from olympus.action import action_queue
        from olympus.olympians.aphrodite import aphrodite
        from olympus.graces.aglaia import aglaia

        touched = 0
        while True:
            pending = action_queue.pending()
            delphi = action_queue.delphi_pending()
            print(aglaia.section(f"Zeus console — {len(pending)} queued, {len(delphi)} delphi-pending"))

            if not pending and not delphi:
                print(aglaia.murmur("  no actions await Zeus."))
                break

            all_actions = pending + delphi
            rows = [(a.id[:24], a.risk_class, a.status, a.summary[:80]) for a in all_actions]
            print(aphrodite.table(("id", "risk", "status", "summary"), rows))

            try:
                cmd = input("\n  ratify <id> | reject <id> <reason> | q : ").strip()
            except (KeyboardInterrupt, EOFError):
                print()
                break
            if cmd == "q" or not cmd:
                break
            parts = cmd.split(maxsplit=2)
            verb = parts[0]
            if verb == "ratify" and len(parts) >= 2:
                aid = parts[1]
                quote = parts[2] if len(parts) > 2 else "ratified at console"
                # accept prefix-match on id
                full = next((a.id for a in all_actions if a.id.startswith(aid)), None)
                if full is None:
                    print(aphrodite.wine_dark(f"  no action matches {aid!r}"))
                    continue
                self.ratify(full, quote=quote)
                print(aphrodite.laurel(f"  ratified {full[:24]}"))
                touched += 1
            elif verb == "reject" and len(parts) >= 2:
                aid = parts[1]
                reason = parts[2] if len(parts) > 2 else "rejected at console"
                full = next((a.id for a in all_actions if a.id.startswith(aid)), None)
                if full is None:
                    print(aphrodite.wine_dark(f"  no action matches {aid!r}"))
                    continue
                self.reject(full, reason=reason)
                print(aphrodite.laurel(f"  rejected {full[:24]}"))
                touched += 1
            else:
                print(aphrodite.wine_dark(f"  unknown command: {cmd!r}"))
        return touched


zeus = Zeus()
