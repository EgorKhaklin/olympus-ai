"""Ananke — deterministic seed source (the cannot-be-otherwise).

The claim being tested: the same name returns the same seed bytes,
across calls, across instances; rng() yields a deterministic
sequence; context() records the use to Mnemosyne; empty name raises.
"""
from __future__ import annotations

import pathlib as _pl
import sys as _sys
_ROOT = _pl.Path(__file__).resolve().parent.parent
_SRC = _ROOT / "src"
if str(_SRC) not in _sys.path:
    _sys.path.insert(0, str(_SRC))

import unittest


class TestAnanke(unittest.TestCase):

    def test_same_name_same_seed(self):
        from olympus.primordials.ananke import ananke
        s1 = ananke.seed("test:reproducibility")
        s2 = ananke.seed("test:reproducibility")
        self.assertEqual(s1, s2)

    def test_different_names_different_seeds(self):
        from olympus.primordials.ananke import ananke
        self.assertNotEqual(
            ananke.seed("test:a"),
            ananke.seed("test:b"),
        )

    def test_seed_is_64bit_int(self):
        from olympus.primordials.ananke import ananke
        s = ananke.seed("test:int-range")
        self.assertIsInstance(s, int)
        self.assertGreaterEqual(s, 0)
        self.assertLess(s, 1 << 64)

    def test_empty_name_raises(self):
        from olympus.primordials.ananke import ananke
        with self.assertRaises(ValueError):
            ananke.seed("")

    def test_seed_bytes(self):
        from olympus.primordials.ananke import ananke
        b1 = ananke.seed_bytes("test:bytes", n=32)
        b2 = ananke.seed_bytes("test:bytes", n=32)
        self.assertEqual(b1, b2)
        self.assertEqual(len(b1), 32)
        # Different lengths produce a prefix of the same material
        b64 = ananke.seed_bytes("test:bytes", n=64)
        self.assertEqual(b64[:32], b1)

    def test_rng_deterministic(self):
        from olympus.primordials.ananke import ananke
        r1 = ananke.rng("test:rng-determinism")
        r2 = ananke.rng("test:rng-determinism")
        seq1 = [r1.randint(0, 1000) for _ in range(10)]
        seq2 = [r2.randint(0, 1000) for _ in range(10)]
        self.assertEqual(seq1, seq2)

    def test_rng_shuffle_reproducible(self):
        from olympus.primordials.ananke import ananke
        items = list(range(20))
        a = items.copy()
        b = items.copy()
        ananke.rng("test:shuffle-20").shuffle(a)
        ananke.rng("test:shuffle-20").shuffle(b)
        self.assertEqual(a, b)
        # And it actually shuffles (not identity)
        self.assertNotEqual(a, list(range(20)))

    def test_context_yields_rng_and_records(self):
        from olympus.primordials.ananke import ananke
        from olympus.titans.mnemosyne import mnemosyne
        before = len(mnemosyne.recall("ananke.seeded"))
        with ananke.context("test:ctx",
                              purpose="unit-test") as rng:
            n = rng.randint(0, 100)
        after = len(mnemosyne.recall("ananke.seeded"))
        self.assertGreater(after, before)
        self.assertIsInstance(n, int)

    def test_seed_stable_across_python_invocations(self):
        """Sanity: SHA-256 is stable. The seed for 'olympus' is a
        known-fixed value across runs. (First 8 bytes of
        SHA-256(b'olympus') = 4b8823ed9e5c2392, big-endian.)"""
        from olympus.primordials.ananke import ananke
        expected = int.from_bytes(
            bytes.fromhex("4b8823ed9e5c2392"), "big"
        )
        self.assertEqual(ananke.seed("olympus"), expected)


if __name__ == "__main__":
    unittest.main()
