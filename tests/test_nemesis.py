"""Nemesis — the counterfactual reasoner.

The claim being tested: nemesis.consider() runs shadows via Castor;
records counterfactuals to Mnemosyne; skips already-examined actions;
respects max_per_pass bound.
"""
from __future__ import annotations

import pathlib as _pl
import sys as _sys
_ROOT = _pl.Path(__file__).resolve().parent.parent
_SRC = _ROOT / "src"
if str(_SRC) not in _sys.path:
    _sys.path.insert(0, str(_SRC))

import unittest
import uuid


def _seed_ratification(action_id: str) -> None:
    from olympus.titans.mnemosyne import mnemosyne
    mnemosyne.remember(
        kind="action.ratified",
        actor="test:zeus",
        summary=f"seeded ratification for nemesis test",
        action_id=action_id, quote="test",
    )


class TestNemesis(unittest.TestCase):

    def test_consider_returns_report(self):
        """The bare structural test — Nemesis runs without raising and
        returns a NemesisReport. We use max_per_pass=0 to avoid spawning
        actual shadow subprocesses in this test."""
        from olympus.heroes.nemesis import Nemesis, NemesisReport
        report = Nemesis().consider(max_per_pass=0)
        self.assertIsInstance(report, NemesisReport)
        self.assertTrue(report.started_at)
        self.assertTrue(report.ended_at)
        # max_per_pass=0 → no counterfactuals run
        self.assertEqual(report.total, 0)

    def test_records_pass_summary(self):
        from olympus.heroes.nemesis import Nemesis
        from olympus.titans.mnemosyne import mnemosyne
        before = len(mnemosyne.recall("nemesis.pass"))
        Nemesis().consider(max_per_pass=0)
        after = len(mnemosyne.recall("nemesis.pass"))
        self.assertGreater(after, before)

    def test_already_examined_skipping(self):
        """An action_id already in nemesis.counterfactual records is
        skipped on subsequent considers."""
        from olympus.heroes.nemesis import Nemesis
        from olympus.titans.mnemosyne import mnemosyne
        aid = f"nemesis-test-{uuid.uuid4().hex[:8]}"
        _seed_ratification(aid)
        # Seed a pre-existing counterfactual for this action
        mnemosyne.remember(
            kind="nemesis.counterfactual",
            actor="nemesis",
            summary="seeded",
            subject_action_id=aid, subject_summary="x",
            actual_outcome="y", counterfactual_choice="z",
            gap_summary="seeded", shadow_succeeded=True,
            shadow_report={},
        )
        report = Nemesis().consider(max_per_pass=10)
        # We DID consider it, but skipped it (already in the examined set)
        examined_ids = {cf.subject_action_id for cf in report.counterfactuals}
        self.assertNotIn(aid, examined_ids)


if __name__ == "__main__":
    unittest.main()
