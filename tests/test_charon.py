"""Charon — the ferryman.

The claim being tested: ferry moves old released burdens to Hades;
idempotent (re-run ferries nothing new); records each crossing;
respects retention window.
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


def _seed_old_released_burden(*, op: str = "old-test-op",
                              days_ago: float = 90.0) -> str:
    """Seed an Atlas bear + release pair where release is N days ago."""
    from olympus.titans.mnemosyne import mnemosyne
    bid = uuid.uuid4().hex
    old = (datetime.datetime.now(datetime.timezone.utc)
           - datetime.timedelta(days=days_ago))
    mnemosyne.remember(
        kind="atlas.bear",
        actor=f"atlas:{op}",
        summary=f"seeded old burden for charon test",
        id=bid, op=op, owner="charon-test",
        started_at=(old - datetime.timedelta(seconds=10)).isoformat(),
        payload={"seeded": True},
    )
    mnemosyne.remember(
        kind="atlas.release",
        actor="atlas",
        summary=f"seeded old release",
        id=bid, outcome="ok",
        released_at=old.isoformat(),
    )
    return bid


class TestCharon(unittest.TestCase):

    def test_ferries_old_released_burden(self):
        from olympus.underworld.charon import Charon
        bid = _seed_old_released_burden(days_ago=90.0)
        c = Charon(retention_days=30.0)
        report = c.ferry()
        ferried_ids = {x.burden_id for x in report.crossings}
        self.assertIn(bid, ferried_ids)

    def test_respects_retention_window(self):
        """A burden released 1 day ago is NOT ferried at retention=30d."""
        from olympus.underworld.charon import Charon
        bid = _seed_old_released_burden(days_ago=1.0)
        c = Charon(retention_days=30.0)
        report = c.ferry()
        ferried_ids = {x.burden_id for x in report.crossings}
        self.assertNotIn(bid, ferried_ids)

    def test_idempotent(self):
        from olympus.underworld.charon import Charon
        _seed_old_released_burden(days_ago=90.0)
        c = Charon(retention_days=30.0)
        first = c.ferry()
        second = c.ferry()
        # The second run produces 0 new crossings (everything in first
        # was already ferried)
        first_ids = {x.burden_id for x in first.crossings}
        for x in second.crossings:
            self.assertNotIn(x.burden_id, first_ids,
                "second ferry should not re-ferry burdens from first")

    def test_records_crossings(self):
        from olympus.underworld.charon import Charon
        from olympus.titans.mnemosyne import mnemosyne
        bid = _seed_old_released_burden(days_ago=90.0)
        before = len(mnemosyne.recall("charon.crossing"))
        Charon(retention_days=30.0).ferry()
        after = len(mnemosyne.recall("charon.crossing"))
        self.assertGreater(after, before)
        # Find the specific crossing
        crossings = mnemosyne.recall("charon.crossing")
        ours = [m for m in crossings
                if (m.body or {}).get("burden_id") == bid]
        self.assertGreaterEqual(len(ours), 1)

    def test_ferry_pass_summary_recorded(self):
        from olympus.underworld.charon import Charon
        from olympus.titans.mnemosyne import mnemosyne
        before = len(mnemosyne.recall("charon.ferry-pass"))
        Charon().ferry()
        after = len(mnemosyne.recall("charon.ferry-pass"))
        self.assertGreater(after, before)

    def test_in_flight_burdens_not_ferried(self):
        """A burden with bear but no release is in flight; Charon does
        not touch it."""
        from olympus.titans.mnemosyne import mnemosyne
        from olympus.underworld.charon import Charon
        bid = uuid.uuid4().hex
        old = (datetime.datetime.now(datetime.timezone.utc)
               - datetime.timedelta(days=100))
        mnemosyne.remember(
            kind="atlas.bear",
            actor="atlas:in-flight-test",
            summary="seeded in-flight",
            id=bid, op="in-flight-test", owner="charon-test",
            started_at=old.isoformat(),
            payload={},
        )
        # No release — should NOT be ferried
        report = Charon(retention_days=30.0).ferry()
        ferried_ids = {x.burden_id for x in report.crossings}
        self.assertNotIn(bid, ferried_ids)


if __name__ == "__main__":
    unittest.main()
