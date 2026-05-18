"""Pythagoras — sacred numerics.

The claim being tested: constants are correct; Fibonacci is correct;
golden-section search converges; harmony scoring is well-behaved;
Pythagorean triples are valid.
"""
from __future__ import annotations

import pathlib as _pl
import sys as _sys
_ROOT = _pl.Path(__file__).resolve().parent.parent
_SRC = _ROOT / "src"
if str(_SRC) not in _sys.path:
    _sys.path.insert(0, str(_SRC))

import math
import unittest


class TestConstants(unittest.TestCase):

    def test_phi_value(self):
        from olympus.heroes.pythagoras import PHI
        self.assertAlmostEqual(PHI, 1.6180339887498949, places=10)

    def test_phi_inverse_equals_phi_minus_one(self):
        """One of φ's defining relations: 1/φ = φ − 1."""
        from olympus.heroes.pythagoras import PHI, PHI_INVERSE
        self.assertAlmostEqual(PHI_INVERSE, PHI - 1.0, places=12)

    def test_phi_squared_equals_phi_plus_one(self):
        """The other defining relation: φ² = φ + 1."""
        from olympus.heroes.pythagoras import PHI
        self.assertAlmostEqual(PHI * PHI, PHI + 1.0, places=12)

    def test_pi_e_sqrts(self):
        from olympus.heroes.pythagoras import PI, E, SQRT2, SQRT3, SQRT5
        self.assertAlmostEqual(PI, math.pi)
        self.assertAlmostEqual(E, math.e)
        self.assertAlmostEqual(SQRT2 ** 2, 2.0, places=12)
        self.assertAlmostEqual(SQRT3 ** 2, 3.0, places=12)
        self.assertAlmostEqual(SQRT5 ** 2, 5.0, places=12)


class TestFibonacci(unittest.TestCase):

    def test_fibonacci_known(self):
        from olympus.heroes.pythagoras import fibonacci
        expected = [0, 1, 1, 2, 3, 5, 8, 13, 21, 34, 55, 89, 144]
        for i, want in enumerate(expected):
            self.assertEqual(fibonacci(i), want,
                             f"F({i}) should be {want}")

    def test_fibonacci_rejects_negative(self):
        from olympus.heroes.pythagoras import fibonacci
        with self.assertRaises(ValueError):
            fibonacci(-1)

    def test_fib_sequence(self):
        from olympus.heroes.pythagoras import fib_sequence
        self.assertEqual(fib_sequence(7), [0, 1, 1, 2, 3, 5, 8])
        self.assertEqual(fib_sequence(0), [])

    def test_fib_backoff_grows(self):
        from olympus.heroes.pythagoras import fib_backoff
        delays = [fib_backoff(i, base_seconds=1.0) for i in range(8)]
        # Strictly non-decreasing
        for i in range(1, len(delays)):
            self.assertGreaterEqual(delays[i], delays[i-1])

    def test_fib_backoff_ratio_approaches_phi(self):
        """Late Fibonacci ratios → φ."""
        from olympus.heroes.pythagoras import fib_backoff, PHI
        d10 = fib_backoff(10, base_seconds=1.0)
        d11 = fib_backoff(11, base_seconds=1.0)
        self.assertAlmostEqual(d11 / d10, PHI, places=2)

    def test_fib_backoff_capped(self):
        from olympus.heroes.pythagoras import fib_backoff
        # Large attempt + small cap → returns the cap
        self.assertEqual(fib_backoff(30, base_seconds=1.0,
                                       cap_seconds=10.0), 10.0)


class TestGoldenSectionSearch(unittest.TestCase):

    def test_finds_known_minimum(self):
        """Minimum of (x - 3)² is at x = 3."""
        from olympus.heroes.pythagoras import golden_section_search
        x, f = golden_section_search(
            lambda x: (x - 3.0) ** 2, lo=0.0, hi=10.0,
            tol=1e-6, name="test-min",
        )
        self.assertAlmostEqual(x, 3.0, places=4)
        self.assertLess(f, 1e-6)

    def test_finds_known_maximum(self):
        """Maximum of -(x - 2)² is at x = 2."""
        from olympus.heroes.pythagoras import golden_section_search
        x, f = golden_section_search(
            lambda x: -(x - 2.0) ** 2, lo=0.0, hi=10.0,
            tol=1e-6, minimize=False, name="test-max",
        )
        self.assertAlmostEqual(x, 2.0, places=4)

    def test_rejects_bad_bounds(self):
        from olympus.heroes.pythagoras import golden_section_search
        with self.assertRaises(ValueError):
            golden_section_search(lambda x: x, lo=10.0, hi=0.0)

    def test_records_to_mnemosyne(self):
        from olympus.heroes.pythagoras import golden_section_search
        from olympus.titans.mnemosyne import mnemosyne
        before = len(mnemosyne.recall("pythagoras.search"))
        golden_section_search(
            lambda x: x * x, lo=-1.0, hi=1.0, tol=1e-3,
            name="record-test",
        )
        after = len(mnemosyne.recall("pythagoras.search"))
        self.assertGreater(after, before)


class TestHarmony(unittest.TestCase):

    def test_harmony_phi_is_one(self):
        from olympus.heroes.pythagoras import harmony, PHI
        score = harmony(PHI)
        self.assertEqual(score.nearest_anchor, "phi")
        self.assertAlmostEqual(score.score, 1.0, places=6)

    def test_harmony_phi_inverse_is_one(self):
        from olympus.heroes.pythagoras import harmony, PHI_INVERSE
        score = harmony(PHI_INVERSE)
        self.assertEqual(score.nearest_anchor, "inverse_phi")
        self.assertAlmostEqual(score.score, 1.0, places=6)

    def test_harmony_unity(self):
        from olympus.heroes.pythagoras import harmony
        score = harmony(1.0)
        self.assertEqual(score.nearest_anchor, "unity")
        self.assertAlmostEqual(score.score, 1.0, places=6)

    def test_harmony_far_value_low_score(self):
        from olympus.heroes.pythagoras import harmony
        score = harmony(100.0)
        self.assertLess(score.score, 0.01)

    def test_harmony_nan_handled(self):
        from olympus.heroes.pythagoras import harmony
        score = harmony(float("nan"))
        self.assertEqual(score.score, 0.0)
        self.assertEqual(score.nearest_anchor, "undefined")


class TestPythagoreanTriples(unittest.TestCase):

    def test_triples_satisfy_theorem(self):
        from olympus.heroes.pythagoras import pythagorean_triples
        for a, b, c in pythagorean_triples(below=100):
            self.assertEqual(a * a + b * b, c * c,
                             f"triple ({a},{b},{c}) violates a²+b²=c²")

    def test_classic_triple_present(self):
        """The (3,4,5) triple must appear."""
        from olympus.heroes.pythagoras import pythagorean_triples
        trips = list(pythagorean_triples(below=10))
        self.assertIn((3, 4, 5), trips)


if __name__ == "__main__":
    unittest.main()
