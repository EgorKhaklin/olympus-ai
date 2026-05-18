"""Daedalus — the cartographer.

The claim being tested: cartograph() produces a valid Mermaid document;
all _COGNITIVE_FLOW edges appear; the architecture file is writeable.
"""
from __future__ import annotations

import pathlib as _pl
import sys as _sys
_ROOT = _pl.Path(__file__).resolve().parent.parent
_SRC = _ROOT / "src"
if str(_SRC) not in _sys.path:
    _sys.path.insert(0, str(_SRC))

import re
import tempfile
import unittest


class TestDaedalus(unittest.TestCase):

    def test_cognitive_flow_is_mermaid(self):
        from olympus.heroes.daedalus import Daedalus
        out = Daedalus().render_cognitive_flow()
        self.assertTrue(out.startswith("```mermaid"))
        self.assertIn("flowchart LR", out)
        self.assertTrue(out.rstrip().endswith("```"))

    def test_every_flow_edge_appears(self):
        from olympus.heroes.daedalus import Daedalus
        d = Daedalus()
        out = d.render_cognitive_flow()
        for src, dst, _label in d._COGNITIVE_FLOW:
            sid = d._node_id(src)
            did = d._node_id(dst)
            # Edge appears as `sid -- "label" --> did` or `sid --> did`
            pattern = rf"\b{re.escape(sid)}\b\s*(--.+?--)?>\s*\b{re.escape(did)}\b"
            self.assertRegex(out, pattern,
                f"missing edge {src}→{dst} in rendered cognitive flow")

    def test_tier_map_is_mermaid(self):
        from olympus.heroes.daedalus import Daedalus
        out = Daedalus().render_tier_map()
        self.assertTrue(out.startswith("```mermaid"))
        self.assertIn("flowchart TB", out)
        self.assertTrue(out.rstrip().endswith("```"))

    def test_cartograph_writes_when_flag_set(self):
        from olympus.heroes.daedalus import Daedalus
        from olympus.primordials.gaia import root
        d = Daedalus()
        result = d.cartograph(write=True)
        self.assertGreater(result.bytes_written, 0)
        arch = root.child("codex", "ARCHITECTURE.md")
        self.assertTrue(arch.exists(),
            "cartograph(write=True) should produce codex/ARCHITECTURE.md")
        text = arch.read_text(encoding="utf-8")
        self.assertIn("```mermaid", text)
        self.assertIn("flowchart LR", text)

    def test_cartograph_dry_run_does_not_write(self):
        from olympus.heroes.daedalus import Daedalus
        from olympus.primordials.gaia import root
        arch = root.child("codex", "ARCHITECTURE.md")
        before_exists = arch.exists()
        before_bytes = arch.stat().st_size if before_exists else 0
        result = Daedalus().cartograph(write=False)
        self.assertEqual(result.bytes_written, 0)
        # File state unchanged
        if arch.exists():
            self.assertEqual(arch.stat().st_size, before_bytes)

    def test_full_document_includes_both_diagrams(self):
        from olympus.heroes.daedalus import Daedalus
        doc = Daedalus().render_full_document()
        self.assertIn("Cognitive flow", doc)
        self.assertIn("Tier map", doc)
        self.assertEqual(doc.count("```mermaid"), 2)


if __name__ == "__main__":
    unittest.main()
