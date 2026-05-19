"""Heracles benchmark harness — deterministic, golden, regression-aware.

The claim being tested: the canonical benchmark suite runs end-to-end;
every task records to heracles.benchmark; Ananke-seeded shuffle is
deterministic; the regression flag fires when a previously-passing
task fails.
"""
from __future__ import annotations

import pathlib as _pl
import sys as _sys
_ROOT = _pl.Path(__file__).resolve().parent.parent
_SRC = _ROOT / "src"
if str(_SRC) not in _sys.path:
    _sys.path.insert(0, str(_SRC))

import unittest


class TestHeraclesBenchmark(unittest.TestCase):

    def test_canonical_suite_runs(self):
        from olympus.heroes.heracles import run_canonical_benchmark
        report = run_canonical_benchmark(runner="heuristic")
        self.assertGreater(report.total, 0)
        self.assertEqual(len(report.results), report.total)

    def test_all_canonical_tasks_pass(self):
        """The shipped canonical suite must be fully green by default —
        otherwise the harness's regression detection is meaningless."""
        from olympus.heroes.heracles import run_canonical_benchmark
        report = run_canonical_benchmark(runner="heuristic")
        failures = [r for r in report.results if not r.correct]
        # Note: the deterministic-shuffle task uses a lax correct_fn
        # (just verifies it's a permutation), so it should pass too.
        self.assertEqual(
            failures, [],
            f"canonical benchmark must be green; failures: "
            f"{[(f.task, f.error or f.output) for f in failures]}",
        )

    def test_pass_recorded(self):
        from olympus.heroes.heracles import run_canonical_benchmark
        from olympus.titans.mnemosyne import mnemosyne
        before = len(mnemosyne.recall("heracles.benchmark-pass"))
        run_canonical_benchmark(runner="heuristic-test-pass")
        after = len(mnemosyne.recall("heracles.benchmark-pass"))
        self.assertGreater(after, before)

    def test_individual_results_recorded(self):
        from olympus.heroes.heracles import run_canonical_benchmark
        from olympus.titans.mnemosyne import mnemosyne
        before = len(mnemosyne.recall("heracles.benchmark"))
        run_canonical_benchmark(runner="heuristic-test-individual")
        after = len(mnemosyne.recall("heracles.benchmark"))
        # At least one record per task in the suite
        self.assertGreaterEqual(after - before, 5)

    def test_ananke_seeded_shuffle_reproducible(self):
        """Two runs of the same benchmark task must produce the
        same output (Ananke seed makes shuffle deterministic)."""
        from olympus.primordials.ananke import ananke
        from olympus.heroes.heracles import _bench_runner_random_shuffle
        rng_a = ananke.rng("bench:shuffle-7")
        rng_b = ananke.rng("bench:shuffle-7")
        result_a = _bench_runner_random_shuffle(
            rng_a, {"items": [1, 2, 3, 4, 5, 6, 7]})
        result_b = _bench_runner_random_shuffle(
            rng_b, {"items": [1, 2, 3, 4, 5, 6, 7]})
        self.assertEqual(result_a, result_b)
        # And it's a valid permutation
        self.assertEqual(set(result_a), set(range(1, 8)))

    def test_regression_detected(self):
        """If a previously-passing task fails, regressed=True."""
        from olympus.heroes.heracles import (BenchmarkTask, run_benchmark)
        # First run: passes
        task = BenchmarkTask(
            name=f"reg-test-{_pl.Path(__file__).stem}",
            seed_name="bench:reg-test",
            input={},
            expected=42,
            runner_fn=lambda rng, inp: 42,
        )
        r1 = run_benchmark([task], runner="reg-test-runner")
        self.assertTrue(r1.results[0].correct)
        self.assertFalse(r1.results[0].regressed)
        # Second run with a broken runner: previously passed, now fails
        task_broken = BenchmarkTask(
            name=task.name, seed_name=task.seed_name,
            input={}, expected=42,
            runner_fn=lambda rng, inp: 99,  # wrong
        )
        r2 = run_benchmark([task_broken], runner="reg-test-runner")
        self.assertFalse(r2.results[0].correct)
        self.assertTrue(
            r2.results[0].regressed,
            "regression should be flagged when prior was correct + new is wrong",
        )


if __name__ == "__main__":
    unittest.main()
