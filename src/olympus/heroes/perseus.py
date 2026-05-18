"""Perseus — hero who slew Medusa using her own reflection.

Perseus's polished shield let him see Medusa without facing her
directly. In Olympus, Perseus is the reflection persona — the
agent's facility for examining itself without freezing. When the
agent needs to write a journal entry about what just happened, it
acts as Perseus.
"""
from __future__ import annotations

from olympus.muses.clio import clio


class Perseus:
    """Self-reflection wrapper — writes session-state to the chronicle
    via Clio's journal."""

    def reflect(self, on: str, observation: str) -> None:
        """Reflect on `on`, recording `observation` in today's journal."""
        clio.inscribe("reflection", f"on {on}: {observation}")

    def turn_to_stone(self, observation: str) -> None:
        """Freeze an observation — write it AND swear it on Styx,
        making it unmodifiable."""
        from olympus.underworld.styx import swear
        clio.inscribe("petrified", observation)
        swear(sworn_by="perseus", statement=observation)


perseus = Perseus()
