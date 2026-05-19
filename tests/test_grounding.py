"""tests/test_grounding.py — grounding arc.

Per Delphi 2026-05-19-grounding-arc.md.

Covers:
  - read_file_grounded: whitelisted root, .. rejected, symlink-escape rejected,
    real files return sha + bytes
  - recall_grounded: respects limit, returns JSON-safe dicts
  - cited_paths_in_text: extracts real paths, ignores URLs / versions / Greek names
  - verify_cited_paths: real files exist=True, fabricated exist=False, globs work
  - build_grounding_for_role: each known role yields non-empty JSON; budget cap
  - apply_grounding: confidence downgrade on fabrication; record to Mnemosyne
  - agents.run integration: scripted bridge with fabricated path → penalty applied
"""
from __future__ import annotations

import json
import os
import pathlib
import tempfile

import pytest

from olympus.runtime.grounding import (
    GroundedRead, GroundedCheck,
    read_file_grounded, recall_grounded,
    cited_paths_in_text, verify_cited_paths,
    build_grounding_for_role, apply_grounding,
    CONFIDENCE_PENALTY_PER_FABRICATION,
)
from olympus.runtime.llm_bridge import LLMBridge, LLMResponse
from olympus.titans.mnemosyne import mnemosyne


# ─────────────────────────────────────────────────────────────────────
# read_file_grounded
# ─────────────────────────────────────────────────────────────────────


class TestReadFileGrounded:

    def test_reads_real_file(self):
        # README.md should exist in the project root
        r = read_file_grounded("README.md")
        assert isinstance(r, GroundedRead)
        assert r.exists, f"README.md should exist: {r.error}"
        assert r.bytes_total > 0
        assert len(r.sha256) == 64

    def test_missing_file_is_safe(self):
        r = read_file_grounded("this/does/not/exist.txt")
        assert not r.exists
        assert "not found" in r.error.lower()

    def test_dotdot_escape_rejected(self):
        r = read_file_grounded("../../../etc/passwd")
        assert not r.exists
        assert "outside project root" in r.error.lower()

    def test_empty_path_safe(self):
        r = read_file_grounded("")
        assert not r.exists

    def test_absolute_outside_root_rejected(self):
        r = read_file_grounded("/etc/passwd")
        assert not r.exists
        assert "outside" in r.error.lower()


# ─────────────────────────────────────────────────────────────────────
# recall_grounded
# ─────────────────────────────────────────────────────────────────────


class TestRecallGrounded:

    def test_returns_json_safe_dicts(self):
        # session.completed has plenty of records in the repo state
        out = recall_grounded("session.completed", limit=3)
        assert isinstance(out, list)
        for rec in out:
            assert isinstance(rec, dict)
            assert "kind" in rec
            assert "summary" in rec
            # Must be JSON-encodable
            json.dumps(rec, default=str)

    def test_respects_limit(self):
        out = recall_grounded("session.completed", limit=2)
        assert len(out) <= 2

    def test_unknown_kind_returns_empty(self):
        out = recall_grounded("definitely-not-a-real-kind-xyz", limit=5)
        assert out == []

    def test_negative_limit_returns_empty(self):
        assert recall_grounded("session.completed", limit=0) == []
        assert recall_grounded("session.completed", limit=-1) == []


# ─────────────────────────────────────────────────────────────────────
# cited_paths_in_text
# ─────────────────────────────────────────────────────────────────────


class TestCitedPathsExtraction:

    def test_extracts_project_paths(self):
        text = ("The drift is in src/olympus/cli.py and also in "
                "tests/test_agora.py.")
        paths = cited_paths_in_text(text)
        assert "src/olympus/cli.py" in paths
        assert "tests/test_agora.py" in paths

    def test_extracts_glob_patterns(self):
        text = "Check codex/oracles/delphi/*.md for details"
        paths = cited_paths_in_text(text)
        assert "codex/oracles/delphi/*.md" in paths

    def test_ignores_urls(self):
        text = "See https://example.com/api/v1/users"
        paths = cited_paths_in_text(text)
        assert not any("example.com" in p for p in paths)

    def test_ignores_version_numbers(self):
        text = "We are on version 1.2.3 of the substrate"
        paths = cited_paths_in_text(text)
        assert "1.2.3" not in paths

    def test_ignores_greek_figures(self):
        text = "Hephaestus and Mnemosyne work together"
        paths = cited_paths_in_text(text)
        # Bare names without slash/extension should not be flagged
        assert paths == []

    def test_empty_text_is_empty(self):
        assert cited_paths_in_text("") == []
        assert cited_paths_in_text(None) == []


# ─────────────────────────────────────────────────────────────────────
# verify_cited_paths
# ─────────────────────────────────────────────────────────────────────


class TestVerifyCitedPaths:

    def test_real_path_exists(self):
        checks = verify_cited_paths(["README.md"])
        assert len(checks) == 1
        assert checks[0].exists
        assert checks[0].normalized == "README.md"

    def test_fabricated_path_does_not_exist(self):
        checks = verify_cited_paths([
            "strategic/delphi/debates/abc.md",  # Hephaestus's actual hallucination
        ])
        assert len(checks) == 1
        assert not checks[0].exists
        assert "not found" in checks[0].reason.lower()

    def test_mixed_real_and_fake(self):
        checks = verify_cited_paths([
            "README.md", "fake/path.txt", "src/olympus/cli.py",
        ])
        assert len(checks) == 3
        results = {c.cited: c.exists for c in checks}
        assert results["README.md"] is True
        assert results["fake/path.txt"] is False
        assert results["src/olympus/cli.py"] is True

    def test_glob_matches_existing(self):
        # codex/oracles/delphi/ has many .md files
        checks = verify_cited_paths(["codex/oracles/delphi/*.md"])
        assert checks[0].exists, "glob should match existing files"

    def test_glob_no_matches_fabricated(self):
        checks = verify_cited_paths(["nonexistent/dir/*.fake"])
        assert not checks[0].exists


# ─────────────────────────────────────────────────────────────────────
# build_grounding_for_role
# ─────────────────────────────────────────────────────────────────────


class TestBuildGroundingForRole:

    @pytest.mark.parametrize("role", [
        "hephaestus", "momus", "cassandra", "athena", "figure_proposer",
    ])
    def test_each_role_yields_grounding(self, role):
        block = build_grounding_for_role(role)
        assert isinstance(block, str)
        assert len(block) > 0
        # Must be JSON-parseable
        data = json.loads(block)
        assert isinstance(data, dict)

    def test_unknown_role_returns_empty(self):
        assert build_grounding_for_role("not-a-role") == ""

    def test_budget_cap_respected(self):
        from olympus.runtime.grounding import _BUDGET_CHARS
        for role in ("hephaestus", "athena", "figure_proposer"):
            block = build_grounding_for_role(role)
            assert len(block) <= _BUDGET_CHARS

    def test_figure_proposer_includes_existing_pantheon(self):
        block = build_grounding_for_role("figure_proposer")
        data = json.loads(block)
        assert "existing_figures" in data
        # We have 90+ named figures; at least some should appear
        assert len(data["existing_figures"]) >= 5


# ─────────────────────────────────────────────────────────────────────
# apply_grounding — the full pipeline
# ─────────────────────────────────────────────────────────────────────


class TestApplyGrounding:

    def test_no_fabrication_no_penalty(self):
        parsed = {"confidence": 0.8}
        text = "All clear — see README.md"
        result = apply_grounding(
            role="hephaestus", response_text=text, parsed=parsed)
        assert result["fabricated_paths"] == []
        assert result["grounding_penalty"] == 0.0
        assert result["confidence"] == 0.8

    def test_fabrication_triggers_penalty(self):
        parsed = {"confidence": 0.9}
        text = ("The drift is at strategic/delphi/debates/abc.md and "
                "also at mnemosyne/ledger/decisions.log")
        result = apply_grounding(
            role="hephaestus", response_text=text, parsed=parsed)
        assert len(result["fabricated_paths"]) >= 1
        assert result["grounding_penalty"] == CONFIDENCE_PENALTY_PER_FABRICATION
        # Confidence dropped
        assert result["confidence"] < 0.9
        assert result["confidence"] == pytest.approx(0.7)

    def test_confidence_clamped_to_zero(self):
        parsed = {"confidence": 0.1}
        text = "drift at fake/path.md"
        result = apply_grounding(
            role="hephaestus", response_text=text, parsed=parsed)
        assert result["confidence"] >= 0.0

    def test_grounding_check_recorded(self):
        before = len(mnemosyne.recall("agent.grounding_check"))
        apply_grounding(role="hephaestus",
                         response_text="see README.md",
                         parsed={"confidence": 0.5})
        after = len(mnemosyne.recall("agent.grounding_check"))
        assert after == before + 1

    def test_recorded_payload_has_fabrication_facts(self):
        apply_grounding(role="momus",
                         response_text="check fake/thing.py for AP1",
                         parsed={"confidence": 0.5})
        rec = mnemosyne.recall("agent.grounding_check")[-1]
        assert "fabricated_paths" in rec.body
        assert rec.body["fabricated_count"] >= 1


# ─────────────────────────────────────────────────────────────────────
# Integration: agents.run() now grounds + verifies
# ─────────────────────────────────────────────────────────────────────


class ScriptedBridge(LLMBridge):
    """Returns scripted text; records to Mnemosyne via shared helper."""
    name = "scripted-grounding"

    def __init__(self, text: str) -> None:
        self._text = text

    def call(self, *, system, user, max_tokens=4096, role="", **extra):
        self.last_user = user  # so tests can verify grounding was injected
        resp = LLMResponse(text=self._text, bridge=self.name,
                           model="scripted-1", elapsed_ms=1.0)
        self._record_call(system=system, user=user,
                           response=resp, role=role)
        return resp


class TestAgentsRunIntegration:

    def test_grounding_injected_into_user_prompt(self, monkeypatch):
        from olympus.runtime import agents as agents_mod
        from olympus.runtime import llm_bridge
        scripted = ScriptedBridge(json.dumps({
            "summary": "no drift",
            "drift_observed": "n/a", "proposed_fix": "n/a",
            "rationale": "n/a", "risk_class": "LOW",
            "confidence": 0.9,
        }))
        monkeypatch.setattr(llm_bridge, "bridge", lambda: scripted)
        result = agents_mod.run("hephaestus", "what is drifting?",
                                 check_pan=False)
        # Grounding block must have been prepended
        assert "GROUNDING" in scripted.last_user
        assert "QUESTION" in scripted.last_user
        # Result clean (no fabrication)
        assert result.parsed["fabricated_paths"] == []
        assert result.confidence == pytest.approx(0.9)

    def test_fabricated_response_gets_penalty(self, monkeypatch):
        from olympus.runtime import agents as agents_mod
        from olympus.runtime import llm_bridge
        scripted = ScriptedBridge(json.dumps({
            "summary": "drift at fake/place.md",
            "drift_observed": ("strategic/delphi/debates/xxx.md "
                                "is missing fields"),
            "proposed_fix": "n/a", "rationale": "n/a",
            "risk_class": "LOW", "confidence": 0.9,
        }))
        monkeypatch.setattr(llm_bridge, "bridge", lambda: scripted)
        result = agents_mod.run("hephaestus", "?", check_pan=False)
        assert len(result.parsed["fabricated_paths"]) >= 1
        # Confidence was downgraded
        assert result.confidence < 0.9
        assert result.confidence == pytest.approx(0.7)
