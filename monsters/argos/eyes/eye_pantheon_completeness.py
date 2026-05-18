"""eye_pantheon_completeness — every god named in PANTHEON.md exists on disk."""
from __future__ import annotations

import re

from monsters.argos.base import Eye, EyeFinding, KIND_INFO, KIND_DRIFT
from primordials.gaia import root


class EyePantheonCompleteness(Eye):
    NAME = "eye_pantheon_completeness"
    SLICE = "codex/PANTHEON.md ↔ disk"

    def scan(self) -> list[EyeFinding]:
        text = self._read("codex", "PANTHEON.md")
        if not text:
            return [self._finding("alert", "PANTHEON.md missing", intensity=8.0)]
        # Pull names mentioned as `name.py` in tables — best-effort heuristic.
        mentioned = set(m.group(1) for m in re.finditer(r"`([a-z][a-z_]+)\.py`", text))
        missing: list[str] = []
        for name in mentioned:
            for tier in ("primordials", "titans", "olympians",
                         "underworld", "fates", "furies", "graces",
                         "muses", "heroes", "monsters"):
                if root.child(tier, f"{name}.py").exists():
                    break
            else:
                missing.append(name)
        if missing:
            return [self._finding(KIND_DRIFT,
                f"PANTHEON.md names {len(missing)} module(s) missing from disk",
                intensity=4.0, missing=sorted(missing)[:10])]
        return [self._finding(KIND_INFO,
            f"PANTHEON.md is in sync with disk ({len(mentioned)} modules)")]
