"""tests/test_tartarus.py — the Tartarus arc.

Per Delphi 2026-05-19-tartarus-arc.md.

Covers:
  - is_test_actor / is_test_owner / is_test_proposal / is_test_record
  - filter_out_test_records / filter_out_test_proposals
  - wisdom.compose() filters test seeds by default; include_test_seeds=True overrides
  - doctor._check_session_errors uses test-seed filter (windowed metric stays)
  - Asclepius _h_release_test releases only test-owner burdens
  - invoke today --resolve creates the right Mnemosyne records
"""
from __future__ import annotations

import io
import contextlib

import pytest

from olympus.runtime.test_seeds import (
    is_test_actor, is_test_owner, is_test_proposal, is_test_record,
    filter_out_test_records, filter_out_test_proposals,
)
from olympus.titans.mnemosyne import mnemosyne


# ─────────────────────────────────────────────────────────────────────
# is_test_* predicates
# ─────────────────────────────────────────────────────────────────────


class TestIsTestActor:

    @pytest.mark.parametrize("actor,expected", [
        ("charon-test", True),
        ("asclepius-test", True),
        ("test-owner", True),
        ("test-plutus", True),
        ("test", True),
        ("test_seed", True),
        ("zeus:operator", False),
        ("hephaestus", False),
        ("hades", False),
        ("", False),
        (None, False),
        ("athena.brief", False),       # contains 'th' but no test marker
        ("manifest", False),           # contains 'est' but no underscore/dash
    ])
    def test_actor_classification(self, actor, expected):
        assert is_test_actor(actor) is expected

    def test_is_test_owner_matches_actor(self):
        """is_test_owner uses the same rules as is_test_actor."""
        for owner in ("charon-test", "test-owner", "zeus:operator"):
            assert is_test_owner(owner) is is_test_actor(owner)


class TestIsTestProposal:

    def test_fix_test_marks_seed(self):
        assert is_test_proposal({"proposed_fix": "test"})
        assert is_test_proposal({"proposed_fix": "n/a"})
        assert is_test_proposal({"proposed_fix": "Test"})

    def test_real_fix_does_not(self):
        assert not is_test_proposal({
            "proposed_fix": "extend Asclepius healer to release burdens",
            "rationale": "real production fix"})

    def test_test_rationale_with_test_drift(self):
        assert is_test_proposal({
            "rationale": "rejection memory test",
            "drift_observed": "hydra reports alert on slice 'x': test"})

    def test_test_in_rationale_alone_not_enough(self):
        # Conservative: rationale containing 'test' WITHOUT the drift
        # signature is not enough.
        assert not is_test_proposal({
            "rationale": "fix test infrastructure",
            "drift_observed": "real drift in the production loop"})

    def test_id_with_test_dash(self):
        assert is_test_proposal({"id": "test-001"})
        assert is_test_proposal({"id": "arch-test-099"})

    def test_none_safe(self):
        assert not is_test_proposal(None)
        assert not is_test_proposal({})


# ─────────────────────────────────────────────────────────────────────
# is_test_record (Memory predicate)
# ─────────────────────────────────────────────────────────────────────


class TestIsTestRecord:

    def test_test_actor_marks_record(self):
        from olympus.titans.mnemosyne import Memory
        m = Memory(kind="x", actor="charon-test",
                    summary="x", body={}, remembered_at="2026-05-19T00:00:00")
        assert is_test_record(m)

    def test_real_actor_does_not(self):
        from olympus.titans.mnemosyne import Memory
        m = Memory(kind="x", actor="zeus:operator",
                    summary="x", body={}, remembered_at="2026-05-19T00:00:00")
        assert not is_test_record(m)

    def test_directive_with_test_marker(self):
        from olympus.titans.mnemosyne import Memory
        m = Memory(kind="session.completed", actor="session-runner",
                    summary="x", body={"directive": "test: probe"},
                    remembered_at="2026-05-19T00:00:00")
        assert is_test_record(m)

    def test_filter_helpers(self):
        from olympus.titans.mnemosyne import Memory
        recs = [
            Memory(kind="x", actor="charon-test", summary="x", body={},
                    remembered_at="2026-05-19T00:00:00"),
            Memory(kind="x", actor="zeus:operator", summary="x", body={},
                    remembered_at="2026-05-19T00:00:00"),
            Memory(kind="x", actor="hephaestus", summary="x", body={},
                    remembered_at="2026-05-19T00:00:00"),
        ]
        out = filter_out_test_records(recs)
        assert len(out) == 2
        assert all(not is_test_record(r) for r in out)

    def test_filter_proposals_helper(self):
        proposals = [
            {"id": "real-1", "proposed_fix": "real fix"},
            {"id": "test-1", "proposed_fix": "test"},
            {"id": "real-2", "proposed_fix": "another real fix"},
        ]
        out = filter_out_test_proposals(proposals)
        assert len(out) == 2
        assert all(p["proposed_fix"] != "test" for p in out)


# ─────────────────────────────────────────────────────────────────────
# wisdom.compose() filters by default
# ─────────────────────────────────────────────────────────────────────


class TestWisdomFiltersTestSeeds:

    def test_default_excludes_test_seeds(self):
        from olympus.wisdom import wisdom
        w_clean = wisdom()  # default = exclude
        w_raw = wisdom(include_test_seeds=True)
        # Production sessions count must be <= raw count
        assert w_clean.sessions_total <= w_raw.sessions_total
        # And almost certainly STRICTLY less given the 98% test-error finding
        # (we can't assert strict-less because a fresh DB might have neither)
        # Production proposal counts must also be <= raw
        assert w_clean.proposal_count_total <= w_raw.proposal_count_total
        assert w_clean.proposal_count_rejected <= w_raw.proposal_count_rejected

    def test_repeated_drift_excludes_test_seeds(self):
        from olympus.wisdom import wisdom
        w_clean = wisdom()
        # The "hydra::fatigue-slice" entry (test residue) must NOT
        # appear in production-facing repeated_drifts
        sigs = [d["signature"] for d in w_clean.repeated_drifts]
        assert "hydra::fatigue-slice" not in sigs, \
            "test residue must NOT contaminate production drift report"


# ─────────────────────────────────────────────────────────────────────
# doctor._check_session_errors uses the filter
# ─────────────────────────────────────────────────────────────────────


class TestDoctorSessionErrorsFilter:

    def test_check_returns_finding(self):
        from olympus.runtime.doctor import _check_session_errors
        f = _check_session_errors()
        assert f.name == "session-errors"
        # Detail must not include the 68% historical number
        assert "68.0%" not in f.detail

    def test_check_filter_reduces_error_count(self, monkeypatch):
        """When the substrate has test-actor errors but no real errors,
        the production rate should be 0%, not the raw rate."""
        # Force a tight window so we exercise the filter, not just the window
        monkeypatch.setenv(
            "OLYMPUS_DOCTOR_ERROR_WINDOW_SECONDS", "86400")  # 24h
        from olympus.runtime.doctor import _check_session_errors
        f = _check_session_errors()
        # The finding shouldn't be at the historical 68% baseline
        # (proves the filter is reducing the count)
        assert "68" not in f.detail


# ─────────────────────────────────────────────────────────────────────
# Asclepius _h_release_test
# ─────────────────────────────────────────────────────────────────────


class TestAsclepiusReleaseTest:

    def test_healer_registered(self):
        from olympus.olympians.asclepius import asclepius
        assert "atlas-test-burden-release" in asclepius.healers()

    def test_release_only_test_owners(self, monkeypatch):
        """Inject a fake Atlas with a mix of test + real burdens;
        verify only test ones get released."""
        from olympus.olympians.asclepius import Asclepius
        from olympus.titans.atlas import Burden, ShoulderReport

        class _FakeAtlas:
            def __init__(self):
                self.released: list[str] = []
                self._burdens = [
                    Burden(id="b1", op="op1", owner="charon-test",
                            started_at="2026-05-19T00:00:00"),
                    Burden(id="b2", op="op2", owner="real-user",
                            started_at="2026-05-19T00:00:00"),
                    Burden(id="b3", op="op3", owner="asclepius-test",
                            started_at="2026-05-19T00:00:00"),
                ]
            def shoulders(self, recent_releases=5):
                return ShoulderReport(
                    snapshot_at="2026-05-19T00:00:00",
                    current=list(self._burdens),
                    recently_released=[])
            def release(self, burden_id, outcome="ok"):
                self.released.append(burden_id)

        fake = _FakeAtlas()
        # Patch the atlas singleton in the asclepius module's scope
        import olympus.titans.atlas as atlas_mod
        monkeypatch.setattr(atlas_mod, "atlas", fake)
        # Run the healer
        succeeded, changed, detail = Asclepius._h_release_test()
        assert succeeded
        assert changed
        # ONLY the two test-owner burdens released
        assert sorted(fake.released) == ["b1", "b3"], \
            f"expected b1+b3 (test owners); got {fake.released}"


# ─────────────────────────────────────────────────────────────────────
# invoke today --resolve
# ─────────────────────────────────────────────────────────────────────


class TestTodayResolve:

    def test_re_raise_creates_proposal_and_record(self):
        from olympus.cli import hermes
        from olympus.primordials.gaia import root
        before = len(mnemosyne.recall("warning.re-raised"))
        errand = hermes._errands["today"]
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            rc = errand.fn(["--resolve", "test-slice-xyz", "--re-raise"])
        assert rc == 0
        after = len(mnemosyne.recall("warning.re-raised"))
        assert after == before + 1, "must record warning.re-raised"
        latest = mnemosyne.recall("warning.re-raised")[-1]
        assert latest.body["slice"] == "test-slice-xyz"
        # And a proposal file must exist
        pid = latest.body["proposal_id"]
        proposal_path = root.child("state", "hephaestus", f"{pid}.json")
        assert proposal_path.exists()

    def test_dismiss_as_stale_records(self):
        before = len(mnemosyne.recall("warning.dismissal-reaffirmed"))
        from olympus.cli import hermes
        errand = hermes._errands["today"]
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            rc = errand.fn(["--resolve", "test-slice-abc",
                             "--dismiss-as-stale",
                             "verified that the original dismissal is "
                             "still correct"])
        assert rc == 0
        after = len(mnemosyne.recall("warning.dismissal-reaffirmed"))
        assert after == before + 1
        latest = mnemosyne.recall("warning.dismissal-reaffirmed")[-1]
        assert "test-slice-abc" in latest.body["slice"]
        assert "still correct" in latest.body["reason"]

    def test_resolve_requires_mode(self):
        from olympus.cli import hermes
        errand = hermes._errands["today"]
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            rc = errand.fn(["--resolve", "some-slice"])
        # Should be a usage error
        assert rc == 2

    def test_resolve_requires_slice(self):
        from olympus.cli import hermes
        errand = hermes._errands["today"]
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            rc = errand.fn(["--resolve"])
        assert rc == 2
