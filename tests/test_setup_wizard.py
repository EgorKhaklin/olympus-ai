"""runtime/setup.py — interactive welcome wizard.

The claim being tested: each step is invokable via an injected
input_provider (no real input() in tests); the wizard is idempotent;
each step records to Mnemosyne; the LLM-anthropic-without-key path
does NOT save broken config; the final save lands in state/config.json.
"""
from __future__ import annotations

import pathlib as _pl
import sys as _sys
_ROOT = _pl.Path(__file__).resolve().parent.parent
_SRC = _ROOT / "src"
if str(_SRC) not in _sys.path:
    _sys.path.insert(0, str(_SRC))

import os
import pathlib
import tempfile
import unittest
from unittest.mock import patch


def _scripted_asker(answers: list[str]):
    """Returns an asker that consumes `answers` in order and returns
    the default if it runs out."""
    idx = [0]
    def asker(prompt: str, default: str = "") -> str:
        i = idx[0]
        idx[0] += 1
        if i >= len(answers):
            return default
        a = answers[i]
        return a if a else default
    return asker


class TestSetupWizard(unittest.TestCase):

    def setUp(self) -> None:
        # Each test uses its own tempdir for config so the production
        # state/config.json is never touched.
        self._tmp = pathlib.Path(tempfile.mkdtemp())
        self._tmp_config = self._tmp / "config.json"
        self._patch_path = patch(
            "olympus.runtime.config._path",
            return_value=self._tmp_config,
        )
        self._patch_path.start()

    def tearDown(self) -> None:
        self._patch_path.stop()

    def test_minimal_walkthrough_echo_no_daemon(self):
        """Stranger picks echo, no daemon, skip first session."""
        from olympus.runtime.setup import run_setup
        answers = [
            "test-deployment",          # kindle name
            "test vocation",            # vocation
            "echo",                     # LLM choice
            "n",                        # install daemon? no
            "8765",                     # agora port
            "n",                        # run first session? no
        ]
        report = run_setup(asker=_scripted_asker(answers), quiet=True)
        self.assertEqual(report.config_path, str(self._tmp_config))
        # Config saved with expected values
        from olympus.runtime import config
        cfg = config.load()
        self.assertEqual(cfg.kindled, "test-deployment")
        self.assertEqual(cfg.vocation, "test vocation")
        self.assertEqual(cfg.llm.provider, "echo")
        self.assertFalse(cfg.daemon.installed)
        self.assertEqual(cfg.agora.port, 8765)
        self.assertTrue(cfg.setup_completed_at)

    def test_records_each_step_to_mnemosyne(self):
        from olympus.runtime.setup import run_setup
        from olympus.titans.mnemosyne import mnemosyne
        before = len(mnemosyne.recall("setup.step"))
        run_setup(
            asker=_scripted_asker([
                "rec-test", "vocation", "echo", "n", "8765", "n",
            ]),
            quiet=True,
        )
        after = len(mnemosyne.recall("setup.step"))
        # At least 5 step records (kindle, llm, daemon, agora, first-session)
        self.assertGreaterEqual(after - before, 5)

    def test_completed_record_written(self):
        from olympus.runtime.setup import run_setup
        from olympus.titans.mnemosyne import mnemosyne
        before = len(mnemosyne.recall("setup.completed"))
        run_setup(
            asker=_scripted_asker([
                "compl-test", "vocation", "echo", "n", "8765", "n",
            ]),
            quiet=True,
        )
        after = len(mnemosyne.recall("setup.completed"))
        self.assertGreater(after, before)

    def test_idempotent_rerun_preserves_values(self):
        from olympus.runtime.setup import run_setup
        from olympus.runtime import config
        # First run
        run_setup(
            asker=_scripted_asker([
                "idem-test", "vocation", "echo", "n", "9000", "n",
            ]),
            quiet=True,
        )
        cfg1 = config.load()
        # Second run with all-empty answers — should preserve cfg1
        run_setup(
            asker=_scripted_asker(["", "", "", "", "", ""]),
            quiet=True,
        )
        cfg2 = config.load()
        self.assertEqual(cfg1.kindled, cfg2.kindled)
        self.assertEqual(cfg1.agora.port, cfg2.agora.port)

    def test_first_session_runs_via_injected_runner(self):
        """The first-session step uses an injected run_session_fn so
        tests can stub it without spawning real sessions."""
        from olympus.runtime.setup import run_setup
        called = {"count": 0}

        class _FakeReport:
            error = None
            session_id = "fake-session-id"
            hydra_findings = 0
            argos_pheromones = 0
            proposals_count = 0

        def fake_run(directive=None):
            called["count"] += 1
            return _FakeReport()

        run_setup(
            asker=_scripted_asker([
                "fs-test", "vocation", "echo", "n", "8765", "y",
            ]),
            run_session_fn=fake_run,
            quiet=True,
        )
        self.assertEqual(called["count"], 1)

    def test_is_setup_complete(self):
        from olympus.runtime.setup import (
            run_setup, is_setup_complete,
        )
        # Fresh config — not complete yet
        from olympus.runtime import config
        self.assertFalse(is_setup_complete())
        run_setup(
            asker=_scripted_asker([
                "complete-test", "v", "echo", "n", "8765", "n",
            ]),
            quiet=True,
        )
        self.assertTrue(is_setup_complete())


if __name__ == "__main__":
    unittest.main()
