"""soldier_delphi_freshness — delphi/ directory file count + mtime.

Tracks the cadence of constitutional decisions. INFO-level (not
alerting); the operator wants to SEE Delphi activity, not be paged on it.
"""
from __future__ import annotations

import time

from monsters.argos.satyrs.base import (
    Observation,
    Soldier,
    KIND_INFO,
)


class DelphiFreshnessSoldier(Soldier):
    NAME = "soldier_delphi_freshness"
    DESCRIPTION = "delphi/ file count + most-recent mtime; tracks decision cadence"
    INTENSITY = 0.75
    NODE_PREFIX = "constitution:delphi"

    def observe(self) -> list[Observation]:
        sdir = self.root / "delphi"
        if not sdir.is_dir():
            return []
        files = [f for f in sdir.iterdir() if f.is_file() and f.suffix == ".md"]
        if not files:
            return [Observation(
                node_id=f"{self.NODE_PREFIX}:files",
                value={"count": 0},
                kind=KIND_INFO,
            )]
        try:
            most_recent = max(f.stat().st_mtime for f in files)
        except OSError:
            return []
        age_days = (time.time() - most_recent) / 86400.0
        return [Observation(
            node_id=f"{self.NODE_PREFIX}:files",
            value={
                "count": len(files),
                "most_recent_age_days": round(age_days, 2),
            },
            kind=KIND_INFO,
        )]
