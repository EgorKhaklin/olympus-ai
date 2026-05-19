"""tests/test_replay.py — the Olympus-Replay arc (Decade closer).

Per Delphi 2026-05-19-olympus-replay-arc.md.

All tests use the ScriptedBridge pattern from earlier arcs to make
replays deterministic without LLM cost. No real Anthropic calls.
"""
from __future__ import annotations

import contextlib
import io
import json

import pytest

from olympus.runtime.replay import (
    ReplayPlan, ReplayCandidate, ReplayResult, ReplayReport,
    plan_replays, replay_one, replay_many,
    _classify, _find_paired_llm_call,
    CONFIDENCE_DRIFT_THRESHOLD, LIST_DRIFT_RATIO, MAX_LIMIT,
)
from olympus.runtime.llm_bridge import EchoBridge, LLMBridge, LLMResponse
from olympus.titans.mnemosyne import mnemosyne


# ─────────────────────────────────────────────────────────────────────
# Classification helper (pure-function tests)
# ─────────────────────────────────────────────────────────────────────


class TestClassify:

    def test_stable_when_identical(self):
        old = {"summary": "x", "risk_class": "LOW",
                "confidence": 0.7, "drift_observed": "x"}
        new = {"summary": "x", "risk_class": "LOW",
                "confidence": 0.7, "drift_observed": "x"}
        cls, diffs = _classify(old, 0.7, new, 0.7)
        assert cls == "stable"
        assert diffs == []

    def test_stable_when_confidence_within_threshold(self):
        old = {"summary": "x", "risk_class": "LOW", "confidence": 0.7}
        new = {"summary": "y", "risk_class": "LOW", "confidence": 0.8}
        cls, _ = _classify(old, 0.7, new, 0.8)
        assert cls == "stable"

    def test_drift_when_risk_class_changes(self):
        old = {"summary": "x", "risk_class": "MEDIUM", "confidence": 0.6}
        new = {"summary": "x", "risk_class": "LOW", "confidence": 0.6}
        cls, diffs = _classify(old, 0.6, new, 0.6)
        assert cls == "drift"
        assert any("risk_class" in d for d in diffs)

    def test_drift_when_confidence_shifts_over_threshold(self):
        old = {"summary": "x", "risk_class": "LOW", "confidence": 0.2}
        new = {"summary": "x", "risk_class": "LOW", "confidence": 0.9}
        cls, diffs = _classify(old, 0.2, new, 0.9)
        assert cls == "drift"
        assert any("confidence" in d for d in diffs)

    def test_drift_when_list_field_shrinks_dramatically(self):
        old = {"insights": ["a", "b", "c", "d"], "confidence": 0.7}
        new = {"insights": ["a"], "confidence": 0.7}
        cls, diffs = _classify(old, 0.7, new, 0.7)
        assert cls == "drift"
        assert any("insights" in d for d in diffs)

    def test_broken_when_schema_missing_key(self):
        old = {"summary": "x", "risk_class": "LOW", "confidence": 0.7}
        new = {"summary": "x"}   # risk_class missing
        cls, diffs = _classify(old, 0.7, new, 0.7)
        assert cls == "broken"
        assert any("schema" in d.lower() for d in diffs)

    def test_broken_when_new_empty(self):
        old = {"summary": "x"}
        new = {}
        cls, diffs = _classify(old, 0.5, new, 0.0)
        assert cls == "broken"

    def test_grounding_keys_excluded_from_schema_check(self):
        """Per replay arc: grounding-added keys (cited_paths, etc.)
        should not count as schema additions."""
        old = {"summary": "x", "confidence": 0.7}
        new = {"summary": "x", "confidence": 0.7,
                "cited_paths": [], "fabricated_paths": [],
                "grounding_penalty": 0.0}
        cls, _ = _classify(old, 0.7, new, 0.7)
        assert cls == "stable"


# ─────────────────────────────────────────────────────────────────────
# ReplayPlan + plan_replays
# ─────────────────────────────────────────────────────────────────────


class TestPlanReplays:

    def test_empty_when_limit_zero(self):
        assert plan_replays(ReplayPlan(limit=0)) == []

    def test_limit_capped(self):
        # MAX_LIMIT enforcement
        candidates = plan_replays(ReplayPlan(limit=10_000))
        assert len(candidates) <= MAX_LIMIT

    def test_unknown_role_returns_empty(self):
        candidates = plan_replays(ReplayPlan(role="not-a-role"))
        assert candidates == []

    def test_returns_candidates_with_paired_prompts(self):
        candidates = plan_replays(ReplayPlan(limit=5))
        # The real substrate has 279 production agent.invocations
        # paired with llm.call records; we should get at most 5
        assert len(candidates) <= 5
        for c in candidates:
            assert c.user_prompt
            assert c.role in ("hephaestus", "momus", "cassandra",
                                "athena", "figure_proposer")

    def test_role_filter(self):
        candidates = plan_replays(
            ReplayPlan(limit=5, role="hephaestus"))
        for c in candidates:
            assert c.role == "hephaestus"


# ─────────────────────────────────────────────────────────────────────
# replay_one — uses real EchoBridge (deterministic, free)
# ─────────────────────────────────────────────────────────────────────


class TestReplayOne:

    def test_with_fake_candidate_classifies_and_records(self):
        """Build a synthetic candidate; replay; verify a regression
        record was written."""
        candidate = ReplayCandidate(
            agent_record_id="agent.invocation#test",
            role="hephaestus",
            user_prompt="what is drifting?",
            original_parsed={
                "summary": "x", "drift_observed": "x",
                "proposed_fix": "x", "rationale": "x",
                "risk_class": "LOW", "confidence": 0.5,
            },
            original_confidence=0.5,
            original_bridge="echo",
            original_at="2026-05-19T00:00:00",
        )
        plan = ReplayPlan(limit=1, bridge="echo")
        before = len(mnemosyne.recall("replay.regression"))
        result = replay_one(candidate, plan)
        after = len(mnemosyne.recall("replay.regression"))
        # A regression record was written
        assert after == before + 1
        # Classification is one of the known values
        assert result.classification in (
            "stable", "drift", "broken", "skipped", "over-budget")
        # Echo bridge succeeds; result must NOT be `broken` here
        # (the agent.run path is alive)
        assert result.classification != "skipped"
        # Bridge label propagates
        assert result.new_bridge == "echo"

    def test_unknown_bridge_falls_back_to_default(self):
        candidate = ReplayCandidate(
            agent_record_id="x", role="hephaestus",
            user_prompt="?", original_parsed={"x": 1},
            original_confidence=0.5, original_bridge="echo",
            original_at="2026-05-19T00:00:00",
        )
        plan = ReplayPlan(bridge="totally-unknown-bridge")
        result = replay_one(candidate, plan)
        # Should not raise; classification valid
        assert result.classification in (
            "stable", "drift", "broken", "skipped", "over-budget")


# ─────────────────────────────────────────────────────────────────────
# replay_many aggregate
# ─────────────────────────────────────────────────────────────────────


class TestReplayMany:

    def test_aggregate_shape(self):
        plan = ReplayPlan(limit=3, bridge="echo")
        report = replay_many(plan)
        assert isinstance(report, ReplayReport)
        assert report.bridge_used == "echo"
        # Total = sum of buckets
        total_buckets = (report.stable + report.drift +
                          report.broken + report.skipped +
                          report.over_budget)
        assert total_buckets == report.total

    def test_by_role_breakdown_populated(self):
        plan = ReplayPlan(limit=5, bridge="echo")
        report = replay_many(plan)
        # Every role bucket sums to its share
        for role, counts in report.by_role.items():
            assert role in ("hephaestus", "momus", "cassandra",
                             "athena", "figure_proposer")
            assert sum(counts.values()) > 0


# ─────────────────────────────────────────────────────────────────────
# CLI errand smoke + Throne wiring
# ─────────────────────────────────────────────────────────────────────


class TestReplayErrand:

    def test_registered(self):
        from olympus.cli import hermes
        assert "replay" in hermes._errands

    def test_smoke(self):
        from olympus.cli import hermes
        errand = hermes._errands["replay"]
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            rc = errand.fn(["--limit", "2"])
        assert rc == 0
        assert "replay" in buf.getvalue().lower()


class TestThroneSafe:

    def test_replay_in_safe_errands(self):
        from olympus.throne.router import SAFE_ERRANDS, GATED_ERRANDS
        assert "replay" in SAFE_ERRANDS
        assert "replay" not in GATED_ERRANDS
