"""olympus.runtime.federation — Hermes between deployments.

In myth: Hermes traveled between Olympus, Earth, and the Underworld;
in later syncretism, between Greek and Egyptian pantheons. He was the
cross-realm messenger. In Olympus, federation is **Hermes connecting
one deployment to another**.

`federate(peer_url)` calls a peer Olympus instance's HTTP API to
fetch its status + wisdom, records the response under
`hermes.federation`. Both sides remain read-only on each other's
state — federation only exchanges digests.

This is the foundation for future multi-deployment coordination:
shared insights, alert propagation, distributed proposal review. The
labyrinth arc ships the bare bones.

Per Delphi 2026-05-18-labyrinth-arc.md.
"""
from __future__ import annotations

import json
import time
import urllib.error
import urllib.request
from dataclasses import dataclass, field, asdict
from typing import Any

from olympus.primordials.nyx import Nyx
from olympus.titans.mnemosyne import mnemosyne


_USER_AGENT = "Olympus-Federation/1.0"
_DEFAULT_TIMEOUT_SECONDS = 10.0


@dataclass
class PeerDigest:
    """What we learned about a federated peer."""
    peer_url: str
    fetched_at: str = ""
    reachable: bool = False
    status_code: int = 0
    peer_status: dict[str, Any] = field(default_factory=dict)
    peer_wisdom: dict[str, Any] = field(default_factory=dict)
    peer_specs: list[str] = field(default_factory=list)
    error: str = ""
    elapsed_ms: float = 0.0


def _get_json(url: str, *, timeout_seconds: float) -> tuple[int, Any, str]:
    """One JSON-expecting GET. Returns (status, parsed_or_None, error)."""
    headers = {"User-Agent": _USER_AGENT, "Accept": "application/json"}
    try:
        req = urllib.request.Request(url, headers=headers, method="GET")
        with urllib.request.urlopen(req, timeout=timeout_seconds) as resp:
            raw = resp.read(1024 * 1024)  # 1 MB cap per fetch
            try:
                return resp.status, json.loads(raw), ""
            except json.JSONDecodeError as exc:
                return resp.status, None, f"json-parse: {exc}"
    except urllib.error.HTTPError as exc:
        return exc.code, None, f"HTTPError {exc.code}: {exc.reason}"
    except urllib.error.URLError as exc:
        return 0, None, f"URLError: {exc.reason}"
    except Exception as exc:  # noqa: BLE001
        return 0, None, f"{type(exc).__name__}: {exc}"


def federate(peer_url: str, *,
             timeout_seconds: float = _DEFAULT_TIMEOUT_SECONDS,
             ) -> PeerDigest:
    """Fetch a peer's read-only digest. peer_url is the base URL of a
    running olympus-http-api (e.g., http://192.168.1.50:8765). Records
    the digest to Mnemosyne; never raises."""
    base = peer_url.rstrip("/")
    started = time.perf_counter()
    digest = PeerDigest(peer_url=base,
                        fetched_at=Nyx.now().isoformat())

    # Status — required
    status, payload, err = _get_json(f"{base}/status",
                                      timeout_seconds=timeout_seconds)
    digest.status_code = status
    if err:
        digest.error = err
    elif payload is not None:
        digest.peer_status = payload
        digest.reachable = True

    # Wisdom — best-effort
    if digest.reachable:
        _, wisdom, werr = _get_json(f"{base}/wisdom",
                                     timeout_seconds=timeout_seconds)
        if wisdom is not None:
            digest.peer_wisdom = wisdom
        elif werr:
            digest.error = (digest.error + f" wisdom: {werr}").strip()

        # Specs — best-effort
        _, specs_payload, _ = _get_json(f"{base}/specs",
                                          timeout_seconds=timeout_seconds)
        if specs_payload and isinstance(specs_payload, dict):
            digest.peer_specs = sorted(
                (specs_payload.get("specs") or {}).keys()
            )

    digest.elapsed_ms = (time.perf_counter() - started) * 1000.0

    mnemosyne.remember(
        kind="hermes.federation",
        actor="hermes:federation",
        summary=(f"federated {base}: reachable={digest.reachable} "
                 f"status={digest.status_code} "
                 f"({digest.elapsed_ms:.0f}ms)"
                 + (f" error={digest.error[:60]}" if digest.error else "")),
        **asdict(digest),
    )
    return digest


def known_peers(limit: int = 20) -> list[PeerDigest]:
    """Recent federation digests, newest first. Lets the operator see
    which peers we've talked to and when."""
    out: list[PeerDigest] = []
    for m in mnemosyne.recall("hermes.federation"):
        body = m.body or {}
        try:
            out.append(PeerDigest(
                peer_url=body.get("peer_url", ""),
                fetched_at=body.get("fetched_at", m.remembered_at),
                reachable=bool(body.get("reachable", False)),
                status_code=int(body.get("status_code", 0)),
                peer_status=body.get("peer_status") or {},
                peer_wisdom=body.get("peer_wisdom") or {},
                peer_specs=body.get("peer_specs") or [],
                error=body.get("error", ""),
                elapsed_ms=float(body.get("elapsed_ms", 0.0)),
            ))
        except (TypeError, ValueError):
            continue
    return list(reversed(out))[:limit]
