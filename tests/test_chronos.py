"""tests/test_chronos.py — the Chronos arc.

Per Delphi 2026-05-19-chronos-arc.md.
All tests use deterministic datetimes (passed to `tick(now=...)`) and
monkey-patch state-paths to tmp_path — NO real state/config.json or
state/chronos/ touches (conftest contamination guard enforces).
"""
from __future__ import annotations

import datetime as _dt
import io
import contextlib
import json

import pytest

from olympus.primordials.chronos import (
    Chronos, chronos, RitualSpec, WhenSpec, Fired,
    parse_when, matches_now, next_due,
    MAX_FIRES_PER_TICK,
)
from olympus.runtime.errand_whitelist import AUTOMATED_ERRANDS


# ─────────────────────────────────────────────────────────────────────
# parse_when grammar
# ─────────────────────────────────────────────────────────────────────


class TestParseWhen:

    def test_daily(self):
        w = parse_when("daily 09:00")
        assert w.valid and w.kind == "daily"
        assert w.hour == 9 and w.minute == 0

    def test_weekday(self):
        w = parse_when("weekday 17:30")
        assert w.valid and w.kind == "weekday"
        assert w.hour == 17 and w.minute == 30

    def test_weekend(self):
        w = parse_when("weekend 11:15")
        assert w.valid and w.kind == "weekend"

    def test_specific_day(self):
        w = parse_when("monday 09:00")
        assert w.valid and w.kind == "day"
        assert w.weekday == 0
        w2 = parse_when("sunday 20:00")
        assert w2.weekday == 6

    def test_monthly_no_time(self):
        w = parse_when("monthly 1")
        assert w.valid and w.kind == "monthly"
        assert w.day_of_month == 1 and w.hour == 0 and w.minute == 0

    def test_monthly_with_time(self):
        w = parse_when("monthly 15 08:00")
        assert w.valid
        assert w.day_of_month == 15 and w.hour == 8

    def test_monthly_oob_rejected(self):
        assert not parse_when("monthly 29").valid
        assert not parse_when("monthly 0").valid

    def test_every_minutes(self):
        w = parse_when("every 30m")
        assert w.valid and w.kind == "every"
        assert w.every_minutes == 30

    def test_every_hours(self):
        w = parse_when("every 2h")
        assert w.valid and w.every_minutes == 120

    def test_every_oob_rejected(self):
        assert not parse_when("every 1m").valid  # < 5
        assert not parse_when("every 2000m").valid  # > 1440
        assert not parse_when("every 25h").valid

    def test_hourly(self):
        w = parse_when("hourly")
        assert w.valid and w.kind == "hourly"

    def test_bad_grammar(self):
        assert not parse_when("").valid
        assert not parse_when("xyz").valid
        assert not parse_when("daily 25:00").valid  # bad hour
        assert not parse_when("daily 09:60").valid  # bad minute


# ─────────────────────────────────────────────────────────────────────
# matches_now logic
# ─────────────────────────────────────────────────────────────────────


def _dt_at(year=2026, month=5, day=19, hour=9, minute=0):
    return _dt.datetime(year, month, day, hour, minute, 0)


class TestMatchesNow:

    def test_daily_matches_exact_minute(self):
        w = parse_when("daily 09:00")
        # 2026-05-19 is a Tuesday
        assert matches_now(w, _dt_at(hour=9, minute=0))
        assert not matches_now(w, _dt_at(hour=9, minute=1))
        assert not matches_now(w, _dt_at(hour=10, minute=0))

    def test_weekday_matches_only_weekdays(self):
        w = parse_when("weekday 09:00")
        # Tuesday 2026-05-19
        assert matches_now(w, _dt_at(day=19, hour=9, minute=0))
        # Saturday 2026-05-23
        assert not matches_now(w, _dt_at(day=23, hour=9, minute=0))

    def test_weekend_matches_only_weekends(self):
        w = parse_when("weekend 09:00")
        # Saturday
        assert matches_now(w, _dt_at(day=23, hour=9, minute=0))
        # Tuesday
        assert not matches_now(w, _dt_at(day=19, hour=9, minute=0))

    def test_specific_day(self):
        w = parse_when("monday 09:00")
        # Monday 2026-05-18
        assert matches_now(w, _dt_at(day=18, hour=9, minute=0))
        # Tuesday
        assert not matches_now(w, _dt_at(day=19, hour=9, minute=0))

    def test_monthly(self):
        w = parse_when("monthly 1 09:00")
        assert matches_now(w, _dt_at(day=1, hour=9, minute=0))
        assert not matches_now(w, _dt_at(day=2, hour=9, minute=0))

    def test_hourly(self):
        w = parse_when("hourly")
        assert matches_now(w, _dt_at(hour=14, minute=0))
        assert not matches_now(w, _dt_at(hour=14, minute=30))


# ─────────────────────────────────────────────────────────────────────
# next_due
# ─────────────────────────────────────────────────────────────────────


class TestNextDue:

    def test_daily_today_later(self):
        # now = Tuesday 08:00; next daily 09:00 = same day 09:00
        w = parse_when("daily 09:00")
        nd = next_due(w, _dt_at(hour=8, minute=0))
        assert nd is not None
        assert nd.hour == 9 and nd.minute == 0
        assert nd.day == 19  # same Tuesday

    def test_daily_tomorrow(self):
        w = parse_when("daily 09:00")
        # now = 10:00; next is tomorrow 09:00
        nd = next_due(w, _dt_at(hour=10, minute=0))
        assert nd.day == 20

    def test_weekday_skips_to_monday_from_friday_evening(self):
        # Friday 2026-05-22 18:00 → next weekday 09:00 = Monday 2026-05-25
        w = parse_when("weekday 09:00")
        nd = next_due(w, _dt_at(day=22, hour=18, minute=0))
        # Should be Monday (weekday 0)
        assert nd.weekday() < 5

    def test_invalid_returns_none(self):
        assert next_due(parse_when("garbage"), _dt_at()) is None


# ─────────────────────────────────────────────────────────────────────
# RitualSpec validation
# ─────────────────────────────────────────────────────────────────────


class TestRitualSpec:

    def test_valid(self):
        ok, _ = RitualSpec(id="x", when="daily 09:00",
                            do="today").validate()
        assert ok

    def test_unwhitelisted_errand_rejected(self):
        ok, err = RitualSpec(id="x", when="daily 09:00",
                              do="ratify").validate()
        assert not ok
        assert "whitelist" in err.lower()

    def test_bad_when_rejected(self):
        ok, err = RitualSpec(id="x", when="garbage", do="today").validate()
        assert not ok

    def test_bad_id_rejected(self):
        ok, _ = RitualSpec(id="bad/id", when="daily 09:00",
                            do="today").validate()
        assert not ok


# ─────────────────────────────────────────────────────────────────────
# Chronos.tick with deterministic time + monkey-patched state path
# ─────────────────────────────────────────────────────────────────────


@pytest.fixture
def isolated_chronos(tmp_path, monkeypatch):
    """Redirect state + config paths to tmp; restore the chronos
    singleton's clean state."""
    from olympus.primordials import chronos as chronos_mod
    from olympus.runtime import config as cfg_mod
    # Redirect state file
    fake_state = tmp_path / "rituals_state.json"
    monkeypatch.setattr(chronos_mod, "_state_path",
                         lambda: fake_state)
    # Redirect config file
    fake_cfg = tmp_path / "config.json"
    monkeypatch.setattr(cfg_mod, "_path", lambda: fake_cfg)
    return tmp_path


class TestChronosTick:

    def test_fires_when_match(self, isolated_chronos, monkeypatch):
        from olympus.runtime import config as cfg_mod
        # One ritual matching now
        cfg = cfg_mod.Config()
        cfg.chronos.rituals = [{
            "id": "morning", "when": "daily 09:00", "do": "today",
            "enabled": True,
        }]
        cfg_mod.save(cfg)

        c = Chronos()
        # The today errand records to mnemosyne; ensure that's OK in test
        fired = c.tick(now=_dt_at(hour=9, minute=0))
        assert len(fired) == 1
        assert fired[0].ritual_id == "morning"
        assert fired[0].errand == "today"

    def test_does_not_fire_when_no_match(self, isolated_chronos):
        from olympus.runtime import config as cfg_mod
        cfg = cfg_mod.Config()
        cfg.chronos.rituals = [{
            "id": "morning", "when": "daily 09:00", "do": "today"}]
        cfg_mod.save(cfg)
        c = Chronos()
        fired = c.tick(now=_dt_at(hour=10, minute=30))
        assert fired == []

    def test_does_not_fire_twice_in_window(self, isolated_chronos):
        from olympus.runtime import config as cfg_mod
        cfg = cfg_mod.Config()
        cfg.chronos.rituals = [{
            "id": "morning", "when": "daily 09:00", "do": "today",
            "min_interval_seconds": 3600}]
        cfg_mod.save(cfg)
        c = Chronos()
        first = c.tick(now=_dt_at(hour=9, minute=0))
        # Same minute, should NOT re-fire (interval not yet elapsed)
        second = c.tick(now=_dt_at(hour=9, minute=0, year=2026))
        assert len(first) == 1
        assert second == []

    def test_max_fires_per_tick_ceiling(self, isolated_chronos):
        from olympus.runtime import config as cfg_mod
        cfg = cfg_mod.Config()
        # 5 rituals all matching same minute
        cfg.chronos.rituals = [
            {"id": f"r{i}", "when": "daily 09:00", "do": "today"}
            for i in range(5)
        ]
        cfg_mod.save(cfg)
        c = Chronos()
        fired = c.tick(now=_dt_at(hour=9, minute=0))
        assert len(fired) <= MAX_FIRES_PER_TICK

    def test_disabled_ritual_skipped(self, isolated_chronos):
        from olympus.runtime import config as cfg_mod
        cfg = cfg_mod.Config()
        cfg.chronos.rituals = [{
            "id": "morning", "when": "daily 09:00",
            "do": "today", "enabled": False}]
        cfg_mod.save(cfg)
        c = Chronos()
        assert c.tick(now=_dt_at(hour=9, minute=0)) == []

    def test_invalid_ritual_skipped(self, isolated_chronos):
        from olympus.runtime import config as cfg_mod
        cfg = cfg_mod.Config()
        cfg.chronos.rituals = [{
            "id": "bad", "when": "garbage", "do": "today"}]
        cfg_mod.save(cfg)
        c = Chronos()
        assert c.tick(now=_dt_at(hour=9, minute=0)) == []


# ─────────────────────────────────────────────────────────────────────
# Shared whitelist
# ─────────────────────────────────────────────────────────────────────


class TestSharedWhitelist:

    def test_argos_still_uses_alias(self):
        """ERRAND_WHITELIST in argos must equal AUTOMATED_ERRANDS."""
        from olympus.monsters.argos.eyes.eye_filesystem import (
            ERRAND_WHITELIST,
        )
        assert ERRAND_WHITELIST == AUTOMATED_ERRANDS

    def test_no_gated_errands_in_whitelist(self):
        """Constitutional check: AUTOMATED_ERRANDS must not contain
        any operation that requires Zeus-in-person per S7."""
        from olympus.throne.router import GATED_ERRANDS
        overlap = set(AUTOMATED_ERRANDS) & set(GATED_ERRANDS)
        assert overlap == set(), \
            f"GATED errands leaked into AUTOMATED whitelist: {overlap}"


# ─────────────────────────────────────────────────────────────────────
# CLI smoke
# ─────────────────────────────────────────────────────────────────────


class TestChronosCLI:

    def test_errand_registered(self):
        from olympus.cli import hermes
        assert "chronos" in hermes._errands

    def test_rituals_subcommand(self, isolated_chronos):
        from olympus.cli import hermes
        errand = hermes._errands["chronos"]
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            rc = errand.fn(["rituals"])
        assert rc == 0
        assert "chronos rituals" in buf.getvalue()

    def test_check_valid_expr(self, isolated_chronos):
        from olympus.cli import hermes
        errand = hermes._errands["chronos"]
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            rc = errand.fn(["check", "daily", "09:00"])
        assert rc == 0
        assert "matches_now" in buf.getvalue()

    def test_check_invalid_expr(self, isolated_chronos):
        from olympus.cli import hermes
        errand = hermes._errands["chronos"]
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            rc = errand.fn(["check", "garbage"])
        assert rc == 1

    def test_ritual_add_rejects_bad_errand(self, isolated_chronos):
        from olympus.cli import hermes
        errand = hermes._errands["chronos"]
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            rc = errand.fn(["ritual", "add", "test",
                             "daily", "09:00", "ratify"])
        assert rc == 1
        assert "whitelist" in buf.getvalue().lower()

    def test_ritual_add_remove_round_trip(self, isolated_chronos):
        from olympus.cli import hermes
        from olympus.runtime import config as cfg_mod
        errand = hermes._errands["chronos"]
        # Add
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            rc = errand.fn(["ritual", "add", "rt",
                             "daily", "09:00", "today"])
        assert rc == 0
        assert len(cfg_mod.load().chronos.rituals) == 1
        # Remove
        buf2 = io.StringIO()
        with contextlib.redirect_stdout(buf2):
            rc = errand.fn(["ritual", "remove", "rt"])
        assert rc == 0
        assert cfg_mod.load().chronos.rituals == []
