"""notekeeper-specific HYDRA head.

head_topic_drift — C5 enforcement. Compares the top-5 topics in the
last 7 days vs the prior 30 days. If ≥3 positions have changed,
surface DRIFT so the operator can choose to investigate.
"""
from __future__ import annotations

from collections import Counter

from olympus.monsters.hydra.head import Head, HeadFinding, Severity
from olympus.titans.cronus import Cronus


RECENT_DAYS = 7
PRIOR_DAYS = 30
POSITION_THRESHOLD = 3


class HeadTopicDrift(Head):
    NAME = "topic_drift"
    SLICE = "notekeeper/topic-distribution"
    IMMORTAL = False

    def observe(self) -> list[HeadFinding]:
        from notekeeper.notes import all_notes
        notes = all_notes()
        if not notes:
            return [self._finding(self.SLICE, Severity.INFO,
                "no notes yet; no drift to observe")]

        recent_topics: Counter[str] = Counter()
        prior_topics: Counter[str] = Counter()
        for n in notes:
            age_days = Cronus.age_seconds(n.captured_at) / 86400.0
            if age_days <= RECENT_DAYS:
                for t in n.topics:
                    recent_topics[t] += 1
            elif age_days <= PRIOR_DAYS + RECENT_DAYS:
                for t in n.topics:
                    prior_topics[t] += 1

        recent_top5 = [t for t, _ in recent_topics.most_common(5)]
        prior_top5 = [t for t, _ in prior_topics.most_common(5)]

        if not recent_top5 or not prior_top5:
            return [self._finding(self.SLICE, Severity.INFO,
                f"insufficient data for drift (recent={len(recent_top5)}, "
                f"prior={len(prior_top5)})")]

        # Count topics that appear in recent but at a different position in prior
        shifted = 0
        for i, topic in enumerate(recent_top5):
            if topic not in prior_top5:
                shifted += 1
                continue
            j = prior_top5.index(topic)
            if abs(i - j) >= POSITION_THRESHOLD:
                shifted += 1

        if shifted >= POSITION_THRESHOLD:
            return [self._finding(
                self.SLICE, Severity.DRIFT,
                f"{shifted} top-5 topic(s) shifted ≥{POSITION_THRESHOLD} positions "
                f"between {RECENT_DAYS}-day and {PRIOR_DAYS}-day windows",
                recent=recent_top5, prior=prior_top5,
            )]
        return [self._finding(self.SLICE, Severity.INFO,
            f"topic stability — top-5 mostly unchanged ({shifted} shifts)")]


def attach_to_hydra() -> None:
    """Call once at deployment startup."""
    from olympus.monsters.hydra import hydra
    if not any(type(h) is HeadTopicDrift for h in hydra.heads()):
        hydra.attach(HeadTopicDrift())
