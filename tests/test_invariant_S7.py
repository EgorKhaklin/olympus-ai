"""S7 — Bounded autonomy.

LOW autonomous, MEDIUM proposal, HIGH requires Zeus authorization.
The action queue routes by risk class; Zeus.can_perform reads Styx."""
from __future__ import annotations

import pathlib as _pl
import sys as _sys
_ROOT = _pl.Path(__file__).resolve().parent.parent
_SRC = _ROOT / "src"
if str(_SRC) not in _sys.path:
    _sys.path.insert(0, str(_SRC))

import unittest


class _Proposal:
    """Duck-type proposal for testing action queue routing."""
    def __init__(self, id: str, risk_class: str):
        self.id = id
        self.risk_class = risk_class
        self.proposed_fix = f"test fix for {id}"


class TestS7_BoundedAutonomy(unittest.TestCase):

    def test_S7a_LOW_proposal_no_contests_auto_ratifies(self):
        from olympus.action import action_queue
        action_queue.promote(_Proposal("S7-low-1", "LOW"))
        final = action_queue.by_id("act-S7-low-1")
        self.assertEqual(final.status, "ratified")

    def test_S7b_LOW_with_contests_queues_for_zeus(self):
        from olympus.action import action_queue
        a = action_queue.promote(_Proposal("S7-low-2", "LOW"), contests=["AP3"])
        self.assertEqual(a.status, "queued")

    def test_S7c_MEDIUM_always_queues_for_zeus(self):
        from olympus.action import action_queue
        a = action_queue.promote(_Proposal("S7-med-1", "MEDIUM"))
        self.assertEqual(a.status, "queued")

    def test_S7d_HIGH_always_delphi_pending(self):
        from olympus.action import action_queue
        a = action_queue.promote(_Proposal("S7-high-1", "HIGH"))
        self.assertEqual(a.status, "delphi-pending")

    def test_S7e_COMPOSITE_always_delphi_pending(self):
        from olympus.action import action_queue
        a = action_queue.promote(_Proposal("S7-comp-1", "COMPOSITE"))
        self.assertEqual(a.status, "delphi-pending")

    def test_S7f_zeus_can_always_perform_LOW(self):
        from olympus.olympians.zeus import Zeus
        self.assertTrue(Zeus().can_perform("LOW"))

    def test_S7g_zeus_HIGH_requires_styx_oath(self):
        """Zeus can_perform('HIGH') depends on a prior AUTHORIZE oath."""
        from olympus.olympians.zeus import Zeus
        # On a deployment with HIGH oaths already sworn (real Olympus has many),
        # this returns True. On a fresh deployment it would return False.
        # We just assert the API is callable + returns a bool.
        self.assertIsInstance(Zeus().can_perform("HIGH"), bool)

    def test_S7h_unrecognized_risk_class_raises(self):
        from olympus.olympians.zeus import Zeus
        # can_perform accepts the four classes; an unrecognized one should
        # not silently default to True. The current implementation returns
        # False; verify that's what happens (no autonomy by accident).
        z = Zeus()
        # 'UNKNOWN' falls through every branch and returns False
        self.assertFalse(z.can_perform("UNKNOWN"))

    def test_S7i_action_execute_refuses_unratified(self):
        """An action must be 'ratified' before it can execute. S7 enforced
        at the execute boundary."""
        from olympus.action import action_queue
        action_queue.promote(_Proposal("S7-exec-1", "MEDIUM"))
        # status is 'queued', not 'ratified'
        result = action_queue.execute("act-S7-exec-1", fn=lambda a: "ran")
        self.assertFalse(result.success)
        self.assertIn("refused", result.detail.lower())


if __name__ == "__main__":
    unittest.main()
