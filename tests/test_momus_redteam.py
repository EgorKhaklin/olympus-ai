"""Momus red-team — the AP catalog auditing itself.

The claim being tested: red_team() runs the curated adversarial
corpus through the AP catalog; reports which cases were correctly
handled vs. which slipped through or false-alarmed; records the pass
to Mnemosyne. The most important assertion: a stock release of Momus
correctly handles 100% of the corpus (no slipped, no false alarms).
"""
from __future__ import annotations

import pathlib as _pl
import sys as _sys
_ROOT = _pl.Path(__file__).resolve().parent.parent
_SRC = _ROOT / "src"
if str(_SRC) not in _sys.path:
    _sys.path.insert(0, str(_SRC))

import unittest


class TestMomusRedTeam(unittest.TestCase):

    def test_red_team_returns_report(self):
        from olympus.heroes.momus import Momus, RedTeamReport
        report = Momus().red_team()
        self.assertIsInstance(report, RedTeamReport)
        self.assertGreater(report.total, 0)
        self.assertEqual(len(report.results), report.total)

    def test_pass_recorded_to_mnemosyne(self):
        from olympus.heroes.momus import Momus
        from olympus.titans.mnemosyne import mnemosyne
        before = len(mnemosyne.recall("momus.red-team"))
        Momus().red_team()
        after = len(mnemosyne.recall("momus.red-team"))
        self.assertGreater(after, before)

    def test_all_corpus_cases_correctly_handled(self):
        """The stock Momus must handle every corpus case correctly.
        If this fails, either the AP catalog has a gap (slipped-through)
        or it's over-aggressive (false alarms). Either way, the
        corpus + catalog combination needs tuning."""
        from olympus.heroes.momus import Momus
        report = Momus().red_team()
        self.assertEqual(report.slipped_through, [],
            f"AP catalog gaps detected — these adversarial proposals "
            f"slipped through: "
            f"{[c.name for c in report.slipped_through]}")
        self.assertEqual(report.false_alarms, [],
            f"AP catalog over-aggressive — these legitimate proposals "
            f"were flagged: {[c.name for c in report.false_alarms]}")
        self.assertEqual(report.correct, report.total)

    def test_corpus_has_both_should_catch_and_legitimate_cases(self):
        from olympus.heroes.momus import _ADVERSARIAL_CORPUS
        should_catch = sum(1 for c in _ADVERSARIAL_CORPUS if c.should_catch)
        legitimate = sum(1 for c in _ADVERSARIAL_CORPUS if not c.should_catch)
        self.assertGreaterEqual(should_catch, 5,
            "corpus must include enough adversarial cases to exercise "
            "every AP at least once")
        self.assertGreaterEqual(legitimate, 2,
            "corpus must include legitimate cases to test for false alarms")


if __name__ == "__main__":
    unittest.main()
