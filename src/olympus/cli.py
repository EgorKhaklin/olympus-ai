"""olympus.cli — the single entry point.

Hermes dispatches every named errand. The CLI is a thin wrapper around
the Python API; everything `invoke` does, you can do from Python.

Global flags (place before any errand):
  --json        emit machine-readable output where supported
  --quiet       suppress non-essential output
  --no-color    disable ANSI colors

Use `invoke help <errand>` for per-errand detail.
"""
from __future__ import annotations

import json as _json
import os as _os
import pathlib
import sys
from typing import Any

# Honor global flags before any color modules load
_argv_raw = list(sys.argv[1:])
_GLOBAL_FLAGS: dict[str, bool] = {"json": False, "quiet": False, "no_color": False}
_filtered: list[str] = []
for _a in _argv_raw:
    if _a == "--json":
        _GLOBAL_FLAGS["json"] = True
    elif _a == "--quiet":
        _GLOBAL_FLAGS["quiet"] = True
    elif _a == "--no-color":
        _GLOBAL_FLAGS["no_color"] = True
        _os.environ["NO_COLOR"] = "1"
    else:
        _filtered.append(_a)
sys.argv = [sys.argv[0]] + _filtered


from olympus.olympians.hermes import hermes  # noqa: E402
from olympus.olympians.aphrodite import aphrodite  # noqa: E402
from olympus.graces.aglaia import aglaia  # noqa: E402
from olympus.primordials.gaia import root as _gaia_root  # noqa: E402


def _maybe_json(data: Any, fallback_text: str) -> int:
    if _GLOBAL_FLAGS["json"]:
        sys.stdout.write(_json.dumps(data, default=str, indent=2) + "\n")
    elif not _GLOBAL_FLAGS["quiet"]:
        sys.stdout.write(fallback_text + "\n")
    return 0


# ─────────────────────────────────────────────────────────────────────
# Substrate primitives — register first so help lists them up top
# ─────────────────────────────────────────────────────────────────────


@hermes.register("prime", "session prime — Odysseus takes bearing")
def _prime(_argv: list[str]) -> int:
    from olympus.titans.rhea import rhea
    from olympus.olympians.hestia import hestia
    from olympus.heroes.odysseus import odysseus
    rhea.bring_forth()
    if not _GLOBAL_FLAGS["quiet"]:
        print(aglaia.section("Olympus — session prime"))
    if not hestia.is_lit():
        print(aphrodite.wine_dark(
            "hearth is unlit — run `invoke kindle <name> <vocation>` first"
        ))
        return 1
    h = hestia.hearth()
    bearing = odysseus.take_bearing()
    data = {
        "hearth": {"name": h.name, "vocation": h.vocation, "kindled_at": h.kindled_at},
        "last_memory": bearing.last_summary,
        "last_kind": bearing.last_kind,
        "total_memories": bearing.total_memories,
    }
    text = (
        aphrodite.laurel(f"hearth lit as '{h.name}' (kindled {h.kindled_at})") + "\n"
        + aglaia.murmur(f"  vocation: {h.vocation}") + "\n"
        + (aphrodite.lightning(f"last memory: {bearing.last_kind} — {bearing.last_summary}")
           if bearing.last_summary else aglaia.murmur("  no prior memories")) + "\n"
        + aglaia.murmur(f"  total memories: {bearing.total_memories}")
    )
    return _maybe_json(data, text)


@hermes.register("status", "one-line health snapshot of the substrate")
def _status(_argv: list[str]) -> int:
    from olympus.olympians.hestia import hestia
    from olympus.muses.polyhymnia import polyhymnia
    from olympus.action import action_queue
    from olympus.titans.mnemosyne import mnemosyne
    from olympus.monsters.hydra import hydra
    from olympus.monsters.argos.colony import colony

    hymn = polyhymnia.hymn()
    hearth = hestia.hearth() if hestia.is_lit() else None
    pending = action_queue.pending()
    delphi = action_queue.delphi_pending()
    sessions = mnemosyne.recall("session.completed")

    data = {
        "hearth": {"lit": hearth is not None,
                   "name": hearth.name if hearth else None,
                   "vocation": hearth.vocation if hearth else None},
        "styx": {"total_oaths": hymn.total_oaths, "intact": hymn.intact},
        "hydra": {"heads": len(hydra.heads()),
                  "mortal": hydra.mortal_count(),
                  "immortal": 1 if hydra.immortal() else 0},
        "argos": {"eyes": len(colony.eyes())},
        "actions": {"pending": len(pending), "delphi_pending": len(delphi)},
        "sessions": {"total": len(sessions)},
    }
    rows = [
        ("hearth",   "lit" if hearth else "DARK",
                     f"{hearth.name}" if hearth else "—"),
        ("styx",     f"{hymn.total_oaths} oaths",
                     "intact" if hymn.intact else "BROKEN"),
        ("hydra",    f"{len(hydra.heads())} heads",
                     f"{hydra.mortal_count()} mortal + 1 immortal"),
        ("argos",    f"{len(colony.eyes())} eyes", "registered"),
        ("actions",  f"{len(pending)} queued",
                     f"{len(delphi)} delphi-pending"),
        ("sessions", f"{len(sessions)} total", "in Mnemosyne"),
    ]
    text = aphrodite.table(("tier", "count", "state"), rows)
    return _maybe_json(data, text)


@hermes.register("version", "show Olympus version")
def _version(_argv: list[str]) -> int:
    from olympus import __version__
    if _GLOBAL_FLAGS["json"]:
        print(_json.dumps({"version": __version__}))
    else:
        print(f"olympus {__version__}")
    return 0


@hermes.register("list", "list named modules under a tier — list [tier]")
def _list(argv: list[str]) -> int:
    import pathlib as _pl
    tiers = ("primordials", "titans", "olympians", "underworld",
             "fates", "furies", "graces", "muses", "heroes", "monsters")
    requested = argv[0] if argv else None
    rows: list[tuple[str, str]] = []
    src_root = _gaia_root.child("src", "olympus")
    for t in tiers:
        if requested and t != requested:
            continue
        tier_path = src_root / t
        if not tier_path.is_dir():
            continue
        for f in sorted(tier_path.rglob("*.py")):
            if f.name.startswith("_") or f.name == "base.py":
                continue
            rel = f.relative_to(src_root).as_posix()[:-3]
            rows.append((t, rel))
    if _GLOBAL_FLAGS["json"]:
        print(_json.dumps([{"tier": t, "module": m} for t, m in rows], indent=2))
        return 0
    print(aphrodite.table(("tier", "module"), rows))
    return 0


@hermes.register("describe", "show a god's docstring and interface — describe <tier.god>")
def _describe(argv: list[str]) -> int:
    import importlib
    import inspect
    if not argv:
        print("usage: invoke describe <tier.god>  (e.g., olympians.zeus)")
        return 2
    name = argv[0]
    if not name.startswith("olympus."):
        name = f"olympus.{name}"
    try:
        mod = importlib.import_module(name)
    except ImportError as exc:
        print(aphrodite.wine_dark(f"cannot import {name!r}: {exc}"))
        return 1
    doc = (mod.__doc__ or "(no docstring)").strip()
    print(aglaia.section(f"{name}"))
    print(doc)
    print()
    print(aglaia.subhead("public interface"))
    for n, obj in inspect.getmembers(mod):
        if n.startswith("_") or inspect.ismodule(obj):
            continue
        kind = "class" if inspect.isclass(obj) else (
            "func" if inspect.isfunction(obj) else "var"
        )
        print(f"  {kind:5s}  {n}")
    return 0


@hermes.register("history", "last N sessions — history [N=10]")
def _history(argv: list[str]) -> int:
    from olympus.titans.mnemosyne import mnemosyne
    n = int(argv[0]) if argv else 10
    sessions = mnemosyne.recall("session.completed")[-n:]
    if not sessions:
        print(aglaia.murmur("  no sessions in Mnemosyne yet"))
        return 0
    data = [{"ts": m.remembered_at, "summary": m.summary,
             "session_id": m.body.get("session_id")} for m in sessions]
    if _GLOBAL_FLAGS["json"]:
        print(_json.dumps(data, indent=2))
        return 0
    rows = [(m.remembered_at[:19],
             m.body.get("session_id", "")[:16],
             m.summary[:80]) for m in sessions]
    print(aphrodite.table(("when", "session", "summary"), rows))
    return 0


@hermes.register("bring-forth", "Rhea ensures all required directories exist")
def _bring_forth(_argv: list[str]) -> int:
    from olympus.titans.rhea import rhea
    statuses = rhea.bring_forth()
    if _GLOBAL_FLAGS["json"]:
        print(_json.dumps(statuses, indent=2))
        return 0
    rows = [(rel, status) for rel, status in statuses.items()]
    print(aphrodite.table(("directory", "status"), rows))
    return 0


@hermes.register("kindle", "Hestia lights the hearth — kindle <name> <vocation>")
def _kindle(argv: list[str]) -> int:
    from olympus.olympians.hestia import hestia
    if len(argv) < 2:
        print("usage: invoke kindle <name> <vocation>")
        return 2
    name, vocation = argv[0], " ".join(argv[1:])
    try:
        h = hestia.kindle(name=name, vocation=vocation)
    except RuntimeError as exc:
        print(aphrodite.wine_dark(str(exc)))
        return 1
    print(aphrodite.laurel(f"kindled '{h.name}' at {h.kindled_at}"))
    print(aglaia.murmur(f"  seal: {h.seal}"))
    return 0


@hermes.register("remember", "Mnemosyne — remember <kind> <actor> <summary>")
def _remember(argv: list[str]) -> int:
    from olympus.titans.mnemosyne import mnemosyne
    if len(argv) < 3:
        print("usage: invoke remember <kind> <actor> <summary>")
        return 2
    kind, actor = argv[0], argv[1]
    summary = " ".join(argv[2:])
    m = mnemosyne.remember(kind=kind, actor=actor, summary=summary)
    print(aphrodite.laurel(f"remembered: {m.kind} / {m.actor} / {m.summary}"))
    return 0


@hermes.register("swear", "Styx — swear <by> <statement>")
def _swear(argv: list[str]) -> int:
    from olympus.underworld.styx import swear
    if len(argv) < 2:
        print("usage: invoke swear <by> <statement>")
        return 2
    by = argv[0]
    statement = " ".join(argv[1:])
    o = swear(sworn_by=by, statement=statement)
    print(aphrodite.laurel(f"sworn — seq={o.seq} hash={o.self_hash[:12]}"))
    return 0


@hermes.register("verify", "Tisiphone — verify Styx chain integrity")
def _verify(_argv: list[str]) -> int:
    from olympus.furies.tisiphone import tisiphone
    v = tisiphone.verify_styx()
    if v.intact:
        print(aphrodite.laurel(v.detail))
        return 0
    print(aphrodite.wine_dark(v.detail))
    return 1


@hermes.register("labors", "Heracles performs the twelve canonical labors")
def _labors(_argv: list[str]) -> int:
    from olympus.heroes.heracles import Heracles, CANONICAL_LABORS
    h = Heracles()
    for labor in CANONICAL_LABORS:
        h.assign(labor)
    verdicts = h.perform()
    if _GLOBAL_FLAGS["json"]:
        data = [{"n": v.labor.number, "name": v.labor.name,
                 "target": v.labor.target, "survived": v.survived,
                 "detail": v.detail} for v in verdicts]
        print(_json.dumps(data, indent=2))
        return 0
    rows = [(str(v.labor.number), v.labor.name, v.labor.target,
             "+" if v.survived else "-", v.detail) for v in verdicts]
    print(aphrodite.table(("#", "labor", "target", "result", "detail"), rows))
    failed = sum(1 for v in verdicts if not v.survived)
    if failed:
        print(aphrodite.wine_dark(f"{failed} labor(s) failed"))
        return 1
    print(aphrodite.laurel("all twelve labors survived"))
    return 0


# ─────────────────────────────────────────────────────────────────────
# Loop + action + meta + correlation
# ─────────────────────────────────────────────────────────────────────


@hermes.register("session", "run one cognitive-loop session — session [--verbose] [directive]")
def _session(argv: list[str]) -> int:
    from olympus.session import Session
    verbose = "--verbose" in argv or "-v" in argv
    argv = [a for a in argv if a not in ("--verbose", "-v")]
    directive = " ".join(argv) if argv else None
    s = Session(directive=directive)
    r = s.run()
    if _GLOBAL_FLAGS["json"]:
        print(_json.dumps(r.as_dict(), default=str, indent=2))
    elif not _GLOBAL_FLAGS["quiet"]:
        print(r.render(verbose=verbose))
    return 1 if r.error else 0


@hermes.register("loop", "auto-session on a cadence — loop --interval <seconds> [--count N]")
def _loop(argv: list[str]) -> int:
    import time
    from olympus.session import Session
    interval = 60.0
    count = -1  # forever
    while argv:
        a = argv.pop(0)
        if a == "--interval" and argv:
            interval = float(argv.pop(0))
        elif a == "--count" and argv:
            count = int(argv.pop(0))
    if not _GLOBAL_FLAGS["quiet"]:
        print(aglaia.section(f"loop — every {interval:.0f}s"
                              + (f" × {count}" if count > 0 else "")))
    i = 0
    try:
        while count < 0 or i < count:
            i += 1
            r = Session().run()
            if _GLOBAL_FLAGS["json"]:
                print(_json.dumps({"iteration": i, "report": r.as_dict()}, default=str))
            elif not _GLOBAL_FLAGS["quiet"]:
                print(f"  [{i}] {r.session_id[:16]}  "
                      f"hydra={r.hydra_findings} argos={r.argos_pheromones} "
                      f"proposals={r.proposals_count} duration={r.duration_ms:.0f}ms")
            if count < 0 or i < count:
                time.sleep(interval)
    except KeyboardInterrupt:
        print()
    return 0


@hermes.register("action", "action queue — action <review|delphi|ratify|reject>")
def _action(argv: list[str]) -> int:
    from olympus.action import action_queue
    if not argv:
        print("usage: invoke action <review|delphi|ratify <id> [quote]|reject <id> [reason]>")
        return 2
    verb = argv[0]
    if verb in ("review", "delphi"):
        actions = action_queue.pending() if verb == "review" else action_queue.delphi_pending()
        if not actions:
            print(aglaia.murmur(f"  no {verb} actions"))
            return 0
        if _GLOBAL_FLAGS["json"]:
            import dataclasses as _dc
            print(_json.dumps([_dc.asdict(a) for a in actions], default=str, indent=2))
            return 0
        rows = [(a.id[:28], a.risk_class, a.summary[:80]) for a in actions]
        print(aphrodite.table(("id", "risk", "summary"), rows))
        return 0
    if verb == "ratify" and len(argv) >= 2:
        try:
            a = action_queue.ratify(argv[1], quote=" ".join(argv[2:]) or "ratified via CLI")
            print(aphrodite.laurel(f"ratified {a.id[:28]}"))
            return 0
        except (KeyError, RuntimeError) as exc:
            print(aphrodite.wine_dark(str(exc)))
            return 1
    if verb == "reject" and len(argv) >= 2:
        try:
            a = action_queue.reject(argv[1], reason=" ".join(argv[2:]) or "rejected via CLI")
            print(aphrodite.laurel(f"rejected {a.id[:28]}"))
            return 0
        except KeyError as exc:
            print(aphrodite.wine_dark(str(exc)))
            return 1
    print(aphrodite.wine_dark(f"unknown action subcommand: {verb!r}"))
    return 2


@hermes.register("meta", "Olympus self-portrait (Olympus reasoning about Olympus)")
def _meta(_argv: list[str]) -> int:
    from olympus.meta import portrait
    p = portrait()
    if _GLOBAL_FLAGS["json"]:
        import dataclasses as _dc
        print(_json.dumps(_dc.asdict(p), default=str, indent=2))
        return 0
    print(p.as_text())
    return 0


@hermes.register("correlate", "Argos CorrelationEngine — correlate [window_hours=24]")
def _correlate(argv: list[str]) -> int:
    from olympus.monsters.argos.correlation import correlation
    from olympus.monsters.argos.colony import colony
    window_hours = float(argv[0]) if argv else 24.0
    known_eyes = [e.NAME for e in colony.eyes()]
    report = correlation.correlate(window_hours=window_hours, known_eyes=known_eyes)
    if _GLOBAL_FLAGS["json"]:
        import dataclasses as _dc
        print(_json.dumps({
            "window_hours": report.window_hours,
            "pheromones_considered": report.pheromones_considered,
            "clusters": [_dc.asdict(c) for c in report.clusters],
            "cascades": [_dc.asdict(c) for c in report.cascades],
            "quiet":    [_dc.asdict(q) for q in report.quiet],
        }, default=str, indent=2))
        return 0
    print(aphrodite.banner("Argos correlation",
                           f"window: {window_hours}h · {report.pheromones_considered} pheromone(s)"))
    if report.clusters:
        print(aglaia.subhead(f"Clusters ({len(report.clusters)})"))
        for c in report.clusters[:5]:
            print(f"  · slice {c.slice!r}: {len(c.eyes)} eye(s) "
                  f"({', '.join(c.eyes[:3])}{'...' if len(c.eyes) > 3 else ''}) "
                  f"— intensity {c.intensity_sum:.1f}")
    if report.cascades:
        print(aglaia.subhead(f"Cascades ({len(report.cascades)})"))
        for c in report.cascades[:5]:
            print(f"  · {c.leader} → {c.follower} ({c.instances}x, median {c.median_gap_minutes:.1f}min)")
    if report.quiet:
        print(aglaia.subhead(f"Quiet eyes ({len(report.quiet)})"))
        for q in report.quiet:
            print(f"  · {q.eye}: silent {q.hours_silent:.1f}h")
    if not (report.clusters or report.cascades or report.quiet):
        print(aglaia.murmur("  no cross-eye patterns surfaced in window"))
    return 0


@hermes.register("console", "Zeus operator console — review + ratify pending actions")
def _console(_argv: list[str]) -> int:
    from olympus.olympians.zeus import zeus
    touched = zeus.console()
    print(aglaia.murmur(f"  Zeus touched {touched} action(s)"))
    return 0


@hermes.register("pantheon", "show the complete pantheon (codex/PANTHEON.md)")
def _pantheon(_argv: list[str]) -> int:
    pantheon_md = _gaia_root.child("codex", "PANTHEON.md")
    if not pantheon_md.exists():
        print(aphrodite.wine_dark("codex/PANTHEON.md missing"))
        return 1
    sys.stdout.write(pantheon_md.read_text(encoding="utf-8"))
    return 0


@hermes.register("consult", "consult an oracle — consult <chart|population|hymn|brief>")
def _consult(argv: list[str]) -> int:
    if not argv:
        print("usage: invoke consult <chart|population|hymn|brief>")
        return 2
    what = argv[0]
    if what == "chart":
        from olympus.muses.urania import urania
        print(urania.as_text())
        return 0
    if what == "population":
        from olympus.titans.coeus import coeus
        result = coeus.ask("pantheon-population")
        if _GLOBAL_FLAGS["json"]:
            print(_json.dumps(result, indent=2))
            return 0
        rows = [(k, str(v)) for k, v in result.items()]
        print(aphrodite.table(("tier", "modules"), rows))
        return 0
    if what == "hymn":
        from olympus.muses.polyhymnia import polyhymnia
        h = polyhymnia.hymn()
        if _GLOBAL_FLAGS["json"]:
            print(_json.dumps({"total_oaths": h.total_oaths, "intact": h.intact,
                               "last_oath_ts": h.last_oath_ts,
                               "summary": h.summary}))
            return 0
        print(aphrodite.banner("Polyhymnia's hymn"))
        print(f"  {h.summary}")
        if h.last_oath_ts:
            print(aglaia.murmur(f"  last oath: {h.last_oath_ts}"))
        return 0
    if what == "brief":
        from olympus.olympians.athena import athena
        b = athena.latest()
        if b is None:
            print(aglaia.murmur("  no briefs composed yet"))
            return 0
        print(aphrodite.banner(f"Athena's brief — {b.label}",
                               f"confidence: {b.confidence:.2f}"))
        print("\nFindings:")
        for f in b.findings[:20]:
            print(f"  · {f}")
        print("\nRecommendations:")
        for r in b.recommendations:
            print(f"  · {r}")
        return 0
    print(aphrodite.wine_dark(f"unknown oracle: {what!r}"))
    return 2


@hermes.register("wisdom", "what the substrate has learned across sessions")
def _wisdom(_argv: list[str]) -> int:
    from olympus.wisdom import wisdom as _w
    w = _w()
    if _GLOBAL_FLAGS["json"]:
        import dataclasses as _dc
        print(_json.dumps(_dc.asdict(w), default=str, indent=2))
        return 0
    print(w.as_text())
    return 0


@hermes.register("improve", "Prometheus runs one self-improvement pass — improve [--loop] [--interval N]")
def _improve(argv: list[str]) -> int:
    from olympus.heroes.prometheus import prometheus
    if "--loop" in argv:
        interval = 600.0
        max_iter = -1
        i = 0
        while i < len(argv):
            a = argv[i]
            if a == "--interval" and i + 1 < len(argv):
                interval = float(argv[i + 1]); i += 2; continue
            if a == "--count" and i + 1 < len(argv):
                max_iter = int(argv[i + 1]); i += 2; continue
            i += 1
        prometheus.loop(interval_seconds=interval, max_iterations=max_iter)
        return 0

    report = prometheus.improve()
    if _GLOBAL_FLAGS["json"]:
        import dataclasses as _dc
        print(_json.dumps(_dc.asdict(report), default=str, indent=2))
        return 0
    print(aphrodite.banner("Prometheus — improvement pass",
                           f"{report.handlers_succeeded}/{report.handlers_invoked} succeeded"))
    rows = [
        (r.handler, "ok" if r.succeeded else "FAIL", r.detail[:80])
        for r in report.results
    ]
    print(aphrodite.table(("handler", "result", "detail"), rows))
    return 0 if report.handlers_succeeded == report.handlers_invoked else 1


@hermes.register("iris", "build the static dashboard — iris [--open]")
def _iris(argv: list[str]) -> int:
    from olympus.iris import build
    open_it = "--open" in argv
    out = build(open_in_browser=open_it)
    print(aphrodite.laurel(f"iris built — {out}"))
    if open_it:
        print(aglaia.murmur("  opened in browser"))
    else:
        print(aglaia.murmur(f"  open with: open {out}"))
    return 0


@hermes.register("blessing", "Thalia bestows a closing blessing")
def _blessing(_argv: list[str]) -> int:
    from olympus.muses.thalia_muse import thalia_muse
    from olympus.muses.erato import erato
    print(erato.farewell())
    print(aphrodite.laurel(thalia_muse.blessing()))
    return 0


@hermes.register("shell", "interactive multi-errand REPL")
def _shell(_argv: list[str]) -> int:
    print(aglaia.section("Olympus shell — type errands; 'q' or Ctrl-D to exit"))
    while True:
        try:
            line = input("  invoke ▸ ").strip()
        except (KeyboardInterrupt, EOFError):
            print()
            break
        if line in ("q", "quit", "exit"):
            break
        if not line:
            continue
        parts = line.split()
        rc = hermes.dispatch(parts)
        if rc != 0:
            print(aphrodite.wine_dark(f"  (exit {rc})"))
    return 0


@hermes.register("help", "show help for an errand — help [errand]")
def _help(argv: list[str]) -> int:
    if not argv:
        return hermes.dispatch([])  # falls into Hermes._help
    target = argv[0]
    errand = None
    for e in hermes.errands():
        if e.name == target:
            errand = e
            break
    if errand is None:
        print(aphrodite.wine_dark(f"no such errand: {target!r}"))
        return 1
    print(aglaia.section(f"errand: {errand.name}"))
    print(f"  {errand.summary}")
    print()
    print(aglaia.subhead("global flags (place before errand)"))
    print("  --json       machine-readable output")
    print("  --quiet      suppress non-essential output")
    print("  --no-color   disable ANSI colors")
    return 0


# ─────────────────────────────────────────────────────────────────────


def main(argv: list[str] | None = None) -> int:
    """Entry point. `invoke ...` (pip-installed) and `./scripts/invoke ...`
    both land here."""
    if argv is None:
        argv = sys.argv[1:]
    return hermes.dispatch(argv)


if __name__ == "__main__":
    sys.exit(main())
