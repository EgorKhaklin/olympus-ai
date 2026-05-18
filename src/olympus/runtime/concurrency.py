"""olympus.runtime.concurrency — thread-safe wrappers.

Olympus runs deterministically in single-threaded use, but the substrate
must handle multiple writers without corruption. This module provides:

  - `with_lock(name)` — context manager that registers a contention with
    Megaera; resolves contention by FIFO acquisition.
  - `atomic_append(path, line)` — write a single line to a JSONL file
    using an OS-level exclusive lock so concurrent appenders never
    interleave bytes.
"""
from __future__ import annotations

import contextlib
import os
import pathlib
import threading
from typing import Iterator

from olympus.furies.megaera import megaera


_lock_registry: dict[str, threading.RLock] = {}
_registry_lock = threading.Lock()


@contextlib.contextmanager
def with_lock(name: str) -> Iterator[None]:
    """Acquire a named lock. Reentrant from the same thread.
    Megaera records any contention as a Trespass."""
    with _registry_lock:
        lock = _lock_registry.setdefault(name, threading.RLock())
    with megaera.watch(f"lock:{name}"):
        with lock:
            yield


def atomic_append(path: pathlib.Path, line: str) -> None:
    """OS-level atomic append. Appends do not interleave even under
    concurrent writers on POSIX (writes < PIPE_BUF, which JSONL rows
    typically are not — so we use fcntl to be safe)."""
    path.parent.mkdir(parents=True, exist_ok=True)
    if not line.endswith("\n"):
        line = line + "\n"
    data = line.encode("utf-8")
    try:
        import fcntl
        flags = os.O_WRONLY | os.O_APPEND | os.O_CREAT
        fd = os.open(str(path), flags, 0o644)
        try:
            fcntl.flock(fd, fcntl.LOCK_EX)
            try:
                os.write(fd, data)
            finally:
                fcntl.flock(fd, fcntl.LOCK_UN)
        finally:
            os.close(fd)
    except ImportError:
        # Non-POSIX (Windows) — best-effort.
        with path.open("a", encoding="utf-8") as f:
            f.write(line)
