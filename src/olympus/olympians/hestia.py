"""Hestia — goddess of the hearth, the sacred boundary.

Hestia tended the hearth-fire at the center of every Greek home, and
the central fire at Delphi. She gave up her Olympian seat to Dionysus
to keep the peace, but kept her place at the hearth. In Olympus,
Hestia is the boundary primitive: she defines what is *inside* the
project (sacred, defended) and what is *outside* (open).

The hearth-fire is also identity. A new Olympus deployment lights its
hearth via `hestia.kindle()` once, recording its identity-seal.
"""
from __future__ import annotations

import json
import pathlib
import secrets
from dataclasses import dataclass, asdict

from olympus.primordials.gaia import root
from olympus.primordials.nyx import Nyx


@dataclass
class Hearth:
    name: str               # what this Olympus is called
    kindled_at: str         # ISO ts of first lighting
    seal: str               # cryptographic identity of this deployment
    vocation: str           # one-sentence statement of purpose


class Hestia:
    """Keeper of the hearth-fire. One per deployment."""

    HEARTH_FILE = "state/hestia_hearth.json"

    def __init__(self, hearth_path: pathlib.Path | None = None) -> None:
        self.hearth_path = hearth_path or root.child(self.HEARTH_FILE)
        self.hearth_path.parent.mkdir(parents=True, exist_ok=True)

    def is_lit(self) -> bool:
        return self.hearth_path.exists()

    def kindle(self, name: str, vocation: str) -> Hearth:
        """Light the hearth. If already lit, refuses (Hestia's fire is lit
        once, not relit)."""
        if self.is_lit():
            raise RuntimeError(
                "Hestia's hearth is already lit. To re-kindle, "
                "extinguish first (extinguish_hearth() requires Zeus authorization)."
            )
        h = Hearth(
            name=name,
            kindled_at=Nyx.now().isoformat(),
            seal=secrets.token_hex(16),
            vocation=vocation,
        )
        with self.hearth_path.open("w", encoding="utf-8") as f:
            json.dump(asdict(h), f, indent=2)
        return h

    def hearth(self) -> Hearth | None:
        if not self.is_lit():
            return None
        with self.hearth_path.open("r", encoding="utf-8") as f:
            d = json.load(f)
        return Hearth(**d)


hestia = Hestia()
