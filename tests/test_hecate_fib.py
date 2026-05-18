"""Hecate uses Fibonacci backoff (phi arc).

The claim being tested: _compute_delay returns Fibonacci-scaled
delays by default; 'fixed' and 'none' work as documented; base=0
returns 0; sleep_fn is called with the computed delay if provided.
"""
from __future__ import annotations

import pathlib as _pl
import sys as _sys
_ROOT = _pl.Path(__file__).resolve().parent.parent
_SRC = _ROOT / "src"
if str(_SRC) not in _sys.path:
    _sys.path.insert(0, str(_SRC))

import unittest


class TestHecateFibonacciBackoff(unittest.TestCase):

    def test_compute_delay_fibonacci(self):
        from olympus.underworld.hecate import Hecate
        from olympus.heroes.pythagoras import fib_backoff
        h = Hecate()
        for i in range(5):
            self.assertAlmostEqual(
                h._compute_delay(attempt_index=i,
                                  backoff="fibonacci",
                                  base_seconds=1.0),
                fib_backoff(i, base_seconds=1.0),
                places=8,
            )

    def test_compute_delay_fixed(self):
        from olympus.underworld.hecate import Hecate
        h = Hecate()
        self.assertEqual(
            h._compute_delay(attempt_index=2, backoff="fixed",
                              base_seconds=0.5),
            1.5,  # 0.5 * (2 + 1)
        )

    def test_compute_delay_none(self):
        from olympus.underworld.hecate import Hecate
        h = Hecate()
        self.assertEqual(
            h._compute_delay(attempt_index=5, backoff="none",
                              base_seconds=10.0),
            0.0,
        )

    def test_compute_delay_base_zero_returns_zero(self):
        from olympus.underworld.hecate import Hecate
        h = Hecate()
        self.assertEqual(
            h._compute_delay(attempt_index=3, backoff="fibonacci",
                              base_seconds=0.0),
            0.0,
        )

    def test_sleep_fn_invoked_between_retries(self):
        """When sleep_fn + base_seconds are provided, the backoff
        actually paces the retries."""
        from olympus.underworld.hecate import Hecate, Crossroads
        slept: list[float] = []
        calls: list[int] = []

        def attempt():
            calls.append(1)
            if len(calls) < 3:
                raise RuntimeError("flaky")
            return "ok"

        def fake_sleep(s: float) -> None:
            slept.append(s)

        result = Hecate().at_crossroads(
            attempt,
            on=Crossroads(retry=lambda: None),
            max_retries=3,
            backoff="fibonacci",
            base_seconds=1.0,
            sleep_fn=fake_sleep,
        )
        self.assertEqual(result, "ok")
        # 2 retries happened → 2 sleeps
        self.assertEqual(len(slept), 2)
        # Strictly non-decreasing
        for i in range(1, len(slept)):
            self.assertGreaterEqual(slept[i], slept[i-1])

    def test_existing_callers_unaffected(self):
        """Pre-phi-arc callers passed no backoff args. With
        base_seconds=0 (the default), no sleep is computed and no
        sleep_fn is required."""
        from olympus.underworld.hecate import Hecate, Crossroads
        attempts = [0]

        def attempt():
            attempts[0] += 1
            if attempts[0] < 2:
                raise RuntimeError("flaky")
            return "ok"

        result = Hecate().at_crossroads(
            attempt,
            on=Crossroads(retry=lambda: None),
            max_retries=2,
        )
        self.assertEqual(result, "ok")


if __name__ == "__main__":
    unittest.main()
