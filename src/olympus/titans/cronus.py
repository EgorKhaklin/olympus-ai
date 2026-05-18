"""Cronus — titan of time, deposed king of the cosmos.

Cronus was chief of the Titans, father of Zeus, who deposed him at
the Titanomachy. He swallowed his children to prevent the prophesied
overthrow; it happened anyway. In Olympus, Cronus is time itself —
schedules, durations, the count of moments.

Where Nyx handles ad-hoc background work, Cronus handles structured
schedules: cadences, recurring tasks, the choreography that
Terpsichore (the Muse of dance) reads from.
"""
from __future__ import annotations

import datetime
from dataclasses import dataclass
from typing import Callable


@dataclass(frozen=True)
class Cadence:
    """A named recurring schedule."""
    name: str
    period_seconds: float
    description: str

    @property
    def period(self) -> datetime.timedelta:
        return datetime.timedelta(seconds=self.period_seconds)


# Standard cadences. Each Olympus deployment can register its own.
STANDARD_CADENCES = {
    "moment":  Cadence("moment",         1,    "every second — pulse"),
    "minute":  Cadence("minute",         60,   "every minute"),
    "hour":    Cadence("hour",          3600,  "every hour"),
    "day":     Cadence("day",          86400,  "daily"),
    "week":    Cadence("week",        604800,  "weekly"),
    "month":   Cadence("month",      2592000,  "approximately monthly (30 days)"),
    "season":  Cadence("season",     7776000,  "approximately quarterly (90 days)"),
    "year":    Cadence("year",      31557600,  "approximately yearly (365.25 days)"),
}


class Cronus:
    """Time registry. Provides cadences and time-arithmetic helpers."""

    def __init__(self) -> None:
        self._cadences: dict[str, Cadence] = dict(STANDARD_CADENCES)

    def cadence(self, name: str) -> Cadence | None:
        return self._cadences.get(name)

    def register(self, c: Cadence) -> Cadence:
        self._cadences[c.name] = c
        return c

    def all(self) -> list[Cadence]:
        return list(self._cadences.values())

    @staticmethod
    def now() -> datetime.datetime:
        return datetime.datetime.now(datetime.timezone.utc)

    @staticmethod
    def age_seconds(when: datetime.datetime | str) -> float:
        """Seconds elapsed since `when` (UTC)."""
        if isinstance(when, str):
            when = datetime.datetime.fromisoformat(when.replace("Z", "+00:00"))
        if when.tzinfo is None:
            when = when.replace(tzinfo=datetime.timezone.utc)
        return (Cronus.now() - when).total_seconds()


cronus = Cronus()
