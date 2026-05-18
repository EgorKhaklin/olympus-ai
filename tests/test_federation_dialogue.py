"""Federation + Dialogue.

The claim being tested: Hermes.federate() handles peer-down gracefully
(records error, returns digest with reachable=False); the live
roundtrip works against a real peer (loopback HTTP API). Dialogue
answers known templates and reports `none` for unknown questions.
"""
from __future__ import annotations

import pathlib as _pl
import sys as _sys
_ROOT = _pl.Path(__file__).resolve().parent.parent
_SRC = _ROOT / "src"
if str(_SRC) not in _sys.path:
    _sys.path.insert(0, str(_SRC))

import unittest


class TestFederation(unittest.TestCase):

    def test_peer_down_returns_unreachable(self):
        """Try to federate against an obviously-bad address."""
        from olympus.runtime.federation import federate
        digest = federate("http://127.0.0.1:1",  # port 1 — nothing listens
                          timeout_seconds=2.0)
        self.assertFalse(digest.reachable)
        self.assertTrue(digest.error)

    def test_federate_records_to_mnemosyne(self):
        from olympus.runtime.federation import federate
        from olympus.titans.mnemosyne import mnemosyne
        before = len(mnemosyne.recall("hermes.federation"))
        federate("http://127.0.0.1:1", timeout_seconds=1.0)
        after = len(mnemosyne.recall("hermes.federation"))
        self.assertGreater(after, before)

    def test_known_peers_returns_recorded(self):
        from olympus.runtime.federation import federate, known_peers
        federate("http://127.0.0.1:1", timeout_seconds=1.0)
        peers = known_peers(limit=20)
        self.assertGreaterEqual(len(peers), 1)

    def test_loopback_federation(self):
        """Start our own HTTP API; federate against it."""
        from olympus.runtime.http_api import serve_background
        from olympus.runtime.federation import federate
        handle = serve_background(host="127.0.0.1", port=0)
        try:
            digest = federate(handle.url(""), timeout_seconds=5.0)
            self.assertTrue(digest.reachable)
            self.assertEqual(digest.status_code, 200)
            self.assertIn("hearth", digest.peer_status)
        finally:
            handle.stop()


class TestDialogue(unittest.TestCase):

    def test_help_template(self):
        from olympus.runtime.dialogue import ask
        answer = ask("help")
        self.assertEqual(answer.matched_template, "help")
        self.assertIn("what happened", answer.text)

    def test_what_happened_template(self):
        from olympus.runtime.dialogue import ask
        answer = ask("what happened today")
        self.assertEqual(answer.matched_template, "what-happened")
        self.assertIn("session.completed", answer.sources)

    def test_what_worried_template(self):
        from olympus.runtime.dialogue import ask
        answer = ask("what are we worried about")
        self.assertEqual(answer.matched_template, "what-worried")

    def test_loop_health_template(self):
        from olympus.runtime.dialogue import ask
        answer = ask("how is the loop")
        self.assertEqual(answer.matched_template, "loop-health")

    def test_who_is_template(self):
        from olympus.runtime.dialogue import ask
        answer = ask("who is pan")
        self.assertEqual(answer.matched_template, "who-is")
        self.assertIn("olympians", answer.text.lower())

    def test_what_learned_template(self):
        from olympus.runtime.dialogue import ask
        answer = ask("what has the substrate learned")
        self.assertEqual(answer.matched_template, "what-learned")

    def test_unknown_question_falls_back(self):
        from olympus.runtime.dialogue import ask
        answer = ask("quack quack the platypus")
        self.assertEqual(answer.matched_template, "none")
        self.assertIn("help", answer.text)

    def test_records_to_mnemosyne(self):
        from olympus.runtime.dialogue import ask
        from olympus.titans.mnemosyne import mnemosyne
        before = len(mnemosyne.recall("dialogue.ask"))
        ask("what happened today")
        after = len(mnemosyne.recall("dialogue.ask"))
        self.assertGreater(after, before)


if __name__ == "__main__":
    unittest.main()
