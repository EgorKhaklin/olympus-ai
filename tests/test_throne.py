"""tests/test_throne.py — Zeus's Throne arc.

Per Delphi 2026-05-19-throne-arc.md.

Covers:
  - Router: SAFE_ERRANDS + GATED_ERRANDS disjoint
  - Router: classify() handles direct / run / gated / malformed plans
  - Throne: direct-answer path (one LLM call, no errand exec)
  - Throne: gated-refusal path (S7 — never executes)
  - Throne: run-errands path (executes + synthesizes via 2 LLM calls)
  - Throne: empty input safety
  - Throne: bridge errors don't crash
  - Throne: every turn → throne.turn in Mnemosyne
  - HTTP: POST /throne/turn happy path + validation
  - Agora: throne.html is the new landing page
"""
from __future__ import annotations

import json
import time

import pytest

from olympus.runtime.llm_bridge import EchoBridge, LLMBridge, LLMResponse
from olympus.titans.mnemosyne import mnemosyne
from olympus.throne import (
    Throne, ThroneResponse, Turn,
    SAFE_ERRANDS, GATED_ERRANDS,
    DirectAnswer, RunErrands, RequiresOperator,
)
from olympus.throne.router import classify, build_system_prompt


# ─────────────────────────────────────────────────────────────────────
# Fixture — a scripted bridge that returns predetermined LLM text
# ─────────────────────────────────────────────────────────────────────


class ScriptedBridge(LLMBridge):
    """Returns each scripted response in order. Records to Mnemosyne
    via the shared helper, same as the real bridges."""

    name = "scripted"

    def __init__(self, responses: list[str]) -> None:
        self._responses = list(responses)
        self.calls: list[dict] = []

    def call(self, *, system, user, max_tokens=4096, role="", **extra):
        self.calls.append({"system": system, "user": user, "role": role})
        text = self._responses.pop(0) if self._responses else ""
        resp = LLMResponse(text=text, bridge=self.name,
                           model="scripted-1", elapsed_ms=1.0)
        self._record_call(system=system, user=user, response=resp, role=role)
        return resp


# ─────────────────────────────────────────────────────────────────────
# Router tests
# ─────────────────────────────────────────────────────────────────────


class TestRouter:

    def test_safe_and_gated_are_disjoint(self):
        overlap = set(SAFE_ERRANDS) & set(GATED_ERRANDS)
        assert overlap == set(), \
            f"SAFE_ERRANDS and GATED_ERRANDS must be disjoint: {overlap}"

    def test_classify_direct_answer(self):
        a = classify({"action": "direct", "answer": "hello"})
        assert isinstance(a, DirectAnswer)
        assert a.text == "hello"

    def test_classify_run_one_safe_errand(self):
        a = classify({"action": "run", "errands": [
            {"name": "doctor", "argv": []}]})
        assert isinstance(a, RunErrands)
        assert a.errands == [("doctor", [])]

    def test_classify_run_filters_unknown_errand(self):
        # 'doctor' is safe; 'foo' is unknown — only doctor survives
        a = classify({"action": "run", "errands": [
            {"name": "doctor", "argv": []},
            {"name": "foo", "argv": []}]})
        assert isinstance(a, RunErrands)
        assert a.errands == [("doctor", [])]

    def test_classify_gated_via_action_key(self):
        a = classify({"action": "gated", "errand": "ratify"})
        assert isinstance(a, RequiresOperator)
        assert a.errand == "ratify"
        assert "invoke action ratify" in a.suggested_command

    def test_classify_gated_via_errands_list(self):
        # Even if the LLM tries to sneak a gated errand into the run list,
        # router catches it and refuses
        a = classify({"action": "run", "errands": [
            {"name": "ratify", "argv": ["abc"]}]})
        assert isinstance(a, RequiresOperator)
        assert a.errand == "ratify"

    def test_classify_malformed_plan_is_safe(self):
        # Anything not-a-dict → DirectAnswer with the stringified head
        a = classify("not a dict")
        assert isinstance(a, DirectAnswer)
        a2 = classify({})
        assert isinstance(a2, DirectAnswer)

    def test_classify_agent_errand_with_argv(self):
        a = classify({"action": "run", "errands": [
            {"name": "agent", "argv": ["hephaestus", "drift?"]}]})
        assert isinstance(a, RunErrands)
        assert a.errands == [("agent", ["hephaestus", "drift?"])]

    def test_system_prompt_names_every_errand(self):
        p = build_system_prompt()
        for name in SAFE_ERRANDS:
            assert name in p, f"SAFE errand {name} missing from prompt"
        for name in GATED_ERRANDS:
            assert name in p, f"GATED errand {name} missing from prompt"


# ─────────────────────────────────────────────────────────────────────
# Throne tests
# ─────────────────────────────────────────────────────────────────────


class TestThroneDirect:

    def test_direct_answer_one_call(self):
        bridge = ScriptedBridge([
            json.dumps({"action": "direct",
                        "answer": "Olympus is a cognitive substrate."}),
        ])
        t = Throne(llm=bridge)
        r = t.respond("what is Olympus?")
        assert isinstance(r, ThroneResponse)
        assert "cognitive substrate" in r.answer
        assert r.actions_taken == []
        assert r.suggested_command is None
        assert r.bridge == "scripted"
        assert len(bridge.calls) == 1, "direct answer = one call"

    def test_empty_input_safe(self):
        # No bridge call needed for empty input
        t = Throne(llm=ScriptedBridge([]))
        r = t.respond("")
        assert "empty" in r.answer.lower()


class TestThroneGated:

    def test_ratify_request_refused(self):
        bridge = ScriptedBridge([
            json.dumps({"action": "gated", "errand": "ratify"}),
        ])
        t = Throne(llm=bridge)
        r = t.respond("ratify proposal xyz123")
        assert r.suggested_command is not None
        assert "ratify" in r.suggested_command
        assert "constitution" in r.answer.lower()
        assert r.actions_taken == []
        # Only one LLM call — synthesis is skipped for gated refusals
        assert len(bridge.calls) == 1

    def test_kindle_request_refused(self):
        bridge = ScriptedBridge([
            json.dumps({"action": "gated", "errand": "kindle"}),
        ])
        t = Throne(llm=bridge)
        r = t.respond("kindle my deployment")
        assert "invoke kindle" in r.suggested_command


class TestThroneRunErrands:

    def test_doctor_then_synthesize(self):
        bridge = ScriptedBridge([
            # Routing call: run doctor
            json.dumps({"action": "run", "errands": [
                {"name": "doctor", "argv": []}], "rationale": "user asked"}),
            # Synthesis call: plain answer
            "Everything looks fine; doctor reports a clean substrate.",
        ])
        t = Throne(llm=bridge)
        r = t.respond("how's everything?")
        assert "doctor" in r.actions_taken
        assert "errand:doctor" in r.sources
        assert len(bridge.calls) == 2, "run = routing + synthesis"

    def test_unknown_errand_synthesis_still_ok(self):
        # LLM proposes only an unknown errand → router filters → no
        # errands actually run → action falls back to direct answer
        bridge = ScriptedBridge([
            json.dumps({"action": "run", "errands": [
                {"name": "definitely-not-a-real-errand", "argv": []}]}),
        ])
        t = Throne(llm=bridge)
        r = t.respond("do something weird")
        # No errand executed; only one call (the routing one)
        assert r.actions_taken == []
        assert len(bridge.calls) == 1


class TestThroneRecording:

    def test_every_turn_recorded(self):
        bridge = ScriptedBridge([
            json.dumps({"action": "direct", "answer": "noted"}),
        ])
        t = Throne(llm=bridge)
        before = len(mnemosyne.recall("throne.turn"))
        t.respond("hello throne")
        after = len(mnemosyne.recall("throne.turn"))
        assert after == before + 1, "every turn must be recorded"

    def test_gated_refusal_also_recorded(self):
        bridge = ScriptedBridge([
            json.dumps({"action": "gated", "errand": "ratify"}),
        ])
        t = Throne(llm=bridge)
        before = len(mnemosyne.recall("throne.turn"))
        r = t.respond("just ratify it for me")
        after = len(mnemosyne.recall("throne.turn"))
        assert after == before + 1
        latest = mnemosyne.recall("throne.turn")[-1]
        assert latest.body.get("suggested_command")


class TestThroneBridgeError:

    def test_bridge_exception_does_not_crash(self):
        class BrokenBridge(LLMBridge):
            name = "broken"
            def call(self, **kw):
                raise RuntimeError("simulated network outage")
        t = Throne(llm=BrokenBridge())
        r = t.respond("hello")
        assert "could not reach" in r.answer.lower() or r.error
        # Even when the bridge errors, the turn IS recorded
        latest = mnemosyne.recall("throne.turn")[-1]
        assert latest.body.get("action_kind") == "none"


# ─────────────────────────────────────────────────────────────────────
# HTTP endpoint tests
# ─────────────────────────────────────────────────────────────────────


class TestThroneHTTPEndpoint:

    def test_dispatch_post_routes_to_throne(self):
        # We just test the dispatch_post wrapping; the inner respond()
        # uses the default bridge (echo when env unset). The body shape
        # is what we want to verify.
        from olympus.runtime.http_api import dispatch_post
        status, body = dispatch_post("/throne/turn",
                                      {"input": "hello"})
        assert status == 200
        assert "answer" in body
        assert "actions_taken" in body
        assert "bridge" in body

    def test_dispatch_post_missing_input(self):
        from olympus.runtime.http_api import dispatch_post
        status, body = dispatch_post("/throne/turn", {})
        assert status == 400
        assert "input" in body.get("error", "").lower()

    def test_dispatch_post_input_too_long(self):
        from olympus.runtime.http_api import dispatch_post
        status, body = dispatch_post("/throne/turn",
                                      {"input": "x" * 5000})
        assert status == 400

    def test_dispatch_post_unknown_route(self):
        from olympus.runtime.http_api import dispatch_post
        status, body = dispatch_post("/throne/elsewhere",
                                      {"input": "x"})
        assert status == 405
        assert "/throne/turn" in str(body.get("allowed_post_routes"))


# ─────────────────────────────────────────────────────────────────────
# Agora — throne is the landing page
# ─────────────────────────────────────────────────────────────────────


class TestAgoraThroneLanding:

    def test_throne_template_exists(self):
        from olympus.agora import _STATIC
        assert (_STATIC / "throne.html").exists()

    def test_throne_in_page_index(self):
        from olympus.agora import _PAGES
        # index.html must be sourced from throne.html
        as_dict = dict(_PAGES)
        assert as_dict["index.html"] == "throne.html"
        # dashboard.html remains reachable
        assert "dashboard.html" in as_dict

    def test_nav_includes_throne_brand(self):
        from olympus.agora import _render_nav
        nav = _render_nav()
        assert "Zeus" in nav or "Throne" in nav
        assert "dashboard" in nav

    def test_build_emits_throne_index(self, tmp_path):
        from olympus.agora import build
        out = build(out_dir=tmp_path)
        assert out.exists()
        assert out.name == "index.html"
        html = out.read_text(encoding="utf-8")
        assert "Zeus's Throne" in html or "Throne" in html
        # The Agora chat UI POSTs to /throne/turn
        assert "/throne/turn" in html

    def test_throne_url_substituted_with_real_host(self, tmp_path):
        """Regression: the throne page must have its API URL resolved
        at build time (not left as __API_BASE__ template, and not
        relying on AGORA.API which doesn't exist — the helper exposes
        AGORA.API_BASE). Browsers hit 'Failed to fetch' otherwise."""
        from olympus.agora import build
        out = build(out_dir=tmp_path, api_base="http://127.0.0.1:8765")
        html = out.read_text(encoding="utf-8")
        # The template placeholder must be substituted
        assert "__API_BASE__" not in html, \
            "template placeholder leaked into built HTML"
        # The URL must be present in resolved form
        assert "http://127.0.0.1:8765/throne/turn" in html, \
            "throne URL should be substituted with the real host"
        # And the broken-property bug must not return
        assert "AGORA.API +" not in html, \
            "AGORA.API doesn't exist; use AGORA.API_BASE or substitution"
