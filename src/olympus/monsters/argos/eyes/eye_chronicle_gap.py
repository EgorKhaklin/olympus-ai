"""eye_chronicle_gap — surfaces if codex/CHRONICLE.md has gone too
long without a new entry."""
from __future__ import annotations

import os

from olympus.monsters.argos.base import Eye, EyeFinding, KIND_INFO, KIND_DRIFT
from olympus.primordials.gaia import root
from olympus.titans.cronus import Cronus


CHRONICLE_GAP_DAYS = 30


class EyeChronicleGap(Eye):
    NAME = "eye_chronicle_gap"
    SLICE = "codex/CHRONICLE.md"

    def scan(self) -> list[EyeFinding]:
        path = root.child("codex", "CHRONICLE.md")
        if not path.exists():
            return [self._finding("alert", "CHRONICLE.md missing")]
        mtime = path.stat().st_mtime
        import datetime
        last_mod = datetime.datetime.fromtimestamp(mtime, datetime.timezone.utc)
        age_days = Cronus.age_seconds(last_mod) / 86400.0
        if age_days > CHRONICLE_GAP_DAYS:
            return [self._finding(KIND_DRIFT,
                f"CHRONICLE.md last modified {age_days:.0f}d ago",
                intensity=min(6.0, age_days / 30.0),
                age_days=age_days)]
        return [self._finding(KIND_INFO,
            f"CHRONICLE.md current ({age_days:.0f}d since last modification)")]
