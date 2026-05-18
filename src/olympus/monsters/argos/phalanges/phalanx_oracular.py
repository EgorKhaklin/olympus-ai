"""Phalanx Oracular — eyes that watch Apollo + Delphi surfaces."""
from __future__ import annotations

from olympus.monsters.argos.phalanges.base import Phalanx
from olympus.monsters.argos.eyes.eye_apollo_coverage import EyeApolloCoverage
from olympus.monsters.argos.eyes.eye_delphi_pending import EyeDelphiPending


phalanx_oracular = Phalanx(
    name="oracular",
    concern="watching Apollo + Delphi surfaces",
    eye_classes=[EyeApolloCoverage, EyeDelphiPending],
)
