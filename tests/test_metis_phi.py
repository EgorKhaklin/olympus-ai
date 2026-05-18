"""Metis uses golden-section search (phi arc).

The claim being tested: metis.golden_search_parameter() uses
pythagoras.golden_section_search to find an optimum value; the
resulting Recommendation is well-formed; the search is recorded to
Mnemosyne (S8).
"""
from __future__ import annotations

import pathlib as _pl
import sys as _sys
_ROOT = _pl.Path(__file__).resolve().parent.parent
_SRC = _ROOT / "src"
if str(_SRC) not in _sys.path:
    _sys.path.insert(0, str(_SRC))

import unittest


class TestMetisGoldenSearch(unittest.TestCase):

    def test_finds_minimum_of_synthetic_function(self):
        """Min of (x − 4)² is at x = 4."""
        from olympus.titans.metis import Metis
        rec = Metis().golden_search_parameter(
            parameter_name="synthetic.testparam",
            evaluate=lambda x: (x - 4.0) ** 2,
            lo=0.0, hi=10.0, tol=1e-4,
        )
        self.assertAlmostEqual(float(rec.proposed), 4.0, places=2)
        self.assertEqual(rec.parameter, "synthetic.testparam")
        self.assertEqual(rec.risk_class, "LOW")
        self.assertIn("golden-section", rec.rationale)

    def test_maximize_pathway(self):
        from olympus.titans.metis import Metis
        rec = Metis().golden_search_parameter(
            parameter_name="synthetic.testmax",
            evaluate=lambda x: -((x - 7.0) ** 2),
            lo=0.0, hi=14.0, tol=1e-4,
            minimize=False,
        )
        self.assertAlmostEqual(float(rec.proposed), 7.0, places=2)

    def test_records_search_to_mnemosyne(self):
        from olympus.titans.metis import Metis
        from olympus.titans.mnemosyne import mnemosyne
        before = len(mnemosyne.recall("pythagoras.search"))
        Metis().golden_search_parameter(
            parameter_name="record-trace-test",
            evaluate=lambda x: x ** 2,
            lo=-2.0, hi=2.0, tol=1e-3,
        )
        after = len(mnemosyne.recall("pythagoras.search"))
        self.assertGreater(after, before)

    def test_recommendation_evidence_kinds(self):
        from olympus.titans.metis import Metis
        rec = Metis().golden_search_parameter(
            parameter_name="evidence-test",
            evaluate=lambda x: (x - 1.0) ** 2,
            lo=-3.0, hi=3.0, tol=1e-3,
        )
        self.assertIn("pythagoras.search", rec.evidence_kinds)


if __name__ == "__main__":
    unittest.main()
