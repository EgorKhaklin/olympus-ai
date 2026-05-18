"""Euterpe — musical consonance scoring.

The claim being tested: octave-invariant scoring; exact intervals
get score=1.0; pure dissonance gets low score; classification
buckets are correct.
"""
from __future__ import annotations

import pathlib as _pl
import sys as _sys
_ROOT = _pl.Path(__file__).resolve().parent.parent
_SRC = _ROOT / "src"
if str(_SRC) not in _sys.path:
    _sys.path.insert(0, str(_SRC))

import unittest


class TestEuterpeConsonance(unittest.TestCase):

    def test_intervals_returns_canonical_set(self):
        from olympus.muses.euterpe import euterpe
        names = {n for n, _ in euterpe.intervals()}
        for required in ("unison", "octave", "perfect_fifth",
                          "perfect_fourth", "major_third"):
            self.assertIn(required, names)

    def test_octave_is_perfect(self):
        from olympus.muses.euterpe import euterpe
        c = euterpe.consonance(2.0)
        # Octave folds to unison (2.0 → 1.0), so nearest is unison
        # OR octave depending on the impl; either way it should be
        # perfect-class
        self.assertEqual(c.consonance_class, "perfect")
        self.assertAlmostEqual(c.score, 1.0, places=4)

    def test_perfect_fifth_is_perfect(self):
        from olympus.muses.euterpe import euterpe
        c = euterpe.consonance(1.5)
        self.assertEqual(c.nearest_interval, "perfect_fifth")
        self.assertAlmostEqual(c.score, 1.0, places=4)

    def test_perfect_fourth_is_perfect(self):
        from olympus.muses.euterpe import euterpe
        c = euterpe.consonance(4.0 / 3.0)
        self.assertEqual(c.nearest_interval, "perfect_fourth")
        self.assertAlmostEqual(c.score, 1.0, places=4)

    def test_octave_invariance(self):
        """1.5 (fifth) and 3.0 (fifth above octave) and 0.75 (fifth
        below) should all score as perfect_fifth."""
        from olympus.muses.euterpe import euterpe
        for r in (1.5, 3.0, 0.75):
            c = euterpe.consonance(r)
            self.assertEqual(c.nearest_interval, "perfect_fifth",
                f"{r} should fold to perfect_fifth, got "
                f"{c.nearest_interval}")

    def test_dissonance(self):
        """A tritone-ish ratio (≈1.414) is dissonant by classical
        standards — well off any consonant interval."""
        from olympus.muses.euterpe import euterpe
        c = euterpe.consonance(1.414)  # √2 ≈ tritone
        self.assertLess(c.score, 0.5)
        self.assertEqual(c.consonance_class, "dissonant")

    def test_nan_handled(self):
        from olympus.muses.euterpe import euterpe
        c = euterpe.consonance(float("nan"))
        self.assertEqual(c.consonance_class, "dissonant")
        self.assertEqual(c.nearest_interval, "undefined")


if __name__ == "__main__":
    unittest.main()
