"""Cassandra — the unbelieved prophetess.

The claim being tested: when an ALERT pheromone is dismissed (no
proposal raised OR proposal rejected) and subsequently recurs,
Cassandra detects the vindication. Records to Mnemosyne under
`cassandra.vindicated`.

Tests seed directly to the canonical sources (state/argos_pheromones.jsonl
and state/hephaestus/proposals/) so the production code paths run
unmodified.
"""
from __future__ import annotations

import pathlib as _pl
import sys as _sys
_ROOT = _pl.Path(__file__).resolve().parent.parent
_SRC = _ROOT / "src"
if str(_SRC) not in _sys.path:
    _sys.path.insert(0, str(_SRC))

import datetime
import json
import unittest
import uuid


def _unique_slice(prefix: str) -> str:
    return f"cassandra-test-{prefix}-{uuid.uuid4().hex[:8]}"


def _seed_alert(slice_name: str, *, ts: str | None = None) -> str:
    """Append one ALERT pheromone to the canonical Argos log."""
    from olympus.primordials.gaia import root
    if ts is None:
        ts = datetime.datetime.now(datetime.timezone.utc).isoformat()
    row = {
        "eye": "test-eye",
        "slice": slice_name,
        "kind": "alert",
        "intensity": 1.0,
        "detail": "seeded for cassandra test",
        "evidence": {},
        "deposited_at": ts,
    }
    path = root.child("state", "argos_pheromones.jsonl")
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(row, default=str) + "\n")
    return ts


def _seed_proposal_for(slice_name: str, *, decision: str = "rejected") -> str:
    """Write a proposal file mentioning this slice, then record the
    matching action.ratified / action.rejected in Mnemosyne."""
    from olympus.primordials.gaia import root
    from olympus.titans.mnemosyne import mnemosyne
    pid = f"cassandra-prop-{uuid.uuid4().hex[:10]}"
    action_id = f"act-{pid}"
    proposal = {
        "id": pid,
        "drift_observed": (f"argos reports alert on slice '{slice_name}': "
                           f"seeded for test"),
        "risk_class": "LOW",
    }
    path = root.child("state", "hephaestus", "proposals")
    path.mkdir(parents=True, exist_ok=True)
    (path / f"{pid}.json").write_text(json.dumps(proposal), encoding="utf-8")

    if decision == "rejected":
        mnemosyne.remember(
            kind="action.rejected",
            actor="test:zeus",
            summary=f"rejected {action_id}",
            action_id=action_id, reason="seeded for test",
        )
    elif decision == "ratified":
        mnemosyne.remember(
            kind="action.ratified",
            actor="test:zeus",
            summary=f"ratified {action_id}",
            action_id=action_id, quote="seeded for test",
        )
    return action_id


class TestCassandra(unittest.TestCase):

    def test_silent_dismissal_detected(self):
        """An ALERT-bearing slice with no proposal counts as silent."""
        from olympus.heroes.cassandra import Cassandra
        SLICE = _unique_slice("silent")
        _seed_alert(SLICE)
        ignored = Cassandra().ignored_warnings()
        matched = [w for w in ignored if w.slice == SLICE]
        self.assertEqual(len(matched), 1)
        self.assertEqual(matched[0].dismissal_kind, "silent")

    def test_rejected_dismissal_detected(self):
        from olympus.heroes.cassandra import Cassandra
        SLICE = _unique_slice("rejected")
        _seed_alert(SLICE)
        _seed_proposal_for(SLICE, decision="rejected")
        ignored = Cassandra().ignored_warnings()
        matched = [w for w in ignored if w.slice == SLICE]
        self.assertEqual(len(matched), 1)
        self.assertEqual(matched[0].dismissal_kind, "rejected")

    def test_ratified_proposal_skips_ignored(self):
        """A slice whose proposal was ratified is NOT ignored."""
        from olympus.heroes.cassandra import Cassandra
        SLICE = _unique_slice("ratified")
        _seed_alert(SLICE)
        _seed_proposal_for(SLICE, decision="ratified")
        ignored = Cassandra().ignored_warnings()
        self.assertNotIn(SLICE, {w.slice for w in ignored})

    def test_vindication_when_recurs_after_silent_dismissal(self):
        """Alert (silent dismissal moment = first alert ts), then 2+
        subsequent alerts → vindicated."""
        from olympus.heroes.cassandra import Cassandra
        SLICE = _unique_slice("vindication")
        # First alert sets the dismissal moment
        _seed_alert(SLICE)
        # Two later alerts — strictly later timestamps to satisfy the
        # `t > dismissed_at` condition
        import time as _time
        _time.sleep(0.01)
        _seed_alert(SLICE)
        _time.sleep(0.01)
        _seed_alert(SLICE)
        vindications = Cassandra().vindicated()
        matched = [v for v in vindications if v.slice == SLICE]
        self.assertGreaterEqual(len(matched), 1)
        self.assertGreaterEqual(matched[0].recurrences_after_dismissal, 2)

    def test_review_records_new_vindications(self):
        from olympus.heroes.cassandra import Cassandra
        from olympus.titans.mnemosyne import mnemosyne
        SLICE = _unique_slice("review-record")
        _seed_alert(SLICE)
        import time as _time
        _time.sleep(0.01); _seed_alert(SLICE)
        _time.sleep(0.01); _seed_alert(SLICE)
        before = len(mnemosyne.recall("cassandra.vindicated"))
        report = Cassandra().review()
        after = len(mnemosyne.recall("cassandra.vindicated"))
        if any(v.slice == SLICE for v in report.vindicated):
            self.assertGreater(after, before)

    def test_review_pass_summary_recorded(self):
        from olympus.heroes.cassandra import Cassandra
        from olympus.titans.mnemosyne import mnemosyne
        before = len(mnemosyne.recall("cassandra.review"))
        Cassandra().review()
        after = len(mnemosyne.recall("cassandra.review"))
        self.assertGreater(after, before)


if __name__ == "__main__":
    unittest.main()
