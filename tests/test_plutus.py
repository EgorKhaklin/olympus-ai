"""tests/test_plutus.py — the Plutus arc.

Per Delphi 2026-05-19-plutus-arc.md.

Covers:
  - estimate_dollars math for each known model
  - estimate_dollars handles unknown model (returns 0.0, not error)
  - tally("all") aggregates known records correctly
  - tally("today") respects the date filter
  - by_bridge / by_role / by_model / by_day rollups
  - unknown_model_calls + unknown_models surfaced
  - invalid window raises ValueError
  - errand smoke test: `invoke spend` exits 0
  - throne can run spend (SAFE_ERRANDS contains it)
"""
from __future__ import annotations

import datetime as _dt
import io
import json
import contextlib

import pytest

from olympus.heroes.plutus import (
    plutus, Plutus, CostReport, CostBreakdown,
    PRICING, UNKNOWN_MODEL_KEY, estimate_dollars,
)
from olympus.titans.mnemosyne import mnemosyne


# ─────────────────────────────────────────────────────────────────────
# Pricing math
# ─────────────────────────────────────────────────────────────────────


class TestEstimateDollars:

    def test_opus_47_pricing(self):
        # 1M in + 1M out at opus-4-7 pricing = $5 + $25 = $30
        cost = estimate_dollars(input_tokens=1_000_000,
                                 output_tokens=1_000_000,
                                 model="claude-opus-4-7")
        assert cost == pytest.approx(30.0)

    def test_sonnet_46_pricing(self):
        # 1M in + 1M out at sonnet-4-6 pricing = $3 + $15 = $18
        cost = estimate_dollars(input_tokens=1_000_000,
                                 output_tokens=1_000_000,
                                 model="claude-sonnet-4-6")
        assert cost == pytest.approx(18.0)

    def test_haiku_45_pricing(self):
        cost = estimate_dollars(input_tokens=1_000_000,
                                 output_tokens=1_000_000,
                                 model="claude-haiku-4-5")
        assert cost == pytest.approx(6.0)

    def test_echo_is_free(self):
        cost = estimate_dollars(input_tokens=1_000_000,
                                 output_tokens=1_000_000,
                                 model="echo-1")
        assert cost == 0.0

    def test_unknown_model_returns_zero(self):
        cost = estimate_dollars(input_tokens=1000, output_tokens=1000,
                                 model="some-future-model-not-yet-priced")
        assert cost == 0.0

    def test_small_token_amounts_correct(self):
        # 2000 in + 500 out at opus-4-7
        # ($5/1M * 2000) + ($25/1M * 500) = 0.010 + 0.0125 = 0.0225
        cost = estimate_dollars(input_tokens=2000, output_tokens=500,
                                 model="claude-opus-4-7")
        assert cost == pytest.approx(0.0225)


# ─────────────────────────────────────────────────────────────────────
# tally — aggregation over real Mnemosyne records
# ─────────────────────────────────────────────────────────────────────


class TestTally:

    def test_tally_returns_report(self):
        r = plutus.tally(window="all")
        assert isinstance(r, CostReport)
        assert r.window == "all"
        assert r.snapshot_at  # ISO string set

    def test_tally_aggregates_known_records(self):
        # The substrate has 580+ llm.call records by now
        r = plutus.tally(window="all")
        assert r.total_calls > 0
        assert r.total_input_tokens > 0
        # by_bridge should have at least one entry
        assert len(r.by_bridge) >= 1

    def test_tally_today_subset_of_all(self):
        all_r = plutus.tally(window="all")
        today_r = plutus.tally(window="today")
        assert today_r.total_calls <= all_r.total_calls
        assert today_r.total_input_tokens <= all_r.total_input_tokens

    def test_tally_invalid_window_raises(self):
        with pytest.raises(ValueError, match="unknown window"):
            plutus.tally(window="last_year")

    def test_tally_by_axes_have_correct_sum(self):
        r = plutus.tally(window="all")
        # Each axis (bridge/role/model) should sum to the total
        def _sum(axis):
            return sum(b.calls for b in axis.values())
        assert _sum(r.by_bridge) == r.total_calls
        assert _sum(r.by_role) == r.total_calls
        assert _sum(r.by_model) == r.total_calls

    def test_tally_by_day_is_sorted_newest_first(self):
        r = plutus.tally(window="all")
        days = list(r.by_day.keys())
        if len(days) >= 2:
            assert days[0] >= days[1], "by_day must be sorted descending"

    def test_tally_pricing_used_excludes_unmatched(self):
        r = plutus.tally(window="all")
        # Every key in pricing_used must be a model we saw
        for model in r.pricing_used:
            assert model in r.by_model

    def test_tally_unknown_models_surfaced(self):
        r = plutus.tally(window="all")
        # If any unknown-model calls happened, the list is populated
        if r.unknown_model_calls > 0:
            assert len(r.unknown_models) >= 1


# ─────────────────────────────────────────────────────────────────────
# Window filter logic — uses fake records (no mocking of Mnemosyne)
# ─────────────────────────────────────────────────────────────────────


class TestWindowFilter:

    def test_each_window_constant_present(self):
        # Catches typos in CLI/throne wiring
        for w in ("all", "today", "1h", "24h", "7d", "30d"):
            assert w in plutus.WINDOWS

    def test_today_window_pulls_today_records(self):
        # Insert a fresh llm.call right now → it should be in today's
        # tally even if all other records are older
        before = plutus.tally(window="today").total_calls
        mnemosyne.remember(
            kind="llm.call",
            actor="llm-bridge:test-plutus",
            summary="plutus test seed",
            bridge="test-plutus",
            role="test",
            model="claude-opus-4-7",
            input_tokens=100,
            output_tokens=50,
            elapsed_ms=1.0,
            error="",
        )
        after = plutus.tally(window="today").total_calls
        assert after == before + 1


# ─────────────────────────────────────────────────────────────────────
# JSON serialization
# ─────────────────────────────────────────────────────────────────────


class TestReportToDict:

    def test_to_dict_is_json_safe(self):
        r = plutus.tally(window="all")
        d = r.to_dict()
        json.dumps(d)  # must not raise
        assert d["window"] == "all"
        assert isinstance(d["estimated_usd"], float)

    def test_breakdown_axes_are_plain_dicts(self):
        r = plutus.tally(window="all")
        d = r.to_dict()
        for axis_name in ("by_bridge", "by_role", "by_model", "by_day"):
            axis = d[axis_name]
            assert isinstance(axis, dict)
            for entry in axis.values():
                assert isinstance(entry, dict)
                assert "calls" in entry
                assert "estimated_usd" in entry


# ─────────────────────────────────────────────────────────────────────
# CLI errand smoke test
# ─────────────────────────────────────────────────────────────────────


class TestSpendErrand:

    def test_spend_errand_exits_zero(self):
        from olympus.cli import hermes
        errand = hermes._errands.get("spend")
        assert errand is not None, "spend errand must be registered"
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            rc = errand.fn([])
        assert rc == 0
        out = buf.getvalue()
        assert "Plutus" in out or "spend" in out

    def test_spend_errand_today_flag(self):
        from olympus.cli import hermes
        errand = hermes._errands["spend"]
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            rc = errand.fn(["--today"])
        assert rc == 0
        assert "today" in buf.getvalue()


# ─────────────────────────────────────────────────────────────────────
# Throne integration — spend must be in SAFE_ERRANDS
# ─────────────────────────────────────────────────────────────────────


class TestThroneCanRunSpend:

    def test_spend_in_safe_errands(self):
        from olympus.throne.router import SAFE_ERRANDS, GATED_ERRANDS
        assert "spend" in SAFE_ERRANDS, \
            "throne should be able to answer cost questions"
        assert "spend" not in GATED_ERRANDS

    def test_spend_appears_in_system_prompt(self):
        from olympus.throne.router import build_system_prompt
        p = build_system_prompt()
        assert "spend" in p
