"""Ananke — primordial of necessity, the cannot-be-otherwise.

In myth: Ananke was the personification of compulsion, inevitability,
and necessity — older than the gods. What Ananke decrees, even Zeus
must accept. The Greek word ἀνάγκη also means *constraint*.

In Olympus, Ananke is the **deterministic seed source**. Given a
*name*, she returns the same seed bytes every time — across runs,
machines, Python versions. This is what makes Olympus reproducible:
no benchmark, replay, or shadow run uses `os.urandom`, `time.time()`,
or `random.seed()` without a name. Everything goes through Ananke.

The mechanism is simple: SHA-256 of the name is the seed. There is no
state, no clock, no entropy source. **The same name always returns
the same bytes** — that is what necessity means.

Re-arguing the prior refusal. The missing-figures arc refused Ananke
on AP8+AP3 ("duplicates Furies / S-tests"). The new role is
*deterministic seed source for reproducibility* — distinct from
Furies (invariant enforcement) and from Themis (constitutional law).
Per Delphi 2026-05-18-akropolis-arc.md.
"""
from __future__ import annotations

import hashlib
import random
from contextlib import contextmanager
from dataclasses import dataclass, field
from typing import Iterator

from olympus.primordials.nyx import Nyx


@dataclass
class SeedRecord:
    """One use of Ananke — recorded so reproducibility is auditable."""
    name: str
    seed_hex: str          # first 16 hex chars of the SHA-256
    used_at: str
    purpose: str = ""


# ─────────────────────────────────────────────────────────
# Ananke — pure functions; no state; no I/O on the hot path
# ─────────────────────────────────────────────────────────


class Ananke:
    """The cannot-be-otherwise. SHA-256(name) → seed. No state."""

    @staticmethod
    def seed(name: str) -> int:
        """Return the deterministic 64-bit seed for `name`."""
        if not name:
            raise ValueError("Ananke.seed requires a non-empty name")
        digest = hashlib.sha256(name.encode("utf-8")).digest()
        # Take the first 8 bytes as a big-endian unsigned int
        return int.from_bytes(digest[:8], "big")

    @staticmethod
    def seed_bytes(name: str, *, n: int = 32) -> bytes:
        """Return n deterministic seed bytes for `name`. For larger
        keying material (e.g., a random.Random's full 624-word state),
        use rng() — this returns raw bytes for callers that prefer them."""
        if not name:
            raise ValueError("Ananke.seed_bytes requires a non-empty name")
        # Hash + extend if more than 32 bytes requested
        out = b""
        counter = 0
        while len(out) < n:
            material = name.encode("utf-8") + b":" + str(counter).encode("ascii")
            out += hashlib.sha256(material).digest()
            counter += 1
        return out[:n]

    @staticmethod
    def rng(name: str) -> random.Random:
        """Return a `random.Random` seeded deterministically from
        `name`. Same name → same RNG state → same sequence."""
        return random.Random(Ananke.seed(name))

    @staticmethod
    @contextmanager
    def context(name: str, *, purpose: str = "") -> Iterator[random.Random]:
        """A context manager that yields a deterministic RNG and
        records the use to Mnemosyne (S8 reconstructable). Operators
        can answer "what randomness did this benchmark use?" from
        the audit trail alone.
        """
        from olympus.titans.mnemosyne import mnemosyne
        digest_hex = hashlib.sha256(
            name.encode("utf-8")).hexdigest()[:16]
        rng = Ananke.rng(name)
        used_at = Nyx.now().isoformat()
        try:
            yield rng
        finally:
            mnemosyne.remember(
                kind="ananke.seeded",
                actor="ananke",
                summary=(f"seeded RNG for {name!r}"
                         + (f" — {purpose}" if purpose else "")),
                name=name,
                seed_hex=digest_hex,
                used_at=used_at,
                purpose=purpose,
            )


ananke = Ananke()
