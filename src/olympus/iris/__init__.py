"""Iris — the rainbow-messenger.

In myth: Iris is the rainbow, the swift messenger who carries
communications between the gods and mortals. In Olympus: the static
dashboard that translates JSONL records into something an operator
can read at a glance.

Iris is deliberately humble:

    - no server (open the rendered HTML directly in any browser)
    - no framework (vanilla JS, no React, no Vue, no build step)
    - no inline scripts (CSP-clean; data is inline JSON, not code)
    - no opaque storage (every panel maps back to a JSONL kind)

The build step reads the substrate state (Mnemosyne kinds, Styx chain,
Argos pheromones, action queue) and renders one HTML file. Data is
embedded as a JSON island; the JS reads `window.OLYMPUS_DATA`. This
keeps Iris file:// safe — no CORS, no fetch, no server.

Per Delphi 2026-05-18-self-improvement-arc.md.
"""
from __future__ import annotations

import dataclasses
import json
import pathlib
from dataclasses import dataclass, field
from typing import Any

from olympus.primordials.gaia import root
from olympus.primordials.nyx import Nyx


# ─────────────────────────────────────────────────────────
# Snapshot — the data Iris embeds in the page
# ─────────────────────────────────────────────────────────


@dataclass
class IrisSnapshot:
    """Everything the dashboard needs, captured at build time."""
    built_at: str = ""
    olympus_version: str = ""
    sessions: list[dict[str, Any]] = field(default_factory=list)
    slice_heatmap: list[dict[str, Any]] = field(default_factory=list)
    prophecies: list[dict[str, Any]] = field(default_factory=list)
    proposals: list[dict[str, Any]] = field(default_factory=list)
    prometheus_passes: list[dict[str, Any]] = field(default_factory=list)
    prometheus_handlers: list[dict[str, Any]] = field(default_factory=list)
    styx: dict[str, Any] = field(default_factory=dict)
    counts: dict[str, int] = field(default_factory=dict)


# ─────────────────────────────────────────────────────────
# JSONL reader — tolerant of missing files
# ─────────────────────────────────────────────────────────


def _read_jsonl(path: pathlib.Path) -> list[dict[str, Any]]:
    """Read a JSONL file, skipping malformed lines. Returns [] if missing."""
    if not path.exists():
        return []
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    return rows


def _mn(kind: str) -> list[dict[str, Any]]:
    """Read a Mnemosyne kind. (Sanitization: matches Mnemosyne's _path.)"""
    safe = "".join(c for c in kind if c.isalnum() or c in "_-")
    return _read_jsonl(root.child("state", "mnemosyne", f"{safe}.jsonl"))


# ─────────────────────────────────────────────────────────
# Builder — assemble a snapshot from the substrate
# ─────────────────────────────────────────────────────────


def collect_snapshot() -> IrisSnapshot:
    """Read every state source Iris cares about and assemble the
    snapshot. Pure: no writes."""
    snap = IrisSnapshot()
    snap.built_at = Nyx.now().isoformat()
    try:
        from olympus import __version__ as _v
        snap.olympus_version = _v
    except Exception:  # noqa: BLE001
        snap.olympus_version = "unknown"

    # Sessions — last 50
    sessions = _mn("sessioncompleted")[-50:]
    snap.sessions = [
        {
            "ts": s.get("remembered_at", ""),
            "session_id": (s.get("body") or {}).get("session_id", ""),
            "summary": s.get("summary", ""),
            "hydra_findings": (s.get("body") or {}).get("hydra_findings", 0),
            "argos_pheromones": (s.get("body") or {}).get("argos_pheromones", 0),
            "proposals": (s.get("body") or {}).get("proposals_count", 0),
            "duration_ms": (s.get("body") or {}).get("duration_ms", 0),
            "prophecies_verified": (s.get("body") or {}).get("prophecies_verified", 0),
            "fury_alerts": (s.get("body") or {}).get("fury_alerts", []),
        }
        for s in sessions
    ]

    # Slice heatmap — count alert vs info per slice from hydra runs
    slice_counts: dict[str, dict[str, int]] = {}
    for m in _mn("hydrarun"):
        body = m.get("body") or {}
        findings = body.get("findings", [])
        for f in findings:
            if isinstance(f, dict):
                sl = f.get("slice", "—")
                sev = f.get("severity", "info")
                slot = slice_counts.setdefault(sl, {"alert": 0, "info": 0})
                if sev == "alert":
                    slot["alert"] += 1
                else:
                    slot["info"] += 1
    snap.slice_heatmap = [
        {"slice": sl, "alert": v["alert"], "info": v["info"]}
        for sl, v in sorted(
            slice_counts.items(),
            key=lambda kv: (-kv[1]["alert"], -kv[1]["info"], kv[0]),
        )
    ][:30]

    # Prophecies — last 50 verifications
    prophs = _mn("prophecyverified")[-50:]
    snap.prophecies = [
        {
            "ts": p.get("remembered_at", ""),
            "name": (p.get("body") or {}).get("prediction", ""),
            "accepted": (p.get("body") or {}).get("accepted"),
            "horizon": (p.get("body") or {}).get("horizon", ""),
        }
        for p in prophs
    ]

    # Proposals — combine ratified + rejected
    ratified = _mn("actionratified")
    rejected = _mn("actionrejected")
    proms = []
    for m in ratified[-50:]:
        body = m.get("body") or {}
        proms.append({
            "ts": m.get("remembered_at", ""),
            "summary": m.get("summary", ""),
            "outcome": "ratified",
            "drift": body.get("drift_signature", body.get("signature", "")),
        })
    for m in rejected[-50:]:
        body = m.get("body") or {}
        proms.append({
            "ts": m.get("remembered_at", ""),
            "summary": m.get("summary", ""),
            "outcome": "rejected",
            "drift": body.get("drift_signature", body.get("signature", "")),
        })
    proms.sort(key=lambda p: p["ts"], reverse=True)
    snap.proposals = proms[:50]

    # Prometheus — passes and per-handler outcomes
    snap.prometheus_passes = [
        {
            "ts": m.get("remembered_at", ""),
            "summary": m.get("summary", ""),
            "succeeded": (m.get("body") or {}).get("succeeded", 0),
            "invoked": (m.get("body") or {}).get("invoked", 0),
        }
        for m in _mn("prometheuspass")[-50:]
    ]
    snap.prometheus_handlers = [
        {
            "ts": m.get("remembered_at", ""),
            "actor": m.get("actor", ""),
            "handler": (m.get("body") or {}).get("handler", ""),
            "succeeded": (m.get("body") or {}).get("succeeded"),
            "summary": m.get("summary", ""),
        }
        for m in _mn("prometheushandler")[-50:]
    ]

    # Styx chain — totals + last oath
    styx_rows = _read_jsonl(root.child("state", "styx.jsonl"))
    snap.styx = {
        "total_oaths": len(styx_rows),
        "last_seq": styx_rows[-1].get("seq") if styx_rows else None,
        "last_hash": (styx_rows[-1].get("self_hash", "")[:16]
                      if styx_rows else ""),
        "last_ts": styx_rows[-1].get("sworn_at", "") if styx_rows else "",
    }

    # Top-line counts
    snap.counts = {
        "sessions": len(snap.sessions),
        "prophecies": len(snap.prophecies),
        "proposals": len(snap.proposals),
        "prometheus_passes": len(snap.prometheus_passes),
        "slices": len(snap.slice_heatmap),
        "oaths": snap.styx["total_oaths"],
    }
    return snap


# ─────────────────────────────────────────────────────────
# Renderer — assemble the static HTML file
# ─────────────────────────────────────────────────────────


_HERE = pathlib.Path(__file__).resolve().parent
_STATIC = _HERE / "static"


def render(snapshot: IrisSnapshot,
           out_path: pathlib.Path | None = None) -> pathlib.Path:
    """Render the dashboard into a single static HTML file.

    The template, CSS, and JS are inlined into the output so that the
    operator can open `index.html` directly without a server — file://
    works, no CORS, no fetch."""
    if out_path is None:
        out_dir = root.child("state", "iris")
        out_dir.mkdir(parents=True, exist_ok=True)
        out_path = out_dir / "index.html"

    template = (_STATIC / "template.html").read_text(encoding="utf-8")
    css = (_STATIC / "iris.css").read_text(encoding="utf-8")
    js = (_STATIC / "iris.js").read_text(encoding="utf-8")
    data_json = json.dumps(
        dataclasses.asdict(snapshot), default=str, ensure_ascii=False,
    )
    # Defuse any "</script>" that might appear in user-supplied summaries.
    # Inside a JSON-text <script>, the only sequence that ends the block is
    # "</"; splitting it neutralizes the breakout without altering the data.
    data_json = data_json.replace("</", "<\\/")

    html = (template
            .replace("/*__IRIS_CSS__*/", css)
            .replace("/*__IRIS_JS__*/", js)
            .replace("__IRIS_DATA__", data_json)
            .replace("__BUILT_AT__", snapshot.built_at)
            .replace("__OLYMPUS_VERSION__", snapshot.olympus_version))

    out_path.write_text(html, encoding="utf-8")
    return out_path


def build(open_in_browser: bool = False) -> pathlib.Path:
    """Full Iris build: collect + render. Optionally open in browser."""
    snap = collect_snapshot()
    out = render(snap)
    if open_in_browser:
        import webbrowser
        webbrowser.open(out.as_uri())
    return out
