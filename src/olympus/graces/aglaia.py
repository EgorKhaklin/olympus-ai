"""Aglaia — Splendor, one of the three Graces.

Aglaia attends to splendor — the visible beauty of things presented
well. In Olympus she formats banners, headers, and the accent details
that distinguish "this output cared" from "this output worked."
"""
from __future__ import annotations

from olympus.olympians.aphrodite import GOLD, RESET, BOLD, DIM, LAUREL, SEA


class Aglaia:
    """Splendor — banners, headers, accent formatting."""

    @staticmethod
    def crown(text: str) -> str:
        """A title with a laurel-crown effect."""
        return f"{GOLD}❦  {BOLD}{text}{RESET}  {GOLD}❦{RESET}"

    @staticmethod
    def section(title: str, width: int = 60) -> str:
        """A section heading bordered by gold lines."""
        bar = "═" * width
        return f"\n{GOLD}{bar}{RESET}\n  {BOLD}{title}{RESET}\n{GOLD}{bar}{RESET}\n"

    @staticmethod
    def subhead(title: str) -> str:
        return f"{SEA}── {title} ──{RESET}"

    @staticmethod
    def murmur(text: str) -> str:
        """Dim text — for things that are present but not central."""
        return f"{DIM}{text}{RESET}"


aglaia = Aglaia()
