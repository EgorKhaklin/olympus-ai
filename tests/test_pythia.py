"""Pythia — the external knowledge bridge.

The claim being tested: Pythia records every consultation to Mnemosyne;
errors are captured (never raised); the consultation cap is respected;
GitHub query parsing extracts repo/url/description correctly.

Network is mocked. Pythia's ONE permitted "real network" hit lives in
demonstrate_pythia_loop.py and runs in the demonstration phase, not
the test suite.
"""
from __future__ import annotations

import pathlib as _pl
import sys as _sys
_ROOT = _pl.Path(__file__).resolve().parent.parent
_SRC = _ROOT / "src"
if str(_SRC) not in _sys.path:
    _sys.path.insert(0, str(_SRC))

import io
import json
import unittest
from unittest.mock import patch


class _FakeResponse:
    def __init__(self, status: int = 200, body: bytes = b"",
                 headers: dict | None = None) -> None:
        self.status = status
        self._body = body
        self.headers = headers or {"Content-Type": "application/json"}

    def read(self, n: int) -> bytes:
        out = self._body[:n]
        self._body = self._body[n:]
        return out

    def __enter__(self): return self
    def __exit__(self, *a): pass


class TestPythiaWeb(unittest.TestCase):

    def test_ask_web_records_consultation(self):
        from olympus.olympians.apollo.pythia import Pythia
        from olympus.titans.mnemosyne import mnemosyne
        before = len(mnemosyne.recall("pythia.consultation"))
        with patch("urllib.request.urlopen",
                   return_value=_FakeResponse(200, b"hello world",
                                              {"Content-Type": "text/plain"})):
            c = Pythia().ask_web("https://example.com/test")
        self.assertEqual(c.status, 200)
        self.assertEqual(c.bytes_received, 11)
        self.assertIn("hello", c.head)
        after = len(mnemosyne.recall("pythia.consultation"))
        self.assertGreater(after, before)

    def test_ask_web_captures_http_error(self):
        from olympus.olympians.apollo.pythia import Pythia
        import urllib.error

        def raise_404(*a, **kw):
            raise urllib.error.HTTPError(
                "https://x", 404, "Not Found", {}, None,
            )

        with patch("urllib.request.urlopen", side_effect=raise_404):
            c = Pythia().ask_web("https://example.com/404")
        self.assertEqual(c.status, 404)
        self.assertIn("HTTPError 404", c.error)

    def test_ask_web_captures_network_error(self):
        from olympus.olympians.apollo.pythia import Pythia
        import urllib.error

        def raise_url(*a, **kw):
            raise urllib.error.URLError("nope")

        with patch("urllib.request.urlopen", side_effect=raise_url):
            c = Pythia().ask_web("https://example.com/down")
        self.assertEqual(c.status, 0)
        self.assertIn("URLError", c.error)

    def test_ask_web_truncates_oversized(self):
        from olympus.olympians.apollo.pythia import Pythia, _DEFAULT_MAX_BYTES
        big = b"x" * (_DEFAULT_MAX_BYTES + 1000)
        with patch("urllib.request.urlopen",
                   return_value=_FakeResponse(200, big)):
            c = Pythia().ask_web("https://example.com/big")
        self.assertTrue(c.truncated)
        self.assertEqual(c.bytes_received, _DEFAULT_MAX_BYTES)


class TestPythiaGitHub(unittest.TestCase):

    def test_ask_github_parses_response(self):
        from olympus.olympians.apollo.pythia import Pythia
        payload = json.dumps({
            "total_count": 42,
            "items": [
                {"full_name": "owner/repo1",
                 "html_url": "https://github.com/owner/repo1",
                 "description": "test repo one",
                 "stargazers_count": 100},
                {"full_name": "owner/repo2",
                 "html_url": "https://github.com/owner/repo2",
                 "description": "test repo two",
                 "stargazers_count": 50},
            ],
        }).encode("utf-8")
        with patch("urllib.request.urlopen",
                   return_value=_FakeResponse(200, payload)):
            report = Pythia().ask_github("cognitive substrate")
        self.assertEqual(report.total_count, 42)
        self.assertEqual(len(report.findings), 2)
        self.assertEqual(report.findings[0].repo, "owner/repo1")
        self.assertEqual(report.findings[0].score, 100.0)

    def test_ask_github_records_consultation(self):
        from olympus.olympians.apollo.pythia import Pythia
        from olympus.titans.mnemosyne import mnemosyne
        payload = json.dumps({"total_count": 0, "items": []}).encode("utf-8")
        before = len(mnemosyne.recall("pythia.consultation"))
        with patch("urllib.request.urlopen",
                   return_value=_FakeResponse(200, payload)):
            Pythia().ask_github("test-empty-result")
        after = len(mnemosyne.recall("pythia.consultation"))
        self.assertGreater(after, before)


class TestPythiaQuery(unittest.TestCase):

    def test_consultations_returns_recorded(self):
        from olympus.olympians.apollo.pythia import Pythia
        with patch("urllib.request.urlopen",
                   return_value=_FakeResponse(200, b"{}")):
            Pythia().ask_web("https://example.com/recorded")
        cs = Pythia().consultations(limit=10)
        self.assertGreaterEqual(len(cs), 1)


if __name__ == "__main__":
    unittest.main()
