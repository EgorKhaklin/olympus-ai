"""HTTP API write-channel for proposals.

The claim being tested: POST /proposals/raise accepts a well-formed
JSON body and creates a Hephaestus-channel proposal file; rejects
missing fields, bad risk_class, malformed JSON; other POST paths
return 405; the write goes through the same queue any internal source
uses (S3 preserved).
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


class TestHttpWriteChannel(unittest.TestCase):

    def test_post_dispatch_creates_proposal(self):
        from olympus.runtime.http_api import dispatch_post
        from olympus.primordials.gaia import root
        proposals_dir = root.child("state", "hephaestus", "proposals")
        before = len(list(proposals_dir.glob("http-*.json"))) \
                 if proposals_dir.exists() else 0
        status, body = dispatch_post("/proposals/raise", {
            "summary": "test http proposal",
            "proposed_fix": "rotate the test slice",
            "rationale": "the test slice grew",
            "raised_by": "test-harness",
            "risk_class": "LOW",
        })
        self.assertEqual(status, 201)
        self.assertTrue(body.get("ok"))
        self.assertTrue(body.get("proposal_id", "").startswith("http-"))
        after = len(list(proposals_dir.glob("http-*.json")))
        self.assertEqual(after, before + 1)

    def test_missing_fields_400(self):
        from olympus.runtime.http_api import dispatch_post
        status, body = dispatch_post("/proposals/raise", {
            "summary": "incomplete",
        })
        self.assertEqual(status, 400)
        self.assertIn("missing", body)

    def test_invalid_risk_class_400(self):
        from olympus.runtime.http_api import dispatch_post
        status, body = dispatch_post("/proposals/raise", {
            "summary": "test", "proposed_fix": "test",
            "rationale": "test", "raised_by": "test",
            "risk_class": "ULTRA-HIGH",
        })
        self.assertEqual(status, 400)
        self.assertIn("invalid", body["error"].lower())

    def test_unknown_post_path_405(self):
        from olympus.runtime.http_api import dispatch_post
        status, body = dispatch_post("/something-else", {})
        self.assertEqual(status, 405)
        self.assertIn("/proposals/raise", body["allowed_post_routes"])

    def test_post_records_to_mnemosyne(self):
        from olympus.runtime.http_api import dispatch_post
        from olympus.titans.mnemosyne import mnemosyne
        before = len(mnemosyne.recall("http.proposal-raised"))
        dispatch_post("/proposals/raise", {
            "summary": "mnemosyne record test",
            "proposed_fix": "x", "rationale": "y",
            "raised_by": "test",
        })
        after = len(mnemosyne.recall("http.proposal-raised"))
        self.assertGreater(after, before)


class TestHttpWriteChannelLive(unittest.TestCase):
    """End-to-end POST roundtrip via the live server."""

    def test_post_via_live_server(self):
        from olympus.runtime.http_api import serve_background
        import urllib.request
        handle = serve_background(host="127.0.0.1", port=0)
        try:
            body = json.dumps({
                "summary": "live-server proposal test",
                "proposed_fix": "x",
                "rationale": "y",
                "raised_by": "live-test",
            }).encode("utf-8")
            req = urllib.request.Request(
                handle.url("/proposals/raise"), data=body,
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=5) as resp:
                self.assertEqual(resp.status, 201)
                payload = json.loads(resp.read())
            self.assertTrue(payload["ok"])
        finally:
            handle.stop()


if __name__ == "__main__":
    unittest.main()
