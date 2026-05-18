"""Runtime tests — boundaries, concurrency, persistence, recovery."""
from __future__ import annotations

import pathlib as _pl
import sys as _sys
_ROOT = _pl.Path(__file__).resolve().parent.parent
_SRC = _ROOT / 'src'
if str(_SRC) not in _sys.path:
    _sys.path.insert(0, str(_SRC))

import json
import pathlib
import tempfile
import threading
import unittest


class TestBoundaries(unittest.TestCase):

    def test_bounded_wraps_exception(self):
        from olympus.runtime.boundaries import bounded

        @bounded(name="test.boom", quarantine_on_error=False,
                 record_in_mnemosyne=False)
        def boom():
            raise ValueError("kaboom")

        r = boom()
        self.assertFalse(r.ok)
        self.assertIn("ValueError", r.error)

    def test_bounded_returns_value_on_success(self):
        from olympus.runtime.boundaries import bounded

        @bounded(name="test.ok", quarantine_on_error=False,
                 record_in_mnemosyne=False)
        def ok():
            return 42

        r = ok()
        self.assertTrue(r.ok)
        self.assertEqual(r.value, 42)


class TestConcurrency(unittest.TestCase):

    def test_atomic_append_is_thread_safe(self):
        from olympus.runtime.concurrency import atomic_append
        tmp = pathlib.Path(tempfile.mkdtemp()) / "appendlog.jsonl"

        N_THREADS = 8
        ROWS_PER = 20

        def writer(thread_id: int):
            for i in range(ROWS_PER):
                atomic_append(tmp, json.dumps({"t": thread_id, "i": i}))

        threads = [threading.Thread(target=writer, args=(t,))
                   for t in range(N_THREADS)]
        for t in threads: t.start()
        for t in threads: t.join()

        # Every line must parse as JSON (no interleaved bytes)
        with tmp.open("r", encoding="utf-8") as f:
            rows = [json.loads(line) for line in f if line.strip()]
        self.assertEqual(len(rows), N_THREADS * ROWS_PER)


class TestPersistence(unittest.TestCase):

    def test_integrity_check_finds_corruption(self):
        from olympus.runtime.persistence import integrity_check
        tmp = pathlib.Path(tempfile.mkdtemp()) / "corrupt.jsonl"
        tmp.write_text('{"a":1}\n{"b":2}\nthis is not json\n{"c":3}\n',
                       encoding="utf-8")
        intact, bad, err = integrity_check(tmp)
        self.assertFalse(intact)
        self.assertEqual(bad, 3)
        self.assertIsNotNone(err)

    def test_compact_drops_filtered_rows(self):
        from olympus.runtime.persistence import compact_jsonl
        tmp = pathlib.Path(tempfile.mkdtemp()) / "compact.jsonl"
        with tmp.open("w", encoding="utf-8") as f:
            for i in range(10):
                f.write(json.dumps({"i": i, "keep": i % 2 == 0}) + "\n")
        dropped = compact_jsonl(tmp, keep_predicate=lambda r: r["keep"])
        self.assertEqual(dropped, 5)
        with tmp.open("r", encoding="utf-8") as f:
            remaining = [json.loads(line) for line in f if line.strip()]
        self.assertEqual(len(remaining), 5)
        self.assertTrue(all(r["keep"] for r in remaining))


class TestRecovery(unittest.TestCase):

    def test_retire_component_moves_to_ended(self):
        from olympus.runtime.recovery import retire_component
        from olympus.titans.iapetus import iapetus, LifecyclePhase
        retire_component("test-component-recovery",
                         final_state={"last_value": 42},
                         reason="unit-test")
        lc = iapetus.of("test-component-recovery")
        self.assertEqual(lc.phase, LifecyclePhase.ENDED)


if __name__ == "__main__":
    unittest.main()
