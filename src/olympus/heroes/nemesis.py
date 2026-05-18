"""Nemesis — goddess of retribution and divine balance.

In myth: her name means "to distribute" or "to give what is due." She
measured the gap between what a mortal did and what they should have
done — and acted on the gap.

In Olympus, Nemesis is the **counterfactual reasoner**. For any
recent ratified action, she asks: *"what would have happened if the
opposite choice had been made?"* She uses Castor to spawn a shadow
session where the alternative is applied; she uses Pollux to compare
the shadow report with what production actually did; she records
the *gap* under `nemesis.counterfactual`.

The recursion: if Nemesis finds that the counterfactual would have
produced measurably better outcomes (more proposals correctly
ratified, fewer Cassandra vindications, shorter Atlas burdens),
Metis can feed that signal into parameter tuning. Nemesis names what
*should have been*; Metis recommends how to make it so.

Note: counterfactuals are inherently expensive (a full shadow session
per consideration). Nemesis runs deliberately and bounded — by
default she examines only the **last N=3** ratified actions per pass,
and only ones not already examined.

Per Delphi 2026-05-18-labyrinth-arc.md.
"""
from __future__ import annotations

import shutil
from dataclasses import dataclass, field, asdict
from typing import Any

from olympus.primordials.nyx import Nyx
from olympus.titans.mnemosyne import mnemosyne


@dataclass
class Counterfactual:
    """One counterfactual evaluation — what was, vs. what could have been."""
    subject_action_id: str
    subject_summary: str
    actual_outcome: str             # what production did
    counterfactual_choice: str      # what the shadow tried
    gap_summary: str                # one-line gap description
    shadow_succeeded: bool
    shadow_report: dict[str, Any] = field(default_factory=dict)
    examined_at: str = ""

    def __post_init__(self) -> None:
        if not self.examined_at:
            self.examined_at = Nyx.now().isoformat()


@dataclass
class NemesisReport:
    started_at: str
    ended_at: str = ""
    actions_considered: int = 0
    counterfactuals: list[Counterfactual] = field(default_factory=list)
    skipped_already_examined: int = 0

    @property
    def total(self) -> int:
        return len(self.counterfactuals)


class Nemesis:
    """The counterfactual reasoner. Measures gap between what was
    decided and what could have been."""

    DEFAULT_MAX_PER_PASS = 3

    def consider(self, *,
                  max_per_pass: int = DEFAULT_MAX_PER_PASS,
                  cleanup_shadows: bool = True
                  ) -> NemesisReport:
        """Examine the last N ratified actions; run a counterfactual
        shadow for each not yet examined; record gaps."""
        report = NemesisReport(started_at=Nyx.now().isoformat())
        examined_ids = self._already_examined()
        recent = self._recent_ratifications()
        # newest first
        recent.reverse()

        for m in recent:
            if report.total >= max_per_pass:
                break
            action_id = (m.body or {}).get("action_id", "")
            if not action_id:
                continue
            report.actions_considered += 1
            if action_id in examined_ids:
                report.skipped_already_examined += 1
                continue

            cf = self._run_counterfactual(
                action_id=action_id,
                summary=m.summary,
                cleanup_shadow=cleanup_shadows,
            )
            report.counterfactuals.append(cf)
            # Record per-counterfactual
            mnemosyne.remember(
                kind="nemesis.counterfactual",
                actor="nemesis",
                summary=(f"counterfactual for {action_id}: "
                         f"{cf.gap_summary}"),
                **asdict(cf),
            )

        mnemosyne.remember(
            kind="nemesis.pass",
            actor="nemesis",
            summary=(f"considered {report.actions_considered} action(s); "
                     f"recorded {report.total} counterfactual(s)"),
            actions_considered=report.actions_considered,
            total=report.total,
            skipped_already_examined=report.skipped_already_examined,
        )
        report.ended_at = Nyx.now().isoformat()
        return report

    # ─────────────────────────────────────────────────────────
    # Internal helpers
    # ─────────────────────────────────────────────────────────

    @staticmethod
    def _already_examined() -> set[str]:
        out: set[str] = set()
        for m in mnemosyne.recall("nemesis.counterfactual"):
            aid = (m.body or {}).get("subject_action_id", "")
            if aid:
                out.add(aid)
        return out

    @staticmethod
    def _recent_ratifications() -> list[Any]:
        # Limit to recent — old ratifications aren't actionable for
        # tuning anyway. Look at the most recent 20.
        return mnemosyne.recall("action.ratified")[-20:]

    @staticmethod
    def _run_counterfactual(*, action_id: str, summary: str,
                             cleanup_shadow: bool) -> Counterfactual:
        """The counterfactual: what if we had not run this iteration?

        The simplest credible counterfactual: skip one session.
        Castor runs the shadow without applying the original directive;
        we compare what the shadow saw vs. what production recorded."""
        from olympus.heroes.castor import castor
        from olympus.heroes.pollux import pollux

        shadow = castor.shadow_session(
            directive=f"counterfactual for {action_id}",
            timeout_seconds=45.0,
        )

        # Compare what the shadow's session saw against what the prod
        # session immediately before the ratification saw.
        prod_report = Nemesis._prod_report_near(action_id)
        comparison = pollux.compare(
            prod_report or {},
            shadow.session_report or {},
            left_label=f"prod-near-{action_id[:12]}",
            right_label=f"shadow-cf",
        )

        if cleanup_shadow and shadow.shadow_root:
            shutil.rmtree(shadow.shadow_root, ignore_errors=True)

        gap_summary = (f"{len(comparison.differences)} field(s) differ "
                       f"between prod-context and counterfactual shadow")
        return Counterfactual(
            subject_action_id=action_id,
            subject_summary=summary,
            actual_outcome=f"action {action_id} ratified in production",
            counterfactual_choice="alternative shadow session",
            gap_summary=gap_summary,
            shadow_succeeded=shadow.succeeded,
            shadow_report=shadow.session_report,
        )

    @staticmethod
    def _prod_report_near(action_id: str) -> dict[str, Any] | None:
        """Find the production session.completed record whose timing
        is closest to the action's ratification."""
        # Find the ratification ts
        for m in mnemosyne.recall("action.ratified"):
            if (m.body or {}).get("action_id") == action_id:
                ratified_at = m.remembered_at
                # Find the prod session.completed nearest to ratified_at
                sessions = mnemosyne.recall("session.completed")
                if not sessions:
                    return None
                # Closest by ts (simple linear scan; volumes are small)
                nearest = min(
                    sessions,
                    key=lambda s: abs(_ts_delta(s.remembered_at,
                                                ratified_at)),
                )
                return nearest.body or {}
        return None


def _ts_delta(a: str, b: str) -> float:
    """Absolute seconds between two iso timestamps; large fallback if
    either parses badly."""
    import datetime
    try:
        da = datetime.datetime.fromisoformat(a)
        db = datetime.datetime.fromisoformat(b)
        return abs((da - db).total_seconds())
    except (ValueError, TypeError):
        return 1e18


nemesis = Nemesis()
