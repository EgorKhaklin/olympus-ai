"""S1 — Mnemosyne: append-only audit-of-record discipline.

Every load-bearing decision writes to an append-only record. Old entries
are byte-frozen. Recall returns rows in insertion order. Per-kind files
are isolated."""
from __future__ import annotations

import pathlib as _pl
import sys as _sys
_ROOT = _pl.Path(__file__).resolve().parent.parent
_SRC = _ROOT / "src"
if str(_SRC) not in _sys.path:
    _sys.path.insert(0, str(_SRC))

import json
import pathlib
import tempfile
import unittest

from olympus.titans.mnemosyne import Mnemosyne, Memory


class TestS1_AppendOnly(unittest.TestCase):

    def _fresh(self):
        tmp = pathlib.Path(tempfile.mkdtemp())
        return Mnemosyne(base_path=tmp), tmp

    def test_S1a_remember_writes_one_row(self):
        m, base = self._fresh()
        m.remember(kind="test", actor="actor-1", summary="first")
        rows = m.recall("test")
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0].summary, "first")

    def test_S1b_recall_returns_in_insertion_order(self):
        m, _ = self._fresh()
        for i in range(20):
            m.remember(kind="ordered", actor="x", summary=str(i))
        rows = m.recall("ordered")
        self.assertEqual([r.summary for r in rows], [str(i) for i in range(20)])

    def test_S1c_per_kind_isolation(self):
        m, _ = self._fresh()
        m.remember(kind="kind-a", actor="x", summary="a-entry")
        m.remember(kind="kind-b", actor="x", summary="b-entry")
        self.assertEqual(len(m.recall("kind-a")), 1)
        self.assertEqual(len(m.recall("kind-b")), 1)
        # cross-recall returns nothing
        self.assertEqual(m.recall("kind-c"), [])

    def test_S1d_actor_filter(self):
        m, _ = self._fresh()
        m.remember(kind="filtered", actor="actor-a", summary="from a")
        m.remember(kind="filtered", actor="actor-b", summary="from b")
        m.remember(kind="filtered", actor="actor-a", summary="from a again")
        a_rows = m.recall("filtered", actor="actor-a")
        self.assertEqual(len(a_rows), 2)
        self.assertTrue(all(r.actor == "actor-a" for r in a_rows))

    def test_S1e_no_mutation_after_append(self):
        """Earlier rows must be byte-identical after later appends."""
        m, base = self._fresh()
        m.remember(kind="immutable", actor="x", summary="early")
        path = base / "immutable.jsonl"
        before = path.read_text(encoding="utf-8")
        for _ in range(10):
            m.remember(kind="immutable", actor="x", summary="later")
        after = path.read_text(encoding="utf-8")
        # the first line must be present unchanged at the start
        self.assertTrue(after.startswith(before),
            "S1 violation: earlier rows mutated")

    def test_S1f_kinds_listing_includes_all_files(self):
        m, _ = self._fresh()
        for k in ("alpha", "beta", "gamma"):
            m.remember(kind=k, actor="x", summary=k)
        self.assertEqual(sorted(m.kinds()), ["alpha", "beta", "gamma"])

    def test_S1g_body_fields_round_trip(self):
        m, _ = self._fresh()
        m.remember(kind="bodied", actor="x", summary="with body",
                   extra_field=42, nested={"a": [1, 2, 3]})
        row = m.recall("bodied")[0]
        self.assertEqual(row.body["extra_field"], 42)
        self.assertEqual(row.body["nested"], {"a": [1, 2, 3]})

    def test_S1h_kind_filename_sanitization(self):
        """Unusual kind names must not write outside the base dir."""
        m, base = self._fresh()
        m.remember(kind="../../escape-attempt", actor="x", summary="?")
        # No file should be created outside base
        outside = base.parent.glob("escape-attempt*")
        self.assertEqual(list(outside), [])

    def test_S1i_remember_returns_memory_object(self):
        m, _ = self._fresh()
        ret = m.remember(kind="return", actor="x", summary="test")
        self.assertIsInstance(ret, Memory)
        self.assertEqual(ret.actor, "x")
        self.assertEqual(ret.summary, "test")
        self.assertTrue(ret.remembered_at)


if __name__ == "__main__":
    unittest.main()
