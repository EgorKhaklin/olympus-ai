"""scripts/loop.sh — the bash cron orchestration.

The claim being tested: loop.sh exists, is executable, accepts the
documented flags, and `--dry-run` runs without invoking the substrate
(so installing it in crontab won't surprise anyone the first time it
fires before the operator has reviewed the script).
"""
from __future__ import annotations

import os
import pathlib as _pl
import subprocess
import sys as _sys
import unittest

_ROOT = _pl.Path(__file__).resolve().parent.parent


class TestLoopScript(unittest.TestCase):

    LOOP = _ROOT / "scripts" / "loop.sh"

    def test_exists_and_executable(self):
        self.assertTrue(self.LOOP.exists(), "scripts/loop.sh missing")
        self.assertTrue(os.access(self.LOOP, os.X_OK),
                        "scripts/loop.sh not executable")

    def test_starts_with_bash_shebang(self):
        first = self.LOOP.read_text(encoding="utf-8").splitlines()[0]
        self.assertTrue(first.startswith("#!"),
                        "loop.sh must start with shebang")
        self.assertIn("bash", first)

    def test_dry_run_succeeds_without_invoking_substrate(self):
        """--dry-run must not call invoke (so it's safe to test the
        loop wiring on a fresh checkout without side-effects)."""
        result = subprocess.run(
            [str(self.LOOP), "--dry-run"],
            capture_output=True, text=True, timeout=15,
        )
        self.assertEqual(result.returncode, 0,
                         f"dry-run exited {result.returncode}: "
                         f"{result.stderr}")
        out = result.stdout + result.stderr
        self.assertIn("DRY-RUN", out)
        self.assertIn("session", out)
        self.assertIn("improve", out)

    def test_help_documents_crontab(self):
        """--help should print the crontab example so an operator
        installing this never has to read the source."""
        result = subprocess.run(
            [str(self.LOOP), "--help"],
            capture_output=True, text=True, timeout=10,
        )
        self.assertEqual(result.returncode, 0)
        body = result.stdout
        self.assertIn("crontab", body.lower())

    def test_unknown_flag_rejected(self):
        result = subprocess.run(
            [str(self.LOOP), "--this-flag-does-not-exist"],
            capture_output=True, text=True, timeout=10,
        )
        self.assertNotEqual(result.returncode, 0)


if __name__ == "__main__":
    unittest.main()
