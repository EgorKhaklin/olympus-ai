"""Phalanx Oracular — eyes that watch Apollo + Delphi surfaces."""
from __future__ import annotations

from monsters.argos.phalanges.base import Phalanx
from monsters.argos.eyes.eye_apollo_coverage import EyeApolloCoverage
from monsters.argos.eyes.eye_delphi_pending import EyeDelphiPending


phalanx_oracular = Phalanx(
    name="oracular",
    concern="watching Apollo + Delphi surfaces",
    eye_classes=[EyeApolloCoverage, EyeDelphiPending],
)
