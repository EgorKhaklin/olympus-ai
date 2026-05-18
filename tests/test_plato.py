"""Plato — five-solid taxonomy.

The claim being tested: every Platonic solid is registered with the
canonical vertex count and element; classify() returns the right
solid for known figures; cosmos() covers a meaningful chunk of the
pantheon.
"""
from __future__ import annotations

import pathlib as _pl
import sys as _sys
_ROOT = _pl.Path(__file__).resolve().parent.parent
_SRC = _ROOT / "src"
if str(_SRC) not in _sys.path:
    _sys.path.insert(0, str(_SRC))

import unittest


class TestPlato(unittest.TestCase):

    def test_five_solids_present(self):
        from olympus.heroes.plato import plato
        names = {s.name for s in plato.solids()}
        self.assertEqual(names, {"tetrahedron", "cube", "octahedron",
                                  "dodecahedron", "icosahedron"})

    def test_canonical_vertex_counts(self):
        from olympus.heroes.plato import plato
        expected = {"tetrahedron": 4, "cube": 8, "octahedron": 6,
                    "dodecahedron": 12, "icosahedron": 20}
        for s in plato.solids():
            self.assertEqual(s.vertices, expected[s.name])

    def test_canonical_elements(self):
        from olympus.heroes.plato import plato
        expected = {"tetrahedron": "fire", "cube": "earth",
                    "octahedron": "air", "dodecahedron": "cosmos",
                    "icosahedron": "water"}
        for s in plato.solids():
            self.assertEqual(s.element, expected[s.name])

    def test_classify_known_figures(self):
        """Spot-check canonical classifications."""
        from olympus.heroes.plato import plato
        cases = [
            ("hydra", "tetrahedron"),       # observation
            ("mnemosyne", "cube"),          # state
            ("athena", "octahedron"),       # reasoning
            ("zeus", "dodecahedron"),       # authority
            ("prometheus", "icosahedron"),  # execution
        ]
        for figure, expected in cases:
            s = plato.classify(figure)
            self.assertIsNotNone(s,
                f"{figure!r} should be classified")
            self.assertEqual(s.name, expected,
                f"{figure!r} should be {expected!r}, got {s.name!r}")

    def test_classify_case_insensitive(self):
        from olympus.heroes.plato import plato
        self.assertEqual(plato.classify("ATHENA").name, "octahedron")

    def test_unclassified_returns_none(self):
        from olympus.heroes.plato import plato
        self.assertIsNone(plato.classify("not-a-real-figure"))

    def test_cosmos_covers_pantheon(self):
        """Most named figures should be classified. Allow a few
        unclassified (a new figure may temporarily lack a mapping)."""
        from olympus.heroes.plato import plato
        cosmos = plato.cosmos()
        self.assertGreaterEqual(len(cosmos), 40,
            "Plato's taxonomy should cover most named figures")

    def test_members_returns_correct_set(self):
        from olympus.heroes.plato import plato
        # Cube members must include the obvious state-figures
        cube_members = set(plato.members("cube"))
        for required in ("mnemosyne", "atlas", "charon"):
            self.assertIn(required, cube_members,
                f"{required!r} should be a cube member")

    def test_solid_lookup(self):
        from olympus.heroes.plato import plato
        s = plato.solid("octahedron")
        self.assertIsNotNone(s)
        self.assertEqual(s.element, "air")


if __name__ == "__main__":
    unittest.main()
