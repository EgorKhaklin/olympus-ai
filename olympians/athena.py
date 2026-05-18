"""Athena — goddess of wisdom and strategy.

Athena sprang fully-armored from Zeus's forehead. She is strategy
itself: the considered move, the chosen course. In Olympus, Athena is
the strategic-synthesis primitive — she reads what HYDRA's heads have
observed, what Argos's eyes have noted, and produces a brief.

The brief is a structured summary that Hephaestus consults when
proposing changes. It is the bridge between observation and action.
"""
from __future__ import annotations

import json
import pathlib
from dataclasses import dataclass, field, asdict
from typing import Any

from primordials.gaia import root
from primordials.nyx import Nyx


@dataclass
class Brief:
    """A strategic synthesis. Produced by Athena, consulted by
    Hephaestus and Zeus."""
    label: str
    composed_at: str
    findings: list[dict[str, Any]] = field(default_factory=list)
    recommendations: list[str] = field(default_factory=list)
    confidence: float = 0.5      # 0.0 (guess) .. 1.0 (certain)


class Athena:
    """Strategic synthesis from substrate observations."""

    BRIEFS_DIR = "olympians/athena_briefs"

    def __init__(self, briefs_path: pathlib.Path | None = None) -> None:
        self.briefs_path = briefs_path or root.child(self.BRIEFS_DIR)
        self.briefs_path.mkdir(parents=True, exist_ok=True)

    def compose(self, label: str, findings: list[dict[str, Any]],
                recommendations: list[str], confidence: float = 0.5) -> Brief:
        """Compose a brief. Always written to disk for Hephaestus to read."""
        brief = Brief(
            label=label,
            composed_at=Nyx.now().isoformat(),
            findings=findings,
            recommendations=recommendations,
            confidence=max(0.0, min(1.0, confidence)),
        )
        ts = brief.composed_at.replace(":", "").replace("-", "").split(".")[0]
        target = self.briefs_path / f"{ts}--{label}.json"
        with target.open("w", encoding="utf-8") as f:
            json.dump(asdict(brief), f, indent=2, default=str)
        return brief

    def latest(self, label: str | None = None) -> Brief | None:
        """Return the most recent brief, optionally filtered by label."""
        glob_pattern = f"*--{label}.json" if label else "*.json"
        files = sorted(self.briefs_path.glob(glob_pattern), reverse=True)
        if not files:
            return None
        with files[0].open("r", encoding="utf-8") as f:
            d = json.load(f)
        return Brief(**d)


athena = Athena()
