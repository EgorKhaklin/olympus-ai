"""S6 — Delphi: strategic-decision discipline.

MEDIUM and HIGH-risk decisions are recorded in codex/oracles/delphi/.
The pre-ship gate refuses HIGH ships without a Delphi reference."""
from __future__ import annotations

import pathlib as _pl
import sys as _sys
_ROOT = _pl.Path(__file__).resolve().parent.parent
_SRC = _ROOT / "src"
if str(_SRC) not in _sys.path:
    _sys.path.insert(0, str(_SRC))

import unittest


class TestS6_DelphiProtocol(unittest.TestCase):

    def test_S6a_delphi_directory_exists(self):
        from olympus.primordials.gaia import root
        delphi = root.child("codex", "oracles", "delphi")
        self.assertTrue(delphi.is_dir(),
            "codex/oracles/delphi/ must exist; this is where decisions live")

    def test_S6b_at_least_one_delphi_recorded(self):
        """The substrate has SHIPPED multiple HIGH/COMPOSITE deltas;
        each one must have a corresponding Delphi file."""
        from olympus.primordials.gaia import root
        delphi = root.child("codex", "oracles", "delphi")
        files = list(delphi.glob("*.md"))
        self.assertGreater(len(files), 0,
            "S6 violation: HIGH/COMPOSITE work has shipped but no Delphi recorded")

    def test_S6c_every_delphi_names_decision(self):
        """Each Delphi file must contain a `## Decision` or `**Decided:**`
        section — that's the load-bearing claim."""
        from olympus.primordials.gaia import root
        delphi = root.child("codex", "oracles", "delphi")
        for f in delphi.glob("*.md"):
            text = f.read_text(encoding="utf-8")
            self.assertTrue(
                "## Decision" in text or "**Decided" in text,
                f"Delphi {f.name} lacks a Decision section",
            )

    def test_S6d_every_delphi_names_position(self):
        """A Delphi must show what was decided (Position A/B/C or similar)."""
        from olympus.primordials.gaia import root
        delphi = root.child("codex", "oracles", "delphi")
        for f in delphi.glob("*.md"):
            text = f.read_text(encoding="utf-8")
            self.assertIn("Position", text,
                f"Delphi {f.name} doesn't name a Position")

    def test_S6e_every_delphi_references_styx(self):
        """A Delphi decision becomes binding only when sworn on Styx.
        Each Delphi file must reference a Styx seq number."""
        from olympus.primordials.gaia import root
        delphi = root.child("codex", "oracles", "delphi")
        for f in delphi.glob("*.md"):
            text = f.read_text(encoding="utf-8").lower()
            self.assertTrue(
                "styx" in text and ("seq" in text or "sworn" in text),
                f"Delphi {f.name} doesn't reference Styx oath",
            )

    def test_S6f_action_queue_routes_high_to_delphi_pending(self):
        """A HIGH-risk proposal must land in delphi-pending, not auto-ratified."""
        from olympus.action import action_queue
        class _P:
            id = "S6-test-1"
            risk_class = "HIGH"
            proposed_fix = "test high promotion"
        a = action_queue.promote(_P())
        self.assertEqual(a.status, "delphi-pending")

    def test_S6g_high_action_ratification_requires_quote(self):
        """Ratifying a delphi-pending action SHOULD swear on Styx with the quote."""
        from olympus.action import action_queue
        from olympus.underworld.styx import styx
        before = len(styx._read_all())
        class _P:
            id = "S6-test-2"
            risk_class = "HIGH"
            proposed_fix = "second high test"
        action_queue.promote(_P())
        action_queue.ratify(f"act-{_P.id}", quote="test quote")
        after = len(styx._read_all())
        self.assertGreater(after, before,
            "ratifying a HIGH action must swear on Styx")


if __name__ == "__main__":
    unittest.main()
