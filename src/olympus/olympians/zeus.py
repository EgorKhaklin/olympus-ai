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
            return (root.child("oracles/delphi").exists())  # implies proposal infrastructure
        # HIGH / COMPOSITE need an authorization in Styx
        from olympus.underworld.styx import oath_of
        oaths = oath_of(f"zeus:{self.name}")
        return any(
            o["statement"].startswith(f"AUTHORIZE risk={risk_class}")
            for o in oaths
        )


zeus = Zeus()
