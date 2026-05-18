"""Clio's narrative auto-writer.

The claim being tested: clio.narrate() composes a Digest from recent
Mnemosyne records; writes a markdown file to codex/journal/<date>-
clio-digest.md; records the pass.
"""
from __future__ import annotations

import pathlib as _pl
import sys as _sys
_ROOT = _pl.Path(__file__).resolve().parent.parent
_SRC = _ROOT / "src"
if str(_SRC) not in _sys.path:
    _sys.path.insert(0, str(_SRC))

import unittest


class TestClioNarrative(unittest.TestCase):

    def test_narrate_returns_digest(self):
        from olympus.muses.clio import Clio, Digest
        digest = Clio().narrate(window_days=7, write=False)
        self.assertIsInstance(digest, Digest)
        self.assertEqual(digest.window_days, 7)
        self.assertTrue(digest.composed_at)

    def test_narrate_writes_file(self):
        from olympus.muses.clio import Clio
        from olympus.primordials.gaia import root
        digest = Clio().narrate(window_days=7, write=True)
        self.assertTrue(digest.path)
        import pathlib
        path = pathlib.Path(digest.path)
        self.assertTrue(path.exists())
        text = path.read_text(encoding="utf-8")
        self.assertIn("Olympus — Clio's digest", text)
        self.assertIn("Headlines", text)
        self.assertIn("Activity", text)

    def test_narrate_records_pass(self):
        from olympus.muses.clio import Clio
        from olympus.titans.mnemosyne import mnemosyne
        before = len(mnemosyne.recall("clio.narrate"))
        Clio().narrate(window_days=7, write=False)
        after = len(mnemosyne.recall("clio.narrate"))
        self.assertGreater(after, before)

    def test_digest_counts_match_recent_records(self):
        """Seed one session.completed; confirm digest counts include it."""
        from olympus.muses.clio import Clio
        from olympus.titans.mnemosyne import mnemosyne
        before_digest = Clio().narrate(window_days=7, write=False)
        before_count = before_digest.sessions_run
        # Seed a session
        mnemosyne.remember(
            kind="session.completed", actor="test:session",
            summary="seeded for clio test",
            session_id="clio-test-session",
            hydra_findings=0, argos_pheromones=0, proposals_count=0,
        )
        after_digest = Clio().narrate(window_days=7, write=False)
        self.assertEqual(after_digest.sessions_run, before_count + 1)


if __name__ == "__main__":
    unittest.main()
