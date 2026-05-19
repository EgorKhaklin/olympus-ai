"""tests/test_plutus_budget.py — the Plutus-Budget arc.

Per Delphi 2026-05-19-plutus-budget-arc.md.

Constitutional discipline: Pan must NOT be involved. Budget is soft
enforcement at the LLM-bridge layer only. All tests monkey-patch the
config path so the operator's real state/config.json is never touched.
"""
from __future__ import annotations

import contextlib
import io
import json

import pytest

from olympus.heroes.plutus import plutus, Plutus, CostReport, CostBreakdown
from olympus.titans.mnemosyne import mnemosyne


# ─────────────────────────────────────────────────────────────────────
# Fixture: isolated config with operator-declared budget
# ─────────────────────────────────────────────────────────────────────


@pytest.fixture
def isolated_budget(tmp_path, monkeypatch):
    """Redirect config to tmp; set up a known budget; isolate
    plutus.budget_* mnemosyne records by timestamp so prior tests'
    acks don't leak in. Return a helper for injecting fake spend."""
    from olympus.runtime import config as cfg_mod
    from olympus.titans import mnemosyne as mnemo_mod
    from olympus.primordials.nyx import Nyx

    fake_cfg = tmp_path / "config.json"
    monkeypatch.setattr(cfg_mod, "_path", lambda: fake_cfg)
    cfg = cfg_mod.Config()
    cfg.plutus.budget.enabled = True
    cfg.plutus.budget.daily_usd = 1.00
    cfg.plutus.budget.weekly_usd = 5.00
    cfg.plutus.budget.monthly_usd = 20.00
    cfg.plutus.budget.warn_at_pct = 80.0
    cfg_mod.save(cfg)

    # Capture fixture start; filter plutus.budget_* records to those
    # recorded AFTER this moment. Production code unaffected.
    start = Nyx.now().isoformat()
    real_recall = mnemo_mod.mnemosyne.recall

    def filtered_recall(kind, *args, **kw):
        out = real_recall(kind, *args, **kw)
        if str(kind).startswith("plutus.budget"):
            return [r for r in out if (r.remembered_at or "") >= start]
        return out

    monkeypatch.setattr(mnemo_mod.mnemosyne, "recall", filtered_recall)

    def _inject(window_to_spend: dict[str, float]):
        """Monkey-patch plutus.tally so given window → given spend."""
        def fake_tally(self, window="all", *, max_by_day_keys=30):
            r = CostReport(window=window)
            r.estimated_usd = float(window_to_spend.get(window, 0.0))
            return r
        monkeypatch.setattr(Plutus, "tally", fake_tally)

    return _inject


# ─────────────────────────────────────────────────────────────────────
# budget_status reporting
# ─────────────────────────────────────────────────────────────────────


class TestBudgetStatus:

    def test_disabled_default(self, tmp_path, monkeypatch):
        from olympus.runtime import config as cfg_mod
        fake = tmp_path / "config.json"
        monkeypatch.setattr(cfg_mod, "_path", lambda: fake)
        # No config = disabled
        s = plutus.budget_status()
        assert s == {"enabled": False}

    def test_under_budget(self, isolated_budget):
        isolated_budget({"today": 0.10, "7d": 0.20, "30d": 0.30})
        s = plutus.budget_status()
        assert s["enabled"] is True
        assert s["daily"]["state"] == "ok"
        assert s["weekly"]["state"] == "ok"
        assert s["monthly"]["state"] == "ok"

    def test_warn_threshold(self, isolated_budget):
        # 0.85 / 1.00 daily = 85% which is at warn (80%)
        isolated_budget({"today": 0.85})
        s = plutus.budget_status()
        assert s["daily"]["state"] == "warn"
        assert 80 <= s["daily"]["pct"] < 100

    def test_over_threshold(self, isolated_budget):
        isolated_budget({"today": 1.15})
        s = plutus.budget_status()
        assert s["daily"]["state"] == "over"
        assert s["daily"]["pct"] >= 100

    def test_is_over_budget(self, isolated_budget):
        isolated_budget({"today": 0.5})
        assert not plutus.is_over_budget()
        isolated_budget({"today": 1.5})
        assert plutus.is_over_budget()


# ─────────────────────────────────────────────────────────────────────
# Acknowledgment semantics
# ─────────────────────────────────────────────────────────────────────


class TestAcknowledgment:

    def test_breach_since_ack_initially_true_when_over(
            self, isolated_budget):
        isolated_budget({"today": 1.5})
        # Fresh ack history — over budget AND not acked
        assert plutus.breach_since_ack() is True

    def test_ack_clears_breach_since_ack(self, isolated_budget):
        isolated_budget({"today": 1.5})
        plutus.acknowledge_breach(reason="test ack")
        # Same spend, post-ack: no new breach
        assert plutus.breach_since_ack() is False

    def test_further_breach_after_ack_re_triggers(
            self, isolated_budget):
        isolated_budget({"today": 1.5})
        plutus.acknowledge_breach(reason="initial")
        assert plutus.breach_since_ack() is False
        # Spend grows further
        isolated_budget({"today": 2.0})
        assert plutus.breach_since_ack() is True

    def test_ack_records_to_mnemosyne(self, isolated_budget):
        isolated_budget({"today": 1.5})
        before = len(mnemosyne.recall("plutus.budget_ack"))
        plutus.acknowledge_breach(reason="for test")
        after = len(mnemosyne.recall("plutus.budget_ack"))
        assert after == before + 1
        latest = mnemosyne.recall("plutus.budget_ack")[-1]
        assert latest.body["reason"] == "for test"


# ─────────────────────────────────────────────────────────────────────
# LLM bridge guard
# ─────────────────────────────────────────────────────────────────────


class TestBridgeGuard:

    def test_anthropic_refuses_over_budget(self, isolated_budget,
                                             monkeypatch):
        """Inject over-budget state; AnthropicBridge.call should return
        a budget-breach error WITHOUT actually calling the SDK."""
        isolated_budget({"today": 1.5})
        from olympus.runtime.llm_bridge import AnthropicBridge

        # Inject a fake client that would error if actually invoked
        # — proves the guard fires BEFORE the client is touched
        class _UnreachableClient:
            class messages:
                @staticmethod
                def stream(*a, **k):
                    raise AssertionError("guard failed — bridge "
                                          "reached the SDK")

        bridge = AnthropicBridge(client=_UnreachableClient())
        resp = bridge.call(system="s", user="u")
        assert resp.error
        assert "budget" in resp.error.lower()

    def test_anthropic_proceeds_when_acknowledged(self, isolated_budget,
                                                    monkeypatch):
        """After acknowledge_breach, the guard should let the call
        proceed (which will then fail at the SDK because the fake
        raises — that's fine, proves the guard was bypassed)."""
        isolated_budget({"today": 1.5})
        plutus.acknowledge_breach(reason="for test")
        from olympus.runtime.llm_bridge import AnthropicBridge

        class _SDKError:
            class messages:
                @staticmethod
                def stream(*a, **k):
                    raise RuntimeError("SDK error AFTER guard")

        bridge = AnthropicBridge(client=_SDKError())
        resp = bridge.call(system="s", user="u")
        # Error should be the SDK error, NOT a budget error
        assert "budget" not in (resp.error or "").lower()

    def test_anthropic_proceeds_when_disabled(self, tmp_path,
                                                monkeypatch):
        """No budget config → no guard → SDK gets called."""
        from olympus.runtime import config as cfg_mod
        fake = tmp_path / "config.json"
        monkeypatch.setattr(cfg_mod, "_path", lambda: fake)

        from olympus.runtime.llm_bridge import AnthropicBridge

        class _SDKError:
            class messages:
                @staticmethod
                def stream(*a, **k):
                    raise RuntimeError("SDK reached")

        bridge = AnthropicBridge(client=_SDKError())
        resp = bridge.call(system="s", user="u")
        assert "budget" not in (resp.error or "").lower()


# ─────────────────────────────────────────────────────────────────────
# Doctor check
# ─────────────────────────────────────────────────────────────────────


class TestDoctorBudgetCheck:

    def test_disabled_is_ok(self, tmp_path, monkeypatch):
        from olympus.runtime import config as cfg_mod
        fake = tmp_path / "config.json"
        monkeypatch.setattr(cfg_mod, "_path", lambda: fake)
        from olympus.runtime.doctor import _check_budget
        f = _check_budget()
        assert f.name == "budget"
        assert f.status == "ok"
        assert "disabled" in f.detail.lower()

    def test_warn_when_at_warn_pct(self, isolated_budget):
        isolated_budget({"today": 0.85})
        from olympus.runtime.doctor import _check_budget
        f = _check_budget()
        assert f.status == "warn"

    def test_fail_when_over_and_not_acked(self, isolated_budget):
        isolated_budget({"today": 1.5})
        from olympus.runtime.doctor import _check_budget
        f = _check_budget()
        assert f.status == "fail"
        assert "REFUSED" in f.detail

    def test_warn_when_over_but_acked(self, isolated_budget):
        isolated_budget({"today": 1.5})
        plutus.acknowledge_breach(reason="x")
        from olympus.runtime.doctor import _check_budget
        f = _check_budget()
        # acked → warn, not fail
        assert f.status == "warn"


# ─────────────────────────────────────────────────────────────────────
# Constitutional check: Pan is NOT involved
# ─────────────────────────────────────────────────────────────────────


class TestPanUntouched:

    def test_pan_state_not_changed_by_budget_breach(self, isolated_budget):
        """Per Delphi: Pan's authority is NOT extended by this arc.
        Budget breach must NOT cause Pan to enter the panicked state."""
        from olympus.olympians.pan import pan
        # Snapshot Pan state BEFORE breach
        pan_before = pan.evaluate()
        # Now induce a breach
        isolated_budget({"today": 1.5})
        assert plutus.is_over_budget()
        # Pan must still be in the same state
        pan_after = pan.evaluate()
        assert pan_after.panicked == pan_before.panicked, \
            "Pan state changed due to budget breach — " \
            "constitutional regression!"


# ─────────────────────────────────────────────────────────────────────
# CLI smoke
# ─────────────────────────────────────────────────────────────────────


class TestSpendCLIExtensions:

    def test_budget_subcommand(self, isolated_budget):
        isolated_budget({"today": 0.5})
        from olympus.cli import hermes
        errand = hermes._errands["spend"]
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            rc = errand.fn(["--budget"])
        assert rc == 0
        out = buf.getvalue()
        assert "budget" in out.lower()

    def test_acknowledge_budget(self, isolated_budget):
        isolated_budget({"today": 1.5})
        before = len(mnemosyne.recall("plutus.budget_ack"))
        from olympus.cli import hermes
        errand = hermes._errands["spend"]
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            rc = errand.fn(["--acknowledge-budget",
                              "--reason", "deliberate test"])
        assert rc == 0
        after = len(mnemosyne.recall("plutus.budget_ack"))
        assert after == before + 1

    def test_budget_disabled_message(self, tmp_path, monkeypatch):
        from olympus.runtime import config as cfg_mod
        fake = tmp_path / "config.json"
        monkeypatch.setattr(cfg_mod, "_path", lambda: fake)
        from olympus.cli import hermes
        errand = hermes._errands["spend"]
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            rc = errand.fn(["--budget"])
        assert rc == 0
        assert "DISABLED" in buf.getvalue() or \
               "disabled" in buf.getvalue().lower()
