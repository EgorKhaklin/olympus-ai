"""Themis publishes formal specs (TLA+).

The claim being tested: every .tla file in codex/specs/ is discovered;
its module name is parsed; its summary is extracted from the first
(*** ... ***) comment.
"""
from __future__ import annotations

import pathlib as _pl
import sys as _sys
_ROOT = _pl.Path(__file__).resolve().parent.parent
_SRC = _ROOT / "src"
if str(_SRC) not in _sys.path:
    _sys.path.insert(0, str(_SRC))

import unittest


class TestThemisSpecs(unittest.TestCase):

    def test_specs_returns_dict(self):
        from olympus.titans.themis import themis
        specs = themis.specs()
        self.assertIsInstance(specs, dict)

    def test_all_three_specs_present(self):
        from olympus.titans.themis import themis
        specs = themis.specs()
        for name in ("styx-append-only", "hephaestus-pipeline",
                     "cognitive-flow"):
            self.assertIn(name, specs,
                f"expected spec {name!r} in codex/specs/")

    def test_module_name_extracted(self):
        from olympus.titans.themis import themis
        specs = themis.specs()
        # Module names should be TLA+ Pascal-case
        self.assertEqual(specs["styx-append-only"]["module_name"],
                         "StyxAppendOnly")
        self.assertEqual(specs["hephaestus-pipeline"]["module_name"],
                         "HephaestusPipeline")
        self.assertEqual(specs["cognitive-flow"]["module_name"],
                         "CognitiveFlow")

    def test_summary_extracted(self):
        from olympus.titans.themis import themis
        specs = themis.specs()
        for name, spec in specs.items():
            self.assertTrue(spec.get("summary"),
                f"spec {name!r} should have a non-empty summary")

    def test_spec_files_have_bytes(self):
        from olympus.titans.themis import themis
        specs = themis.specs()
        for name, spec in specs.items():
            self.assertGreater(spec["bytes"], 100,
                f"spec {name!r} should be substantive (> 100 bytes)")


if __name__ == "__main__":
    unittest.main()
