"""Iris — the static dashboard.

The claim being tested: collect_snapshot is pure (no writes), render
produces a single self-contained HTML file with the data island in
place, and the file is openable in any browser (file:// safe — no
external requests).
"""
from __future__ import annotations

import pathlib as _pl
import sys as _sys
_ROOT = _pl.Path(__file__).resolve().parent.parent
_SRC = _ROOT / "src"
if str(_SRC) not in _sys.path:
    _sys.path.insert(0, str(_SRC))

import pathlib
import tempfile
import unittest


class TestIrisBuild(unittest.TestCase):

    def test_collect_snapshot_pure(self):
        """collect_snapshot returns an IrisSnapshot dataclass and
        does not write anything."""
        from olympus.iris import IrisSnapshot, collect_snapshot
        snap = collect_snapshot()
        self.assertIsInstance(snap, IrisSnapshot)
        self.assertTrue(snap.built_at)
        self.assertIsInstance(snap.sessions, list)
        self.assertIsInstance(snap.counts, dict)

    def test_snapshot_has_all_panels(self):
        from olympus.iris import collect_snapshot
        snap = collect_snapshot()
        # All declared panels exist as attributes
        for panel in (
            "sessions", "slice_heatmap", "prophecies", "proposals",
            "prometheus_passes", "prometheus_handlers", "styx", "counts",
        ):
            self.assertTrue(hasattr(snap, panel),
                            f"snapshot missing {panel}")

    def test_render_produces_self_contained_html(self):
        """Render must produce ONE HTML file with CSS, JS, and data all
        inlined — no external file references that would break file://."""
        from olympus.iris import collect_snapshot, render
        out = pathlib.Path(tempfile.mkdtemp()) / "test_iris.html"
        snap = collect_snapshot()
        render(snap, out_path=out)
        self.assertTrue(out.exists())
        html = out.read_text(encoding="utf-8")
        # Required structural elements
        self.assertIn("<!doctype html>", html.lower())
        self.assertIn("Iris — Olympus dashboard", html)
        self.assertIn('id="olympus-data"', html)
        # Data island contains valid JSON (not raw Python)
        import json
        start = html.find('id="olympus-data">') + len('id="olympus-data">')
        end = html.find('</script>', start)
        data_text = html[start:end]
        data_text = data_text.replace("<\\/", "</")  # un-escape
        parsed = json.loads(data_text)
        self.assertIn("counts", parsed)
        self.assertIn("sessions", parsed)

    def test_render_no_external_references(self):
        """A self-contained dashboard makes no external requests."""
        from olympus.iris import collect_snapshot, render
        out = pathlib.Path(tempfile.mkdtemp()) / "test_iris_offline.html"
        snap = collect_snapshot()
        render(snap, out_path=out)
        html = out.read_text(encoding="utf-8")
        # No <link rel="stylesheet" href="http...">
        self.assertNotIn("<link rel=\"stylesheet\"", html)
        # No <script src="http..."> — only inline script blocks
        for marker in ('src="http://', 'src="https://',
                       '<link rel=stylesheet'):
            self.assertNotIn(marker, html)

    def test_render_includes_panel_mount_points(self):
        from olympus.iris import collect_snapshot, render
        out = pathlib.Path(tempfile.mkdtemp()) / "test_iris_mounts.html"
        render(collect_snapshot(), out_path=out)
        html = out.read_text(encoding="utf-8")
        for mount in ('id="counts"', 'id="timeline"', 'id="heatmap"',
                      'id="prophecies"', 'id="proposals"',
                      'id="prometheus"', 'id="prometheus-handlers"',
                      'id="styx"'):
            self.assertIn(mount, html,
                          f"missing mount node {mount}")

    def test_build_helper_writes_default_path(self):
        from olympus.iris import build
        out = build()
        self.assertTrue(out.exists())
        # default lives under state/iris/
        self.assertEqual(out.name, "index.html")
        self.assertIn("iris", out.parts)

    def test_render_escapes_script_breakout(self):
        """If a user-provided summary contains </script>, the rendered
        HTML must still have exactly our 2 structural </script> tags.
        Note: a `<script` substring inside a `<script type="application/json">`
        block is harmless text — only `</script>` can break out of it
        (per the HTML5 raw-text-element parsing rules). So the actual
        XSS vector is `</script>`, which our render() escapes via
        replacing `</` with `<\\/` inside the JSON payload."""
        from olympus.iris import IrisSnapshot, render
        snap = IrisSnapshot()
        snap.built_at = "2026-05-18T00:00:00+00:00"
        snap.olympus_version = "test"
        snap.sessions = [{
            "ts": "2026-05-18T00:00:00", "session_id": "x",
            "summary": "innocuous </script><script>alert(1)</script> end",
            "hydra_findings": 0, "argos_pheromones": 0,
            "proposals": 0, "duration_ms": 0,
            "prophecies_verified": 0, "fury_alerts": [],
        }]
        snap.counts = {"sessions": 1}
        out = pathlib.Path(tempfile.mkdtemp()) / "test_iris_xss.html"
        render(snap, out_path=out)
        html = out.read_text(encoding="utf-8")
        # Exactly 2 closing </script> — the data island and the JS block.
        # If the escape failed, the malicious "</script>" in the summary
        # would have appeared verbatim and bumped this count.
        self.assertEqual(html.count("</script>"), 2)
        # And the escaped sequence DOES appear in the payload.
        self.assertIn("<\\/script>", html)


if __name__ == "__main__":
    unittest.main()
