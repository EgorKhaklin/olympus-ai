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


@hermes.register("iris", "build the dashboard — iris [--open] [--live [--api URL] [--interval N]]")
def _iris(argv: list[str]) -> int:
    if "--live" in argv:
        from olympus.iris import build_live
        api = "http://127.0.0.1:8765"
        interval = 5.0
        i = 0
        while i < len(argv):
            if argv[i] == "--api" and i + 1 < len(argv):
                api = argv[i + 1]; i += 2; continue
            if argv[i] == "--interval" and i + 1 < len(argv):
                interval = float(argv[i + 1]); i += 2; continue
            i += 1
        open_it = "--open" in argv
        out = build_live(open_in_browser=open_it, api_base=api,
                          interval_seconds=interval)
        print(aphrodite.laurel(f"iris live built — {out}"))
        print(aglaia.murmur(f"  polls {api} every {interval:.1f}s"))
        print(aglaia.murmur(f"  ensure `invoke serve --port "
                            f"{api.rsplit(':', 1)[-1]}` is running"))
        if not open_it:
            print(aglaia.murmur(f"  open with: open {out}"))
        return 0
    from olympus.iris import build
    open_it = "--open" in argv
    out = build(open_in_browser=open_it)
    print(aphrodite.laurel(f"iris built — {out}"))
    if open_it:
        print(aglaia.murmur("  opened in browser"))
    else:
        print(aglaia.murmur(f"  open with: open {out}"))
    return 0


@hermes.register("reflect", "Epimetheus produces hindsights — reflect [--hours N]")
def _reflect(argv: list[str]) -> int:
    from olympus.titans.epimetheus import epimetheus
    hours = 24.0
    i = 0
    while i < len(argv):
        if argv[i] == "--hours" and i + 1 < len(argv):
            hours = float(argv[i + 1]); i += 2; continue
        i += 1
    report = epimetheus.reflect(lookback_hours=hours)
    if _GLOBAL_FLAGS["json"]:
        import dataclasses as _dc
        print(_json.dumps(_dc.asdict(report), default=str, indent=2))
        return 0
    print(aphrodite.banner(
        "Epimetheus — hindsight pass",
        f"lookback {hours}h · {report.total} record(s) · "
        f"{report.surprising} surprising",
    ))
    if not report.records:
        print(aglaia.murmur("  no events in window worth reflecting on"))
        return 0
    rows = [
        (r.subject_kind, r.subject_id[:24],
         "!" if r.surprising else "·",
         r.lesson[:90])
        for r in report.records[:20]
    ]
    print(aphrodite.table(("kind", "subject", "?", "lesson"), rows))
    return 0


@hermes.register("cassandra", "ignored warnings + vindications")
def _cassandra(_argv: list[str]) -> int:
    from olympus.heroes.cassandra import cassandra
    report = cassandra.review()
    if _GLOBAL_FLAGS["json"]:
        import dataclasses as _dc
        print(_json.dumps(_dc.asdict(report), default=str, indent=2))
        return 0
    print(aphrodite.banner(
        "Cassandra — the unbelieved prophetess",
        f"{report.total_ignored} ignored · "
        f"{report.total_vindicated} vindicated",
    ))
    if report.vindicated:
        print(aglaia.subhead("Vindicated (told you so)"))
        for v in report.vindicated[:10]:
            print(f"  · slice {v.slice!r}: dismissed {v.dismissal_kind} "
                  f"— recurred {v.recurrences_after_dismissal}x")
    if report.ignored:
        print(aglaia.subhead(f"Ignored warnings ({len(report.ignored)})"))
        for w in report.ignored[:15]:
            print(f"  · {w.slice}  "
                  f"[{w.dismissal_kind}]  "
                  f"{w.alert_count} alert(s)")
    if not (report.vindicated or report.ignored):
        print(aglaia.murmur("  no dismissed warnings — clean history"))
    return 0


@hermes.register("shoulders", "Atlas — what the substrate is currently carrying")
def _shoulders(_argv: list[str]) -> int:
    from olympus.titans.atlas import atlas
    report = atlas.shoulders()
    if _GLOBAL_FLAGS["json"]:
        import dataclasses as _dc
        print(_json.dumps(_dc.asdict(report), default=str, indent=2))
        return 0
    print(aphrodite.banner(
        "Atlas — burdens currently borne",
        f"{report.current_count} in flight",
    ))
    if report.current:
        rows = [
            (b.op, b.owner[:24], b.started_at[:19], b.id[:12])
            for b in report.current
        ]
        print(aphrodite.table(("op", "owner", "since", "id"), rows))
    else:
        print(aglaia.murmur("  the heavens rest light — no current burdens"))
    if report.recently_released:
        print(aglaia.subhead("Recently released"))
        for b in report.recently_released:
            print(f"  · {b.op:18s}  {b.released_at[:19]}  ({b.outcome})")
    return 0


@hermes.register("panic", "Pan circuit breaker — panic [--clear] [--evaluate]")
def _panic(argv: list[str]) -> int:
    from olympus.olympians.pan import pan
    if "--clear" in argv:
        s = pan.clear(by="zeus:operator", reason="cleared via CLI")
        print(aphrodite.laurel(f"panic cleared at {s.last_transition_at[:19]}"))
        return 0
    state = pan.evaluate() if ("--evaluate" in argv or True) else pan.state()
    if _GLOBAL_FLAGS["json"]:
        import dataclasses as _dc
        print(_json.dumps(_dc.asdict(state), default=str, indent=2))
        return 0
    if state.panicked:
        print(aphrodite.banner("Pan — PANIC STATE", state.detail))
        print(aglaia.murmur(f"  entered: {state.entered_at[:19]}"))
        print(aglaia.murmur(f"  triggering: {state.triggering_violations} "
                            f"violation(s) in {state.window_seconds:.0f}s"))
        print(aphrodite.wine_dark(
            "  ratifications are BLOCKED. Run `invoke panic --clear` "
            "to resume."))
        return 1
    print(aphrodite.banner("Pan — calm", "no panic; ratifications allowed"))
    return 0


@hermes.register("heal", "Asclepius — rebuild derived state")
def _heal(_argv: list[str]) -> int:
    from olympus.olympians.asclepius import asclepius
    report = asclepius.heal()
    if _GLOBAL_FLAGS["json"]:
        import dataclasses as _dc
        print(_json.dumps(_dc.asdict(report), default=str, indent=2))
        return 0
    print(aphrodite.banner(
        "Asclepius — healing pass",
        f"{report.healers_succeeded}/{report.healers_invoked} ok · "
        f"{report.healers_changed} changed",
    ))
    rows = [
        (r.healer,
         "ok" if r.succeeded else "FAIL",
         "changed" if r.changed else "no-op",
         r.detail[:60])
        for r in report.results
    ]
    print(aphrodite.table(("healer", "result", "delta", "detail"), rows))
    return 0 if report.healers_succeeded == report.healers_invoked else 1


@hermes.register("ferry", "Charon — archive released burdens — ferry [--days N]")
def _ferry(argv: list[str]) -> int:
    from olympus.underworld.charon import charon
    days = None
    i = 0
    while i < len(argv):
        if argv[i] == "--days" and i + 1 < len(argv):
            days = float(argv[i + 1]); i += 2; continue
        i += 1
    report = charon.ferry(retention_days=days)
    if _GLOBAL_FLAGS["json"]:
        import dataclasses as _dc
        print(_json.dumps(_dc.asdict(report), default=str, indent=2))
        return 0
    print(aphrodite.banner(
        "Charon — ferry pass",
        f"{report.total_ferried} crossing(s) · "
        f"retention {report.retention_days}d",
    ))
    if report.crossings:
        rows = [
            (c.op, c.burden_id[:12], f"{c.age_days:.1f}d",
             pathlib.Path(c.archived_to).name)
            for c in report.crossings
        ]
        print(aphrodite.table(("op", "burden", "age", "archived-as"), rows))
    else:
        print(aglaia.murmur(f"  no burdens older than "
                            f"{report.retention_days}d to ferry"))
    if report.skipped_already_ferried:
        print(aglaia.murmur(f"  skipped {report.skipped_already_ferried} "
                            f"already-ferried"))
    return 0


@hermes.register("cartograph", "Daedalus — render architecture map — cartograph [--write]")
def _cartograph(argv: list[str]) -> int:
    from olympus.heroes.daedalus import daedalus
    write = "--write" in argv
    result = daedalus.cartograph(write=write)
    if _GLOBAL_FLAGS["json"]:
        import dataclasses as _dc
        print(_json.dumps(_dc.asdict(result), default=str, indent=2))
        return 0
    if write:
        print(aphrodite.laurel(
            f"architecture map written — {result.output_path} "
            f"({result.bytes_written} bytes, {result.diagrams_rendered} "
            f"diagrams)"))
    else:
        doc = daedalus.render_full_document()
        sys.stdout.write(doc)
    return 0


@hermes.register("daemon", "self-improvement daemon — daemon <run|install|status|uninstall>")
def _daemon(argv: list[str]) -> int:
    from olympus.runtime import daemon as _daemon_mod
    if not argv:
        print("usage: invoke daemon <run|install|status|uninstall> [options]")
        return 2
    verb = argv[0]
    rest = argv[1:]

    if verb == "run":
        interval = 600.0
        max_iter = -1
        i = 0
        while i < len(rest):
            if rest[i] == "--interval" and i + 1 < len(rest):
                interval = float(rest[i + 1]); i += 2; continue
            if rest[i] == "--count" and i + 1 < len(rest):
                max_iter = int(rest[i + 1]); i += 2; continue
            i += 1
        print(aglaia.section(
            f"daemon — interval={interval}s "
            + (f"× {max_iter}" if max_iter > 0 else "(forever)")))
        _daemon_mod.run(interval_seconds=interval, max_iterations=max_iter)
        return 0

    if verb == "install":
        interval = 600
        dry = "--dry-run" in rest
        i = 0
        while i < len(rest):
            if rest[i] == "--interval" and i + 1 < len(rest):
                interval = int(rest[i + 1]); i += 2; continue
            i += 1
        result = _daemon_mod.install(interval_seconds=interval, dry_run=dry)
        if _GLOBAL_FLAGS["json"]:
            print(_json.dumps(result, default=str, indent=2)); return 0
        print(aphrodite.banner("daemon install",
                               f"platform: {result.get('platform')}"))
        for k, v in result.items():
            print(f"  {k}: {str(v)[:120]}")
        return 0

    if verb == "uninstall":
        dry = "--dry-run" in rest
        result = _daemon_mod.uninstall(dry_run=dry)
        if _GLOBAL_FLAGS["json"]:
            print(_json.dumps(result, default=str, indent=2)); return 0
        print(aphrodite.banner("daemon uninstall",
                               f"platform: {result.get('platform')}"))
        for k, v in result.items():
            print(f"  {k}: {str(v)[:120]}")
        return 0

    if verb == "status":
        s = _daemon_mod.status()
        if _GLOBAL_FLAGS["json"]:
            import dataclasses as _dc
            print(_json.dumps(_dc.asdict(s), default=str, indent=2))
            return 0
        print(aphrodite.banner(
            f"daemon status — {s.platform}",
            f"installed={s.installed} running={s.running}"
            + (f" pid={s.pid}" if s.pid else "")))
        if s.unit_path:
            print(aglaia.murmur(f"  unit: {s.unit_path}"))
        if s.detail:
            print(aglaia.murmur(f"  detail: {s.detail}"))
        return 0 if (s.installed or not s.installed) else 1

    print(aphrodite.wine_dark(f"unknown daemon subcommand: {verb!r}"))
    return 2


@hermes.register("schemas", "Themis — list/show JSON Schemas — schemas [kind]")
def _schemas(argv: list[str]) -> int:
    from olympus.titans.themis import themis
    schemas = themis.schemas()
    if argv:
        key = argv[0].replace(".", "-")
        if key not in schemas:
            print(aphrodite.wine_dark(
                f"no schema for {argv[0]!r} (try one of: "
                f"{', '.join(sorted(schemas))})"))
            return 1
        sys.stdout.write(_json.dumps(schemas[key], indent=2) + "\n")
        return 0
    if _GLOBAL_FLAGS["json"]:
        print(_json.dumps(sorted(schemas.keys()), indent=2)); return 0
    rows = [
        (name,
         schemas[name].get("title", ""),
         f"{len(schemas[name].get('required', []))} required")
        for name in sorted(schemas.keys())
    ]
    print(aphrodite.table(("schema", "title", "rules"), rows))
    return 0


@hermes.register("pythia", "Pythia — consult outside knowledge — pythia [--web URL | --github QUERY]")
def _pythia(argv: list[str]) -> int:
    from olympus.olympians.apollo.pythia import pythia
    if "--web" in argv:
        i = argv.index("--web")
        if i + 1 >= len(argv):
            print("usage: invoke pythia --web <url>")
            return 2
        url = argv[i + 1]
        c = pythia.ask_web(url)
        if _GLOBAL_FLAGS["json"]:
            import dataclasses as _dc
            print(_json.dumps(_dc.asdict(c), default=str, indent=2))
            return 0
        print(aphrodite.banner(
            "Pythia — web consultation",
            f"{c.status} · {c.bytes_received}B · {c.elapsed_ms:.0f}ms"))
        print(aglaia.murmur(f"  url: {c.url}"))
        if c.error:
            print(aphrodite.wine_dark(f"  error: {c.error}"))
        if c.head:
            print(aglaia.subhead("head"))
            print(c.head[:600])
        return 0 if c.status and 200 <= c.status < 400 else 1
    if "--github" in argv:
        i = argv.index("--github")
        if i + 1 >= len(argv):
            print("usage: invoke pythia --github <query>")
            return 2
        query = " ".join(argv[i + 1:])
        report = pythia.ask_github(query)
        if _GLOBAL_FLAGS["json"]:
            import dataclasses as _dc
            print(_json.dumps(_dc.asdict(report), default=str, indent=2))
            return 0
        print(aphrodite.banner(
            "Pythia — GitHub consultation",
            f"{report.total_count} total · {len(report.findings)} returned"))
        rows = [
            (f.repo[:40], f"{int(f.score)}", f.description[:80])
            for f in report.findings
        ]
        if rows:
            print(aphrodite.table(("repo", "stars", "description"), rows))
        else:
            print(aglaia.murmur("  no results"))
        return 0
    # No subflag — show recent consultations
    cs = pythia.consultations(limit=20)
    if not cs:
        print(aglaia.murmur(
            "  no consultations yet — try:\n"
            "    invoke pythia --github 'agent self-improvement loop'\n"
            "    invoke pythia --web https://example.com"))
        return 0
    print(aphrodite.banner(
        "Pythia — recent consultations",
        f"{len(cs)} most-recent"))
    rows = [
        (c.consulted_at[:19], c.channel,
         str(c.status), c.query[:60])
        for c in cs[:15]
    ]
    print(aphrodite.table(("when", "channel", "code", "query"), rows))
    return 0


@hermes.register("serve", "start the read-only HTTP API — serve [--port N] [--host H]")
def _serve(argv: list[str]) -> int:
    from olympus.runtime.http_api import serve, DEFAULT_HOST, DEFAULT_PORT
    host = DEFAULT_HOST
    port = DEFAULT_PORT
    i = 0
    while i < len(argv):
        if argv[i] == "--port" and i + 1 < len(argv):
            port = int(argv[i + 1]); i += 2; continue
        if argv[i] == "--host" and i + 1 < len(argv):
            host = argv[i + 1]; i += 2; continue
        i += 1
    print(aglaia.section(f"olympus HTTP API — http://{host}:{port}"))
    print(aglaia.murmur("  routes: /  /status  /wisdom  /shoulders  "
                        "/panic  /schemas  /mnemosyne/<kind>"))
    print(aglaia.murmur("  (read-only; Ctrl-C to stop)"))
    serve(host=host, port=port)
    return 0


@hermes.register("shadow", "Castor — run a session in a shadow substrate")
def _shadow(argv: list[str]) -> int:
    from olympus.heroes.castor import castor
    mods: dict[str, str] = {}
    directive = None
    i = 0
    while i < len(argv):
        if argv[i] == "--mod" and i + 1 < len(argv):
            key, _, val = argv[i + 1].partition("=")
            if key:
                mods[key] = val
            i += 2; continue
        if argv[i] == "--directive" and i + 1 < len(argv):
            directive = argv[i + 1]; i += 2; continue
        i += 1
    report = castor.shadow_session(modifications=mods, directive=directive)
    if _GLOBAL_FLAGS["json"]:
        import dataclasses as _dc
        print(_json.dumps(_dc.asdict(report), default=str, indent=2))
        return 0
    print(aphrodite.banner(
        "Castor — shadow session",
        f"rc={report.return_code} succeeded={report.succeeded} "
        f"({report.duration_ms:.0f}ms)"))
    print(aglaia.murmur(f"  shadow root: {report.shadow_root}"))
    if report.error:
        print(aphrodite.wine_dark(f"  error: {report.error}"))
    if report.session_report:
        sr = report.session_report
        print(aglaia.subhead("session report (shadow)"))
        print(f"  session_id: {sr.get('session_id', '')[:24]}")
        print(f"  hydra={sr.get('hydra_findings')} "
              f"argos={sr.get('argos_pheromones')} "
              f"proposals={sr.get('proposals_count')}")
    return 0 if report.succeeded else 1


@hermes.register("tune", "Metis — outcome-driven parameter recommendations")
def _tune(argv: list[str]) -> int:
    from olympus.titans.metis import metis
    hours = 168.0
    raise_proposals = "--no-raise" not in argv
    i = 0
    while i < len(argv):
        if argv[i] == "--hours" and i + 1 < len(argv):
            hours = float(argv[i + 1]); i += 2; continue
        i += 1
    report = metis.advise(lookback_hours=hours,
                          raise_proposals=raise_proposals)
    if _GLOBAL_FLAGS["json"]:
        import dataclasses as _dc
        print(_json.dumps(_dc.asdict(report), default=str, indent=2))
        return 0
    print(aphrodite.banner(
        "Metis — self-tuning advice",
        f"{report.total} recommendation(s) · "
        f"{report.proposals_raised} raised as proposals"))
    if not report.recommendations:
        print(aglaia.murmur(
            f"  no advice from {hours:.0f}h of evidence"))
        return 0
    rows = [
        (r.parameter[:32], str(r.current)[:18],
         str(r.proposed)[:18], f"{r.confidence:.2f}", r.risk_class)
        for r in report.recommendations
    ]
    print(aphrodite.table(
        ("parameter", "current", "proposed", "conf", "risk"), rows))
    return 0


@hermes.register("plugins", "list discovered plugins via entry_points")
def _plugins(_argv: list[str]) -> int:
    from olympus.runtime.plugins import load_all
    manifest = load_all(record_to_mnemosyne=False)
    if _GLOBAL_FLAGS["json"]:
        import dataclasses as _dc
        print(_json.dumps(_dc.asdict(manifest), default=str, indent=2))
        return 0
    print(aphrodite.banner(
        "plugins — entry-point discovery",
        f"{manifest.total_loaded} loaded · {manifest.total_failed} failed"))
    if not (manifest.loaded or manifest.failed):
        print(aglaia.murmur(
            "  no plugins discovered. To author one, see "
            "codex/PLUGINS.md."))
        return 0
    if manifest.loaded:
        rows = [(p.group.split(".")[-1], p.name, p.target[:50])
                for p in manifest.loaded]
        print(aglaia.subhead("loaded"))
        print(aphrodite.table(("group", "name", "target"), rows))
    if manifest.failed:
        rows = [(p.group.split(".")[-1], p.name, p.detail[:60])
                for p in manifest.failed]
        print(aglaia.subhead("failed"))
        print(aphrodite.table(("group", "name", "detail"), rows))
    return 0


@hermes.register("specs", "Themis — list formal specifications (TLA+) — specs [name]")
def _specs(argv: list[str]) -> int:
    from olympus.titans.themis import themis
    specs = themis.specs()
    if argv:
        name = argv[0]
        if name not in specs:
            print(aphrodite.wine_dark(
                f"no spec {name!r}; available: {', '.join(sorted(specs))}"
            ))
            return 1
        spec = specs[name]
        if _GLOBAL_FLAGS["json"]:
            print(_json.dumps(spec, indent=2, default=str))
            return 0
        print(aphrodite.banner(f"spec: {name}", spec.get("module_name", "")))
        print(aglaia.murmur(f"  path: {spec.get('path')}"))
        print(aglaia.murmur(f"  bytes: {spec.get('bytes')}"))
        print()
        print(spec.get("summary", ""))
        return 0
    if _GLOBAL_FLAGS["json"]:
        print(_json.dumps(specs, indent=2, default=str))
        return 0
    if not specs:
        print(aglaia.murmur("  no specs in codex/specs/"))
        return 0
    rows = [(s["name"], s["module_name"],
             str(s["bytes"]),
             (s.get("summary") or "").split("\n")[0][:60])
            for s in specs.values()]
    print(aphrodite.banner("Themis — formal specifications (TLA+)",
                           f"{len(specs)} spec(s) in codex/specs/"))
    print(aphrodite.table(("name", "module", "bytes", "first-line"), rows))
    return 0


@hermes.register("ariadne", "Ariadne — walk a causal chain — ariadne <trace_id>")
def _ariadne(argv: list[str]) -> int:
    from olympus.heroes.ariadne import ariadne
    if not argv:
        print("usage: invoke ariadne <trace_id>")
        return 2
    chain = ariadne.chain(argv[0])
    if _GLOBAL_FLAGS["json"]:
        import dataclasses as _dc
        print(_json.dumps(_dc.asdict(chain), default=str, indent=2))
        return 0
    print(aphrodite.banner(
        f"Ariadne — chain from {argv[0]}",
        f"depth={chain.depth} root_reached={chain.root_reached}"))
    if not chain.events:
        print(aglaia.murmur("  no events found for that trace_id"))
        return 0
    for i, ev in enumerate(chain.events):
        marker = "└─" if i == len(chain.events) - 1 else "├─"
        print(f"  {marker} [{ev.kind}] {ev.actor} — {ev.summary[:80]}")
    return 0


@hermes.register("nemesis", "Nemesis — run counterfactual on recent actions")
def _nemesis(argv: list[str]) -> int:
    from olympus.heroes.nemesis import nemesis
    keep = "--keep-shadows" in argv
    max_n = 3
    i = 0
    while i < len(argv):
        if argv[i] == "--max" and i + 1 < len(argv):
            max_n = int(argv[i + 1]); i += 2; continue
        i += 1
    report = nemesis.consider(max_per_pass=max_n,
                                cleanup_shadows=not keep)
    if _GLOBAL_FLAGS["json"]:
        import dataclasses as _dc
        print(_json.dumps(_dc.asdict(report), default=str, indent=2))
        return 0
    print(aphrodite.banner(
        "Nemesis — counterfactual pass",
        f"considered {report.actions_considered} · "
        f"{report.total} counterfactual(s) · "
        f"{report.skipped_already_examined} skipped"))
    for cf in report.counterfactuals:
        print(aglaia.subhead(f"action {cf.subject_action_id[:24]}"))
        print(f"  actual: {cf.actual_outcome}")
        print(f"  counterfactual: {cf.counterfactual_choice}")
        print(f"  gap: {cf.gap_summary}")
    return 0


@hermes.register("redteam", "Momus — adversarial self-audit of AP catalog")
def _redteam(_argv: list[str]) -> int:
    from olympus.heroes.momus import momus
    report = momus.red_team()
    if _GLOBAL_FLAGS["json"]:
        import dataclasses as _dc
        print(_json.dumps(_dc.asdict(report), default=str, indent=2))
        return 0
    print(aphrodite.banner(
        "Momus — red-team pass",
        f"{report.correct}/{report.total} correct · "
        f"{len(report.slipped_through)} slipped · "
        f"{len(report.false_alarms)} false-alarmed"))
    rows = [
        (r.name[:30],
         "✓" if r.correctly_handled else "✗",
         ",".join(r.expected_aps) or "—",
         ",".join(r.actual_dings) or "—")
        for r in report.results
    ]
    print(aphrodite.table(
        ("case", "ok?", "expected", "actual"), rows))
    if report.slipped_through:
        print(aphrodite.wine_dark(
            f"\n  ⚠ {len(report.slipped_through)} adversarial proposal(s) "
            f"slipped through — AP catalog has gaps"))
        return 1
    return 0


@hermes.register("narrate", "Clio — auto-write a digest — narrate [--days N]")
def _narrate(argv: list[str]) -> int:
    from olympus.muses.clio import clio
    days = 7
    write = "--dry-run" not in argv
    i = 0
    while i < len(argv):
        if argv[i] == "--days" and i + 1 < len(argv):
            days = int(argv[i + 1]); i += 2; continue
        i += 1
    digest = clio.narrate(window_days=days, write=write)
    if _GLOBAL_FLAGS["json"]:
        import dataclasses as _dc
        print(_json.dumps(_dc.asdict(digest), default=str, indent=2))
        return 0
    print(aphrodite.banner(
        f"Clio — digest for last {days}d",
        digest.path or "(not written; --dry-run)"))
    print(f"  sessions: {digest.sessions_run}")
    print(f"  ratified: {digest.proposals_ratified} · "
          f"rejected: {digest.proposals_rejected}")
    print(f"  panics: {digest.panics_entered} · "
          f"vindications: {digest.vindications}")
    if digest.headlines:
        print(aglaia.subhead("Headlines"))
        for h in digest.headlines[:5]:
            print(f"  · {h}")
    return 0


@hermes.register("federate", "Hermes — fetch a peer Olympus digest — federate <url>")
def _federate(argv: list[str]) -> int:
    from olympus.runtime.federation import federate, known_peers
    if not argv:
        peers = known_peers(limit=20)
        if _GLOBAL_FLAGS["json"]:
            import dataclasses as _dc
            print(_json.dumps([_dc.asdict(p) for p in peers],
                              default=str, indent=2))
            return 0
        if not peers:
            print(aglaia.murmur("  no federations recorded"))
            return 0
        print(aphrodite.banner("Hermes — known peers",
                                f"{len(peers)} digest(s)"))
        rows = [(p.fetched_at[:19], p.peer_url[:40],
                 "✓" if p.reachable else "✗",
                 f"{p.elapsed_ms:.0f}ms")
                for p in peers]
        print(aphrodite.table(("when", "peer", "ok", "elapsed"), rows))
        return 0
    digest = federate(argv[0])
    if _GLOBAL_FLAGS["json"]:
        import dataclasses as _dc
        print(_json.dumps(_dc.asdict(digest), default=str, indent=2))
        return 0
    print(aphrodite.banner(
        f"federated {digest.peer_url}",
        f"reachable={digest.reachable} "
        f"status={digest.status_code} "
        f"({digest.elapsed_ms:.0f}ms)"))
    if digest.error:
        print(aphrodite.wine_dark(f"  error: {digest.error}"))
    if digest.peer_status:
        hearth = (digest.peer_status.get("hearth") or {}).get("name")
        styx = (digest.peer_status.get("styx") or {}).get("total_oaths")
        print(aglaia.murmur(f"  peer hearth: {hearth}"))
        print(aglaia.murmur(f"  peer styx oaths: {styx}"))
    if digest.peer_specs:
        print(aglaia.murmur(f"  peer specs: {', '.join(digest.peer_specs)}"))
    return 0 if digest.reachable else 1


@hermes.register("ask", "ask the substrate — ask \"<question>\"")
def _ask(argv: list[str]) -> int:
    from olympus.runtime.dialogue import ask
    question = " ".join(argv)
    answer = ask(question)
    if _GLOBAL_FLAGS["json"]:
        import dataclasses as _dc
        print(_json.dumps(_dc.asdict(answer), default=str, indent=2))
        return 0
    print(aphrodite.banner(
        f"ask: {question[:60]}",
        f"matched: {answer.matched_template}"))
    print(answer.text)
    if answer.sources:
        print()
        print(aglaia.murmur(f"  sources: {', '.join(answer.sources[:5])}"))
    return 0


@hermes.register("pythagoras", "Pythagoras — sacred constants, Fibonacci, harmony")
def _pythagoras(argv: list[str]) -> int:
    from olympus.heroes.pythagoras import (PHI, PHI_INVERSE, PI, E,
                                              SQRT2, SQRT3, SQRT5,
                                              fib_sequence, fib_backoff,
                                              harmony,
                                              pythagorean_triples)
    if argv and argv[0] == "fib":
        n = int(argv[1]) if len(argv) > 1 else 15
        seq = fib_sequence(n)
        if _GLOBAL_FLAGS["json"]:
            print(_json.dumps(seq)); return 0
        print(aphrodite.banner(f"Fibonacci — first {n}", str(seq)))
        return 0
    if argv and argv[0] == "backoff":
        n = int(argv[1]) if len(argv) > 1 else 8
        base = float(argv[2]) if len(argv) > 2 else 1.0
        delays = [fib_backoff(i, base_seconds=base) for i in range(n)]
        if _GLOBAL_FLAGS["json"]:
            print(_json.dumps(delays)); return 0
        rows = [(str(i), f"{d:.3f}s") for i, d in enumerate(delays)]
        print(aphrodite.banner("Fibonacci backoff",
                                f"base={base}s, attempts 0..{n-1}"))
        print(aphrodite.table(("attempt", "delay"), rows))
        return 0
    if argv and argv[0] == "harmony":
        if len(argv) < 2:
            print("usage: invoke pythagoras harmony <ratio>")
            return 2
        r = float(argv[1])
        score = harmony(r)
        if _GLOBAL_FLAGS["json"]:
            import dataclasses as _dc
            print(_json.dumps(_dc.asdict(score),
                              default=str, indent=2))
            return 0
        print(aphrodite.banner(f"harmony({r})",
                                f"nearest {score.nearest_anchor} "
                                f"({score.nearest_value:.6f})"))
        print(f"  distance: {score.distance:.6f}")
        print(f"  score:    {score.score:.6f}")
        return 0
    if argv and argv[0] == "triples":
        below = int(argv[1]) if len(argv) > 1 else 50
        trips = list(pythagorean_triples(below))
        if _GLOBAL_FLAGS["json"]:
            print(_json.dumps(trips)); return 0
        print(aphrodite.banner(
            f"Pythagorean triples (c < {below})",
            f"{len(trips)} primitive triples"))
        for a, b, c in trips:
            print(f"  {a}² + {b}² = {c}²")
        return 0
    # Default: print the constants
    if _GLOBAL_FLAGS["json"]:
        print(_json.dumps({
            "phi": PHI, "phi_inverse": PHI_INVERSE,
            "pi": PI, "e": E,
            "sqrt2": SQRT2, "sqrt3": SQRT3, "sqrt5": SQRT5,
        }, indent=2))
        return 0
    print(aphrodite.banner("Pythagoras — sacred constants", ""))
    rows = [
        ("φ (phi)",      f"{PHI:.10f}"),
        ("1/φ",           f"{PHI_INVERSE:.10f}"),
        ("π (pi)",        f"{PI:.10f}"),
        ("e (Euler)",     f"{E:.10f}"),
        ("√2",            f"{SQRT2:.10f}"),
        ("√3",            f"{SQRT3:.10f}"),
        ("√5",            f"{SQRT5:.10f}"),
    ]
    print(aphrodite.table(("constant", "value"), rows))
    print(aglaia.murmur(
        "  also: invoke pythagoras fib N | backoff N B | "
        "harmony R | triples N"))
    return 0


@hermes.register("plato", "Plato — five-solids taxonomy — plato [classify <name>]")
def _plato(argv: list[str]) -> int:
    from olympus.heroes.plato import plato
    if argv and argv[0] == "classify" and len(argv) >= 2:
        name = argv[1]
        s = plato.classify(name)
        if s is None:
            print(aphrodite.wine_dark(
                f"  {name!r} is not classified in Plato's taxonomy"))
            return 1
        if _GLOBAL_FLAGS["json"]:
            import dataclasses as _dc
            print(_json.dumps(_dc.asdict(s), indent=2)); return 0
        print(aphrodite.banner(
            f"{name} → {s.name}",
            f"{s.element} · {s.function}"))
        print(f"  vertices: {s.vertices}")
        print(f"  {s.description}")
        return 0
    # Default: show the taxonomy
    cosmos = plato.cosmos()
    by_solid: dict[str, list[str]] = {}
    for figure, info in cosmos.items():
        by_solid.setdefault(info["solid"], []).append(figure)
    if _GLOBAL_FLAGS["json"]:
        print(_json.dumps(by_solid, indent=2, default=str)); return 0
    print(aphrodite.banner("Plato — five-solid taxonomy",
                            f"{len(cosmos)} figures classified"))
    for s in plato.solids():
        members = sorted(by_solid.get(s.name, []))
        print(aglaia.subhead(
            f"{s.name} ({s.element} · {s.function}) — "
            f"{len(members)} figure(s)"))
        if members:
            print("  " + ", ".join(members))
    return 0


@hermes.register("harmony", "Pythagoras — substrate ratios scored against φ, 1/φ, 1, 2")
def _harmony(_argv: list[str]) -> int:
    from olympus.heroes.pythagoras import harmony
    from olympus.titans.mnemosyne import mnemosyne
    metrics: list[tuple[str, float, str, float]] = []
    # ratification_rate = ratified / (ratified + rejected)
    ratifications = len(mnemosyne.recall("action.ratified"))
    rejections = len(mnemosyne.recall("action.rejected"))
    if ratifications + rejections > 0:
        r = ratifications / (ratifications + rejections)
        h = harmony(r)
        metrics.append(("ratification_rate", r,
                          h.nearest_anchor, h.score))
    # prophecy acceptance
    profs = mnemosyne.recall("prophecy.verified")
    accepted = sum(1 for m in profs
                    if (m.body or {}).get("accepted") is True)
    rejected_p = sum(1 for m in profs
                      if (m.body or {}).get("accepted") is False)
    if accepted + rejected_p > 0:
        r = accepted / (accepted + rejected_p)
        h = harmony(r)
        metrics.append(("prophecy_acceptance", r,
                          h.nearest_anchor, h.score))
    # Pythia consultation success rate
    cons = mnemosyne.recall("pythia.consultation")
    ok = sum(1 for m in cons
              if 200 <= int((m.body or {}).get("status", 0)) < 400)
    if cons:
        r = ok / len(cons)
        h = harmony(r)
        metrics.append(("pythia_success", r,
                          h.nearest_anchor, h.score))
    if _GLOBAL_FLAGS["json"]:
        print(_json.dumps([{
            "metric": m, "ratio": r, "nearest": n, "score": s,
        } for m, r, n, s in metrics], indent=2))
        return 0
    print(aphrodite.banner(
        "harmony — substrate ratios vs sacred anchors",
        f"{len(metrics)} metric(s) observed"))
    if not metrics:
        print(aglaia.murmur(
            "  insufficient data — run more sessions first"))
        return 0
    rows = [(m, f"{r:.4f}", n, f"{s:.4f}") for m, r, n, s in metrics]
    print(aphrodite.table(
        ("metric", "ratio", "nearest", "score"), rows))
    return 0


@hermes.register("geometry", "Plato + Pythagoras combined — taxonomy + harmony")
def _geometry(_argv: list[str]) -> int:
    from olympus.runtime.http_api import dispatch
    status, body = dispatch("/geometry", {})
    if _GLOBAL_FLAGS["json"]:
        print(_json.dumps(body, default=str, indent=2))
        return 0
    print(aphrodite.banner("geometry — sacred + numerical layer",
                            f"{len(body.get('platonic_solids', []))} solids · "
                            f"{len(body.get('harmony_metrics', {}))} harmony "
                            f"metric(s)"))
    print(aglaia.subhead("Platonic solids"))
    for s in body.get("platonic_solids", []):
        ms = s.get("members", [])
        print(f"  {s['name']:13s} ({s['element']:7s} · "
              f"{s['function']:11s}) {len(ms):3d} figure(s)")
    metrics = body.get("harmony_metrics", {})
    if metrics:
        print(aglaia.subhead("Harmony metrics"))
        for name, info in metrics.items():
            print(f"  {name:25s} ratio={info['ratio']:.4f} "
                  f"→ {info['nearest_anchor']:13s} "
                  f"score={info['score']:.4f}")
    return 0


@hermes.register("hygieia", "Hygieia — whole-substrate wellness checks")
def _hygieia(_argv: list[str]) -> int:
    from olympus.olympians.hygieia import hygieia
    report = hygieia.check()
    if _GLOBAL_FLAGS["json"]:
        import dataclasses as _dc
        print(_json.dumps(_dc.asdict(report), default=str, indent=2))
        return 0
    print(aphrodite.banner(
        "Hygieia — substrate wellness",
        f"{report.well_count} well · {report.warning_count} warning · "
        f"{report.incoherent_count} incoherent"))
    rows = [
        (f.check,
         {"well": "✓", "warning": "!", "incoherent": "✗"}.get(
             f.status, "?"),
         f.detail[:90])
        for f in report.findings
    ]
    print(aphrodite.table(("check", "?", "detail"), rows))
    return 0 if report.incoherent_count == 0 else 1


@hermes.register("phoenix", "Phoenix — find state due for rebirth")
def _phoenix(argv: list[str]) -> int:
    from olympus.heroes.phoenix import phoenix
    staleness = 30.0
    hung_hours = 48.0
    i = 0
    while i < len(argv):
        if argv[i] == "--prophecy-staleness" and i + 1 < len(argv):
            staleness = float(argv[i + 1]); i += 2; continue
        if argv[i] == "--hung-hours" and i + 1 < len(argv):
            hung_hours = float(argv[i + 1]); i += 2; continue
        i += 1
    report = phoenix.consider(prophecy_staleness_days=staleness,
                                hung_burden_hours=hung_hours)
    if _GLOBAL_FLAGS["json"]:
        import dataclasses as _dc
        print(_json.dumps(_dc.asdict(report), default=str, indent=2))
        return 0
    print(aphrodite.banner(
        "Phoenix — rebirth scan",
        f"{report.total} new candidate(s) · "
        f"{report.already_known} already known"))
    if not report.candidates:
        print(aglaia.murmur("  no new rebirth candidates"))
        return 0
    rows = [
        (c.kind, c.subject[:30], f"{c.confidence:.2f}",
         c.reason[:60])
        for c in report.candidates
    ]
    print(aphrodite.table(("kind", "subject", "conf", "reason"), rows))
    return 0


@hermes.register("centrality", "Daedalus — load-bearing figures by graph centrality")
def _centrality(argv: list[str]) -> int:
    from olympus.heroes.daedalus import daedalus
    top = int(argv[0]) if argv else 12
    rankings = daedalus.load_bearing_figures(top=top)
    if _GLOBAL_FLAGS["json"]:
        print(_json.dumps([{"figure": k, "centrality": v}
                            for k, v in rankings], indent=2))
        return 0
    print(aphrodite.banner(
        "Daedalus — load-bearing figures",
        f"top {top} by betweenness centrality"))
    rows = [(figure, f"{score:.4f}") for figure, score in rankings]
    print(aphrodite.table(("figure", "centrality"), rows))
    return 0


@hermes.register("euterpe", "Euterpe — musical consonance scoring — euterpe <ratio>")
def _euterpe(argv: list[str]) -> int:
    from olympus.muses.euterpe import euterpe
    if not argv:
        # Show the interval table
        if _GLOBAL_FLAGS["json"]:
            print(_json.dumps(dict(euterpe.intervals())))
            return 0
        print(aphrodite.banner(
            "Euterpe — consonant intervals",
            "octave-invariant; perceptual ordering"))
        rows = [(name, f"{ratio:.6f}") for name, ratio in euterpe.intervals()]
        print(aphrodite.table(("interval", "ratio"), rows))
        return 0
    ratio = float(argv[0])
    c = euterpe.consonance(ratio)
    if _GLOBAL_FLAGS["json"]:
        import dataclasses as _dc
        print(_json.dumps(_dc.asdict(c), default=str, indent=2))
        return 0
    print(aphrodite.banner(
        f"consonance({ratio})",
        f"{c.nearest_interval} ({c.consonance_class})"))
    print(f"  nearest interval: {c.nearest_interval} (= {c.nearest_ratio:.6f})")
    print(f"  distance:         {c.distance:.6f}")
    print(f"  score:            {c.score:.6f}")
    print(f"  class:            {c.consonance_class}")
    return 0


@hermes.register("today", "the single-action oracle — one concrete thing to do")
def _today(_argv: list[str]) -> int:
    from olympus.runtime.today import today, record
    action = today()
    record(action)
    if _GLOBAL_FLAGS["json"]:
        import dataclasses as _dc
        print(_json.dumps(_dc.asdict(action), default=str, indent=2))
        return 0
    color = {
        "urgent":     aphrodite.wine_dark,
        "noteworthy": aphrodite.lightning,
        "gentle":     aphrodite.laurel,
        "calm":       aphrodite.laurel,
    }.get(action.priority, aphrodite.laurel)
    print(color(f"  [{action.priority}] {action.headline}"))
    if action.detail:
        print(aglaia.murmur(f"  {action.detail}"))
    if action.drawn_from:
        print(aglaia.murmur(f"  sources: {', '.join(action.drawn_from)}"))
    return 0


@hermes.register("agent", "invoke an LLM-agent role — agent <role> [\"<prompt>\"]")
def _agent(argv: list[str]) -> int:
    from olympus.runtime.agents import run, known_roles
    if not argv:
        print("usage: invoke agent <role> [\"<prompt>\"]")
        print(f"  known roles: {', '.join(known_roles())}")
        return 2
    role_name = argv[0]
    user_prompt = " ".join(argv[1:]) if len(argv) > 1 else (
        f"You are operating as {role_name}. Examine the substrate's "
        f"current state and produce your role-specific output. "
        f"Follow the schema exactly."
    )
    result = run(role_name, user_prompt)
    if _GLOBAL_FLAGS["json"]:
        import dataclasses as _dc
        print(_json.dumps(_dc.asdict(result), default=str, indent=2))
        return 0
    print(aphrodite.banner(
        f"agent: {role_name}",
        f"bridge={result.bridge} "
        f"confidence={result.confidence:.2f} "
        f"({result.elapsed_ms:.0f}ms)"))
    if result.error:
        print(aphrodite.wine_dark(f"  error: {result.error[:200]}"))
        return 1
    if result.parsed:
        print(aglaia.subhead("parsed"))
        for k, v in result.parsed.items():
            print(f"  {k}: {str(v)[:120]}")
    if result.raw_text:
        print(aglaia.subhead("raw head"))
        print(result.raw_text[:400])
    return 0


@hermes.register("propose-figure", "LLM-driven new-figure proposal — propose-figure [\"<directive>\"]")
def _propose_figure(argv: list[str]) -> int:
    from olympus.runtime.agents import propose_figure
    directive = " ".join(argv) if argv else None
    result = propose_figure(directive=directive)
    if _GLOBAL_FLAGS["json"]:
        print(_json.dumps(result, default=str, indent=2))
        return 0
    if not result.get("ok"):
        print(aphrodite.wine_dark(
            f"  proposal failed: {result.get('error', 'unknown')}"))
        return 1
    print(aphrodite.banner(
        f"new-figure proposal: {result['figure_name']}",
        f"tier={result['tier']} · "
        f"confidence={result['confidence']:.2f}"))
    print(aglaia.murmur(f"  proposal id: {result['proposal_id']}"))
    print(aglaia.murmur(f"  written to:  {result['proposal_path']}"))
    print()
    print(aphrodite.lightning(
        "  next steps (operator):\n"
        "    1. invoke action delphi      # see delphi-pending\n"
        "    2. review the proposal file\n"
        "    3. write a Delphi document if ratifying\n"
        "    4. invoke action ratify <id> \"<quote>\"   OR   reject <id>"
    ))
    return 0


@hermes.register("calibration", "agent calibration over time — calibration [role]")
def _calibration(argv: list[str]) -> int:
    from olympus.runtime.agents import calibration, known_roles
    if argv:
        rows = [calibration(argv[0])]
    else:
        rows = [calibration(r) for r in known_roles()]
        rows.append(calibration())  # aggregate row
    if _GLOBAL_FLAGS["json"]:
        print(_json.dumps(rows, default=str, indent=2))
        return 0
    print(aphrodite.banner(
        "agent calibration", f"{len(rows)} row(s)"))
    table_rows = [
        (str(r.get("role", "?")),
         str(r.get("total_invocations", 0)),
         f"{r.get('avg_confidence', 0):.3f}",
         f"{r.get('parse_failure_rate', 0):.2%}",
         f"{r.get('error_rate', 0):.2%}")
        for r in rows
    ]
    print(aphrodite.table(
        ("role", "calls", "avg-conf", "parse-fail%", "error%"),
        table_rows))
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


_PLUGINS_LOADED = False


def _load_plugins_once() -> None:
    """Load registered plugins once per process. Silent on failure —
    plugin errors are recorded in Mnemosyne but never abort the CLI."""
    global _PLUGINS_LOADED
    if _PLUGINS_LOADED:
        return
    _PLUGINS_LOADED = True
    if _os.environ.get("OLYMPUS_DISABLE_PLUGINS") == "1":
        return
    try:
        from olympus.runtime.plugins import load_all
        load_all(record_to_mnemosyne=False)
    except Exception:  # noqa: BLE001
        # Plugin loader itself never raises, but be defensive
        pass


def main(argv: list[str] | None = None) -> int:
    """Entry point. `invoke ...` (pip-installed) and `./scripts/invoke ...`
    both land here."""
    if argv is None:
        argv = sys.argv[1:]
    _load_plugins_once()
    return hermes.dispatch(argv)


if __name__ == "__main__":
    sys.exit(main())
