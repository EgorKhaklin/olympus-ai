"""S8 — Continuity of Understanding.

Every load-bearing action the agent takes must be reconstructible —
what was done, why, on whose authority — from the substrate's own
records alone."""
from __future__ import annotations

import pathlib as _pl
import sys as _sys
_ROOT = _pl.Path(__file__).resolve().parent.parent
_SRC = _ROOT / "src"
if str(_SRC) not in _sys.path:
    _sys.path.insert(0, str(_SRC))

import unittest


LOAD_BEARING_KINDS = (
    "decision", "thread.spun", "thread.cut", "hydra.run",
    "colony.deploy", "bootstrap", "invariant.violated",
    "session.completed", "action.promoted", "action.ratified",
    "action.executed", "action.rejected", "action.failed",
)


class TestS8_ContinuityOfUnderstanding(unittest.TestCase):

    def setUp(self) -> None:
        # Clear Pan so ratification tests aren't blocked by
        # cross-test invariant-violation accumulation.
        from olympus.olympians.pan import pan
        pan.clear(by="test", reason="test_invariant_S8 setUp")

    def test_S8a_themis_names_S8(self):
        from olympus.titans.themis import themis
        inv = themis.by_id("S8")
        self.assertIsNotNone(inv)
        body = (inv.name + " " + inv.statement).lower()
        self.assertTrue(
            any(k in body for k in ("reconstructible", "continuity",
                                     "reconstruct", "obscure", "understanding")),
            f"S8 should be named 'Continuity of Understanding'; got {inv.name}",
        )

    def test_S8b_cosmogony_mentions_S8(self):
        from olympus.titans.themis import themis
        self.assertTrue(themis.cosmogony_mentions("S8"))

    def test_S8c_momus_AP6_enforces_understanding(self):
        from olympus.heroes.momus import momus
        ap6 = momus.by_id("AP6")
        self.assertIsNotNone(ap6)
        body = (ap6.name + " " + ap6.description + " " + ap6.refusal).lower()
        self.assertTrue(
            any(k in body for k in ("reconstruct", "obscur", "understanding",
                                     "rationale")),
            f"AP6 must enforce S8; got {ap6.name}",
        )

    def test_S8d_eye_understanding_gap_registered(self):
        from olympus.monsters.argos.colony import colony
        names = [e.NAME for e in colony.eyes()]
        self.assertIn("eye_understanding_gap", names,
            "S8 structural enforcement requires eye_understanding_gap")

    def test_S8e_no_load_bearing_memory_is_anonymous(self):
        from olympus.titans.mnemosyne import mnemosyne
        gaps: list[str] = []
        for kind in mnemosyne.kinds():
            if kind not in LOAD_BEARING_KINDS:
                continue
            for m in mnemosyne.recall(kind):
                if not m.actor or not m.summary:
                    gaps.append(f"{kind}@{m.remembered_at}")
        self.assertEqual([], gaps,
            f"S8 violation — anonymous load-bearing memories: {gaps[:5]}")

    def test_S8f_every_session_has_a_memory(self):
        """Every session must leave at least one session.completed entry
        with its session_id in the body. Reconstructability of sessions."""
        from olympus.titans.mnemosyne import mnemosyne
        # If sessions have ever run, all of them must carry a session_id
        sessions = mnemosyne.recall("session.completed")
        for m in sessions:
            self.assertIn("session_id", m.body,
                f"session.completed memory at {m.remembered_at} has no session_id")

    def test_S8g_every_oath_has_a_sworn_by(self):
        """Every Styx oath must record who swore it. Reconstructability
        of constitutional commitments."""
        from olympus.underworld.styx import styx
        for row in styx._read_all():
            self.assertTrue(row.get("sworn_by"),
                f"Styx oath seq={row.get('seq')} has empty sworn_by")
            self.assertTrue(row.get("statement"),
                f"Styx oath seq={row.get('seq')} has empty statement")

    def test_S8h_styx_chain_is_intact(self):
        """The whole oath chain must hash-verify clean. Tampered oaths
        are S8 violations by definition (you can't reconstruct from a
        record that's been edited)."""
        from olympus.underworld.styx import styx
        intact, bad = styx.verify()
        self.assertTrue(intact,
            f"S8 violation — Styx tampered at seq={bad}")

    def test_S8i_action_lifecycle_is_reconstructible(self):
        """Each action's transitions are append-only and recallable.
        Given an action_id, we can find every state transition."""
        import secrets
        from olympus.action import action_queue
        from olympus.titans.mnemosyne import mnemosyne

        uniq = secrets.token_hex(4)
        class _P:
            id = f"S8-recon-{uniq}"
            risk_class = "MEDIUM"
            proposed_fix = "reconstructability test"

        action_queue.promote(_P())
        action_queue.ratify(f"act-{_P.id}", quote="for the test")

        # Recall both promotion and ratification — at least one of each
        # for this unique action_id
        promotions = mnemosyne.recall("action.promoted")
        ratifications = mnemosyne.recall("action.ratified")
        prom = [m for m in promotions if m.body.get("action_id") == f"act-{_P.id}"]
        rat = [m for m in ratifications if m.body.get("action_id") == f"act-{_P.id}"]
        self.assertGreaterEqual(len(prom), 1,
            "S8 violation — no promotion memory for this action")
        self.assertGreaterEqual(len(rat), 1,
            "S8 violation — no ratification memory for this action")


if __name__ == "__main__":
    unittest.main()
