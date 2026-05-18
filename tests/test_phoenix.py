"""Phoenix — cyclical regeneration.

The claim being tested: phoenix.consider() finds rebirth candidates;
already-recorded candidates aren't re-emitted; the pass is recorded.
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
import uuid


class TestPhoenix(unittest.TestCase):

    def test_consider_returns_report(self):
        from olympus.heroes.phoenix import phoenix, RebirthReport
        report = phoenix.consider()
        self.assertIsInstance(report, RebirthReport)
        self.assertTrue(report.started_at)
        self.assertTrue(report.ended_at)

    def test_consider_records_pass(self):
        from olympus.heroes.phoenix import phoenix
        from olympus.titans.mnemosyne import mnemosyne
        before = len(mnemosyne.recall("phoenix.pass"))
        phoenix.consider()
        after = len(mnemosyne.recall("phoenix.pass"))
        self.assertGreater(after, before)

    def test_old_retired_prophecy_becomes_candidate(self):
        """Seed a retired prophecy with an old timestamp; Phoenix
        should pick it up as a rebirth candidate."""
        from olympus.heroes.phoenix import phoenix
        from olympus.titans.mnemosyne import mnemosyne
        # Use a unique name so it doesn't already exist in
        # phoenix.candidate
        name = f"phoenix-test-old-retired-{uuid.uuid4().hex[:8]}"
        old_ts = (datetime.datetime.now(datetime.timezone.utc)
                  - datetime.timedelta(days=60))
        # Force the retirement timestamp to look old by inserting
        # directly into the mnemosyne file (Mnemosyne.remember always
        # uses now()).
        import json
        from olympus.primordials.gaia import root
        path = root.child("state", "mnemosyne", "prophecyretired.jsonl")
        path.parent.mkdir(parents=True, exist_ok=True)
        row = {
            "kind": "prophecy.retired",
            "actor": "test:phoenix",
            "summary": "seeded old retired prophecy",
            "body": {"prediction": name, "rejection_count": 3},
            "remembered_at": old_ts.isoformat(),
        }
        with path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(row) + "\n")
        report = phoenix.consider(prophecy_staleness_days=30.0)
        cand_subjects = {c.subject for c in report.candidates}
        self.assertIn(name, cand_subjects,
            f"Phoenix should surface old retired prophecy "
            f"{name!r}; got: {cand_subjects}")

    def test_recent_retired_not_candidate(self):
        """A recently-retired prophecy is NOT yet stale."""
        from olympus.heroes.phoenix import phoenix
        from olympus.titans.mnemosyne import mnemosyne
        # Use Mnemosyne directly (timestamp = now)
        name = f"phoenix-test-recent-{uuid.uuid4().hex[:8]}"
        mnemosyne.remember(
            kind="prophecy.retired",
            actor="test:phoenix",
            summary="recent",
            prediction=name, rejection_count=3,
        )
        report = phoenix.consider(prophecy_staleness_days=30.0)
        cand_subjects = {c.subject for c in report.candidates}
        self.assertNotIn(name, cand_subjects)

    def test_idempotent_skip_already_known(self):
        """Running phoenix.consider() twice should not duplicate
        candidates."""
        from olympus.heroes.phoenix import phoenix
        from olympus.titans.mnemosyne import mnemosyne
        first = phoenix.consider()
        first_names = {(c.kind, c.subject) for c in first.candidates}
        second = phoenix.consider()
        second_names = {(c.kind, c.subject) for c in second.candidates}
        # Anything in second should NOT have been in first
        for k in second_names:
            self.assertNotIn(k, first_names,
                f"Phoenix re-emitted {k} on second consider")


if __name__ == "__main__":
    unittest.main()
