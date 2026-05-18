"""Apollo's prophecy cycle becomes operational.

The claim: predictions whose horizon has passed are auto-verified at
session start. Outcomes are recorded in Mnemosyne. acceptance_rate()
reflects reality.
"""
from __future__ import annotations

import pathlib as _pl
import sys as _sys
_ROOT = _pl.Path(__file__).resolve().parent.parent
_SRC = _ROOT / "src"
if str(_SRC) not in _sys.path:
    _sys.path.insert(0, str(_SRC))

import datetime
import unittest


class TestProphecyCycle(unittest.TestCase):

    def _fresh_apollo(self):
        from olympus.olympians.apollo import Apollo
        return Apollo()

    def test_consult_due_verifies_only_past_horizon(self):
        a = self._fresh_apollo()
        from olympus.olympians.apollo import Prediction
        a.predict(Prediction(
            name="due-test-past",
            statement="past-horizon",
            horizon=datetime.date(2020, 1, 1),  # past
            verify=lambda: True,
        ))
        a.predict(Prediction(
            name="due-test-future",
            statement="future-horizon",
            horizon=datetime.date(2099, 1, 1),  # future
            verify=lambda: True,
        ))
        results = a.consult_due()
        names = {r["name"] for r in results}
        self.assertIn("due-test-past", names)
        self.assertNotIn("due-test-future", names)

    def test_consult_due_records_in_mnemosyne(self):
        from olympus.titans.mnemosyne import mnemosyne
        a = self._fresh_apollo()
        from olympus.olympians.apollo import Prediction
        a.predict(Prediction(
            name="mnemosyne-record-test",
            statement="x",
            horizon=datetime.date(2020, 1, 1),
            verify=lambda: True,
        ))
        before = len(mnemosyne.recall("prophecy.verified"))
        a.consult_due()
        after = len(mnemosyne.recall("prophecy.verified"))
        self.assertGreater(after, before)
        # The most recent prophecy.verified record names our prediction
        last = mnemosyne.recall("prophecy.verified")[-1]
        self.assertEqual(last.body.get("prediction"), "mnemosyne-record-test")
        self.assertIs(last.body.get("accepted"), True)

    def test_consult_due_records_rejected_outcomes(self):
        from olympus.titans.mnemosyne import mnemosyne
        a = self._fresh_apollo()
        from olympus.olympians.apollo import Prediction
        a.predict(Prediction(
            name="reject-test",
            statement="will be false",
            horizon=datetime.date(2020, 1, 1),
            verify=lambda: False,
        ))
        a.consult_due()
        last = mnemosyne.recall("prophecy.verified")[-1]
        self.assertEqual(last.body.get("prediction"), "reject-test")
        self.assertIs(last.body.get("accepted"), False)

    def test_consult_due_already_verified_skipped(self):
        a = self._fresh_apollo()
        from olympus.olympians.apollo import Prediction
        a.predict(Prediction(
            name="once-only",
            statement="x",
            horizon=datetime.date(2020, 1, 1),
            verify=lambda: True,
        ))
        first = a.consult_due()
        second = a.consult_due()
        # Already-verified predictions are skipped on subsequent calls
        first_names = {r["name"] for r in first}
        second_names = {r["name"] for r in second}
        self.assertIn("once-only", first_names)
        self.assertNotIn("once-only", second_names)

    def test_acceptance_rate_reflects_outcomes(self):
        a = self._fresh_apollo()
        from olympus.olympians.apollo import Prediction
        # 2 truthy, 1 falsy
        for i, vf in enumerate([lambda: True, lambda: True, lambda: False]):
            a.predict(Prediction(
                name=f"rate-test-{i}",
                statement="x",
                horizon=datetime.date(2020, 1, 1),
                verify=vf,
            ))
        a.consult_due()
        self.assertAlmostEqual(a.acceptance_rate(), 2.0 / 3.0, places=4)


if __name__ == "__main__":
    unittest.main()
