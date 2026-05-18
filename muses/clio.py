"""Clio — Muse of history.

Clio holds the scrolls of history. In Olympus she writes and reads
the chronicle: the daily journal where decisions, learnings, and
shipped work are noted.
"""
from __future__ import annotations

import pathlib

from primordials.gaia import root
from primordials.nyx import Nyx


class Clio:
    """Reader and writer of codex/journal/."""

    JOURNAL = "codex/journal"

    def __init__(self) -> None:
        self.journal_path = root.child(self.JOURNAL)
        self.journal_path.mkdir(parents=True, exist_ok=True)

    def _today_file(self) -> pathlib.Path:
        return self.journal_path / f"{Nyx.now().strftime('%Y-%m-%d')}.md"

    def inscribe(self, kind: str, text: str) -> pathlib.Path:
        """Append a line to today's journal under a `kind` (decision/
        learning/observation/etc.)."""
        f = self._today_file()
        if not f.exists():
            f.write_text(f"# {Nyx.now().strftime('%Y-%m-%d')}\n\n", encoding="utf-8")
        with f.open("a", encoding="utf-8") as fh:
            ts = Nyx.now().strftime("%H:%M")
            fh.write(f"- **{kind}** {ts} — {text}\n")
        return f

    def days(self) -> list[pathlib.Path]:
        return sorted(self.journal_path.glob("*.md"))


clio = Clio()
