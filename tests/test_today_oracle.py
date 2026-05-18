"""today oracle + iris live mode.

The claim being tested: today() returns a TodaysAction; priority
ordering works (panic > vindication > … > calm); record() persists;
iris live build produces a valid HTML page with a polling script.
"""
from __future__ import annotations

import pathlib as _pl
import sys as _sys
_ROOT = _pl.Path(__file__).resolve().parent.parent
_SRC = _ROOT / "src"
if str(_SRC) not in _sys.path:
    _sys.path.insert(0, str(_SRC))

import re
import unittest


class TestTodayOracle(unittest.TestCase):

    def test_today_returns_action(self):
        from olympus.runtime.today import today, TodaysAction
        action = today()
        self.assertIsInstance(action, TodaysAction)
        self.assertIn(action.priority,
                       {"urgent", "noteworthy", "gentle", "calm"})
        self.assertTrue(action.headline)

    def test_record_persists(self):
        from olympus.runtime.today import today, record
        from olympus.titans.mnemosyne import mnemosyne
        before = len(mnemosyne.recall("today.action"))
        record(today())
        after = len(mnemosyne.recall("today.action"))
        self.assertGreater(after, before)

    def test_panic_takes_priority(self):
        """If Pan is panicked, today() must return urgent."""
        from olympus.runtime.today import today
        from olympus.olympians.pan import pan, PanicState
        import datetime
        # Force Pan into panic
        pan._write_state(PanicState(
            panicked=True,
            entered_at=datetime.datetime.now(datetime.timezone.utc).isoformat(),
            last_transition_at=datetime.datetime.now(datetime.timezone.utc).isoformat(),
            detail="forced for today-oracle test",
        ))
        try:
            action = today()
            self.assertEqual(action.priority, "urgent")
            self.assertIn("Pan", action.headline)
        finally:
            pan.clear(by="test", reason="today-oracle cleanup")


class TestIrisLive(unittest.TestCase):

    def test_render_live_produces_html(self):
        from olympus.iris import render_live
        import pathlib, tempfile
        out = pathlib.Path(tempfile.mkdtemp()) / "live.html"
        render_live(out_path=out, api_base="http://127.0.0.1:9999",
                     interval_seconds=10.0)
        self.assertTrue(out.exists())
        text = out.read_text(encoding="utf-8")
        self.assertIn("<!doctype html>", text.lower())
        self.assertIn("I R I S", text)
        self.assertIn("L I V E", text)

    def test_live_html_includes_polling_script(self):
        from olympus.iris import render_live
        import pathlib, tempfile
        out = pathlib.Path(tempfile.mkdtemp()) / "live.html"
        render_live(out_path=out, api_base="http://x:1",
                     interval_seconds=3.0)
        text = out.read_text(encoding="utf-8")
        # The polling logic is the load-bearing piece
        self.assertIn("setInterval", text)
        self.assertIn("XMLHttpRequest", text)
        self.assertIn("/status", text)
        # Interval substituted (3.0s → 3000 ms)
        self.assertIn("3000", text)

    def test_live_html_substitutes_api_base(self):
        from olympus.iris import render_live
        import pathlib, tempfile
        out = pathlib.Path(tempfile.mkdtemp()) / "live.html"
        render_live(out_path=out, api_base="http://peer.example:8765",
                     interval_seconds=5.0)
        text = out.read_text(encoding="utf-8")
        self.assertIn("http://peer.example:8765", text)
        # No unsubstituted placeholders
        self.assertNotIn("__API_BASE__", text)
        self.assertNotIn("__INTERVAL_MS__", text)
        self.assertNotIn("__INTERVAL_S__", text)


if __name__ == "__main__":
    unittest.main()
