"""olympus.runtime.http_api — read-only JSON surface.

The claim being tested: dispatch() routes correctly for each documented
path; write methods all return 405; live server roundtrip works.
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
import urllib.request


class TestDispatch(unittest.TestCase):
    """Direct dispatch() tests — no socket, fast."""

    def test_root_returns_route_index(self):
        from olympus.runtime.http_api import dispatch
        status, body = dispatch("/", {})
        self.assertEqual(status, 200)
        self.assertEqual(body["service"], "olympus-http-api")
        # Labyrinth arc: API gained POST /proposals/raise. The substrate
        # state is still read-only — writes go to the proposal queue,
        # not to substrate state — but the field name reflects that.
        self.assertIn("read_only_writes", body)
        self.assertIn("Hephaestus", body["read_only_writes"])
        self.assertIn("GET /healthz", body["routes"])
        self.assertIn("POST /proposals/raise", body["routes"])

    def test_healthz(self):
        from olympus.runtime.http_api import dispatch
        status, body = dispatch("/healthz", {})
        self.assertEqual(status, 200)
        self.assertTrue(body["ok"])

    def test_status_returns_structured_object(self):
        from olympus.runtime.http_api import dispatch
        status, body = dispatch("/status", {})
        self.assertEqual(status, 200)
        for key in ("hearth", "styx", "hydra", "argos",
                    "actions", "sessions"):
            self.assertIn(key, body)

    def test_wisdom_returns_aggregate(self):
        from olympus.runtime.http_api import dispatch
        status, body = dispatch("/wisdom", {})
        self.assertEqual(status, 200)
        self.assertIn("insights", body)
        self.assertIn("sessions_total", body)

    def test_schemas_list(self):
        from olympus.runtime.http_api import dispatch
        status, body = dispatch("/schemas", {})
        self.assertEqual(status, 200)
        self.assertIn("schemas", body)
        self.assertIn("prophecy-verified", body["schemas"])

    def test_schemas_specific(self):
        from olympus.runtime.http_api import dispatch
        status, body = dispatch("/schemas/prophecy.verified", {})
        self.assertEqual(status, 200)
        self.assertEqual(body["title"], "prophecy.verified body")

    def test_schemas_unknown_404(self):
        from olympus.runtime.http_api import dispatch
        status, body = dispatch("/schemas/no-such-schema", {})
        self.assertEqual(status, 404)
        self.assertIn("error", body)

    def test_mnemosyne_route_paginates(self):
        from olympus.runtime.http_api import dispatch
        status, body = dispatch("/mnemosyne/session.completed",
                                {"limit": ["3"]})
        self.assertEqual(status, 200)
        self.assertLessEqual(body["returned"], 3)
        self.assertEqual(body["kind"], "session.completed")

    def test_mnemosyne_empty_kind_400(self):
        from olympus.runtime.http_api import dispatch
        status, body = dispatch("/mnemosyne/", {})
        self.assertEqual(status, 400)

    def test_unknown_route_404(self):
        from olympus.runtime.http_api import dispatch
        status, body = dispatch("/no-such-route", {})
        self.assertEqual(status, 404)


class TestLiveServer(unittest.TestCase):
    """End-to-end: start the server, hit it with urllib, shut down."""

    def test_roundtrip_healthz(self):
        from olympus.runtime.http_api import serve_background
        handle = serve_background(host="127.0.0.1", port=0)
        try:
            with urllib.request.urlopen(handle.url("/healthz"),
                                         timeout=3) as resp:
                body = json.loads(resp.read())
            self.assertEqual(resp.status, 200)
            self.assertTrue(body["ok"])
        finally:
            handle.stop()

    def test_roundtrip_status(self):
        from olympus.runtime.http_api import serve_background
        handle = serve_background(host="127.0.0.1", port=0)
        try:
            with urllib.request.urlopen(handle.url("/status"),
                                         timeout=3) as resp:
                body = json.loads(resp.read())
            self.assertEqual(resp.status, 200)
            self.assertIn("hearth", body)
        finally:
            handle.stop()

    def test_write_methods_blocked(self):
        from olympus.runtime.http_api import serve_background
        import urllib.error
        handle = serve_background(host="127.0.0.1", port=0)
        try:
            req = urllib.request.Request(
                handle.url("/status"), method="POST", data=b"x",
            )
            try:
                urllib.request.urlopen(req, timeout=3)
                self.fail("POST should be refused")
            except urllib.error.HTTPError as exc:
                self.assertEqual(exc.code, 405)
        finally:
            handle.stop()


if __name__ == "__main__":
    unittest.main()
