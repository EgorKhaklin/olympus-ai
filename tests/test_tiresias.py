"""Tiresias — ground-truth tracker for agent claims.

The claim being tested: claims persist with a unique id; verification
records hit/miss; calibration computes Brier score correctly;
buckets distribute confidence properly; out-of-range confidence is
rejected.
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


def _u() -> str:
    return f"test-tiresias-{uuid.uuid4().hex[:8]}"


class TestTiresias(unittest.TestCase):

    def test_claim_returns_id(self):
        from olympus.heroes.tiresias import tiresias
        cid = tiresias.claim(
            claimant=f"test:{_u()}",
            claim="x will happen",
            expected="x",
            confidence=0.7,
        )
        self.assertTrue(cid.startswith("t-"))

    def test_invalid_confidence_rejected(self):
        from olympus.heroes.tiresias import tiresias
        with self.assertRaises(ValueError):
            tiresias.claim(claimant="x", claim="y", expected="z",
                            confidence=1.5)

    def test_verify_hit(self):
        from olympus.heroes.tiresias import tiresias
        cid = tiresias.claim(claimant="t:hit",
                              claim="will be 42",
                              expected="42", confidence=0.9)
        v = tiresias.verify(cid, observed="42", hit=True)
        self.assertEqual(v.outcome, "hit")

    def test_verify_miss(self):
        from olympus.heroes.tiresias import tiresias
        cid = tiresias.claim(claimant="t:miss", claim="will be 7",
                              expected="7", confidence=0.6)
        v = tiresias.verify(cid, observed="9", hit=False)
        self.assertEqual(v.outcome, "miss")

    def test_verify_inconclusive_via_fallback(self):
        from olympus.heroes.tiresias import tiresias
        cid = tiresias.claim(claimant="t:inc", claim="ambiguous",
                              expected="", confidence=0.5)
        v = tiresias.verify(cid, observed="")
        self.assertEqual(v.outcome, "inconclusive")

    def test_verify_unknown_claim_raises(self):
        from olympus.heroes.tiresias import tiresias
        with self.assertRaises(KeyError):
            tiresias.verify("nonexistent-id", observed="x", hit=True)

    def test_calibration_brier_score(self):
        """Confidence 1.0 + hit = brier 0; confidence 1.0 + miss =
        brier 1. Mix them and check arithmetic."""
        from olympus.heroes.tiresias import tiresias
        claimant = f"t:brier-{_u()}"
        c1 = tiresias.claim(claimant=claimant, claim="a",
                             expected="x", confidence=1.0)
        tiresias.verify(c1, observed="x", hit=True)   # brier 0
        c2 = tiresias.claim(claimant=claimant, claim="b",
                             expected="x", confidence=1.0)
        tiresias.verify(c2, observed="y", hit=False)  # brier 1
        report = tiresias.calibration(claimant)
        self.assertEqual(report.verified_claims, 2)
        self.assertAlmostEqual(report.brier_score, 0.5, places=6)
        self.assertEqual(report.hits, 1)
        self.assertEqual(report.misses, 1)

    def test_calibration_buckets(self):
        from olympus.heroes.tiresias import tiresias
        claimant = f"t:bucket-{_u()}"
        # Three claims in 0.8-1.0 bucket; one hit
        for i, hit in enumerate([True, False, False]):
            cid = tiresias.claim(claimant=claimant,
                                   claim=f"bucket-test-{i}",
                                   expected="x", confidence=0.95)
            tiresias.verify(cid, observed="x" if hit else "y", hit=hit)
        report = tiresias.calibration(claimant)
        self.assertEqual(report.bucket_hit_rate["0.8-1.0"], 1.0 / 3.0)

    def test_open_claims_returns_unverified(self):
        from olympus.heroes.tiresias import tiresias
        claimant = f"t:open-{_u()}"
        cid = tiresias.claim(claimant=claimant, claim="x",
                              expected="x", confidence=0.5)
        open_ones = tiresias.open_claims(claimant=claimant)
        self.assertIn(cid, [c.claim_id for c in open_ones])
        # Verify it; now it's not open
        tiresias.verify(cid, observed="x", hit=True)
        open_ones = tiresias.open_claims(claimant=claimant)
        self.assertNotIn(cid, [c.claim_id for c in open_ones])


if __name__ == "__main__":
    unittest.main()
