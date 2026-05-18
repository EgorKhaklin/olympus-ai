"""Chaos — the primordial void from which all things came.

In Hesiod's *Theogony*, Chaos is the first being: a yawning gap, the
unformed state before order. Olympus's Chaos module is the null /
uninitialized / empty primitive — the state a component is in before
it has been touched by any other deity.

Use Chaos when you need to express "this is genuinely nothing" — not
empty string, not None-as-error, but the philosophically prior state.
"""
from __future__ import annotations

from typing import Any


class Chaos:
    """The primordial void. Singleton. Comparable, hashable, falsy.

    `Chaos()` always returns the same instance. Use `void` as the
    canonical reference.
    """

    _instance: "Chaos | None" = None

    def __new__(cls) -> "Chaos":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __bool__(self) -> bool:
        return False

    def __repr__(self) -> str:
        return "<Chaos>"

    def __eq__(self, other: Any) -> bool:
        return isinstance(other, Chaos)

    def __hash__(self) -> int:
        return hash("Chaos")


void = Chaos()


def is_void(x: Any) -> bool:
    """True iff x is the primordial void (not just None or empty)."""
    return isinstance(x, Chaos)
