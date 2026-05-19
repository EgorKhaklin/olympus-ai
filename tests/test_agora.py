"""agora/ — operator interactive web UI.

The claim being tested: build() emits five HTML pages; placeholders
are substituted; pages reference the configured API base; every page
includes the nav.
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


class TestAgoraBuild(unittest.TestCase):

    def test_build_emits_five_pages(self):
        from olympus.agora import build
        out_dir = pathlib.Path(tempfile.mkdtemp())
        index_path = build(out_dir=out_dir)
        self.assertEqual(index_path.name, "index.html")
        for name in ("index.html", "setup.html", "doctor.html",
                      "today.html", "agents.html"):
            self.assertTrue(
                (out_dir / name).exists(),
                f"agora page {name!r} missing",
            )

    def test_placeholders_substituted(self):
        from olympus.agora import build
        out_dir = pathlib.Path(tempfile.mkdtemp())
        build(out_dir=out_dir,
              api_base="http://test-host:9999",
              interval_seconds=7.0)
        for name in ("index.html", "setup.html", "doctor.html",
                      "today.html", "agents.html"):
            text = (out_dir / name).read_text(encoding="utf-8")
            self.assertNotIn("__API_BASE__", text)
            self.assertNotIn("__INTERVAL_MS__", text)
            self.assertNotIn("__BUILT_AT__", text)
            self.assertNotIn("__AGORA_NAV__", text)
            self.assertNotIn("/*__AGORA_CSS__*/", text)
            self.assertNotIn("/*__AGORA_JS__*/", text)

    def test_api_base_appears_in_pages(self):
        from olympus.agora import build
        out_dir = pathlib.Path(tempfile.mkdtemp())
        build(out_dir=out_dir, api_base="http://my-host:1234")
        index_text = (out_dir / "index.html").read_text(encoding="utf-8")
        self.assertIn("http://my-host:1234", index_text)

    def test_interval_substituted_as_ms(self):
        from olympus.agora import build
        out_dir = pathlib.Path(tempfile.mkdtemp())
        build(out_dir=out_dir, interval_seconds=3.0)
        index_text = (out_dir / "index.html").read_text(encoding="utf-8")
        # 3.0s → 3000ms
        self.assertIn("3000", index_text)

    def test_nav_present_on_every_page(self):
        """Per Delphi 2026-05-19-throne-arc.md: nav brand is now
        Zeus's Throne (index.html is the chat); the dashboard moves
        to dashboard.html."""
        from olympus.agora import build
        out_dir = pathlib.Path(tempfile.mkdtemp())
        build(out_dir=out_dir)
        for name in ("index.html", "dashboard.html", "setup.html",
                      "doctor.html", "today.html", "agents.html"):
            text = (out_dir / name).read_text(encoding="utf-8")
            # Brand is now Zeus's Throne (the chat landing page)
            self.assertTrue(
                "Throne" in text or "Zeus" in text,
                f"{name} should contain the Throne/Zeus brand")
            self.assertIn("setup.html", text,
                f"{name} should link to setup")

    def test_pages_use_only_read_only_endpoints(self):
        """Read-mostly pages do not invoke POST. Per Delphi
        2026-05-19-throne-arc.md: index.html is now the Throne chat
        (which DOES post to /throne/turn), so index is exempt. The
        dashboard, today, doctor, and agents pages remain read-only.

        Note: the bundled agora.js DEFINES `AGORA.post` so the string
        "POST" appears on every page in the helper; we check only that
        no page *invokes* it (`AGORA.post(`) or makes a direct fetch
        with a POST method."""
        from olympus.agora import build
        out_dir = pathlib.Path(tempfile.mkdtemp())
        build(out_dir=out_dir)
        for name in ("dashboard.html", "today.html",
                      "doctor.html", "agents.html"):
            text = (out_dir / name).read_text(encoding="utf-8")
            self.assertNotIn('AGORA.post(', text,
                f"{name} unexpectedly invokes AGORA.post(")
            self.assertNotIn('method: "POST"', text,
                f"{name} unexpectedly does a direct fetch POST")
            self.assertNotIn('method:"POST"', text,
                f"{name} unexpectedly does a direct fetch POST")


if __name__ == "__main__":
    unittest.main()
