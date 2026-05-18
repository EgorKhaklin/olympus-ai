"""Euphrosyne — Good Cheer, one of the three Graces.

Euphrosyne's name means "mirth." She is the lightness that makes
difficult news bearable. In Olympus she rewrites raw exceptions into
operator-facing messages that explain the problem without panic.
"""
from __future__ import annotations

from typing import Type

from olympus.olympians.aphrodite import RESET, WINE, GOLD, DIM


class Euphrosyne:
    """Friendly error messages."""

    # A small dictionary of well-known exception types → friendly
    # phrasings. The format is `(prefix, suggestion)`.
    _FRIENDS: dict[str, tuple[str, str]] = {
        "FileNotFoundError": (
            "A file Olympus expected to find was missing",
            "Check the path; consider running rhea.bring_forth() to "
            "ensure all required directories exist.",
        ),
        "PermissionError": (
            "Olympus was refused permission",
            "The hearth-fire requires write access to this path; "
            "check ownership or run under the right account.",
        ),
        "KeyError": (
            "Something Olympus looked up was not registered",
            "Verify the spelling and check whether registration ran.",
        ),
        "RuntimeError": (
            "Olympus reached a state it refuses to operate in",
            "Read the message; it names the violated constraint.",
        ),
    }

    @classmethod
    def reframe(cls, exc: BaseException) -> str:
        """Render an exception with a friendly preface + the technical
        detail. Returns a string fit for the operator."""
        name = type(exc).__name__
        prefix, suggestion = cls._FRIENDS.get(
            name,
            ("Something unexpected happened",
             "Read the trace and consult the codex if the cause is unclear."),
        )
        return (
            f"{WINE}◐ {prefix}{RESET} "
            f"{DIM}({name}){RESET}\n"
            f"  {exc}\n"
            f"  {GOLD}→{RESET} {suggestion}"
        )


euphrosyne = Euphrosyne()
