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

from olympus.primordials.gaia import root
from olympus.primordials.nyx import Nyx


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

    BRIEFS_DIR = "state/athena"

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

    # ─────────────────────────────────────────────────────────
    # Real synthesis — consume HYDRA + Argos directly
    # ─────────────────────────────────────────────────────────

    def compose_from(self, hydra_report: Any, argos_census: Any, *,
                     label: str, directive: str | None = None) -> Brief:
        """Synthesize a brief from a HydraReport + Argos Census.

        Strategy:
          - Every HYDRA ALERT becomes a high-severity finding
          - Every Argos alert pheromone becomes a finding
          - HYDRA drifts + Argos drifts become medium-severity findings
          - Recommendations are surfaced from any slice with ≥2 findings
            (cross-tier corroboration, the load-bearing pattern)
          - Confidence is a function of corroboration count
        """
        findings: list[dict[str, Any]] = []
        slice_to_signals: dict[str, list[str]] = {}

        # HYDRA contributions
        for f in getattr(hydra_report, "findings", []):
            severity = getattr(f.severity, "value", str(f.severity))
            findings.append({
                "source": "hydra",
                "head": f.head,
                "slice": f.slice,
                "severity": severity,
                "detail": f.detail,
            })
            slice_to_signals.setdefault(f.slice, []).append(f"hydra:{f.head}:{severity}")

        # Argos contributions
        for p in getattr(argos_census, "pheromones", []):
            findings.append({
                "source": "argos",
                "eye": p.eye,
                "slice": p.slice,
                "kind": p.kind,
                "intensity": p.intensity,
                "detail": p.detail,
            })
            slice_to_signals.setdefault(p.slice, []).append(f"argos:{p.eye}:{p.kind}")

        # Surface recommendations from any slice with ≥2 signals (corroboration)
        recommendations: list[str] = []
        for slice_name, signals in slice_to_signals.items():
            if len(signals) >= 2:
                alert_count = sum(1 for s in signals if "alert" in s)
                if alert_count:
                    recommendations.append(
                        f"slice '{slice_name}' surfaced in {len(signals)} signal(s) "
                        f"with {alert_count} alert(s) — investigate"
                    )
                else:
                    recommendations.append(
                        f"slice '{slice_name}' has {len(signals)} corroborating signal(s) — "
                        f"likely stable; consider promoting to a baseline expectation"
                    )

        if directive:
            recommendations.append(
                f"operator directive: {directive!r} — synthesize against the brief above"
            )

        # Confidence: proportional to how many slices were observed by both tiers
        cross_tier = sum(
            1 for sigs in slice_to_signals.values()
            if any("hydra:" in s for s in sigs) and any("argos:" in s for s in sigs)
        )
        confidence = min(0.5 + 0.1 * cross_tier, 0.95)

        return self.compose(
            label=label,
            findings=findings,
            recommendations=recommendations,
            confidence=confidence,
        )


athena = Athena()
