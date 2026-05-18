"""Aphrodite — goddess of love, beauty, desire.

Aphrodite makes the world worth looking at. In Olympus, Aphrodite is
the aesthetics primitive — terminal-output formatting, color, layout,
and the small things that make CLI output beautiful rather than
serviceable.

The Graces (Aglaia, Euphrosyne, Thalia) serve Aphrodite. They handle
specific aesthetic concerns; Aphrodite is the high-level interface.
"""
from __future__ import annotations

import os
import sys
from typing import Iterable


# ANSI codes — used only when stdout is a TTY and TERM is not "dumb"
_USE_COLOR = (
    sys.stdout.isatty()
    and os.environ.get("TERM", "").lower() != "dumb"
    and not os.environ.get("NO_COLOR")
)

RESET = "\033[0m" if _USE_COLOR else ""
BOLD = "\033[1m" if _USE_COLOR else ""
DIM = "\033[2m" if _USE_COLOR else ""
ITALIC = "\033[3m" if _USE_COLOR else ""

# Greek wine-dark sea palette
GOLD = "\033[38;5;220m" if _USE_COLOR else ""
WINE = "\033[38;5;88m" if _USE_COLOR else ""
SEA = "\033[38;5;30m" if _USE_COLOR else ""
MARBLE = "\033[38;5;253m" if _USE_COLOR else ""
LAUREL = "\033[38;5;108m" if _USE_COLOR else ""
EMBER = "\033[38;5;208m" if _USE_COLOR else ""


class Aphrodite:
    """Aesthetic helpers for terminal output."""

    @staticmethod
    def banner(title: str, subtitle: str = "") -> str:
        """A two-line bordered banner."""
        bar = "═" * max(len(title), len(subtitle))
        out = f"{GOLD}╔{bar}╗{RESET}\n"
        out += f"{GOLD}║{BOLD}{title:<{len(bar)}}{RESET}{GOLD}║{RESET}\n"
        if subtitle:
            out += f"{GOLD}║{DIM}{subtitle:<{len(bar)}}{RESET}{GOLD}║{RESET}\n"
        out += f"{GOLD}╚{bar}╝{RESET}"
        return out

    @staticmethod
    def laurel(text: str) -> str:
        """Wreathe `text` in laurel — for things that succeeded."""
        return f"{LAUREL}🜂  {text}{RESET}"

    @staticmethod
    def lightning(text: str) -> str:
        """Mark `text` as Zeus-attention — for things that need decision."""
        return f"{GOLD}⚡ {text}{RESET}"

    @staticmethod
    def wine_dark(text: str) -> str:
        """Wine-dark sea — for things that failed."""
        return f"{WINE}◐ {text}{RESET}"

    @staticmethod
    def divider(width: int = 60, char: str = "─") -> str:
        return f"{DIM}{char * width}{RESET}"

    @staticmethod
    def table(headers: Iterable[str], rows: Iterable[Iterable[str]]) -> str:
        """Render a simple aligned table."""
        rows_list = [list(map(str, row)) for row in rows]
        headers_list = list(headers)
        widths = [len(h) for h in headers_list]
        for row in rows_list:
            for i, cell in enumerate(row):
                if i < len(widths):
                    widths[i] = max(widths[i], len(cell))
        sep = "  "
        lines = [sep.join(f"{BOLD}{h:<{widths[i]}}{RESET}" for i, h in enumerate(headers_list))]
        lines.append(sep.join("─" * w for w in widths))
        for row in rows_list:
            lines.append(sep.join(f"{cell:<{widths[i]}}" for i, cell in enumerate(row)))
        return "\n".join(lines)


aphrodite = Aphrodite()
