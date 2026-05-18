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
        "version": "1.1",
        "routes": [
            "GET /",
            "GET /healthz",
            "GET /status",
            "GET /wisdom",
            "GET /shoulders",
            "GET /panic",
            "GET /schemas",
            "GET /schemas/<kind>",
            "GET /specs",
            "GET /geometry",
            "GET /mnemosyne/<kind>?limit=N",
            "POST /proposals/raise",
        ],
        "read_only_writes": "POST /proposals/raise enters the Hephaestus "
                            "→ Momus → Delphi → Zeus pipeline; substrate "
                            "state is never mutated directly via HTTP",
    }


def _route_specs(_query: dict) -> tuple[int, dict]:
    from olympus.titans.themis import themis
    return 200, {"specs": themis.specs()}


def _route_geometry(_query: dict) -> tuple[int, dict]:
    """Plato's taxonomy + Pythagoras's harmony report."""
    from olympus.heroes.plato import plato
    from olympus.heroes.pythagoras import (PHI, PHI_INVERSE, PI, E,
                                              SQRT2, SQRT3, SQRT5,
                                              harmony)
    from olympus.titans.mnemosyne import mnemosyne
    cosmos = plato.cosmos()
    by_solid: dict[str, list[str]] = {}
    for figure, info in cosmos.items():
        by_solid.setdefault(info["solid"], []).append(figure)
    for k in by_solid:
        by_solid[k].sort()

    # Real substrate ratios — score each against the harmonic anchors
    ratifications = mnemosyne.recall("action.ratified")
    rejections = mnemosyne.recall("action.rejected")
    accepted = sum(1 for m in mnemosyne.recall("prophecy.verified")
                    if (m.body or {}).get("accepted") is True)
    rejected_p = sum(1 for m in mnemosyne.recall("prophecy.verified")
                      if (m.body or {}).get("accepted") is False)

    metrics: dict[str, dict[str, float | str]] = {}
    if (ratifications or rejections):
        denom = len(ratifications) + len(rejections)
        if denom > 0:
            ratio = len(ratifications) / denom
            h = harmony(ratio)
            metrics["ratification_rate"] = {
                "ratio": ratio,
                "nearest_anchor": h.nearest_anchor,
                "score": h.score,
            }
    if (accepted + rejected_p) > 0:
        ratio = accepted / (accepted + rejected_p)
        h = harmony(ratio)
        metrics["prophecy_acceptance"] = {
            "ratio": ratio,
            "nearest_anchor": h.nearest_anchor,
            "score": h.score,
        }

    return 200, {
        "constants": {
            "phi": PHI, "phi_inverse": PHI_INVERSE,
            "pi": PI, "e": E,
            "sqrt2": SQRT2, "sqrt3": SQRT3, "sqrt5": SQRT5,
        },
        "platonic_solids": [
            {"name": s.name, "vertices": s.vertices,
             "element": s.element, "function": s.function,
             "description": s.description,
             "members": by_solid.get(s.name, [])}
            for s in plato.solids()
        ],
        "harmony_metrics": metrics,
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


def _route_raise_proposal(body: dict) -> tuple[int, dict]:
    """POST /proposals/raise — the ONLY write surface. Accepts a JSON
    body and creates a Hephaestus-channel proposal under
    state/hephaestus/proposals/. The proposal then routes through the
    standard Momus → Delphi → Zeus pipeline.

    S3 (read-only observation) is preserved: this does NOT write to
    substrate state directly; it adds to the proposal queue, which is
    the same queue every internal source uses."""
    import json as _json
    import uuid
    from olympus.primordials.gaia import root
    from olympus.primordials.nyx import Nyx
    from olympus.titans.mnemosyne import mnemosyne

    # Validate required fields
    required = ("summary", "proposed_fix", "rationale", "raised_by")
    missing = [f for f in required if not body.get(f)]
    if missing:
        return 400, {"error": "missing required fields", "missing": missing,
                     "required": list(required)}
    risk = body.get("risk_class", "LOW")
    if risk not in {"LOW", "MEDIUM", "HIGH", "COMPOSITE"}:
        return 400, {"error": f"invalid risk_class {risk!r}",
                     "allowed": ["LOW", "MEDIUM", "HIGH", "COMPOSITE"]}

    pid = f"http-{Nyx.now().strftime('%Y%m%dT%H%M%SZ')}-{uuid.uuid4().hex[:8]}"
    proposal = {
        "id": pid,
        "drift_observed": (
            f"{body['raised_by']} raised via HTTP API: "
            f"{body['summary']}"
        ),
        "summary": body["summary"],
        "proposed_fix": body["proposed_fix"],
        "rationale": body["rationale"],
        "risk_class": risk,
        "raised_by": body["raised_by"],
        "raised_at": Nyx.now().isoformat(),
        "raised_via": "http-api",
    }
    proposals_dir = root.child("state", "hephaestus", "proposals")
    proposals_dir.mkdir(parents=True, exist_ok=True)
    target = proposals_dir / f"{pid}.json"
    target.write_text(_json.dumps(proposal, indent=2), encoding="utf-8")

    mnemosyne.remember(
        kind="http.proposal-raised",
        actor=f"http-api:{body['raised_by']}",
        summary=f"proposal {pid} raised via HTTP — {body['summary'][:80]}",
        proposal_id=pid,
        risk_class=risk,
        raised_by=body["raised_by"],
        proposal_path=str(target),
    )
    return 201, {
        "ok": True,
        "proposal_id": pid,
        "risk_class": risk,
        "next_step": "proposal will route through Momus → Delphi → Zeus",
        "proposal_path": str(target),
    }


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
    if path == "/specs":
        return _route_specs(query)
    if path == "/geometry":
        return _route_geometry(query)
    if path.startswith("/mnemosyne/"):
        kind = path[len("/mnemosyne/"):]
        if not kind:
            return 400, {"error": "specify /mnemosyne/<kind>"}
        return _route_mnemosyne(query, kind=kind)
    return 404, {"error": f"no route for {path!r}",
                 "routes": _route_root({})[1]["routes"]}


def dispatch_post(path: str, body: dict) -> tuple[int, dict]:
    """POST dispatch — exactly one route. The constitutional reason for
    keeping this tiny: every new write surface is a new attack surface."""
    if path == "/proposals/raise":
        return _route_raise_proposal(body)
    return 405, {"error": f"POST not allowed at {path!r}",
                 "allowed_post_routes": ["/proposals/raise"]}


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

    # The only path that accepts POST — every other POST returns 405
    # BEFORE we even try to parse the body. This keeps the API honestly
    # read-only-except-for-this-one-route.
    _POST_ALLOWED_PATHS = ("/proposals/raise",)

    def do_POST(self) -> None:  # noqa: N802
        """The only allowed POST routes go through dispatch_post; any
        other path returns 405 without inspecting the body."""
        try:
            parsed = urlparse(self.path)
            if parsed.path not in self._POST_ALLOWED_PATHS:
                self._write(405, {
                    "error": f"POST not allowed at {parsed.path!r}",
                    "allowed_post_routes": list(self._POST_ALLOWED_PATHS),
                })
                return
            length = int(self.headers.get("Content-Length", "0"))
            raw = self.rfile.read(length) if length > 0 else b""
            try:
                body = json.loads(raw) if raw else {}
            except json.JSONDecodeError as exc:
                self._write(400, {"error": f"body is not JSON: {exc}"})
                return
            if not isinstance(body, dict):
                self._write(400, {"error": "POST body must be a JSON object"})
                return
            status, payload = dispatch_post(parsed.path, body)
        except Exception as exc:  # noqa: BLE001
            status, payload = 500, {"error": f"{type(exc).__name__}: {exc}"}
        self._write(status, payload)

    def _method_not_allowed(self) -> None:
        self._write(405, {"error": "this API is read-only except for "
                                    "POST /proposals/raise; "
                                    "use `invoke` for other mutations"})

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
