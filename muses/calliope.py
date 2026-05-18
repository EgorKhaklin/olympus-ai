"""Calliope — Muse of epic poetry; chief among the Muses.

Calliope inspired Homer. Her domain is long-form narrative: the codex.
In Olympus she lists and surfaces the long-form documents in codex/.
"""
from __future__ import annotations

import pathlib
from dataclasses import dataclass

from primordials.gaia import root


@dataclass
class Volume:
    path: pathlib.Path
    title: str
    word_count: int


class Calliope:
    """Reader of the codex."""

    CODEX = "codex"

    def volumes(self) -> list[Volume]:
        path = root.child(self.CODEX)
        if not path.exists():
            return []
        vols: list[Volume] = []
        for f in sorted(path.glob("*.md")):
            text = f.read_text(encoding="utf-8")
            first_h1 = next(
                (line[2:].strip() for line in text.splitlines() if line.startswith("# ")),
                f.stem,
            )
            vols.append(Volume(
                path=f, title=first_h1, word_count=len(text.split()),
            ))
        return vols


calliope = Calliope()
