"""tests/test_mcp_server.py — the Hermes-MCP arc.

Per Delphi 2026-05-19-hermes-mcp-arc.md.

All tests are in-process — we feed JSON-RPC requests directly into
`dispatch()` or simulate the stdio loop with StringIO. No subprocess.
"""
from __future__ import annotations

import io
import json

import pytest

from olympus.runtime.mcp_server import (
    dispatch, serve_stdio, probe,
    _safe_tools, _execute_errand,
    MCP_PROTOCOL_VERSION, SERVER_NAME,
    PARSE_ERROR, INVALID_REQUEST, METHOD_NOT_FOUND,
    TOOL_NOT_FOUND, TOOL_GATED,
)
from olympus.titans.mnemosyne import mnemosyne


# ─────────────────────────────────────────────────────────────────────
# initialize handshake
# ─────────────────────────────────────────────────────────────────────


def _req(method: str, *, params: dict | None = None,
          rid: int | str | None = 1) -> dict:
    out: dict = {"jsonrpc": "2.0", "method": method}
    if rid is not None:
        out["id"] = rid
    if params is not None:
        out["params"] = params
    return out


class TestInitialize:

    def test_shape(self):
        r = dispatch(_req("initialize"))
        assert r is not None
        assert r["jsonrpc"] == "2.0"
        result = r["result"]
        assert result["protocolVersion"] == MCP_PROTOCOL_VERSION
        assert result["serverInfo"]["name"] == SERVER_NAME
        assert "capabilities" in result
        assert "tools" in result["capabilities"]


class TestPing:

    def test_returns_empty_result(self):
        r = dispatch(_req("ping"))
        assert r["result"] == {}


# ─────────────────────────────────────────────────────────────────────
# tools/list
# ─────────────────────────────────────────────────────────────────────


class TestToolsList:

    def test_returns_all_safe_errands(self):
        from olympus.throne.router import SAFE_ERRANDS
        r = dispatch(_req("tools/list"))
        tools = r["result"]["tools"]
        names = {t["name"] for t in tools}
        assert names == set(SAFE_ERRANDS.keys())

    def test_excludes_gated_errands(self):
        from olympus.throne.router import GATED_ERRANDS
        r = dispatch(_req("tools/list"))
        names = {t["name"] for t in r["result"]["tools"]}
        # NO overlap with gated
        assert names.isdisjoint(set(GATED_ERRANDS.keys())), \
            "tools/list must not expose any GATED errand"

    def test_each_tool_has_input_schema(self):
        r = dispatch(_req("tools/list"))
        for t in r["result"]["tools"]:
            assert "inputSchema" in t
            schema = t["inputSchema"]
            assert schema["type"] == "object"
            assert "args" in schema["properties"]
            assert schema["additionalProperties"] is False

    def test_each_tool_has_description(self):
        r = dispatch(_req("tools/list"))
        for t in r["result"]["tools"]:
            assert t["description"]


# ─────────────────────────────────────────────────────────────────────
# tools/call — happy path
# ─────────────────────────────────────────────────────────────────────


class TestToolsCallHappy:

    def test_runs_doctor(self):
        r = dispatch(_req("tools/call", params={
            "name": "doctor", "arguments": {"args": ""}}))
        result = r["result"]
        assert "content" in result
        assert isinstance(result["content"], list)
        # First content block is text
        assert result["content"][0]["type"] == "text"
        # And the doctor output mentions known check names
        text = result["content"][0]["text"]
        assert "vault" in text or "styx" in text

    def test_records_to_mnemosyne(self):
        before = len(mnemosyne.recall("mcp.tool_call"))
        dispatch(_req("tools/call", params={
            "name": "blessing", "arguments": {"args": ""}}))
        after = len(mnemosyne.recall("mcp.tool_call"))
        assert after == before + 1

    def test_empty_args_works(self):
        # status takes no args; ensure empty string doesn't break
        r = dispatch(_req("tools/call", params={
            "name": "status", "arguments": {"args": ""}}))
        # status returns the tier table; check no error
        assert "result" in r


# ─────────────────────────────────────────────────────────────────────
# tools/call — gated + missing + bad
# ─────────────────────────────────────────────────────────────────────


class TestToolsCallSafety:

    def test_gated_errand_rejected(self):
        # ratify is GATED — must NOT be reachable
        r = dispatch(_req("tools/call", params={
            "name": "ratify", "arguments": {"args": "some-pid"}}))
        assert "error" in r
        assert r["error"]["code"] == TOOL_GATED
        assert "GATED" in r["error"]["message"] or \
               "gated" in r["error"]["message"].lower()

    def test_hephaestus_apply_gated(self):
        # hephaestus (apply) is GATED per arc 16
        r = dispatch(_req("tools/call", params={
            "name": "hephaestus", "arguments": {"args": "apply x"}}))
        assert "error" in r
        assert r["error"]["code"] == TOOL_GATED

    def test_unknown_tool_returns_error(self):
        r = dispatch(_req("tools/call", params={
            "name": "nonexistent-tool-xyz", "arguments": {}}))
        assert "error" in r
        assert r["error"]["code"] == TOOL_NOT_FOUND

    def test_missing_name_invalid_params(self):
        r = dispatch(_req("tools/call", params={"arguments": {}}))
        assert "error" in r


# ─────────────────────────────────────────────────────────────────────
# Misc protocol
# ─────────────────────────────────────────────────────────────────────


class TestProtocol:

    def test_unknown_method_not_found(self):
        r = dispatch(_req("nonexistent/method"))
        assert "error" in r
        assert r["error"]["code"] == METHOD_NOT_FOUND

    def test_notification_returns_none(self):
        # No `id` field → notification; dispatch returns None
        req = {"jsonrpc": "2.0", "method": "notifications/initialized"}
        assert dispatch(req) is None

    def test_unknown_notification_silent(self):
        # No id, unknown method → silent (no response)
        req = {"jsonrpc": "2.0", "method": "unknown/notification"}
        assert dispatch(req) is None

    def test_non_dict_request_invalid(self):
        r = dispatch("not a dict")  # type: ignore[arg-type]
        assert "error" in r
        assert r["error"]["code"] == INVALID_REQUEST

    def test_wrong_jsonrpc_version(self):
        r = dispatch({"jsonrpc": "1.0", "method": "ping", "id": 1})
        assert "error" in r
        assert r["error"]["code"] == INVALID_REQUEST

    def test_prompts_list_empty(self):
        r = dispatch(_req("prompts/list"))
        assert r["result"]["prompts"] == []

    def test_resources_list_empty(self):
        r = dispatch(_req("resources/list"))
        assert r["result"]["resources"] == []


# ─────────────────────────────────────────────────────────────────────
# Stdio loop
# ─────────────────────────────────────────────────────────────────────


class TestStdioLoop:

    def test_simple_session(self):
        """Init + tools/list + EOF — verify the loop exits cleanly
        and emits 2 responses."""
        in_buf = io.StringIO(
            json.dumps(_req("initialize")) + "\n"
            + json.dumps(_req("tools/list", rid=2)) + "\n"
        )
        out_buf = io.StringIO()
        rc = serve_stdio(stdin=in_buf, stdout=out_buf)
        assert rc == 0
        lines = [ln for ln in out_buf.getvalue().splitlines() if ln]
        assert len(lines) == 2
        # First is initialize response
        first = json.loads(lines[0])
        assert first["result"]["protocolVersion"] == MCP_PROTOCOL_VERSION

    def test_malformed_json_returns_parse_error(self):
        in_buf = io.StringIO(
            "this is not json\n"
            + json.dumps(_req("ping", rid=99)) + "\n"
        )
        out_buf = io.StringIO()
        rc = serve_stdio(stdin=in_buf, stdout=out_buf)
        assert rc == 0
        lines = [ln for ln in out_buf.getvalue().splitlines() if ln]
        # First response is parse-error; second is ping result
        first = json.loads(lines[0])
        assert "error" in first
        assert first["error"]["code"] == PARSE_ERROR
        second = json.loads(lines[1])
        assert second["result"] == {}

    def test_eof_clean_exit(self):
        in_buf = io.StringIO("")
        out_buf = io.StringIO()
        rc = serve_stdio(stdin=in_buf, stdout=out_buf)
        assert rc == 0
        assert out_buf.getvalue() == ""


# ─────────────────────────────────────────────────────────────────────
# CLI errand + probe
# ─────────────────────────────────────────────────────────────────────


class TestErrandAndProbe:

    def test_errand_registered(self):
        from olympus.cli import hermes
        assert "mcp" in hermes._errands

    def test_probe_returns_zero(self):
        rc = probe()
        assert rc == 0
