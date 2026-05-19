"""Agora — the operator's interactive web UI.

In Greek antiquity: the agora (ἀγορά) was the public marketplace and
civic gathering place — where citizens conducted business, heard
oracles, and made decisions. It was where Athens *happened*.

In Olympus, Agora is the **operator's interactive web surface**.
Iris is the read-only dashboard (snapshot or live); Agora is where
the operator gathers their substrate's current state, sees what the
oracles are saying, and decides what to do next.

Per Delphi 2026-05-18-xenia-arc.md.

Design:
  - Vanilla HTML/CSS/JS — no framework, no build step (matches Iris)
  - All pages consume the read-only HTTP API (`invoke serve`)
  - Setup page is a *guide* showing CLI steps, not a replacement
    (the constitution-bearing actions stay on the CLI by design)
  - Five pages: dashboard, setup, doctor, today, agents
"""
from __future__ import annotations

import dataclasses
import json
import pathlib

from olympus.primordials.gaia import root
from olympus.primordials.nyx import Nyx


_HERE = pathlib.Path(__file__).resolve().parent
_STATIC = _HERE / "static"


# The page index — operator opens index.html to begin.
# Per Delphi 2026-05-19-throne-arc.md: throne is the landing page;
# the substrate-status dashboard moves to dashboard.html.
_PAGES: tuple[tuple[str, str], ...] = (
    ("index.html",      "throne.html"),
    ("dashboard.html",  "dashboard.html"),
    ("setup.html",      "setup.html"),
    ("doctor.html",     "doctor.html"),
    ("today.html",      "today.html"),
    ("agents.html",     "agents.html"),
    # Per Delphi 2026-05-19-eos-arc.md — Decade-surfacing pages
    ("spend.html",      "spend.html"),
    ("library.html",    "library.html"),
    ("watches.html",    "watches.html"),
    ("rituals.html",    "rituals.html"),
    ("replay.html",     "replay.html"),
    ("proposals.html",  "proposals.html"),
)


def build(out_dir: pathlib.Path | None = None,
          *,
          api_base: str = "http://127.0.0.1:8765",
          interval_seconds: float = 5.0) -> pathlib.Path:
    """Render Agora into `state/agora/`. Returns the index path.

    Operator opens `state/agora/index.html` in their browser; the
    pages poll the HTTP API every `interval_seconds`. Operator runs
    `invoke serve` first."""
    if out_dir is None:
        out_dir = root.child("state", "agora")
    out_dir.mkdir(parents=True, exist_ok=True)
    css = (_STATIC / "agora.css").read_text(encoding="utf-8")
    js = (_STATIC / "agora.js").read_text(encoding="utf-8")
    nav = _render_nav()
    built_at = Nyx.now().isoformat()

    for filename, template_name in _PAGES:
        template_path = _STATIC / template_name
        if not template_path.exists():
            continue
        html = template_path.read_text(encoding="utf-8")
        out_html = (html
                    .replace("/*__AGORA_CSS__*/", css)
                    .replace("/*__AGORA_JS__*/", js)
                    .replace("__AGORA_NAV__", nav)
                    .replace("__API_BASE__", api_base)
                    .replace("__INTERVAL_MS__",
                              str(int(interval_seconds * 1000)))
                    .replace("__BUILT_AT__", built_at))
        (out_dir / filename).write_text(out_html, encoding="utf-8")
    return out_dir / "index.html"


def _render_nav() -> str:
    """Top navigation rendered identically on every page.

    Per Delphi 2026-05-19-eos-arc.md — extended to 11 items grouped
    cleanly. Throne stays the brand-anchored landing page."""
    return (
        '<nav class="agora-nav">'
        '<a class="brand" href="index.html">👑 Zeus\'s Throne</a>'
        '<a href="dashboard.html">dashboard</a>'
        '<a href="today.html">today</a>'
        '<a href="doctor.html">doctor</a>'
        '<a href="spend.html">spend</a>'
        '<a href="library.html">library</a>'
        '<a href="watches.html">watches</a>'
        '<a href="rituals.html">rituals</a>'
        '<a href="replay.html">replay</a>'
        '<a href="proposals.html">proposals</a>'
        '<a href="agents.html">agents</a>'
        '<a href="setup.html">setup</a>'
        '</nav>'
    )


def open_in_browser(index_path: pathlib.Path) -> None:
    """Open the rendered Agora index in the operator's default browser."""
    import webbrowser
    webbrowser.open(index_path.as_uri())
