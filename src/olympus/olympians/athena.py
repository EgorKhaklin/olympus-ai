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
    # History-aware fields — Athena's reasoning over Mnemosyne
    insights: list[str] = field(default_factory=list)
    recurring_slices: list[dict[str, Any]] = field(default_factory=list)
    newly_alerted_slices: list[str] = field(default_factory=list)
    resolved_slices: list[str] = field(default_factory=list)
    stable_slices: list[str] = field(default_factory=list)


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

        # History-aware reasoning — read Mnemosyne for prior session shape
        current_alert_slices = {
            f["slice"] for f in findings
            if f.get("severity") == "alert" or f.get("kind") == "alert"
        }
        history = self._read_history(window=7)
        recurring, newly_alerted, resolved, stable, insights = \
            self._reason_over_history(current_alert_slices, slice_to_signals, history)

        # History elevates confidence when current state corroborates prior pattern
        if recurring:
            confidence = min(confidence + 0.05 * len(recurring[:5]), 0.98)

        if directive:
            recommendations.append(
                f"operator directive: {directive!r} — synthesize against the brief above"
            )

        return self._compose_with_insights(
            label=label,
            findings=findings,
            recommendations=recommendations,
            confidence=confidence,
            insights=insights,
            recurring=recurring,
            newly_alerted=newly_alerted,
            resolved=resolved,
            stable=stable,
        )

    # ─────────────────────────────────────────────────────────
    # History-aware reasoning — Athena reads Mnemosyne
    # ─────────────────────────────────────────────────────────

    def _read_history(self, *, window: int) -> list[dict[str, Any]]:
        """Pull the last `window` session.completed memories."""
        from olympus.titans.mnemosyne import mnemosyne
        sessions = mnemosyne.recall("session.completed")[-window:]
        out: list[dict[str, Any]] = []
        for m in sessions:
            out.append({
                "remembered_at": m.remembered_at,
                "session_id": m.body.get("session_id"),
                "summary": m.summary,
            })
        return out

    def _read_recent_briefs(self, *, window: int) -> list[Brief]:
        """Pull the last `window` Brief json files. Returns oldest-first."""
        import json as _json
        files = sorted(self.briefs_path.glob("*.json"))[-window:]
        out: list[Brief] = []
        for f in files:
            try:
                with f.open("r", encoding="utf-8") as fh:
                    d = _json.load(fh)
                # Be tolerant of older Brief shapes that don't have new fields
                out.append(Brief(
                    label=d.get("label", ""),
                    composed_at=d.get("composed_at", ""),
                    findings=d.get("findings", []),
                    recommendations=d.get("recommendations", []),
                    confidence=d.get("confidence", 0.5),
                    insights=d.get("insights", []),
                    recurring_slices=d.get("recurring_slices", []),
                    newly_alerted_slices=d.get("newly_alerted_slices", []),
                    resolved_slices=d.get("resolved_slices", []),
                    stable_slices=d.get("stable_slices", []),
                ))
            except Exception:  # noqa: BLE001
                continue
        return out

    def _reason_over_history(
        self,
        current_alert_slices: set[str],
        current_slice_signals: dict[str, list[str]],
        history: list[dict[str, Any]],
    ) -> tuple[list[dict[str, Any]], list[str], list[str], list[str], list[str]]:
        """Run the cross-session reasoning. Returns
        (recurring, newly_alerted, resolved, stable, insights).
        """
        prior_briefs = self._read_recent_briefs(window=7)
        prior_alerts: list[set[str]] = []
        prior_stable: list[set[str]] = []
        for b in prior_briefs:
            alert_set: set[str] = set()
            stable_set: set[str] = set()
            for f in b.findings:
                sl = f.get("slice")
                if not sl:
                    continue
                sev = f.get("severity") or f.get("kind")
                if sev == "alert":
                    alert_set.add(sl)
                elif sev == "info":
                    stable_set.add(sl)
            prior_alerts.append(alert_set)
            prior_stable.append(stable_set)

        # Recurring: alerted in ≥3 of last 7 briefs
        slice_to_alert_count: dict[str, int] = {}
        for s_set in prior_alerts:
            for sl in s_set:
                slice_to_alert_count[sl] = slice_to_alert_count.get(sl, 0) + 1
        for sl in current_alert_slices:
            slice_to_alert_count[sl] = slice_to_alert_count.get(sl, 0) + 1

        recurring = [
            {"slice": sl, "alerts_in_last_n": cnt, "window": len(prior_briefs) + 1}
            for sl, cnt in slice_to_alert_count.items() if cnt >= 3
        ]
        recurring.sort(key=lambda r: -r["alerts_in_last_n"])

        # Newly alerted: alerted this session, NOT alerted in last 5
        recent_alert_union: set[str] = set()
        for s_set in prior_alerts[-5:]:
            recent_alert_union.update(s_set)
        newly_alerted = sorted(current_alert_slices - recent_alert_union)

        # Resolved: alerted in the most recent prior brief, not this session
        most_recent_prior_alerts: set[str] = (
            prior_alerts[-1] if prior_alerts else set()
        )
        resolved = sorted(most_recent_prior_alerts - current_alert_slices)

        # Stable: INFO in ≥ majority of available prior briefs (min 2)
        # AND not currently alerting. Threshold scales with history size
        # so insights say something meaningful even early on.
        slice_to_stable_count: dict[str, int] = {}
        for s_set in prior_stable[-7:]:
            for sl in s_set:
                slice_to_stable_count[sl] = slice_to_stable_count.get(sl, 0) + 1
        recent_history_len = min(len(prior_stable), 7)
        stable_threshold = max(2, recent_history_len // 2 + 1)
        stable = sorted(
            sl for sl, cnt in slice_to_stable_count.items()
            if cnt >= stable_threshold and sl not in current_alert_slices
        )

        # Insights — concrete cross-session claims as English
        insights: list[str] = []
        for r in recurring[:3]:
            insights.append(
                f"slice {r['slice']!r} has alerted in {r['alerts_in_last_n']} "
                f"of the last {r['window']} session(s) — pattern, not noise"
            )
        for sl in newly_alerted[:2]:
            insights.append(
                f"slice {sl!r} is newly alerting; "
                f"no prior alert in the last 5 sessions"
            )
        for sl in resolved[:2]:
            insights.append(
                f"slice {sl!r} resolved since the prior session"
            )
        if stable and not recurring and not newly_alerted:
            insights.append(
                f"{len(stable)} slice(s) have been stable across the last "
                f"{min(7, len(prior_briefs))} sessions"
            )
        if not prior_briefs:
            insights.append(
                "no prior sessions to reason against; this brief is the baseline"
            )
        elif not insights:
            # We have history but nothing patterned — say so explicitly so
            # operators reading the brief know Athena DID reason and found
            # nothing remarkable yet.
            insights.append(
                f"{len(prior_briefs)} prior brief(s) examined; "
                f"no recurring patterns or transitions detected yet"
            )

        return recurring, newly_alerted, resolved, stable, insights

    def _compose_with_insights(
        self, *, label: str, findings: list[dict[str, Any]],
        recommendations: list[str], confidence: float,
        insights: list[str],
        recurring: list[dict[str, Any]],
        newly_alerted: list[str],
        resolved: list[str],
        stable: list[str],
    ) -> Brief:
        """Same as compose() but with the new history-aware fields."""
        brief = Brief(
            label=label,
            composed_at=Nyx.now().isoformat(),
            findings=findings,
            recommendations=recommendations,
            confidence=max(0.0, min(1.0, confidence)),
            insights=insights,
            recurring_slices=recurring,
            newly_alerted_slices=newly_alerted,
            resolved_slices=resolved,
            stable_slices=stable,
        )
        ts = brief.composed_at.replace(":", "").replace("-", "").split(".")[0]
        target = self.briefs_path / f"{ts}--{label}.json"
        with target.open("w", encoding="utf-8") as f:
            json.dump(asdict(brief), f, indent=2, default=str)
        return brief


athena = Athena()
