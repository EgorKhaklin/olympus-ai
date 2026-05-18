"""Hermes — messenger of the gods, conductor of souls.

Hermes is fast, cunning, and crosses every boundary — the only god who
moves freely between Olympus, earth, and the underworld. In Olympus,
Hermes is the communication primitive: the CLI dispatch surface, the
inter-module messenger, the bridge between the operator and the
pantheon.

Every CLI command goes through Hermes. He routes it to the right deity.
"""
from __future__ import annotations

import sys
from dataclasses import dataclass
from typing import Callable, Any


@dataclass
class Errand:
    """A registered command Hermes can run."""
    name: str
    summary: str
    fn: Callable[[list[str]], int]      # argv → exit code


class Hermes:
    """CLI dispatcher. Registers errands, runs them on demand."""

    def __init__(self) -> None:
        self._errands: dict[str, Errand] = {}

    def register(self, name: str, summary: str) -> Callable[[Callable], Callable]:
        """Decorator: registers an errand."""
        def deco(fn: Callable[[list[str]], int]) -> Callable[[list[str]], int]:
            self._errands[name] = Errand(name=name, summary=summary, fn=fn)
            return fn
        return deco

    def dispatch(self, argv: list[str]) -> int:
        """Run the named errand. argv[0] is the command name."""
        if not argv:
            return self._help()
        cmd, rest = argv[0], argv[1:]
        if cmd in ("-h", "--help", "help"):
            return self._help()
        errand = self._errands.get(cmd)
        if errand is None:
            sys.stderr.write(f"hermes: unknown errand: {cmd!r}\n")
            return self._help()
        try:
            return errand.fn(rest)
        except KeyboardInterrupt:
            return 130

    def _help(self) -> int:
        from olympus.olympians.aphrodite import aphrodite
        sys.stdout.write(aphrodite.banner("Hermes", "errands of the pantheon") + "\n\n")
        if not self._errands:
            sys.stdout.write("  (no errands registered)\n")
            return 0
        rows = [(name, e.summary) for name, e in sorted(self._errands.items())]
        sys.stdout.write(aphrodite.table(("errand", "summary"), rows) + "\n")
        return 0

    def errands(self) -> list[Errand]:
        return list(self._errands.values())


hermes = Hermes()
