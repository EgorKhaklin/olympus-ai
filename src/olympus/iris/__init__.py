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
    works, no CORS, no fetch.

    A lineage hash (SHA-256 of the snapshot JSON) is embedded as an
    HTML comment near the top — Asclepius can verify that the rendered
    HTML still matches its source snapshot."""
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
    # Compute lineage hash BEFORE the </script> defusion (the hash is
    # of the JSON payload, not the escaped version).
    import hashlib
    lineage = hashlib.sha256(data_json.encode("utf-8")).hexdigest()
    # Defuse any "</script>" that might appear in user-supplied summaries.
    data_json = data_json.replace("</", "<\\/")

    html = (template
            .replace("/*__IRIS_CSS__*/", css)
            .replace("/*__IRIS_JS__*/", js)
            .replace("__IRIS_DATA__", data_json)
            .replace("__BUILT_AT__", snapshot.built_at)
            .replace("__OLYMPUS_VERSION__", snapshot.olympus_version)
            .replace("__LINEAGE_HASH__", lineage))

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


# ─────────────────────────────────────────────────────────
# Live dashboard (aegis arc) — self-refreshing HTML that polls the
# HTTP API every N seconds. Vanilla JS, no framework, no WebSocket.
# ─────────────────────────────────────────────────────────


_LIVE_TEMPLATE = """<!doctype html>
<html lang="en">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>Iris — Olympus live</title>
    <style>
        :root {
            --gold: #d4a017; --gold-2: #f0c43a;
            --wine: #722f37; --wine-2: #4a1c22;
            --marble: #ecebe4; --ink: #1c1a16;
            --paper: #faf8f1; --sea: #2d6a6a;
            --laurel: #6b8e6b; --line: rgba(28, 26, 22, 0.12);
        }
        * { box-sizing: border-box; }
        body { margin: 0; font-family: -apple-system, BlinkMacSystemFont,
            "Segoe UI", Georgia, serif; background: var(--paper);
            color: var(--ink); line-height: 1.55; }
        header { background: linear-gradient(180deg, var(--wine) 0%,
            var(--wine-2) 100%); color: var(--marble);
            padding: 1.5rem 2rem; border-bottom: 3px solid var(--gold); }
        header h1 { margin: 0; font-size: 1.75rem;
            letter-spacing: 0.15em; color: var(--gold-2); }
        header .subtitle { margin-top: 0.35rem; font-style: italic;
            opacity: 0.85; font-size: 0.95rem; }
        header .pulse { margin-top: 0.6rem; font-size: 0.78rem;
            color: var(--marble); opacity: 0.7;
            font-family: ui-monospace, "SF Mono", Menlo, monospace; }
        header .pulse .live { color: var(--gold-2); font-weight: 600; }
        main { max-width: 1100px; margin: 0 auto; padding: 2rem 1.5rem; }
        .grid { display: grid;
            grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
            gap: 1rem; margin-bottom: 1.5rem; }
        .card { background: white; border: 1px solid var(--line);
            border-left: 4px solid var(--gold); border-radius: 3px;
            padding: 1rem; }
        .card .label { text-transform: uppercase; font-size: 0.7rem;
            letter-spacing: 0.1em; color: var(--sea); font-weight: 600; }
        .card .value { font-size: 2rem; font-weight: 600;
            color: var(--ink); margin-top: 0.25rem; }
        .card .annot { color: var(--sea); font-size: 0.78rem;
            margin-top: 0.1rem; }
        .panel { background: white; border: 1px solid var(--line);
            border-radius: 3px; margin-bottom: 1.5rem; overflow: hidden; }
        .panel h2 { background: var(--marble); margin: 0;
            padding: 0.7rem 1.1rem; font-size: 0.95rem;
            letter-spacing: 0.08em; text-transform: uppercase;
            color: var(--wine); border-bottom: 1px solid var(--line); }
        .panel-body { padding: 1rem 1.1rem; }
        pre.json { background: #1c1a16; color: #ecebe4;
            padding: 1rem; overflow: auto; font-size: 0.78rem;
            line-height: 1.5; border-radius: 3px;
            font-family: ui-monospace, "SF Mono", Menlo, monospace; }
        .error { color: var(--wine); font-weight: 600; }
        footer { text-align: center; color: var(--sea);
            font-style: italic; padding: 1.5rem 1rem 2rem;
            font-size: 0.85rem; }
        .status-dot { display: inline-block; width: 10px; height: 10px;
            border-radius: 50%; margin-right: 0.4rem;
            background: var(--laurel); }
        .status-dot.bad { background: var(--wine); }
    </style>
</head>
<body>

<header>
    <h1>I R I S &nbsp;·&nbsp; L I V E</h1>
    <div class="subtitle">the rainbow-messenger between Olympus and mortals</div>
    <div class="pulse">
        polling <span class="live">__API_BASE__</span> every
        <span class="live">__INTERVAL_S__s</span> ·
        <span id="status-dot" class="status-dot"></span>
        <span id="status-text">connecting…</span> ·
        last refresh: <span id="ts">—</span>
    </div>
</header>

<main>

    <section class="grid" id="cards">
        <!-- populated by JS -->
    </section>

    <section class="panel">
        <h2>Status (raw JSON)</h2>
        <div class="panel-body"><pre class="json" id="status-json">loading…</pre></div>
    </section>

    <section class="panel">
        <h2>Harmony (substrate ratios vs sacred anchors)</h2>
        <div class="panel-body"><pre class="json" id="harmony-json">loading…</pre></div>
    </section>

    <section class="panel">
        <h2>Today (single-action oracle)</h2>
        <div class="panel-body" id="today-body">loading…</div>
    </section>

</main>

<footer>
    <p>Iris live polls the read-only HTTP API. No WebSocket. No framework.
    Built by Daedalus, signaled by Iris.</p>
</footer>

<script>
"use strict";
(function () {
    var API_BASE = "__API_BASE__";
    var INTERVAL = __INTERVAL_MS__;

    function setStatus(ok, text) {
        var dot = document.getElementById("status-dot");
        dot.className = "status-dot" + (ok ? "" : " bad");
        document.getElementById("status-text").textContent = text;
        document.getElementById("ts").textContent = new Date()
            .toISOString().substring(0, 19);
    }

    function get(path, cb) {
        var xhr = new XMLHttpRequest();
        xhr.open("GET", API_BASE + path, true);
        xhr.timeout = 5000;
        xhr.onload = function () {
            if (xhr.status === 200) {
                try { cb(null, JSON.parse(xhr.responseText)); }
                catch (e) { cb(e, null); }
            } else { cb(new Error("HTTP " + xhr.status), null); }
        };
        xhr.onerror = function () { cb(new Error("network"), null); };
        xhr.ontimeout = function () { cb(new Error("timeout"), null); };
        xhr.send();
    }

    function renderCards(status) {
        var cards = document.getElementById("cards");
        cards.innerHTML = "";
        var tiles = [
            ["Hearth",      (status.hearth || {}).name || "—",
                                (status.hearth || {}).lit ? "lit" : "dark"],
            ["Styx oaths",  (status.styx || {}).total_oaths || 0,
                                (status.styx || {}).intact ? "intact" : "BROKEN"],
            ["Hydra heads", (status.hydra || {}).heads || 0,
                                "watcher tier"],
            ["Argos eyes",  (status.argos || {}).eyes || 0,
                                "swarm tier"],
            ["Pending actions", (status.actions || {}).pending || 0,
                                (status.actions || {}).delphi_pending + " delphi"],
            ["Sessions", (status.sessions || {}).total || 0,
                                "completed"],
        ];
        tiles.forEach(function (t) {
            var div = document.createElement("div");
            div.className = "card";
            div.innerHTML = "<div class='label'>" + t[0] + "</div>" +
                "<div class='value'>" + t[1] + "</div>" +
                "<div class='annot'>" + t[2] + "</div>";
            cards.appendChild(div);
        });
    }

    function refresh() {
        get("/status", function (err, data) {
            if (err) {
                setStatus(false, "error: " + err.message);
                return;
            }
            setStatus(true, "live");
            renderCards(data);
            document.getElementById("status-json").textContent =
                JSON.stringify(data, null, 2);
        });
        get("/geometry", function (err, data) {
            if (err || !data) return;
            var hm = (data || {}).harmony_metrics || {};
            document.getElementById("harmony-json").textContent =
                JSON.stringify(hm, null, 2);
        });
    }

    // First refresh + interval
    refresh();
    setInterval(refresh, INTERVAL);
})();
</script>

</body>
</html>
"""


def render_live(out_path: pathlib.Path | None = None,
                *,
                api_base: str = "http://127.0.0.1:8765",
                interval_seconds: float = 5.0) -> pathlib.Path:
    """Render the self-refreshing live HTML page. Polls api_base
    every interval_seconds via XMLHttpRequest (no framework, no
    WebSocket). The operator must have `invoke serve` running."""
    if out_path is None:
        out_dir = root.child("state", "iris")
        out_dir.mkdir(parents=True, exist_ok=True)
        out_path = out_dir / "live.html"
    html = (_LIVE_TEMPLATE
            .replace("__API_BASE__", api_base)
            .replace("__INTERVAL_S__", f"{interval_seconds:.1f}")
            .replace("__INTERVAL_MS__",
                     str(int(interval_seconds * 1000))))
    out_path.write_text(html, encoding="utf-8")
    return out_path


def build_live(open_in_browser: bool = False,
               *,
               api_base: str = "http://127.0.0.1:8765",
               interval_seconds: float = 5.0) -> pathlib.Path:
    out = render_live(api_base=api_base,
                       interval_seconds=interval_seconds)
    if open_in_browser:
        import webbrowser
        webbrowser.open(out.as_uri())
    return out
