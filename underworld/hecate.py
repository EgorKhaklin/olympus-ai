"""Hecate — goddess of crossroads, magic, and the in-between.

Hecate stood where three roads met, torch in each hand, attending to
transitions between states. In Olympus, Hecate handles error recovery
and state transitions — the moment something is failing and could go
one of several ways.

Use Hecate when you need to choose a recovery path: retry, abandon,
quarantine, or escalate.
"""
from __future__ import annotations

import logging
from typing import Callable, TypeVar
from dataclasses import dataclass

from primordials.tartarus import quarantine


T = TypeVar("T")
logger = logging.getLogger("olympus.hecate")


@dataclass
class Crossroads:
    """A decision point. Each of the four roads is a callable."""
    retry: Callable[[], T] | None = None        # try again
    abandon: Callable[[], T] | None = None      # give up gracefully
    descend: Callable[[T], None] | None = None  # send to underworld archive
    escalate: Callable[[Exception], None] | None = None  # raise to Zeus


class Hecate:
    """Crossroads attendant. Given a failing operation, chooses the
    path that satisfies the constitution."""

    def at_crossroads(
        self,
        attempt: Callable[[], T],
        on: Crossroads,
        max_retries: int = 3,
    ) -> T | None:
        """Try `attempt`. If it raises:
          1. Up to `max_retries` retries (if on.retry is provided).
          2. Quarantine the exception via Tartarus.
          3. Call on.abandon if provided, else on.escalate.
        """
        last_exc: Exception | None = None
        retries = max_retries if on.retry else 0
        for i in range(retries + 1):
            try:
                return attempt()
            except Exception as exc:
                last_exc = exc
                logger.warning(
                    "Hecate: attempt failed (%d/%d): %s",
                    i + 1, retries + 1, exc,
                )
                if i < retries and on.retry:
                    on.retry()
                    continue
                break

        # All retries exhausted
        if last_exc is not None:
            quarantine(
                {"exc_type": type(last_exc).__name__, "exc": str(last_exc)},
                reason="hecate: attempt exhausted retries",
                witness="hecate",
            )

        if on.abandon:
            return on.abandon()

        if on.escalate and last_exc:
            on.escalate(last_exc)

        if last_exc:
            raise last_exc
        return None


hecate = Hecate()
at_crossroads = hecate.at_crossroads
