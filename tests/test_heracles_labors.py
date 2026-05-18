"""Heracles's twelve labors as real substrate kill-tests."""
from __future__ import annotations

import pathlib as _pl
import sys as _sys
_ROOT = _pl.Path(__file__).resolve().parent.parent
_SRC = _ROOT / 'src'
if str(_SRC) not in _sys.path:
    _sys.path.insert(0, str(_SRC))

import unittest

from olympus.heroes.heracles import Heracles, CANONICAL_LABORS


class TestHeracleanLabors(unittest.TestCase):

    def test_all_twelve_labors_survive(self):
        h = Heracles()
        for labor in CANONICAL_LABORS:
            h.assign(labor)
        verdicts = h.perform()
        self.assertEqual(len(verdicts), 12)
        failed = [v for v in verdicts if not v.survived]
        self.assertEqual([], [(v.labor.name, v.detail) for v in failed],
            f"Heraclean labor(s) failed: {[(v.labor.name, v.detail) for v in failed]}")


if __name__ == "__main__":
    unittest.main()
