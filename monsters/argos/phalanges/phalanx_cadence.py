"""Phalanx Cadence — eyes that watch rhythms of operation."""
from __future__ import annotations

from monsters.argos.phalanges.base import Phalanx
from monsters.argos.eyes.eye_journal_silence import EyeJournalSilence
from monsters.argos.eyes.eye_chronicle_gap import EyeChronicleGap
from monsters.argos.eyes.eye_oath_freshness import EyeOathFreshness


phalanx_cadence = Phalanx(
    name="cadence",
    concern="watching rhythms of operation",
    eye_classes=[EyeJournalSilence, EyeChronicleGap, EyeOathFreshness],
)
