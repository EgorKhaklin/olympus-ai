"""olympus.runtime.http_api — read-only JSON surface over localhost.

The substrate writes JSONL audit records to disk. Until now, the only
way to read them programmatically was to import olympus from Python.
This module exposes a localhost HTTP API so external observers
(dashboards, monitors, curl) can read substrate state without coupling
to the Python module.

Strictly **read-only**. S3 applies: external readers may query, never
command. Any mutation goes through `invoke`, which has the full
Hephaestus → Momus → Delphi pipeline.

Pure stdlib (`http.server`, `json`, `urllib.parse`). No framework.
No third-party dependency. Binds to `127.0.0.1` by default so it is
not reachable from the network; an operator can override.

Per Delphi 2026-05-18-recursion-arc.md.
"""
from __future__ import annotations

import json
import threading
from dataclasses import dataclass
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any
from urllib.parse import parse_qs, urlparse


DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 8765
SERVER_BANNER = "olympus-http-api/1.0"


# ─────────────────────────────────────────────────────────
# Route handlers — each returns (status_code, payload_dict)
# ─────────────────────────────────────────────────────────


def _route_root(_query: dict) -> tuple[int, dict]:
    return 200, {
        "service": "olympus-http-api",
        "version": "1.0",
        "routes": [
            "GET /",
            "GET /healthz",
            "GET /status",
            "GET /wisdom",
            "GET /shoulders",
            "GET /panic",
            "GET /schemas",
            "GET /schemas/<kind>",
            "GET /mnemosyne/<kind>?limit=N",
        ],
        "read_only": True,
    }


def _route_healthz(_query: dict) -> tuple[int, dict]:
    return 200, {"ok": True}


def _route_status(_query: dict) -> tuple[int, dict]:
    from olympus.olympians.hestia import hestia
    from olympus.muses.polyhymnia import polyhymnia
    from olympus.action import action_queue
    from olympus.titans.mnemosyne import mnemosyne
    from olympus.monsters.hydra import hydra
    from olympus.monsters.argos.colony import colony

    hymn = polyhymnia.hymn()
    hearth = hestia.hearth() if hestia.is_lit() else None
    return 200, {
        "hearth": {"lit": hearth is not None,
                   "name": hearth.name if hearth else None,
                   "vocation": hearth.vocation if hearth else None},
        "styx": {"total_oaths": hymn.total_oaths, "intact": hymn.intact},
        "hydra": {"heads": len(hydra.heads()),
                  "immortal": 1 if hydra.immortal() else 0},
        "argos": {"eyes": len(colony.eyes())},
        "actions": {
            "pending": len(action_queue.pending()),
            "delphi_pending": len(action_queue.delphi_pending()),
        },
        "sessions": {"total": len(mnemosyne.recall("session.completed"))},
    }


def _route_wisdom(_query: dict) -> tuple[int, dict]:
    import dataclasses as _dc
    from olympus.wisdom import wisdom as _w
    return 200, _dc.asdict(_w())


def _route_shoulders(_query: dict) -> tuple[int, dict]:
    import dataclasses as _dc
    from olympus.titans.atlas import atlas
    return 200, _dc.asdict(atlas.shoulders())


def _route_panic(_query: dict) -> tuple[int, dict]:
    import dataclasses as _dc
    from olympus.olympians.pan import pan
    return 200, _dc.asdict(pan.evaluate())


def _route_schemas(_query: dict, *,
                   kind: str | None = None) -> tuple[int, dict]:
    from olympus.titans.themis import themis
    schemas = themis.schemas()
    if kind is None:
        return 200, {"schemas": sorted(schemas.keys())}
    key = kind.replace(".", "-")
    if key not in schemas:
        return 404, {"error": f"unknown schema {kind!r}",
                     "available": sorted(schemas.keys())}
    return 200, schemas[key]


def _route_mnemosyne(query: dict, *, kind: str) -> tuple[int, dict]:
    from olympus.titans.mnemosyne import mnemosyne
    limit = int(query.get("limit", ["50"])[0])
    limit = max(1, min(limit, 500))
    records = mnemosyne.recall(kind)
    # Return newest-first, capped
    out = []
    for m in records[-limit:]:
        out.append({
            "kind": m.kind, "actor": m.actor, "summary": m.summary,
            "body": m.body, "remembered_at": m.remembered_at,
        })
    return 200, {
        "kind": kind, "total": len(records), "returned": len(out),
        "records": list(reversed(out)),
    }


# ─────────────────────────────────────────────────────────
# Dispatch table — declarative; lets tests assert coverage
# ─────────────────────────────────────────────────────────


def dispatch(path: str, query: dict[str, list[str]]) -> tuple[int, dict]:
    """Pure function — given a URL path + query dict, return
    (status, body). Used by both the HTTP handler and the tests."""
    if path == "/" or path == "":
        return _route_root(query)
    if path == "/healthz":
        return _route_healthz(query)
    if path == "/status":
        return _route_status(query)
    if path == "/wisdom":
        return _route_wisdom(query)
    if path == "/shoulders":
        return _route_shoulders(query)
    if path == "/panic":
        return _route_panic(query)
    if path == "/schemas":
        return _route_schemas(query)
    if path.startswith("/schemas/"):
        return _route_schemas(query, kind=path[len("/schemas/"):])
    if path.startswith("/mnemosyne/"):
        kind = path[len("/mnemosyne/"):]
        if not kind:
            return 400, {"error": "specify /mnemosyne/<kind>"}
        return _route_mnemosyne(query, kind=kind)
    return 404, {"error": f"no route for {path!r}",
                 "routes": _route_root({})[1]["routes"]}


# ─────────────────────────────────────────────────────────
# HTTP handler — single class, no framework
# ─────────────────────────────────────────────────────────


class OlympusHandler(BaseHTTPRequestHandler):
    server_version = SERVER_BANNER
    sys_version = ""  # don't leak python version in headers

    def _write(self, status: int, payload: Any) -> None:
        body = json.dumps(payload, default=str, indent=2).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        # Pre-emptive CORS so a local dashboard can curl us
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET")
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self) -> None:  # noqa: N802 (http.server API)
        try:
            parsed = urlparse(self.path)
            query = parse_qs(parsed.query)
            status, payload = dispatch(parsed.path, query)
        except Exception as exc:  # noqa: BLE001
            status, payload = 500, {"error": f"{type(exc).__name__}: {exc}"}
        self._write(status, payload)

    def _method_not_allowed(self) -> None:
        self._write(405, {"error": "this API is read-only; "
                                    "use `invoke` for mutations"})

    do_POST = _method_not_allowed
    do_PUT = _method_not_allowed
    do_DELETE = _method_not_allowed
    do_PATCH = _method_not_allowed

    def log_message(self, fmt: str, *args: Any) -> None:
        # Quiet by default — operator can wrap stderr if they want logs.
        return


# ─────────────────────────────────────────────────────────
# Server lifecycle — foreground + background
# ─────────────────────────────────────────────────────────


@dataclass
class _ServerHandle:
    """Returned by serve_background(). Call .stop() to shut down."""
    host: str
    port: int
    _server: ThreadingHTTPServer
    _thread: threading.Thread

    def stop(self, *, timeout: float = 2.0) -> None:
        self._server.shutdown()
        self._server.server_close()
        self._thread.join(timeout=timeout)

    def url(self, path: str = "") -> str:
        return f"http://{self.host}:{self.port}{path}"


def make_server(host: str = DEFAULT_HOST,
                port: int = DEFAULT_PORT) -> ThreadingHTTPServer:
    """Create (but don't start) the HTTP server. Useful for tests
    that want full control over the lifecycle."""
    return ThreadingHTTPServer((host, port), OlympusHandler)


def serve(host: str = DEFAULT_HOST,
          port: int = DEFAULT_PORT) -> None:
    """Foreground entry point. Blocks until SIGINT or close."""
    server = make_server(host, port)
    print(f"olympus-http-api listening on http://{host}:{port}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.shutdown()
        server.server_close()


def serve_background(host: str = DEFAULT_HOST,
                     port: int = 0) -> _ServerHandle:
    """Start the server on a background thread. port=0 → OS picks a
    free port; the handle exposes the chosen .port. Useful for tests."""
    server = make_server(host, port)
    chosen_port = server.server_address[1]
    thread = threading.Thread(
        target=server.serve_forever, daemon=True,
        name="olympus-http-api",
    )
    thread.start()
    return _ServerHandle(host=host, port=chosen_port,
                         _server=server, _thread=thread)
