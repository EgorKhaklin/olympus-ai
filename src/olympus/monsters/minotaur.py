"""The Minotaur — bull-headed dweller of the Cretan labyrinth.

The Minotaur lived at the heart of Daedalus's labyrinth, demanding
seven youths every nine years. Theseus killed him using Ariadne's
thread. In Olympus, the Minotaur is the recursive-structure walker:
he descends into nested data with explicit step-tracking, refusing
to recurse past a safe depth.
"""
from __future__ import annotations

from typing import Any, Iterator


class MinotaurDepthExceeded(RuntimeError):
    pass


class Minotaur:
    """Recursive-structure walker with explicit depth cap."""

    def __init__(self, max_depth: int = 32) -> None:
        self.max_depth = max_depth

    def descend(self, obj: Any, depth: int = 0) -> Iterator[tuple[int, str, Any]]:
        """Yield (depth, key_path, leaf) for every leaf in `obj`.
        Refuses to recurse past max_depth (raises)."""
        if depth > self.max_depth:
            raise MinotaurDepthExceeded(
                f"minotaur: refused at depth {depth} (cap={self.max_depth})"
            )
        if isinstance(obj, dict):
            for k, v in obj.items():
                yield from self._walk(f"{k}", v, depth + 1)
        elif isinstance(obj, (list, tuple)):
            for i, v in enumerate(obj):
                yield from self._walk(f"[{i}]", v, depth + 1)
        else:
            yield (depth, "", obj)

    def _walk(self, prefix: str, value: Any, depth: int) -> Iterator[tuple[int, str, Any]]:
        if isinstance(value, (dict, list, tuple)):
            for d, sub, leaf in self.descend(value, depth):
                joined = f"{prefix}.{sub}" if sub else prefix
                yield (d, joined, leaf)
        else:
            yield (depth, prefix, value)


minotaur = Minotaur()
