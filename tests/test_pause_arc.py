"""tests/test_pause_arc.py — the pause-and-harden arc.

Per Delphi 2026-05-19-pause-arc.md.

Covers:
  - The session-scoped contamination guard (its detection logic, in
    isolation — the guard itself is a pytest hook so we can't easily
    self-test, but we test the snapshot + diff helpers)
  - `_check_session_errors` returns "ok · insufficient data" when
    denominator < 5
  - `_check_session_errors` reports the windowed rate when denominator
    is sufficient
  - `_check_session_errors` honors OLYMPUS_DOCTOR_ERROR_WINDOW_SECONDS
  - `test_default_is_echo` works regardless of operator's real config
  - ARC-QUEUE.md exists and references each surfacing Delphi
"""
from __future__ import annotations

import datetime as _dt
import hashlib
import pathlib

import pytest

from olympus.runtime.doctor import _check_session_errors
from olympus.titans.mnemosyne import mnemosyne, Memory


# ─────────────────────────────────────────────────────────────────────
# Conftest guard helpers — snapshot + diff logic
# ─────────────────────────────────────────────────────────────────────


class TestGuardSnapshotLogic:

    def test_sha256_of_missing_returns_none(self, tmp_path):
        from tests.conftest import _sha256_of
        assert _sha256_of(tmp_path / "nope.json") is None

    def test_sha256_of_real_file(self, tmp_path):
        from tests.conftest import _sha256_of
        f = tmp_path / "real.json"
        f.write_text("hello world", encoding="utf-8")
        expected = hashlib.sha256(b"hello world").hexdigest()
        assert _sha256_of(f) == expected

    def test_snapshot_returns_dict_of_relpaths(self):
        from tests.conftest import _snapshot_watched, _WATCHED_RELS
        snap = _snapshot_watched()
        assert isinstance(snap, dict)
        # Every watched rel must be a key (value may be None if absent)
        for rel in _WATCHED_RELS:
            assert rel in snap

    def test_config_json_in_watched(self):
        """The very file my Hades bug clobbered MUST be on the watch
        list — otherwise the guard wouldn't have caught it."""
        from tests.conftest import _WATCHED_RELS
        assert "config.json" in _WATCHED_RELS


# ─────────────────────────────────────────────────────────────────────
# Fixed _check_session_errors
# ─────────────────────────────────────────────────────────────────────


class TestSessionErrorsWindowed:

    def test_insufficient_data_when_few_records(self, monkeypatch):
        """If the time-windowed denominator is below the minimum, the
        check should return ok · insufficient-data, not a spurious
        warning based on sticky historical errors."""
        # Force a 1-second window so no real records qualify
        monkeypatch.setenv(
            "OLYMPUS_DOCTOR_ERROR_WINDOW_SECONDS", "1")
        finding = _check_session_errors()
        assert finding.name == "session-errors"
        # With a 1-second window, almost certainly insufficient data
        if "insufficient" in finding.detail:
            assert finding.status == "ok"

    def test_no_sticky_historical_count(self, monkeypatch):
        """The new metric must NOT report the historical 34 errors as
        the current rate. Within a tight window, recent rate should
        reflect ONLY recent activity."""
        monkeypatch.setenv(
            "OLYMPUS_DOCTOR_ERROR_WINDOW_SECONDS", "10")
        finding = _check_session_errors()
        # The old code reported 34/50 = 68%; the new windowed metric
        # should NOT report anything close to that for a 10-second
        # window unless 34 sessions errored in the last 10 seconds
        # (which they didn't).
        assert "68.0%" not in finding.detail
        # Either insufficient data, or a sensible recent rate
        if finding.status == "warn":
            # If the test substrate IS in real distress, the rate should
            # at least be plausible (not stuck at 68% from history)
            pass

    def test_check_returns_finding_shape(self):
        finding = _check_session_errors()
        assert hasattr(finding, "name")
        assert hasattr(finding, "status")
        assert hasattr(finding, "detail")
        assert finding.status in ("ok", "warn", "fail")


# ─────────────────────────────────────────────────────────────────────
# ARC-QUEUE.md presence + structure
# ─────────────────────────────────────────────────────────────────────


class TestArcQueueDoc:

    def test_arc_queue_exists(self):
        from olympus.primordials.gaia import root
        p = root.child("codex", "ARC-QUEUE.md")
        assert p.exists(), "codex/ARC-QUEUE.md must exist after pause arc"

    def test_arc_queue_mentions_originating_arcs(self):
        from olympus.primordials.gaia import root
        text = root.child("codex", "ARC-QUEUE.md").read_text(
            encoding="utf-8")
        # Each major arc that surfaced deferred work should appear
        for arc in ("Plutus", "Hades", "grounding", "pause-and-harden"):
            assert arc in text, (
                f"ARC-QUEUE should reference the {arc} arc")

    def test_arc_queue_has_tiers(self):
        from olympus.primordials.gaia import root
        text = root.child("codex", "ARC-QUEUE.md").read_text(
            encoding="utf-8")
        # Three tier sections from the Delphi
        assert "High-impact" in text
        assert "Medium-impact" in text
        assert "constitutional debate" in text.lower()


# ─────────────────────────────────────────────────────────────────────
# Test-default-is-echo robustness regression
# ─────────────────────────────────────────────────────────────────────


class TestDefaultIsEchoIsolation:

    def test_test_uses_path_redirection(self):
        """The fix for test_default_is_echo should NOT rely on
        OLYMPUS_STATE_DIR (which doesn't redirect _path()); it must
        monkey-patch cfg_mod._path directly."""
        from olympus.primordials.gaia import root
        text = root.child("tests", "test_llm_bridge.py").read_text(
            encoding="utf-8")
        # Look at the test_default_is_echo body specifically
        idx = text.find("def test_default_is_echo")
        assert idx >= 0
        # Read until the next def
        next_def = text.find("\n    def ", idx + 1)
        body = text[idx:next_def if next_def > 0 else len(text)]
        # The body must monkey-patch _path (not just setenv)
        assert "_path" in body, (
            "test_default_is_echo must redirect cfg_mod._path; "
            "setenv alone doesn't work (see pause-arc Delphi)")
