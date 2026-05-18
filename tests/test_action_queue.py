"""Action queue tests — promotion, ratification, execution, rejection."""
from __future__ import annotations

import pathlib as _pl
import sys as _sys
_ROOT = _pl.Path(__file__).resolve().parent.parent
_SRC = _ROOT / 'src'
if str(_SRC) not in _sys.path:
    _sys.path.insert(0, str(_SRC))

import unittest

from olympus.action import action_queue


class _FakeProposal:
    """Minimal duck-type matching the Proposal shape action_queue.promote uses."""
    def __init__(self, id: str, risk_class: str, proposed_fix: str = "do the thing"):
        self.id = id
        self.risk_class = risk_class
        self.proposed_fix = proposed_fix


class TestActionQueue(unittest.TestCase):

    def test_low_proposal_auto_ratifies(self):
        p = _FakeProposal(id="auto-test-1", risk_class="LOW")
        a = action_queue.promote(p, contests=[])
        # auto-ratified LOW promotes to ratified
        final = action_queue.by_id(a.id)
        self.assertEqual(final.status, "ratified")
        self.assertIn("auto:LOW", final.ratified_by)

    def test_medium_proposal_queues_for_zeus(self):
        p = _FakeProposal(id="queue-test-1", risk_class="MEDIUM")
        a = action_queue.promote(p, contests=[])
        self.assertEqual(a.status, "queued")

    def test_high_proposal_is_delphi_pending(self):
        p = _FakeProposal(id="delphi-test-1", risk_class="HIGH")
        a = action_queue.promote(p, contests=[])
        self.assertEqual(a.status, "delphi-pending")

    def test_low_with_momus_contests_queues_for_zeus(self):
        p = _FakeProposal(id="contested-low-1", risk_class="LOW")
        a = action_queue.promote(p, contests=["AP3"])
        self.assertEqual(a.status, "queued")

    def test_ratify_then_execute(self):
        p = _FakeProposal(id="exec-test-1", risk_class="MEDIUM")
        action_queue.promote(p)
        action_queue.ratify(f"act-{p.id}", quote="approved for test")
        result = action_queue.execute(
            f"act-{p.id}",
            fn=lambda action: "all done",
        )
        self.assertTrue(result.success)
        self.assertEqual(result.detail, "all done")

    def test_execute_unratified_refuses(self):
        p = _FakeProposal(id="exec-refused-1", risk_class="MEDIUM")
        action_queue.promote(p)
        result = action_queue.execute(
            f"act-{p.id}",
            fn=lambda action: "should-not-run",
        )
        self.assertFalse(result.success)
        self.assertIn("refused", result.detail)

    def test_execution_failure_quarantined(self):
        from olympus.underworld.hades import hades
        before = hades.population()
        p = _FakeProposal(id="exec-fail-1", risk_class="MEDIUM")
        action_queue.promote(p)
        action_queue.ratify(f"act-{p.id}", quote="approved-to-fail")
        result = action_queue.execute(
            f"act-{p.id}",
            fn=lambda a: (_ for _ in ()).throw(RuntimeError("boom")),
        )
        self.assertFalse(result.success)
        # Hades archives the failure
        self.assertGreater(hades.population(), before)


if __name__ == "__main__":
    unittest.main()
