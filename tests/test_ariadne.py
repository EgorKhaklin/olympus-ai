"""Ariadne — the causal-lineage thread through the Labyrinth.

The claim being tested: ariadne.thread() writes a Mnemosyne record
with trace_id (and optional parent_trace_id); ariadne.chain() walks
back-pointers to produce the causal chain; descendants() walks
forward; cycles + deep chains are bounded by MAX_DEPTH.
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


def _unique(prefix: str) -> str:
    return f"{prefix}-{uuid.uuid4().hex[:8]}"


class TestAriadne(unittest.TestCase):

    def test_thread_writes_record_with_trace_id(self):
        from olympus.heroes.ariadne import ariadne
        from olympus.titans.mnemosyne import mnemosyne
        kind = _unique("ariadne-test-thread")
        tid = ariadne.thread(
            kind=kind, actor="test", summary="seed",
        )
        records = mnemosyne.recall(kind)
        self.assertEqual(len(records), 1)
        self.assertEqual((records[0].body or {}).get("trace_id"), tid)

    def test_chain_walks_parent_pointers(self):
        from olympus.heroes.ariadne import ariadne
        kind = _unique("ariadne-test-chain")
        root_id = ariadne.thread(kind=kind, actor="test",
                                  summary="root")
        mid_id = ariadne.thread(kind=kind, actor="test",
                                 summary="mid",
                                 parent_trace_id=root_id)
        leaf_id = ariadne.thread(kind=kind, actor="test",
                                  summary="leaf",
                                  parent_trace_id=mid_id)
        chain = ariadne.chain(leaf_id)
        self.assertEqual(chain.depth, 3)
        self.assertTrue(chain.root_reached)
        self.assertEqual(chain.events[0].trace_id, leaf_id)
        self.assertEqual(chain.events[-1].trace_id, root_id)

    def test_chain_handles_missing_trace_id(self):
        from olympus.heroes.ariadne import ariadne
        chain = ariadne.chain("nonexistent-trace-id")
        self.assertEqual(chain.depth, 0)
        self.assertEqual(chain.events, [])

    def test_descendants_walks_forward(self):
        from olympus.heroes.ariadne import ariadne
        kind = _unique("ariadne-test-descend")
        root_id = ariadne.thread(kind=kind, actor="test",
                                  summary="root")
        child1 = ariadne.thread(kind=kind, actor="test",
                                  summary="c1",
                                  parent_trace_id=root_id)
        child2 = ariadne.thread(kind=kind, actor="test",
                                  summary="c2",
                                  parent_trace_id=root_id)
        ariadne.thread(kind=kind, actor="test",
                        summary="gc",
                        parent_trace_id=child1)
        descendants = ariadne.descendants(root_id)
        descendant_ids = {d.trace_id for d in descendants}
        self.assertIn(child1, descendant_ids)
        self.assertIn(child2, descendant_ids)
        # Grandchild also present
        self.assertEqual(len(descendants), 3)

    def test_cycle_bounded_by_max_depth(self):
        from olympus.heroes.ariadne import Ariadne
        a = Ariadne()
        # Manually craft a cycle via low-level mnemosyne writes
        from olympus.titans.mnemosyne import mnemosyne
        kind = _unique("ariadne-test-cycle")
        a_id = "ta-cyc-a"; b_id = "ta-cyc-b"
        mnemosyne.remember(kind=kind, actor="test", summary="A",
                           trace_id=a_id, parent_trace_id=b_id)
        mnemosyne.remember(kind=kind, actor="test", summary="B",
                           trace_id=b_id, parent_trace_id=a_id)
        chain = a.chain(a_id)
        # Should NOT loop forever
        self.assertLessEqual(chain.depth, a.MAX_DEPTH)
        self.assertGreater(chain.truncated_at_depth, 0)


if __name__ == "__main__":
    unittest.main()
