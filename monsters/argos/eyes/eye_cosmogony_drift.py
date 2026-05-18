"""eye_cosmogony_drift — checks that codex/COSMOGONY.md still names
every substrate invariant (S1–S8)."""
from __future__ import annotations

from monsters.argos.base import Eye, EyeFinding, KIND_INFO, KIND_ALERT


class EyeCosmogonyDrift(Eye):
    NAME = "eye_cosmogony_drift"
    SLICE = "codex/COSMOGONY.md"

    def scan(self) -> list[EyeFinding]:
        text = self._read("codex", "COSMOGONY.md")
        if not text:
            return [self._finding(KIND_ALERT, "COSMOGONY.md is missing")]
        missing = [f"S{i}" for i in range(1, 9) if f"S{i}" not in text]
        if missing:
            return [self._finding(KIND_ALERT,
                f"COSMOGONY.md missing {missing}", intensity=8.0,
                missing=missing)]
        return [self._finding(KIND_INFO,
            "COSMOGONY.md names all eight substrate invariants",
            invariant_count=8)]
