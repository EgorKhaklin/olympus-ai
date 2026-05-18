"""S5 — Apollo falsifiability.

Every prediction is a predicate that can be checked. Predictions
without verify() are refused at register-time."""
from __future__ import annotations

import pathlib as _pl
import sys as _sys
_ROOT = _pl.Path(__file__).resolve().parent.parent
_SRC = _ROOT / "src"
if str(_SRC) not in _sys.path:
    _sys.path.insert(0, str(_SRC))

import datetime
import unittest

from olympus.olympians.apollo import Apollo, Prediction


def _fresh_apollo() -> Apollo:
    return Apollo()


class TestS5_Falsifiability(unittest.TestCase):

    def test_S5a_apollo_refuses_no_verify(self):
        a = _fresh_apollo()
        with self.assertRaises(ValueError):
            a.predict(Prediction(
                name="bad",
                statement="no verify",
                horizon=datetime.date(2099, 1, 1),
                verify=None,
            ))

    def test_S5b_apollo_accepts_callable_verify(self):
        a = _fresh_apollo()
        p = a.predict(Prediction(
            name="good", statement="has verify",
            horizon=datetime.date(2099, 1, 1),
            verify=lambda: True,
        ))
        self.assertEqual(p.name, "good")

    def test_S5c_consult_runs_verify_and_records_outcome(self):
        a = _fresh_apollo()
        a.predict(Prediction(
            name="will-be-true", statement="x",
            horizon=datetime.date.today(),
            verify=lambda: True,
        ))
        outcome = a.consult("will-be-true")
        self.assertTrue(outcome)
        # the prediction now carries .accepted
        self.assertTrue(a.by_name("will-be-true").accepted)

    def test_S5d_consult_handles_verify_returning_false(self):
        a = _fresh_apollo()
        a.predict(Prediction(
            name="will-be-false", statement="x",
            horizon=datetime.date.today(),
            verify=lambda: False,
        ))
        outcome = a.consult("will-be-false")
        self.assertFalse(outcome)
        self.assertFalse(a.by_name("will-be-false").accepted)

    def test_S5e_consult_handles_verify_raising(self):
        a = _fresh_apollo()
        def bad():
            raise RuntimeError("verify exploded")
        a.predict(Prediction(
            name="exploder", statement="x",
            horizon=datetime.date.today(),
            verify=bad,
        ))
        outcome = a.consult("exploder")
        self.assertIsNone(outcome)
        # the error is recorded in evidence
        ev = a.by_name("exploder").evidence
        self.assertIn("verify_error", ev)

    def test_S5f_acceptance_rate_only_counts_verified(self):
        a = _fresh_apollo()
        a.predict(Prediction("yes-1", "x", datetime.date.today(), lambda: True))
        a.predict(Prediction("yes-2", "x", datetime.date.today(), lambda: True))
        a.predict(Prediction("no-1",  "x", datetime.date.today(), lambda: False))
        a.predict(Prediction("pending", "x", datetime.date(2099, 1, 1), lambda: True))
        # Verify three; leave one pending
        a.consult("yes-1")
        a.consult("yes-2")
        a.consult("no-1")
        rate = a.acceptance_rate()
        self.assertAlmostEqual(rate, 2.0 / 3.0, places=4)

    def test_S5g_unverified_returns_none_acceptance_rate(self):
        a = _fresh_apollo()
        a.predict(Prediction("pending", "x", datetime.date.today(), lambda: True))
        # never consult
        self.assertIsNone(a.acceptance_rate())

    def test_S5h_predictions_listing(self):
        a = _fresh_apollo()
        for i in range(5):
            a.predict(Prediction(f"p-{i}", "x", datetime.date.today(),
                                 lambda: True))
        self.assertEqual(len(a.predictions()), 5)


if __name__ == "__main__":
    unittest.main()
