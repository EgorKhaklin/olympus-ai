"""notekeeper-specific Apollo predictions.

Two falsifiable predictions about the operator's behavior:

  fewer-than-N-stale-in-N-days  the operator will revisit / capture
                                related notes faster than they go stale
  topic-diversity-grows         topic diversity (distinct top-5) over
                                a 7-day window will grow month over month

Each prediction carries a verify() callable — S5 enforced.
"""
from __future__ import annotations

import datetime
from collections import Counter

from olympus.olympians.apollo import apollo, Prediction
from olympus.titans.cronus import Cronus


def _stale_count_under_N(threshold: int) -> bool:
    from notekeeper.notes import all_notes
    stale = sum(
        1 for n in all_notes()
        if Cronus.age_seconds(n.captured_at) / 86400.0 > 30
    )
    return stale < threshold


def _topic_diversity_growing() -> bool:
    """Compare last-7-days distinct-top-topics vs prior-7-days."""
    from notekeeper.notes import all_notes
    recent: Counter[str] = Counter()
    prior: Counter[str] = Counter()
    for n in all_notes():
        age = Cronus.age_seconds(n.captured_at) / 86400.0
        if age <= 7:
            for t in n.topics: recent[t] += 1
        elif age <= 14:
            for t in n.topics: prior[t] += 1
    return len(recent) > len(prior)


def register_with_apollo() -> None:
    """Call once at deployment startup. Idempotent: re-registering
    overwrites the existing prediction with the same name."""
    apollo.predict(Prediction(
        name="notekeeper.stale-under-50",
        statement=("Fewer than 50 notes will be stale (>30 days) "
                   "at the 30-day horizon."),
        horizon=datetime.date.today() + datetime.timedelta(days=30),
        verify=lambda: _stale_count_under_N(50),
    ))
    apollo.predict(Prediction(
        name="notekeeper.topic-diversity-growing",
        statement=("Distinct topics in the trailing 7 days will exceed "
                   "distinct topics in the preceding 7 days, on review."),
        horizon=datetime.date.today() + datetime.timedelta(days=14),
        verify=_topic_diversity_growing,
    ))
