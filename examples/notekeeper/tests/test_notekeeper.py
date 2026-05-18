"""End-to-end notekeeper test — verifies the full deployment."""
from __future__ import annotations

import pathlib as _pl
import sys as _sys
_THIS = _pl.Path(__file__).resolve()
_REPO = _THIS.parent.parent.parent.parent     # examples/notekeeper/tests → repo root
_SRC = _REPO / "src"
_NK = _REPO / "examples" / "notekeeper"
for p in (_SRC, _NK):
    if str(p) not in _sys.path:
        _sys.path.insert(0, str(p))

import unittest

from notekeeper.notes import capture, all_notes, by_topic, infer_topics
from notekeeper.eyes import (
    EyeUntopicedNotes, EyeStaleNotes, EyeCaptureVelocity,
    register_with_colony,
)
from notekeeper.heads import HeadTopicDrift, attach_to_hydra
from notekeeper.predictions import register_with_apollo


class TestInferTopics(unittest.TestCase):

    def test_empty_text_no_topics(self):
        self.assertEqual(infer_topics(""), [])
        self.assertEqual(infer_topics("   "), [])

    def test_stopwords_excluded(self):
        topics = infer_topics("the and of the and")
        self.assertEqual(topics, [])

    def test_high_frequency_token_ranks_first(self):
        topics = infer_topics(
            "olympus olympus olympus athena hephaestus athena olympus"
        )
        self.assertEqual(topics[0], "olympus")


class TestCapture(unittest.TestCase):

    def test_capture_returns_note_with_id_topics(self):
        n = capture("argos sees everything; athena synthesizes briefs")
        self.assertTrue(n.id)
        self.assertIn("argos", n.topics + [])  # rank may vary; argos is one
        self.assertEqual(n.text, "argos sees everything; athena synthesizes briefs")

    def test_capture_refuses_empty(self):
        with self.assertRaises(ValueError):
            capture("   ")

    def test_capture_appears_in_all_notes(self):
        before = len(all_notes())
        capture("a unique note about chimera and minotaur for the test suite")
        after = len(all_notes())
        self.assertGreaterEqual(after - before, 1)

    def test_by_topic_returns_captured_note(self):
        capture("hyperion hyperion hyperion brightness brightness brightness")
        results = by_topic("hyperion")
        self.assertTrue(any("hyperion" in n.text for n in results))


class TestEyes(unittest.TestCase):

    def test_eye_untopiced_runs(self):
        e = EyeUntopicedNotes()
        result = e.scan()
        self.assertEqual(len(result), 1)
        self.assertIn(result[0].kind, ("info", "drift"))

    def test_eye_stale_runs(self):
        e = EyeStaleNotes()
        result = e.scan()
        self.assertEqual(len(result), 1)

    def test_eye_capture_velocity_runs(self):
        e = EyeCaptureVelocity()
        result = e.scan()
        self.assertEqual(len(result), 1)


class TestHead(unittest.TestCase):

    def test_head_topic_drift_runs(self):
        h = HeadTopicDrift()
        result = h.observe()
        self.assertEqual(len(result), 1)


class TestIntegration(unittest.TestCase):

    def test_setup_then_session_runs_clean(self):
        """Register notekeeper components; run a session; verify the new
        eyes and head appear in the report."""
        from olympus.olympians.hestia import hestia
        if not hestia.is_lit():
            hestia.kindle(name="notekeeper-test",
                          vocation="domain test for notekeeper deployment")

        register_with_colony()
        attach_to_hydra()
        register_with_apollo()

        # capture a few notes so the eyes have something to look at
        for txt in [
            "hera bindings between olympus modules",
            "athena synthesis of hydra and argos",
            "apollo predicts the future",
        ]:
            capture(txt)

        from olympus.session import Session
        r = Session(directive="notekeeper integration test").run()
        self.assertIsNone(r.error, f"session errored: {r.error}")
        # the new eyes should appear in the by_eye breakdown
        eye_names = set(r.argos_by_eye.keys())
        self.assertIn("eye_untopiced_notes", eye_names)
        self.assertIn("eye_stale_notes", eye_names)
        self.assertIn("eye_capture_velocity", eye_names)
        # the new head should appear
        head_names = set(r.hydra_by_head.keys())
        self.assertIn("topic_drift", head_names)


if __name__ == "__main__":
    unittest.main()
