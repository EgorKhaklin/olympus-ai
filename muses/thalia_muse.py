"""Thalia — Muse of comedy.

(Distinct from Thalia of the Graces — Greek mythology has two figures
named Thalia. The Grace handles doc-tone helpers; the Muse handles
the comedic / casual register.)

In Olympus, Thalia the Muse renders casual lines: README footers,
chat-style updates, the lightness that prevents the system from
feeling like a tribunal.
"""
from __future__ import annotations

import random


class ThaliaMuse:
    """Casual register helpers."""

    _BLESSINGS = (
        "May your eyes never sleep, like Argos's.",
        "May your heads regrow, like Hydra's.",
        "May your oaths be kept, lest the Furies hunt you.",
        "May the threads spun for you be long.",
        "May the hearth-fire never go out.",
    )

    @staticmethod
    def blessing() -> str:
        """A random closing blessing for output."""
        return random.choice(ThaliaMuse._BLESSINGS)


thalia_muse = ThaliaMuse()
