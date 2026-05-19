"""Atalanta scalability harness — measure how operations scale.

The claim being tested: scale() runs build/run/teardown per size;
returns ScaleReport with monotonically non-decreasing percentiles
(in expectation; allow noise); records each point to Mnemosyne;
handles operations that error per size without aborting the report.
"""
from __future__ import annotations

import pathlib as _pl
import sys as _sys
_ROOT = _pl.Path(__file__).resolve().parent.parent
_SRC = _ROOT / "src"
if str(_SRC) not in _sys.path:
    _sys.path.insert(0, str(_SRC))

import unittest


class TestAtalantaScale(unittest.TestCase):

    def test_scale_returns_report(self):
        from olympus.heroes.atalanta import atalanta, ScaleReport
        report = atalanta.scale(
            "test-noop",
            build_state=lambda n: n,
            run_op=lambda s: None,
            sizes=[1, 10, 100],
            iterations_per_size=5,
        )
        self.assertIsInstance(report, ScaleReport)
        self.assertEqual(len(report.points), 3)

    def test_scale_records_points(self):
        from olympus.heroes.atalanta import atalanta
        from olympus.titans.mnemosyne import mnemosyne
        before = len(mnemosyne.recall("atalanta.scale-point"))
        atalanta.scale(
            "test-record",
            build_state=lambda n: list(range(n)),
            run_op=lambda lst: sum(lst),
            sizes=[10, 100],
            iterations_per_size=3,
        )
        after = len(mnemosyne.recall("atalanta.scale-point"))
        self.assertEqual(after - before, 2)

    def test_scale_grows_with_size(self):
        """For a quadratic-time operation, p50 should clearly grow
        with size — not asserting strict ordering due to timing noise,
        but the largest size should be measurably slower than the
        smallest."""
        from olympus.heroes.atalanta import atalanta
        # An intentionally O(n²) op so growth is visible
        def quad(lst):
            total = 0
            for x in lst:
                for y in lst:
                    total += x * y
            return total
        report = atalanta.scale(
            "test-quad",
            build_state=lambda n: list(range(n)),
            run_op=quad,
            sizes=[10, 200],
            iterations_per_size=3,
        )
        small_p50 = report.points[0].p50_ms
        large_p50 = report.points[-1].p50_ms
        self.assertGreater(large_p50, small_p50,
            f"p50 at n=200 should exceed p50 at n=10 (saw "
            f"{large_p50:.3f}ms vs {small_p50:.3f}ms)")

    def test_scale_handles_op_error_per_size(self):
        """If run_op raises at one size, the point captures the error
        but the rest of the sizes still run."""
        from olympus.heroes.atalanta import atalanta

        def runner(state):
            if state == 100:
                raise RuntimeError("intentional at n=100")

        report = atalanta.scale(
            "test-error",
            build_state=lambda n: n,
            run_op=runner,
            sizes=[10, 100, 200],
            iterations_per_size=3,
        )
        self.assertEqual(len(report.points), 3)
        # The middle point has an error; the others ran
        self.assertEqual(report.points[0].error, "")
        self.assertIn("intentional", report.points[1].error)
        self.assertEqual(report.points[2].error, "")

    def test_percentile_helper_is_correct(self):
        from olympus.heroes.atalanta import _percentile
        samples = [1.0, 2.0, 3.0, 4.0, 5.0]
        self.assertEqual(_percentile(samples, 0), 1.0)
        self.assertEqual(_percentile(samples, 100), 5.0)
        self.assertEqual(_percentile(samples, 50), 3.0)


if __name__ == "__main__":
    unittest.main()
