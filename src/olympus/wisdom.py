"""olympus.wisdom — the substrate reasons over its own record.

Wisdom is what makes the mythology earn its overhead. The substrate
doesn't just OBSERVE and RECORD; it READS its own record and surfaces
cross-session understanding the operator wouldn't have without it.

`portrait()` answers "what is Olympus right now."
`wisdom()` answers "what has Olympus learned across sessions."
"""
from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field
from typing import Any


@dataclass
class Wisdom:
    composed_at: str
    sessions_examined: int

    # Patterns: which slices keep alerting?
    recurring_slices: list[dict[str, Any]] = field(default_factory=list)
    slice_alert_counts: dict[str, int] = field(default_factory=dict)

    # Proposal patterns: which proposals keep coming back?
    repeated_drifts: list[dict[str, Any]] = field(default_factory=list)
    proposal_count_total: int = 0
    proposal_count_rejected: int = 0
    proposal_count_ratified: int = 0
    proposal_count_executed: int = 0

    # Momus patterns: which AP ids fire most often?
    contest_counts: dict[str, int] = field(default_factory=dict)

    # Prophecy: how well are predictions holding up?
    prophecies_verified: int = 0
    prophecies_accepted: int = 0
    prophecies_rejected: int = 0
    prophecy_acceptance_rate: float | None = None

    # Constitutional commitments
    oaths_total: int = 0
    oath_kinds_by_actor: dict[str, int] = field(default_factory=dict)

    # Activity rhythm
    sessions_total: int = 0
    sessions_with_errors: int = 0

    # Plain-language insights derived from the above
    insights: list[str] = field(default_factory=list)

    def as_text(self) -> str:
        lines: list[str] = []
        lines.append(f"# Olympus wisdom — {self.composed_at}")
        lines.append("")
        lines.append(f"_examined {self.sessions_examined} session(s)_")
        lines.append("")

        if self.insights:
            lines.append("## What the substrate has learned")
            for ins in self.insights:
                lines.append(f"  · {ins}")
            lines.append("")

        if self.recurring_slices:
            lines.append("## Recurring slices (most-alerted)")
            for s in self.recurring_slices[:10]:
                lines.append(f"  · {s['slice']}  —  {s['count']} alert(s)")
            lines.append("")

        if self.repeated_drifts:
            lines.append("## Repeated drift proposals (Hephaestus has surfaced these often)")
            for d in self.repeated_drifts[:10]:
                lines.append(f"  · {d['signature']}  —  {d['count']} proposal(s)")
            lines.append("")

        if self.contest_counts:
            lines.append("## Momus AP catalog usage")
            for ap_id, n in sorted(self.contest_counts.items(),
                                    key=lambda kv: -kv[1])[:8]:
                lines.append(f"  · {ap_id}  —  {n} contest(s)")
            lines.append("")

        if self.prophecies_verified:
            rate = (f"{self.prophecy_acceptance_rate:.1%}"
                    if self.prophecy_acceptance_rate is not None else "n/a")
            lines.append("## Apollo's prophecy accuracy")
            lines.append(f"  · {self.prophecies_verified} prophet-cycle(s) completed")
            lines.append(f"  · {self.prophecies_accepted} accepted · "
                         f"{self.prophecies_rejected} rejected  ({rate})")
            lines.append("")

        lines.append("## Actions")
        lines.append(f"  · {self.proposal_count_total} proposal(s) total")
        lines.append(f"  · {self.proposal_count_ratified} ratified · "
                     f"{self.proposal_count_executed} executed · "
                     f"{self.proposal_count_rejected} rejected")
        lines.append("")

        lines.append("## Constitution")
        lines.append(f"  · {self.oaths_total} oath(s) on Styx")
        if self.oath_kinds_by_actor:
            for actor, n in sorted(self.oath_kinds_by_actor.items(),
                                    key=lambda kv: -kv[1])[:5]:
                lines.append(f"    {actor}: {n}")
        lines.append("")

        lines.append("## Activity")
        lines.append(f"  · {self.sessions_total} session(s) completed")
        if self.sessions_with_errors:
            lines.append(f"  · {self.sessions_with_errors} session(s) errored")
        lines.append("")
        return "\n".join(lines)


def wisdom() -> Wisdom:
    """Compose the current wisdom-portrait by reasoning over Mnemosyne
    and Styx. Pure read — never writes."""
    import re as _re
    from olympus.primordials.nyx import Nyx
    from olympus.titans.mnemosyne import mnemosyne
    from olympus.underworld.styx import styx

    w = Wisdom(
        composed_at=Nyx.now().isoformat(),
        sessions_examined=0,
    )

    # Activity
    sessions = mnemosyne.recall("session.completed")
    errored = mnemosyne.recall("session.errored")
    w.sessions_total = len(sessions)
    w.sessions_examined = len(sessions)
    w.sessions_with_errors = len(errored)

    # Recurring slices: read every brief, count alert-slice occurrences
    # The brief is the structured artifact; reading it is reasoning over
    # the agent's prior conclusions, not raw observations.
    slice_alert_counter: Counter[str] = Counter()
    for m in sessions:
        # Each session.completed memory has the count fields but not the
        # alert slice names. Reach into Athena's brief files instead.
        pass
    # Reach into Athena's briefs directly (already on disk)
    from olympus.primordials.gaia import root
    briefs_dir = root.child("state", "athena")
    if briefs_dir.exists():
        import json as _json
        for f in sorted(briefs_dir.glob("*.json")):
            try:
                with f.open("r", encoding="utf-8") as fh:
                    d = _json.load(fh)
            except Exception:  # noqa: BLE001
                continue
            for finding in d.get("findings", []):
                if (finding.get("severity") == "alert"
                        or finding.get("kind") == "alert"):
                    slice_alert_counter[finding.get("slice", "?")] += 1

    w.slice_alert_counts = dict(slice_alert_counter)
    w.recurring_slices = [
        {"slice": sl, "count": cnt}
        for sl, cnt in slice_alert_counter.most_common(20)
        if cnt >= 2
    ]

    # Proposal patterns: walk action.* memories
    promoted = mnemosyne.recall("action.promoted")
    rejected = mnemosyne.recall("action.rejected")
    ratified = mnemosyne.recall("action.ratified")
    executed = mnemosyne.recall("action.executed")
    w.proposal_count_total = len(promoted)
    w.proposal_count_rejected = len(rejected)
    w.proposal_count_ratified = len(ratified)
    w.proposal_count_executed = len(executed)

    # Repeated drifts — extract signature from each rejected proposal
    drift_counter: Counter[str] = Counter()
    for m in rejected:
        aid = m.body.get("action_id", "")
        if aid.startswith("act-"):
            pid = aid[4:]
        else:
            pid = aid
        proposal_path = root.child("state", "hephaestus", f"{pid}.json")
        if proposal_path.exists():
            try:
                import json as _json
                with proposal_path.open("r", encoding="utf-8") as fh:
                    p = _json.load(fh)
                drift = p.get("drift_observed", "")
                match = _re.match(
                    r"(hydra|argos|\?)\s+reports.*?slice\s+'([^']+)'",
                    drift,
                )
                if match:
                    drift_counter[f"{match.group(1)}::{match.group(2)}"] += 1
            except Exception:  # noqa: BLE001
                pass
    w.repeated_drifts = [
        {"signature": sig, "count": cnt}
        for sig, cnt in drift_counter.most_common(10)
        if cnt >= 2
    ]

    # Prophecy accuracy
    prophecies = mnemosyne.recall("prophecy.verified")
    w.prophecies_verified = len(prophecies)
    w.prophecies_accepted = sum(
        1 for m in prophecies if m.body.get("accepted") is True
    )
    w.prophecies_rejected = sum(
        1 for m in prophecies if m.body.get("accepted") is False
    )
    total_verified = w.prophecies_accepted + w.prophecies_rejected
    w.prophecy_acceptance_rate = (
        w.prophecies_accepted / total_verified if total_verified else None
    )

    # Constitutional commitments
    oaths = styx._read_all()
    w.oaths_total = len(oaths)
    actor_counter: Counter[str] = Counter()
    for o in oaths:
        actor_counter[o.get("sworn_by", "?")] += 1
    w.oath_kinds_by_actor = dict(actor_counter)

    # Insights — concrete cross-session claims as English
    insights: list[str] = []
    if w.recurring_slices:
        top = w.recurring_slices[0]
        insights.append(
            f"slice {top['slice']!r} has alerted {top['count']} time(s) "
            f"across the brief archive — strongest recurring pattern"
        )
    if w.repeated_drifts:
        top_d = w.repeated_drifts[0]
        insights.append(
            f"drift {top_d['signature']!r} has been proposed {top_d['count']} "
            f"time(s) and rejected — Hephaestus stops nagging on this"
        )
    if w.prophecies_verified and w.prophecy_acceptance_rate is not None:
        insights.append(
            f"Apollo's prediction acceptance rate is "
            f"{w.prophecy_acceptance_rate:.1%} over "
            f"{total_verified} verified prophet-cycle(s)"
        )
    if w.proposal_count_total:
        ratify_rate = w.proposal_count_ratified / w.proposal_count_total
        insights.append(
            f"of {w.proposal_count_total} proposal(s) ever surfaced by "
            f"Hephaestus, {ratify_rate:.0%} were ratified by Zeus"
        )
    if w.sessions_total and w.sessions_with_errors:
        err_rate = w.sessions_with_errors / w.sessions_total
        insights.append(
            f"{err_rate:.1%} of sessions errored — investigate if > 5%"
        )
    if not insights:
        insights.append(
            "not enough history yet to extract patterns; "
            "run more sessions and revisit"
        )
    w.insights = insights

    return w
