"""Eros — generative force, oldest of the gods.

In Hesiod, Eros is one of the first beings — not the love-god of later
poetry, but the primordial drive that brings things into existence.
Olympus's Eros is the creation primitive: deterministic factories that
generate new components from a seed.

Use Eros when you need to bring a thing into being for the first time.
"""
from __future__ import annotations

import hashlib
import string
import secrets
from typing import Iterable


class Eros:
    """The generative force. Deterministic and seedable; same seed
    always produces the same offspring."""

    @staticmethod
    def begotten_id(prefix: str, seed: str) -> str:
        """Deterministic id from a seed. Same (prefix, seed) → same id.
        The prefix is human-readable; the suffix is the first 12 hex
        chars of the SHA-256 of the seed."""
        h = hashlib.sha256(seed.encode("utf-8")).hexdigest()[:12]
        return f"{prefix}-{h}"

    @staticmethod
    def fresh_id(prefix: str, length: int = 12) -> str:
        """Cryptographically-random id. Use when uniqueness matters
        more than reproducibility."""
        alphabet = string.ascii_lowercase + string.digits
        suffix = "".join(secrets.choice(alphabet) for _ in range(length))
        return f"{prefix}-{suffix}"

    @staticmethod
    def threads(seed: str, count: int) -> Iterable[str]:
        """Yield `count` deterministic ids spun from a single seed.
        Used by Clotho when threading multiple fates from one cause."""
        for i in range(count):
            yield Eros.begotten_id("thread", f"{seed}::{i}")


generate = Eros()
