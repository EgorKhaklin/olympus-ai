"""Nyx — Night, mother of Sleep and Death.

Nyx is the personification of Night, born of Chaos. She is older than
the Olympians; even Zeus is wary of her. Olympus's Nyx handles
background processes — work that happens while no one is watching.

Use Nyx for cron jobs, async tasks, anything that runs after dark.
"""
from __future__ import annotations

import datetime
import threading
from typing import Callable


class Nyx:
    """Background-task scheduler. Each scheduled callable runs in its
    own daemon thread, returning when the program exits.

    Nyx does not persist anything across sessions — that is Mnemosyne's
    domain. Nyx is the night-shift: ephemeral, parallel, quiet.
    """

    def __init__(self) -> None:
        self._threads: list[threading.Thread] = []

    def after_dark(self, fn: Callable[[], None], name: str | None = None) -> threading.Thread:
        """Run `fn` in a daemon thread. Returns the thread handle."""
        t = threading.Thread(target=fn, name=name or fn.__name__, daemon=True)
        t.start()
        self._threads.append(t)
        return t

    def active(self) -> int:
        """Count of Nyx's children still in the dark."""
        return sum(1 for t in self._threads if t.is_alive())

    @staticmethod
    def now() -> datetime.datetime:
        """The hour, UTC. Nyx keeps no local time."""
        return datetime.datetime.now(datetime.timezone.utc)


nyx = Nyx()
after_dark = nyx.after_dark
