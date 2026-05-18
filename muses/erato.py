"""Erato — Muse of love poetry, the warmer arts.

Erato governs the prose that *invites* rather than instructs.
In Olympus she renders user-facing text in a friendly register — not
the terse declarative of the constitution, but the welcoming voice
of a guide.
"""
from __future__ import annotations


class Erato:
    """Friendly prose helpers. Used by Hermes when emitting welcome
    text, help, onboarding."""

    @staticmethod
    def welcome(operator: str = "traveller") -> str:
        return (
            f"Welcome, {operator}. The pantheon stands ready. "
            f"To consult the oracle, ask Delphi. "
            f"To know what HYDRA has seen, ask the heads. "
            f"For the swarm's count, ask Argos's eyes."
        )

    @staticmethod
    def farewell() -> str:
        return (
            "May your threads be long, your oaths kept, and your "
            "drift detected early. The hearth-fire is banked; "
            "Hestia keeps watch."
        )


erato = Erato()
