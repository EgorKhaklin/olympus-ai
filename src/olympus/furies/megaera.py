"""Megaera — the jealous one, middle of the Furies.

Megaera punished marital infidelity and oath-breaking among kin. In
Olympus she watches for concurrency violations: two writers entering
the same resource without coordination, two threads claiming the
same lock, the silent races that produce inconsistency.
"""
from __future__ import annotations

import contextlib
import threading
from collections import defaultdict
from dataclasses import dataclass


@dataclass
class Trespass:
    resource: str
    incumbent: str
    intruder: str
    detected_at: str


class Megaera:
    """Concurrency-violation watcher. Tracks which thread holds each
    named resource; if a second thread tries to claim without waiting,
    a Trespass is recorded."""

    def __init__(self) -> None:
        self._holders: dict[str, str] = {}
        self._lock = threading.Lock()
        self.trespasses: list[Trespass] = []

    @contextlib.contextmanager
    def watch(self, resource: str):
        """Context manager: claim `resource` for the duration. If
        another thread held it when this enters, records a Trespass."""
        me = threading.current_thread().name
        from olympus.primordials.nyx import Nyx
        with self._lock:
            incumbent = self._holders.get(resource)
            if incumbent is not None and incumbent != me:
                self.trespasses.append(Trespass(
                    resource=resource, incumbent=incumbent,
                    intruder=me, detected_at=Nyx.now().isoformat(),
                ))
            self._holders[resource] = me
        try:
            yield
        finally:
            with self._lock:
                if self._holders.get(resource) == me:
                    self._holders.pop(resource, None)


megaera = Megaera()
