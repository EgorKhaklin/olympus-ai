"""Hades — king of the underworld, keeper of what is no longer active.

Hades was not death itself; he was the *ruler of the dead*. The shades
in his realm were not erased — they were stored, named, and could be
visited (rarely) by the living. Olympus's Hades is the archive: the
place inactive artifacts go where they remain inspectable, never
deleted, but no longer in the main flow.

`descend(name, payload)` archives a record under `underworld/hades/`.
`ascend(name)` retrieves it. Neither operation modifies the original.
"""
from __future__ import annotations

import json
import pathlib
import re
from typing import Any

from olympus.primordials.gaia import root
from olympus.primordials.nyx import Nyx


class Hades:
    """The archive. Append-only, indexed by name."""

    REALM = "state/hades"

    def __init__(self, realm_path: pathlib.Path | None = None) -> None:
        self.realm_path = realm_path or root.child(self.REALM)
        self.realm_path.mkdir(parents=True, exist_ok=True)

    @staticmethod
    def _slug(name: str) -> str:
        return re.sub(r"[^a-zA-Z0-9._-]+", "_", name)[:120]

    def descend(self, name: str, payload: Any) -> pathlib.Path:
        """Archive `payload` under `name`. Returns the path."""
        slug = self._slug(name)
        ts = Nyx.now().strftime("%Y%m%dT%H%M%SZ")
        target = self.realm_path / f"{ts}--{slug}.json"
        with target.open("w", encoding="utf-8") as f:
            json.dump({"name": name, "ts": ts, "payload": payload}, f, indent=2, default=str)
        return target

    def ascend(self, name: str) -> list[dict[str, Any]]:
        """Recall all shades archived under `name`. Most recent first."""
        slug = self._slug(name)
        shades: list[dict[str, Any]] = []
        for f in sorted(self.realm_path.glob(f"*--{slug}.json"), reverse=True):
            with f.open("r", encoding="utf-8") as fh:
                shades.append(json.load(fh))
        return shades

    def population(self) -> int:
        """Count of shades currently in the realm."""
        return sum(1 for _ in self.realm_path.glob("*.json"))


hades = Hades()
descend = hades.descend
ascend = hades.ascend
