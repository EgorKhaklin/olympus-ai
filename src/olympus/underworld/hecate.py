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

from olympus.primordials.tartarus import quarantine


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
        *,
        backoff: str = "fibonacci",
        base_seconds: float = 0.0,
        sleep_fn: Callable[[float], None] | None = None,
    ) -> T | None:
        """Try `attempt`. If it raises:
          1. Up to `max_retries` retries (if on.retry is provided).
          2. Quarantine the exception via Tartarus.
          3. Call on.abandon if provided, else on.escalate.

        Phi arc: retry timing uses Fibonacci backoff by default
        (`pythagoras.fib_backoff`). The ratio between successive
        delays approaches φ ≈ 1.618 — smoother than exponential's
        2.0. Pass `backoff='none'` to disable; pass `sleep_fn` to
        actually sleep between retries (omitted by default so existing
        callers don't gain a side-effect).
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
                    delay = self._compute_delay(
                        attempt_index=i,
                        backoff=backoff,
                        base_seconds=base_seconds,
                    )
                    if sleep_fn is not None and delay > 0:
                        sleep_fn(delay)
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

    @staticmethod
    def _compute_delay(*, attempt_index: int, backoff: str,
                        base_seconds: float) -> float:
        """Pure function — no I/O — returns seconds.

        backoff='fibonacci' → pythagoras.fib_backoff (default)
        backoff='fixed'      → base_seconds × (attempt+1)
        backoff='none'       → 0
        """
        if base_seconds <= 0 or backoff == "none":
            return 0.0
        if backoff == "fibonacci":
            from olympus.heroes.pythagoras import fib_backoff
            return fib_backoff(attempt_index, base_seconds=base_seconds)
        if backoff == "fixed":
            return base_seconds * (attempt_index + 1)
        return 0.0


hecate = Hecate()
at_crossroads = hecate.at_crossroads
