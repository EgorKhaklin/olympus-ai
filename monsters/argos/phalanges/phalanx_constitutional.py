"""Phalanx Constitutional — eyes that watch the substrate's own laws."""
from __future__ import annotations

from monsters.argos.phalanges.base import Phalanx
from monsters.argos.eyes.eye_cosmogony_drift import EyeCosmogonyDrift
from monsters.argos.eyes.eye_pantheon_completeness import EyePantheonCompleteness
from monsters.argos.eyes.eye_styx_chain_intact import EyeStyxChainIntact
from monsters.argos.eyes.eye_understanding_gap import EyeUnderstandingGap


phalanx_constitutional = Phalanx(
    name="constitutional",
    concern="watching the substrate's own laws",
    eye_classes=[EyeCosmogonyDrift, EyePantheonCompleteness,
                 EyeStyxChainIntact, EyeUnderstandingGap],
)
