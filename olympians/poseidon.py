"""Poseidon — earth-shaker, lord of the sea.

Poseidon's domain is the moving water: streams, currents, tides. In
Olympus, Poseidon is the data-flow primitive — a simple in-memory
event bus with subscribe / publish semantics. The sea is always in
motion.

This is the minimal substrate; deployments add backing (Redis, Kafka,
SQS) by subclassing.
"""
from __future__ import annotations

import threading
from collections import defaultdict
from typing import Callable, Any


class Poseidon:
    """In-memory publish/subscribe. Thread-safe; subscribers run inline
    on the publisher thread unless wrapped via Nyx.

    For production deployments, swap the implementation for a durable
    queue. Poseidon is the API; the sea-floor is yours.
    """

    def __init__(self) -> None:
        self._streams: dict[str, list[Callable[[Any], None]]] = defaultdict(list)
        self._lock = threading.RLock()
        self._published_count: dict[str, int] = defaultdict(int)

    def subscribe(self, stream: str, fn: Callable[[Any], None]) -> None:
        """Subscribe `fn` to `stream`. Each published event invokes `fn(event)`."""
        with self._lock:
            self._streams[stream].append(fn)

    def publish(self, stream: str, event: Any) -> int:
        """Publish `event` to `stream`. Returns the number of subscribers
        that received it."""
        with self._lock:
            subs = list(self._streams.get(stream, []))
            self._published_count[stream] += 1
        for fn in subs:
            try:
                fn(event)
            except Exception:
                # Subscriber failure does not break the stream
                # (Hecate's domain — but at the substrate level, we just
                # don't drown the publisher)
                pass
        return len(subs)

    def stats(self) -> dict[str, int]:
        """Per-stream published-event count."""
        with self._lock:
            return dict(self._published_count)


poseidon = Poseidon()
