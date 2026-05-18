"""Phalanx Substrate — eyes that watch the filesystem layout."""
from __future__ import annotations

from olympus.monsters.argos.phalanges.base import Phalanx
from olympus.monsters.argos.eyes.eye_pantheon_completeness import EyePantheonCompleteness


phalanx_substrate = Phalanx(
    name="substrate",
    concern="watching the filesystem layout",
    eye_classes=[EyePantheonCompleteness],
)
