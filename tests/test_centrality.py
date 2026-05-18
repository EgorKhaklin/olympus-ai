"""Daedalus — graph centrality on _COGNITIVE_FLOW.

The claim being tested: graph() returns nodes + in/out edge maps;
degree() returns per-node {in, out, total}; centrality() returns
0..1 scores; load-bearing figures rank Zeus/Mnemosyne near the top.
"""
from __future__ import annotations

import pathlib as _pl
import sys as _sys
_ROOT = _pl.Path(__file__).resolve().parent.parent
_SRC = _ROOT / "src"
if str(_SRC) not in _sys.path:
    _sys.path.insert(0, str(_SRC))

import unittest


class TestDaedalusGraph(unittest.TestCase):

    def test_graph_returns_nodes_and_edges(self):
        from olympus.heroes.daedalus import daedalus
        nodes, out_e, in_e = daedalus.graph()
        self.assertGreater(len(nodes), 10)
        self.assertIsInstance(out_e, dict)
        self.assertIsInstance(in_e, dict)

    def test_degree_includes_known_node(self):
        from olympus.heroes.daedalus import daedalus
        deg = daedalus.degree()
        # Mnemosyne is referenced many times — should have high in-degree
        self.assertIn("Mnemosyne", deg)
        self.assertGreater(deg["Mnemosyne"]["in"], 3,
            "Mnemosyne should have high in-degree (many writers)")

    def test_centrality_returns_scores(self):
        from olympus.heroes.daedalus import daedalus
        c = daedalus.centrality()
        self.assertGreater(len(c), 10)
        for node, score in c.items():
            self.assertGreaterEqual(score, 0.0,
                f"centrality of {node!r} should be >= 0")
            self.assertLessEqual(score, 1.0,
                f"centrality of {node!r} should be <= 1")

    def test_load_bearing_top_includes_central_figure(self):
        """At least one of {Mnemosyne, Hephaestus, Athena, Zeus,
        Atlas} should appear in the top 10 by centrality."""
        from olympus.heroes.daedalus import daedalus
        top = daedalus.load_bearing_figures(top=10)
        names = {name for name, _ in top}
        central_candidates = {"Mnemosyne", "Hephaestus", "Athena",
                              "Zeus", "Atlas"}
        self.assertTrue(names & central_candidates,
            f"top-10 by centrality should include a known central "
            f"figure; got {names}")


if __name__ == "__main__":
    unittest.main()
