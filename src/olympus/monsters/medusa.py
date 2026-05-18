"""Medusa — gorgon whose gaze turned the living to stone.

Medusa froze whatever met her eye. In Olympus, Medusa is the snapshot
primitive: she captures the current state of a named subject and
preserves it, immutable, in Hades.
"""
from __future__ import annotations

import json
import pathlib
from typing import Any

from olympus.primordials.gaia import root
from olympus.underworld.hades import descend


class Medusa:
    """Snapshot primitive — freezes state into stone (archive)."""

    def gaze(self, subject: str, state: Any) -> pathlib.Path:
        """Snapshot `state` under `subject`. Returns the archived path."""
        return descend(f"medusa--{subject}", state)


medusa = Medusa()
