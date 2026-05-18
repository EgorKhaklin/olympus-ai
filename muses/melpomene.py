"""Melpomene — Muse of tragedy.

Melpomene's mask weeps. In Olympus she records post-mortems and
failure analyses — the structured artifact written after something
went wrong, naming what was lost and what was learned.
"""
from __future__ import annotations

import pathlib
from dataclasses import dataclass

from primordials.gaia import root
from primordials.nyx import Nyx


@dataclass
class PostMortem:
    title: str
    timeline: str
    root_cause: str
    lessons: list[str]


class Melpomene:
    POSTMORTEMS = "codex/postmortems"

    def __init__(self) -> None:
        self.path = root.child(self.POSTMORTEMS)
        self.path.mkdir(parents=True, exist_ok=True)

    def record(self, pm: PostMortem) -> pathlib.Path:
        ts = Nyx.now().strftime("%Y-%m-%d")
        slug = "".join(c if c.isalnum() else "-" for c in pm.title.lower())[:80]
        f = self.path / f"{ts}--{slug}.md"
        text = (
            f"# {pm.title}\n\n"
            f"_Recorded: {Nyx.now().isoformat()}_\n\n"
            f"## Timeline\n\n{pm.timeline}\n\n"
            f"## Root cause\n\n{pm.root_cause}\n\n"
            f"## Lessons\n\n"
            + "\n".join(f"- {l}" for l in pm.lessons)
            + "\n"
        )
        f.write_text(text, encoding="utf-8")
        return f


melpomene = Melpomene()
