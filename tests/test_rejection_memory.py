"""Hephaestus learns from rejection.

The claim: a drift signature that Zeus rejected in the last 7 days does
not get re-proposed. After 3 rejections, the loop emits 'proposal-fatigue'.
"""
from __future__ import annotations

import pathlib as _pl
import sys as _sys
_ROOT = _pl.Path(__file__).resolve().parent.parent
_SRC = _ROOT / "src"
if str(_SRC) not in _sys.path:
    _sys.path.insert(0, str(_SRC))

import unittest


class TestRejectionMemory(unittest.TestCase):

    def test_drift_signature_is_canonical(self):
        from olympus.olympians.hephaestus import hephaestus
        sig1 = hephaestus._drift_signature(source="hydra", slice_name="codex/X")
        sig2 = hephaestus._drift_signature(source="hydra", slice_name="codex/X")
        sig3 = hephaestus._drift_signature(source="argos", slice_name="codex/X")
        self.assertEqual(sig1, sig2)
        self.assertNotEqual(sig1, sig3)

    def test_recently_rejected_returns_set(self):
        from olympus.olympians.hephaestus import hephaestus
        result = hephaestus._recently_rejected_drift_signatures(window_days=7)
        self.assertIsInstance(result, set)

    def test_proposal_fatigue_after_chronic_rejection(self):
        """If a drift signature has been rejected 3+ times historically,
        surface_from emits a 'proposal-fatigue' rather than re-proposing."""
        # Build a brief that would normally trigger a proposal on slice 'fatigue-slice'
        from olympus.olympians.athena import Brief
        from olympus.olympians.hephaestus import hephaestus
        from olympus.action import action_queue

        class _P:
            id = "fatigue-seed"
            risk_class = "MEDIUM"
            proposed_fix = "test"
            drift_observed = "hydra reports alert on slice 'fatigue-slice'"

        # We need a real proposal saved on disk so the signature lookup works.
        proposal = hephaestus.propose(
            drift_observed="hydra reports alert on slice 'fatigue-slice': test",
            proposed_fix="test",
            risk_class="MEDIUM",
            rationale="rejection memory test",
        )
        # Promote + reject the same proposal 3 times → chronic.
        for i in range(3):
            class _P:
                id = proposal.id
                risk_class = "MEDIUM"
                proposed_fix = "test"
            action_queue.promote(_P())
            action_queue.reject(f"act-{proposal.id}", reason=f"reject {i}")

        chronic = hephaestus._chronically_rejected_drift_signatures(threshold=3)
        self.assertIn("hydra::fatigue-slice", chronic)

        # Now call surface_from with a brief containing the same drift
        brief = Brief(
            label="fatigue-test",
            composed_at="",
            findings=[{
                "source": "hydra",
                "head": "test-head",
                "slice": "fatigue-slice",
                "severity": "alert",
                "detail": "still alerting",
            }],
            recommendations=[],
        )
        proposals = hephaestus.surface_from(brief)
        # Exactly one proposal should be the fatigue signal, no
        # repeat investigation proposal.
        fatigue = [p for p in proposals if "proposal-fatigue" in p.drift_observed]
        repeat = [p for p in proposals
                  if "fatigue-slice" in p.drift_observed
                  and "proposal-fatigue" not in p.drift_observed]
        self.assertEqual(len(fatigue), 1)
        self.assertEqual(repeat, [])


if __name__ == "__main__":
    unittest.main()
