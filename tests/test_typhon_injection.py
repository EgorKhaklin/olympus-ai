"""Typhon — fault injection with reverters.

The claim being tested: typhon.inject() refuses without confirm=True;
each known scenario actually disturbs state; revert() restores it;
records typhon.injection + typhon.recovery to Mnemosyne.
"""
from __future__ import annotations

import pathlib as _pl
import sys as _sys
_ROOT = _pl.Path(__file__).resolve().parent.parent
_SRC = _ROOT / "src"
if str(_SRC) not in _sys.path:
    _sys.path.insert(0, str(_SRC))

import unittest


class TestTyphonInjection(unittest.TestCase):

    def test_refuses_without_confirm(self):
        from olympus.monsters.typhon import typhon
        with self.assertRaises(RuntimeError):
            typhon.inject("delete-pan-state")

    def test_unknown_scenario_raises(self):
        from olympus.monsters.typhon import typhon
        with self.assertRaises(KeyError):
            typhon.inject("not-a-real-scenario", confirm=True)

    def test_injectable_list(self):
        from olympus.monsters.typhon import typhon
        injectable = set(typhon.injectable())
        for required in ("delete-pan-state",
                          "seed-fake-violations",
                          "break-styx-chain"):
            self.assertIn(required, injectable)

    def test_delete_pan_state_inject_and_revert(self):
        from olympus.monsters.typhon import typhon
        from olympus.primordials.gaia import root
        pan_state = root.child("state", "pan", "state.json")
        # Ensure there's something to delete first
        pan_state.parent.mkdir(parents=True, exist_ok=True)
        if not pan_state.exists():
            pan_state.write_text('{"panicked": false}', encoding="utf-8")
        original = pan_state.read_text(encoding="utf-8")
        injection = typhon.inject("delete-pan-state", confirm=True)
        self.assertFalse(pan_state.exists(), "state should be deleted")
        injection.revert()
        self.assertTrue(pan_state.exists(),
                        "revert should restore state file")
        self.assertEqual(pan_state.read_text(encoding="utf-8"),
                         original)

    def test_seed_fake_violations_recorded(self):
        from olympus.monsters.typhon import typhon
        from olympus.titans.mnemosyne import mnemosyne
        before = len(mnemosyne.recall("invariant.violated"))
        injection = typhon.inject("seed-fake-violations",
                                    confirm=True, n=3)
        try:
            after = len(mnemosyne.recall("invariant.violated"))
            self.assertEqual(after - before, 3)
        finally:
            injection.revert()

    def test_injection_recorded_to_mnemosyne(self):
        from olympus.monsters.typhon import typhon
        from olympus.titans.mnemosyne import mnemosyne
        before_inj = len(mnemosyne.recall("typhon.injection"))
        before_rec = len(mnemosyne.recall("typhon.recovery"))
        injection = typhon.inject("seed-fake-violations",
                                    confirm=True, n=2)
        injection.revert()
        after_inj = len(mnemosyne.recall("typhon.injection"))
        after_rec = len(mnemosyne.recall("typhon.recovery"))
        self.assertGreater(after_inj, before_inj)
        self.assertGreater(after_rec, before_rec)

    def test_break_styx_chain_detected_by_tisiphone(self):
        """The real proof: an injected break is DETECTED by the
        substrate's own integrity check (Tisiphone)."""
        from olympus.monsters.typhon import typhon
        from olympus.furies.tisiphone import tisiphone
        # Verify clean first
        baseline = tisiphone.verify_styx()
        self.assertTrue(baseline.intact)
        injection = typhon.inject("break-styx-chain", confirm=True)
        try:
            broken = tisiphone.verify_styx()
            self.assertFalse(
                broken.intact,
                "Tisiphone should detect the injected styx chain break",
            )
        finally:
            injection.revert()
        recovered = tisiphone.verify_styx()
        self.assertTrue(recovered.intact,
                        "revert should restore chain integrity")


if __name__ == "__main__":
    unittest.main()
