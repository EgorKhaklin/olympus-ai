"""Daedalus — sacred-geometry SVG diagrams.

The claim being tested: the Metatron's Cube SVG is well-formed XML
with the expected 13 nodes + 78 edges; the Vesica Piscis SVG has 2
circles and 3 labels; the full ARCHITECTURE.md document embeds them.
"""
from __future__ import annotations

import pathlib as _pl
import sys as _sys
_ROOT = _pl.Path(__file__).resolve().parent.parent
_SRC = _ROOT / "src"
if str(_SRC) not in _sys.path:
    _sys.path.insert(0, str(_SRC))

import unittest
import xml.etree.ElementTree as ET


class TestDaedalusSVG(unittest.TestCase):

    def test_metatron_cube_is_valid_xml(self):
        from olympus.heroes.daedalus import Daedalus
        svg = Daedalus().render_metatron_cube()
        # Parses as XML
        root = ET.fromstring(svg)
        self.assertTrue(root.tag.endswith("svg"),
                        f"root should be <svg>, got {root.tag}")

    def test_metatron_cube_has_13_node_circles(self):
        """13 node circles for the 13 canonical figures."""
        from olympus.heroes.daedalus import Daedalus
        svg = Daedalus().render_metatron_cube()
        root = ET.fromstring(svg)
        # Find every circle with class containing "node-circle"
        node_circles = [
            el for el in root.iter()
            if el.tag.endswith("circle")
            and "node-circle" in (el.attrib.get("class") or "")
        ]
        self.assertEqual(len(node_circles), 13,
            "Metatron's Cube must have exactly 13 node circles")

    def test_metatron_cube_has_78_edges(self):
        """Every-to-every of 13 nodes = C(13,2) = 78 edges."""
        from olympus.heroes.daedalus import Daedalus
        svg = Daedalus().render_metatron_cube()
        root = ET.fromstring(svg)
        edges = [
            el for el in root.iter()
            if el.tag.endswith("line")
            and "edge" in (el.attrib.get("class") or "")
        ]
        self.assertEqual(len(edges), 78,
            f"expected C(13,2)=78 edges, got {len(edges)}")

    def test_metatron_cube_labels_all_thirteen(self):
        from olympus.heroes.daedalus import Daedalus, daedalus
        svg = Daedalus().render_metatron_cube()
        for figure in Daedalus._METATRON_13:
            self.assertIn(f">{figure}<", svg,
                f"label for {figure!r} missing from SVG")

    def test_vesica_piscis_is_valid_xml(self):
        from olympus.heroes.daedalus import Daedalus
        svg = Daedalus().render_vesica_piscis(
            left_label="left", right_label="right",
            center_label="meet",
        )
        root = ET.fromstring(svg)
        self.assertTrue(root.tag.endswith("svg"))

    def test_vesica_piscis_has_two_circles(self):
        from olympus.heroes.daedalus import Daedalus
        svg = Daedalus().render_vesica_piscis()
        root = ET.fromstring(svg)
        circles = [el for el in root.iter()
                   if el.tag.endswith("circle")]
        self.assertEqual(len(circles), 2)

    def test_vesica_piscis_has_labels(self):
        from olympus.heroes.daedalus import Daedalus
        svg = Daedalus().render_vesica_piscis(
            left_label="LEFT-DOMAIN",
            right_label="RIGHT-DOMAIN",
            center_label="MEET",
        )
        self.assertIn("LEFT-DOMAIN", svg)
        self.assertIn("RIGHT-DOMAIN", svg)
        self.assertIn("MEET", svg)

    def test_full_document_embeds_svg_diagrams(self):
        from olympus.heroes.daedalus import Daedalus
        doc = Daedalus().render_full_document()
        # Both SVG diagrams should be inlined
        self.assertGreaterEqual(doc.count("<svg "), 2,
            "ARCHITECTURE.md should embed at least 2 SVG diagrams")
        self.assertIn("Metatron", doc)
        self.assertIn("Vesica Piscis", doc)


if __name__ == "__main__":
    unittest.main()
