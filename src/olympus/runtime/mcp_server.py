"""olympus.runtime.mcp_server — minimal MCP server over stdio.

Per Delphi 2026-05-19-hermes-mcp-arc.md.

The Model Context Protocol (MCP) is Anthropic's standard for connecting
AI models to external tools. This module implements a minimal pure-Python
MCP server that exposes Olympus's SAFE_ERRANDS as MCP tools, so the
operator can call them from Claude Code (or any MCP-capable client)
without leaving the editor.

Transport: JSON-RPC 2.0 over line-delimited JSON on stdin/stdout.
Logging: stderr only (stdout is the protocol channel).
Constitutional whitelist: SAFE_ERRANDS — same set the Throne uses.
GATED ops are NEVER reachable through this surface.
"""
from __future__ import annotations

import io
import json
import re
import sys
import time
import traceback
from contextlib import redirect_stdout
from dataclasses import dataclass
from typing import Any, Callable, IO


# ─────────────────────────────────────────────────────────────────────
# Protocol constants
# ─────────────────────────────────────────────────────────────────────


MCP_PROTOCOL_VERSION = "2024-11-05"
SERVER_NAME = "olympus"
SERVER_VERSION = "0.1.0"


# JSON-RPC error codes (per spec)
PARSE_ERROR = -32700
INVALID_REQUEST = -32600
METHOD_NOT_FOUND = -32601
INVALID_PARAMS = -32602
INTERNAL_ERROR = -32603

# MCP-specific
TOOL_NOT_FOUND = -32001
TOOL_GATED = -32002


_TIMEOUT_S = 60


# ─────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────


def _log(msg: str) -> None:
    """Logging goes to stderr — stdout is the protocol channel."""
    print(f"[olympus-mcp] {msg}", file=sys.stderr, flush=True)


def _err_response(rid: Any, code: int, message: str,
                    data: dict | None = None) -> dict:
    err = {"code": code, "message": message}
    if data:
        err["data"] = data
    return {"jsonrpc": "2.0", "id": rid, "error": err}


def _ok_response(rid: Any, result: Any) -> dict:
    return {"jsonrpc": "2.0", "id": rid, "result": result}


# ─────────────────────────────────────────────────────────────────────
# Tool registry — built from SAFE_ERRANDS
# ─────────────────────────────────────────────────────────────────────


def _safe_tools() -> list[dict]:
    """Return the MCP tool descriptors for every SAFE_ERRAND."""
    from olympus.throne.router import SAFE_ERRANDS
    out: list[dict] = []
    for name, meta in sorted(SAFE_ERRANDS.items()):
        desc = (f"{meta.get('desc','')} "
                 f"(args: {meta.get('argv_hint','no args')})")
        out.append({
            "name": name,
            "description": desc,
            "inputSchema": {
                "type": "object",
                "properties": {
                    "args": {
                        "type": "string",
                        "description": (
                            "Arguments passed to the errand "
                            "(space-separated; tokenized server-side). "
                            "Empty string for no-arg errands."),
                    },
                },
                "additionalProperties": False,
            },
        })
    return out


def _is_safe(tool_name: str) -> bool:
    from olympus.throne.router import SAFE_ERRANDS
    return tool_name in SAFE_ERRANDS


def _is_gated(tool_name: str) -> bool:
    from olympus.throne.router import GATED_ERRANDS
    return tool_name in GATED_ERRANDS


# ─────────────────────────────────────────────────────────────────────
# Tool execution
# ─────────────────────────────────────────────────────────────────────


_ANSI_RX = re.compile(r"\x1b\[[0-9;]*m")


def _tokenize_args(args_str: str) -> list[str]:
    """Tokenize a string of args. We use shlex for shell-like quoting."""
    import shlex
    if not args_str:
        return []
    try:
        return shlex.split(args_str)
    except ValueError:
        # Malformed quoting → fall back to whitespace split
        return args_str.split()


def _execute_errand(tool_name: str, args_str: str) -> dict[str, Any]:
    """Run a SAFE errand; capture stdout; return the result structure
    used inside tools/call response."""
    started = time.perf_counter()
    result: dict[str, Any] = {
        "ok": False, "tool": tool_name,
        "exit_code": -1, "stdout": "",
        "error": "", "elapsed_ms": 0.0,
    }
    if not _is_safe(tool_name):
        if _is_gated(tool_name):
            result["error"] = (
                f"tool {tool_name!r} is constitution-GATED and cannot "
                "be invoked via MCP (S7). Run it from the CLI directly.")
        else:
            result["error"] = f"tool {tool_name!r} not found"
        return result
    argv = _tokenize_args(args_str)
    try:
        from olympus.cli import hermes
        errand_obj = hermes._errands.get(tool_name)  # type: ignore[attr-defined]
        if errand_obj is None:
            result["error"] = f"errand {tool_name!r} not registered"
            return result
        buf = io.StringIO()
        with redirect_stdout(buf):
            rc = errand_obj.fn(argv)
        result["exit_code"] = int(rc or 0)
        result["ok"] = (result["exit_code"] == 0)
        result["stdout"] = _ANSI_RX.sub("", buf.getvalue())[:8000]
    except SystemExit as exc:
        result["exit_code"] = int(exc.code or 0)
        result["ok"] = (result["exit_code"] == 0)
    except Exception as exc:  # noqa: BLE001
        result["error"] = f"{type(exc).__name__}: {exc}"
    result["elapsed_ms"] = (time.perf_counter() - started) * 1000.0

    # Audit
    try:
        from olympus.titans.mnemosyne import mnemosyne
        mnemosyne.remember(
            kind="mcp.tool_call",
            actor="mcp-server",
            summary=(f"{tool_name} ({len(argv)} arg(s)) "
                     f"rc={result['exit_code']} "
                     f"{result['elapsed_ms']:.0f}ms"
                     + (f" ERROR={result['error'][:60]}"
                        if result['error'] else "")),
            tool=tool_name,
            args=argv[:10],
            exit_code=result["exit_code"],
            elapsed_ms=result["elapsed_ms"],
            error=result["error"],
            stdout_head=result["stdout"][:512],
        )
    except Exception:  # noqa: BLE001
        pass
    return result


# ─────────────────────────────────────────────────────────────────────
# MCP method handlers
# ─────────────────────────────────────────────────────────────────────


def _handle_initialize(req: dict) -> dict:
    return _ok_response(req.get("id"), {
        "protocolVersion": MCP_PROTOCOL_VERSION,
        "serverInfo": {
            "name": SERVER_NAME,
            "version": SERVER_VERSION,
        },
        "capabilities": {
            "tools": {"listChanged": False},
            "prompts": {"listChanged": False},
            "resources": {"listChanged": False},
        },
    })


def _handle_tools_list(req: dict) -> dict:
    return _ok_response(req.get("id"), {"tools": _safe_tools()})


def _handle_tools_call(req: dict) -> dict:
    params = req.get("params") or {}
    name = str(params.get("name", "")).strip()
    arguments = params.get("arguments") or {}
    if not name:
        return _err_response(req.get("id"), INVALID_PARAMS,
                              "missing 'name' in tools/call params")
    args_str = str(arguments.get("args", ""))
    if not _is_safe(name):
        # Be explicit about WHY: gated vs not-found
        if _is_gated(name):
            return _err_response(
                req.get("id"), TOOL_GATED,
                (f"tool {name!r} is constitution-GATED; "
                 "MCP only exposes SAFE_ERRANDS. Run it from the "
                 "CLI directly."))
        return _err_response(req.get("id"), TOOL_NOT_FOUND,
                              f"tool {name!r} not found")
    exec_result = _execute_errand(name, args_str)
    content_blocks: list[dict] = []
    if exec_result["stdout"]:
        content_blocks.append({
            "type": "text", "text": exec_result["stdout"]})
    if exec_result["error"]:
        content_blocks.append({
            "type": "text",
            "text": f"\n[error] {exec_result['error']}"})
    if not content_blocks:
        content_blocks.append({"type": "text", "text": "(no output)"})
    return _ok_response(req.get("id"), {
        "content": content_blocks,
        "isError": not exec_result["ok"],
    })


def _handle_ping(req: dict) -> dict:
    return _ok_response(req.get("id"), {})


def _handle_prompts_list(req: dict) -> dict:
    return _ok_response(req.get("id"), {"prompts": []})


def _handle_resources_list(req: dict) -> dict:
    return _ok_response(req.get("id"), {"resources": []})


_METHOD_HANDLERS: dict[str, Callable[[dict], dict]] = {
    "initialize": _handle_initialize,
    "tools/list": _handle_tools_list,
    "tools/call": _handle_tools_call,
    "ping": _handle_ping,
    "prompts/list": _handle_prompts_list,
    "resources/list": _handle_resources_list,
}


# ─────────────────────────────────────────────────────────────────────
# Dispatch
# ─────────────────────────────────────────────────────────────────────


def dispatch(req: dict) -> dict | None:
    """Route one parsed JSON-RPC request to its handler. Returns the
    response dict, OR None if the request was a notification (no id)."""
    if not isinstance(req, dict):
        return _err_response(None, INVALID_REQUEST,
                              "request must be a JSON object")
    if req.get("jsonrpc") != "2.0":
        return _err_response(req.get("id"), INVALID_REQUEST,
                              "jsonrpc must be '2.0'")
    method = req.get("method")
    if not isinstance(method, str):
        return _err_response(req.get("id"), INVALID_REQUEST,
                              "missing 'method'")
    # Notifications (no id field) — do not respond
    is_notification = "id" not in req
    handler = _METHOD_HANDLERS.get(method)
    if handler is None:
        # `initialized` is a notification we accept silently
        if method == "notifications/initialized" or method == "initialized":
            return None
        if is_notification:
            return None
        return _err_response(req.get("id"), METHOD_NOT_FOUND,
                              f"method {method!r} not found")
    try:
        response = handler(req)
    except Exception as exc:  # noqa: BLE001
        _log(f"handler raised: {exc}\n{traceback.format_exc()}")
        return _err_response(req.get("id"), INTERNAL_ERROR,
                              f"{type(exc).__name__}: {exc}")
    if is_notification:
        return None
    return response


# ─────────────────────────────────────────────────────────────────────
# Stdio loop
# ─────────────────────────────────────────────────────────────────────


def serve_stdio(*, stdin: IO[str] | None = None,
                 stdout: IO[str] | None = None) -> int:
    """Run the MCP server on stdin/stdout (the standard transport).
    Returns exit code 0 on clean EOF, non-zero on fatal error.

    For tests, pass in StringIO objects."""
    sin = stdin if stdin is not None else sys.stdin
    sout = stdout if stdout is not None else sys.stdout
    _log(f"server starting ({SERVER_NAME} {SERVER_VERSION}; "
         f"protocol {MCP_PROTOCOL_VERSION})")
    line_count = 0
    while True:
        try:
            line = sin.readline()
        except KeyboardInterrupt:
            _log("interrupted; clean exit")
            return 0
        if not line:
            _log(f"stdin EOF after {line_count} line(s); clean exit")
            return 0
        line = line.strip()
        if not line:
            continue
        line_count += 1
        try:
            req = json.loads(line)
        except json.JSONDecodeError as exc:
            resp = _err_response(None, PARSE_ERROR,
                                  f"invalid JSON: {exc}")
            sout.write(json.dumps(resp, default=str) + "\n")
            sout.flush()
            continue
        # Batch support
        if isinstance(req, list):
            batch_out: list[dict] = []
            for item in req:
                r = dispatch(item)
                if r is not None:
                    batch_out.append(r)
            if batch_out:
                sout.write(json.dumps(batch_out, default=str) + "\n")
                sout.flush()
            continue
        resp = dispatch(req)
        if resp is not None:
            sout.write(json.dumps(resp, default=str) + "\n")
            sout.flush()


def probe() -> int:
    """One-shot: print server info + tool list to stderr; exit 0.
    Useful for operator-debugging."""
    tools = _safe_tools()
    _log(f"server={SERVER_NAME} {SERVER_VERSION} "
         f"protocol={MCP_PROTOCOL_VERSION}")
    _log(f"tools available ({len(tools)}):")
    for t in tools:
        _log(f"  {t['name']:<14} {t['description'][:80]}")
    return 0


__all__ = [
    "serve_stdio", "probe", "dispatch",
    "MCP_PROTOCOL_VERSION", "SERVER_NAME", "SERVER_VERSION",
    "_safe_tools", "_execute_errand",  # exposed for tests
]
