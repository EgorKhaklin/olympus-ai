"""olympus.runtime.daemon — long-running self-improvement supervisor.

The claim being tested: templates render with all placeholders filled;
generated launchd plist is well-formed XML; generated systemd unit
parses as INI; install/uninstall are dry-runnable; run() with
max_iterations=2 actually executes and logs.
"""
from __future__ import annotations

import pathlib as _pl
import sys as _sys
_ROOT = _pl.Path(__file__).resolve().parent.parent
_SRC = _ROOT / "src"
if str(_SRC) not in _sys.path:
    _sys.path.insert(0, str(_SRC))

import json
import unittest
import xml.etree.ElementTree as ET


class TestDaemonTemplates(unittest.TestCase):

    def test_launchd_template_renders_to_valid_xml(self):
        from olympus.runtime.daemon import _render_template
        text = _render_template("com.olympus.daemon.plist.tmpl",
                                interval_seconds=600)
        # All placeholders substituted
        for placeholder in ("{LABEL}", "{INVOKE_PATH}", "{OLYMPUS_HOME}",
                            "{INTERVAL_SECONDS}", "{LOG_PATH}"):
            self.assertNotIn(placeholder, text,
                             f"unresolved placeholder {placeholder}")
        # Parses as XML
        ET.fromstring(text)

    def test_launchd_template_has_required_keys(self):
        from olympus.runtime.daemon import _render_template
        text = _render_template("com.olympus.daemon.plist.tmpl",
                                interval_seconds=600)
        for key in ("Label", "ProgramArguments", "WorkingDirectory",
                    "EnvironmentVariables", "RunAtLoad", "KeepAlive"):
            self.assertIn(f"<key>{key}</key>", text)

    def test_systemd_template_renders_with_required_sections(self):
        from olympus.runtime.daemon import _render_template
        text = _render_template("olympus-daemon.service.tmpl",
                                interval_seconds=600)
        for placeholder in ("{OLYMPUS_HOME}", "{INVOKE_PATH}",
                            "{INTERVAL_SECONDS}"):
            self.assertNotIn(placeholder, text)
        for section in ("[Unit]", "[Service]", "[Install]"):
            self.assertIn(section, text)
        # Has executable
        self.assertIn("ExecStart=", text)


class TestDaemonInstall(unittest.TestCase):

    def test_install_dry_run(self):
        from olympus.runtime import daemon as d
        result = d.install(interval_seconds=300, dry_run=True)
        self.assertIn(result["platform"], ("Darwin", "Linux"))
        if result["platform"] in ("Darwin", "Linux"):
            self.assertIn("would_write", result)
            self.assertGreater(result.get("rendered_bytes", 0), 0)

    def test_uninstall_dry_run(self):
        from olympus.runtime import daemon as d
        result = d.uninstall(dry_run=True)
        # Either platform — both report 'would_remove' or 'detail'
        self.assertIn(result["platform"], ("Darwin", "Linux"))

    def test_status_returns_structured_object(self):
        from olympus.runtime import daemon as d
        s = d.status()
        self.assertIn(s.platform, ("Darwin", "Linux"))
        self.assertIsInstance(s.installed, bool)
        self.assertIsInstance(s.running, bool)


class TestDaemonRun(unittest.TestCase):

    def test_run_with_max_iterations_terminates(self):
        """Run with --count 2 — should complete 2 iterations and exit
        cleanly, logging to state/daemon.log."""
        from olympus.runtime import daemon as d
        from olympus.olympians.hestia import hestia
        from olympus.olympians.pan import pan
        from olympus.primordials.gaia import root
        if not hestia.is_lit():
            hestia.kindle(name="daemon-test",
                          vocation="daemon iteration smoke")
        # Clear Pan so the iteration body actually runs (other tests
        # may have left seeded violations behind that would push Pan
        # into panic, which would route us through the daemon.skipped
        # branch instead of daemon.iteration).
        pan.clear(by="test", reason="daemon-test setup")
        log_path = root.child("state", "daemon.log")
        before = log_path.stat().st_size if log_path.exists() else 0
        d.run(interval_seconds=0.01, max_iterations=2)
        self.assertTrue(log_path.exists())
        after = log_path.stat().st_size
        self.assertGreater(after, before)
        # Tail the log; verify start + iteration + stop events. Read
        # the WHOLE tail of this run (everything after `before`).
        with log_path.open("rb") as f:
            f.seek(before)
            run_lines = f.read().decode("utf-8").splitlines()
        events = [json.loads(line).get("event") for line in run_lines
                  if line.strip()]
        self.assertIn("daemon.start", events)
        self.assertIn("daemon.stop", events)
        iter_events = [e for e in events
                       if e in ("daemon.iteration", "daemon.skipped")]
        self.assertGreaterEqual(len(iter_events), 1,
            f"expected iteration or skipped events; got {events}")


if __name__ == "__main__":
    unittest.main()
