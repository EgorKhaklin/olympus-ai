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


@hermes.register("today", "the single-action oracle — today "
                            "[--resolve <slice> --re-raise|--dismiss-as-stale "
                            "\"<reason>\"]")
def _today(argv: list[str]) -> int:
    """Per Delphi 2026-05-19-tartarus-arc.md: `--resolve` lets the
    operator close longstanding findings the oracle keeps surfacing.
    Two outcomes: --re-raise (creates a fresh proposal) or
    --dismiss-as-stale (records operator's rationale; suppresses for 7d)."""
    # --resolve sub-mode
    if argv and argv[0] == "--resolve":
        return _today_resolve(argv[1:])
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


def _today_resolve(argv: list[str]) -> int:
    """`invoke today --resolve <slice> [--re-raise | --dismiss-as-stale "<reason>"]`"""
    from olympus.titans.mnemosyne import mnemosyne
    from olympus.primordials.nyx import Nyx
    if not argv:
        print(aglaia.murmur(
            "usage: invoke today --resolve <slice> "
            "[--re-raise | --dismiss-as-stale \"<reason>\"]"))
        return 2
    slice_id = argv[0]
    mode = None
    reason = ""
    i = 1
    while i < len(argv):
        if argv[i] == "--re-raise":
            mode = "re-raise"; i += 1
        elif argv[i] == "--dismiss-as-stale":
            mode = "dismiss-as-stale"
            if i + 1 < len(argv):
                reason = argv[i + 1]; i += 2
            else:
                i += 1
        else:
            i += 1
    if mode is None:
        print(aglaia.murmur(
            "must specify --re-raise OR --dismiss-as-stale \"<reason>\""))
        return 2
    if mode == "re-raise":
        # Create a fresh proposal in the Hephaestus queue referencing
        # the original finding. This goes through normal Momus→Delphi→Zeus.
        import uuid
        from olympus.primordials.gaia import root
        pid = (f"resolve-{Nyx.now().strftime('%Y%m%dT%H%M%SZ')}-"
               f"{uuid.uuid4().hex[:8]}")
        proposal = {
            "id": pid,
            "drift_observed": (
                f"today --resolve --re-raise: operator re-raised "
                f"slice '{slice_id}' after prior dismissal"),
            "summary": f"re-raise of slice {slice_id}",
            "proposed_fix": "operator decision; investigate the slice",
            "rationale": "today --resolve --re-raise",
            "risk_class": "MEDIUM",
            "raised_by": "zeus:operator",
            "raised_at": Nyx.now().isoformat(),
            "raised_via": "today-resolve",
            "original_slice": slice_id,
        }
        target = root.child("state", "hephaestus", f"{pid}.json")
        target.parent.mkdir(parents=True, exist_ok=True)
        import json as _json
        target.write_text(_json.dumps(proposal, indent=2), encoding="utf-8")
        mnemosyne.remember(
            kind="warning.re-raised",
            actor="zeus:operator",
            summary=f"re-raised slice '{slice_id}' as proposal {pid}",
            slice=slice_id,
            proposal_id=pid,
        )
        print(aphrodite.laurel(
            f"re-raised slice '{slice_id}' as proposal {pid}"))
        print(aglaia.murmur(f"  proposal: {target}"))
        return 0
    # dismiss-as-stale
    mnemosyne.remember(
        kind="warning.dismissal-reaffirmed",
        actor="zeus:operator",
        summary=f"dismissed slice '{slice_id}' as stale: "
                f"{reason[:80]}",
        slice=slice_id,
        reason=reason,
        suppress_until_days=7,
    )
    print(aphrodite.laurel(
        f"dismissed slice '{slice_id}' as stale (suppressed 7d)"))
    if reason:
        print(aglaia.murmur(f"  rationale: {reason}"))
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


@hermes.register("setup", "interactive welcome wizard (start here, stranger)")
def _setup(_argv: list[str]) -> int:
    from olympus.runtime.setup import run_setup
    run_setup()
    return 0


@hermes.register("replay", "Olympus-Replay — regression harness over "
                            "past agent.invocation; "
                            "replay [--limit N] [--role R] [--since Nh] "
                            "[--use-anthropic] [--include-test-seeds]")
def _replay(argv: list[str]) -> int:
    """Per Delphi 2026-05-19-olympus-replay-arc.md."""
    from olympus.runtime.replay import (
        ReplayPlan, replay_many, MAX_LIMIT,
    )
    limit = 20
    role: str | None = None
    since_hours: float | None = None
    bridge = "echo"
    include_test_seeds = False
    i = 0
    while i < len(argv):
        a = argv[i]
        if a == "--limit" and i + 1 < len(argv):
            try:
                limit = max(1, min(int(argv[i + 1]), MAX_LIMIT))
            except ValueError:
                pass
            i += 2; continue
        if a == "--role" and i + 1 < len(argv):
            role = argv[i + 1]; i += 2; continue
        if a == "--since" and i + 1 < len(argv):
            s = argv[i + 1].strip().lower()
            try:
                if s.endswith("h"):
                    since_hours = float(s[:-1])
                elif s.endswith("d"):
                    since_hours = float(s[:-1]) * 24.0
                else:
                    since_hours = float(s)
            except ValueError:
                pass
            i += 2; continue
        if a == "--use-anthropic":
            bridge = "anthropic"; i += 1; continue
        if a == "--include-test-seeds":
            include_test_seeds = True; i += 1; continue
        i += 1
    plan = ReplayPlan(
        limit=limit, role=role,
        since_hours=since_hours, bridge=bridge,
        include_test_seeds=include_test_seeds,
    )
    report = replay_many(plan)

    if _GLOBAL_FLAGS["json"]:
        import dataclasses as _dc
        print(_json.dumps(_dc.asdict(report), default=str, indent=2))
        return 0

    print(aphrodite.banner(
        f"replay — {report.total} candidate(s) · bridge={report.bridge_used}",
        f"stable={report.stable} · drift={report.drift} · "
        f"broken={report.broken} · skipped={report.skipped}"
        + (f" · over-budget={report.over_budget}"
           if report.over_budget else "")))
    if report.by_role:
        print(aglaia.section("by role"))
        for r, counts in sorted(report.by_role.items()):
            print(aglaia.murmur(
                f"  {r:<18} stable={counts['stable']} · "
                f"drift={counts['drift']} · broken={counts['broken']} · "
                f"skipped={counts['skipped']}"))
    if report.drift_examples:
        print(aglaia.section("drift examples"))
        for ex in report.drift_examples[:5]:
            print(aglaia.murmur(
                f"  {ex.role}/{ex.candidate_id}:  "
                f"{'; '.join(ex.diffs[:2])[:100]}"))
    if report.broken_examples:
        print(aglaia.section("broken examples"))
        for ex in report.broken_examples[:5]:
            print(aglaia.murmur(
                f"  {ex.role}/{ex.candidate_id}:  "
                f"{(ex.error or '; '.join(ex.diffs))[:100]}"))
    return 0


@hermes.register("mcp", "Olympus as MCP server (stdio); "
                          "mcp [--probe]")
def _mcp(argv: list[str]) -> int:
    """Per Delphi 2026-05-19-hermes-mcp-arc.md.

    Run Olympus as an MCP server over stdio (the standard transport).
    The operator wires this into Claude Code's mcp_servers.json:

        {"mcpServers": {"olympus":
            {"command": "<invoke-path>", "args": ["mcp"]}}}

    `--probe` prints server info + tool list to stderr then exits.
    """
    from olympus.runtime.mcp_server import serve_stdio, probe
    if "--probe" in argv:
        return probe()
    return serve_stdio()


@hermes.register("speak", "TTS via macOS `say`; "
                            "speak [\"<text>\"] [--voice V] [--rate N] [--block]")
def _speak(argv: list[str]) -> int:
    """Per Delphi 2026-05-19-throne-voice-arc.md.

    Speak the given text aloud via the active VoiceBackend (default:
    MacosSayBackend on macOS, NullBackend elsewhere). Records to
    Mnemosyne under `voice.spoken`."""
    from olympus.runtime.voice import speak, get_backend
    voice = ""
    rate = 0
    blocking = False
    text_parts: list[str] = []
    i = 0
    while i < len(argv):
        a = argv[i]
        if a == "--voice" and i + 1 < len(argv):
            voice = argv[i + 1]; i += 2; continue
        if a == "--rate" and i + 1 < len(argv):
            try:
                rate = int(argv[i + 1])
            except ValueError:
                pass
            i += 2; continue
        if a in ("--block", "--blocking"):
            blocking = True; i += 1; continue
        text_parts.append(a); i += 1
    text = " ".join(text_parts).strip()
    if not text:
        print(aglaia.murmur(
            'usage: invoke speak "<text>" '
            "[--voice V] [--rate N] [--block]"))
        return 2
    backend = get_backend()
    if not backend.available():
        print(aglaia.murmur(
            f"  TTS not configured on this platform "
            f"(backend={backend.name})"))
        return 1
    result = speak(text, voice=voice, rate=rate, blocking=blocking)
    if _GLOBAL_FLAGS["json"]:
        import dataclasses as _dc
        print(_json.dumps(_dc.asdict(result), default=str, indent=2))
        return 0
    badge = "✓" if result.ok else "✗"
    truncated = " (truncated)" if result.truncated else ""
    print(aglaia.murmur(
        f"  {badge} spoke {result.chars}c via {result.backend}{truncated}"
        + (f"  error={result.error[:80]}" if result.error else "")))
    return 0 if result.ok else 1


@hermes.register("demeter", "Demeter — knowledge-base ingestion; "
                              "demeter <ingest|library|forget>")
def _demeter(argv: list[str]) -> int:
    """Per Delphi 2026-05-19-demeter-library-arc.md.

    Operator drops .md/.txt/.pdf into state/demeter/library/;
    `invoke demeter ingest` chunks each file and records chunks to
    Mnemosyne under `demeter.chunk`. Hippocrene's `recall` errand
    finds them automatically (demeter.chunk is in DEFAULT_KINDS).
    """
    from olympus.olympians.demeter import library
    sub = argv[0] if argv else "library"

    if sub == "ingest":
        reingest = "--reingest" in argv
        limit: int | None = None
        i = 1
        while i < len(argv):
            if argv[i] == "--limit" and i + 1 < len(argv):
                try:
                    limit = int(argv[i + 1])
                except ValueError:
                    pass
                i += 2; continue
            i += 1
        report = library.ingest(reingest=reingest, limit=limit)
        if _GLOBAL_FLAGS["json"]:
            import dataclasses as _dc
            print(_json.dumps(_dc.asdict(report), default=str, indent=2))
            return 0
        print(aphrodite.banner(
            "demeter ingest" + (" --reingest" if reingest else ""),
            f"ingested={report.documents_ingested} · "
            f"unchanged={report.documents_unchanged} · "
            f"skipped={report.documents_skipped} · "
            f"chunks={report.chunks_recorded}"))
        if report.by_extension:
            print(aglaia.section("by extension"))
            for ext, n in sorted(report.by_extension.items(),
                                   key=lambda kv: -kv[1]):
                print(aglaia.murmur(f"  {ext:<8} {n}"))
        if report.skipped:
            print(aglaia.section("skipped (head 10)"))
            for s in report.skipped[:10]:
                print(aglaia.murmur(
                    f"  {s['path']:<48} {s['reason'][:80]}"))
        return 0

    if sub == "library":
        docs = library.documents()
        print(aphrodite.banner(
            "demeter library", f"{len(docs)} document(s) tracked"))
        if not docs:
            print(aglaia.murmur(
                "  (no documents yet — drop .md/.txt/.pdf into "
                "state/demeter/library/ then run `invoke demeter ingest`)"))
            return 0
        print(aglaia.murmur(
            f"  {'source':<50} {'chunks':>6}  {'sha':<14}  ingested_at"))
        for d in docs:
            print(aglaia.murmur(
                f"  {d['source_path']:<50} {d['chunk_count']:>6}  "
                f"{d['sha256'][:12]:<14}  "
                f"{d.get('ingested_at','')[:19]}"))
        return 0

    if sub == "forget":
        if len(argv) < 2:
            print(aglaia.murmur(
                "usage: invoke demeter forget <document_id>"))
            return 2
        doc_id = argv[1]
        ok = library.forget(doc_id)
        if ok:
            print(aphrodite.laurel(
                f"forgot document '{doc_id}' (chunks remain in "
                "Mnemosyne under demeter.chunk; S1 preserved)"))
            return 0
        print(aglaia.murmur(f"  no document with id {doc_id!r}"))
        return 1

    print(aglaia.murmur(
        f"  unknown subcommand {sub!r}; "
        "valid: ingest, library, forget"))
    return 2


@hermes.register("hephaestus", "Hephaestus — apply ratified proposals "
                                "as real git PRs; "
                                "hephaestus <pending|apply <pid> [--really]>")
def _hephaestus(argv: list[str]) -> int:
    """Per Delphi 2026-05-19-hephaestus-pr-arc.md.

    `pending` — list ratified proposals not yet applied.
    `apply <pid>` — dry-run by default; `--really` performs the work.
    """
    from olympus.runtime import git_ops
    from olympus.primordials.gaia import root
    from olympus.primordials.nyx import Nyx
    from olympus.titans.mnemosyne import mnemosyne
    import json as _json

    sub = argv[0] if argv else "pending"

    if sub == "pending":
        ratified = mnemosyne.recall("action.ratified")
        applied = mnemosyne.recall("prometheus.applied")
        applied_pids = {m.body.get("proposal_id") for m in applied}
        pending: list[tuple[str, str]] = []
        for m in ratified:
            aid = m.body.get("action_id", "")
            pid = aid[4:] if aid.startswith("act-") else aid
            if not pid or pid in applied_pids:
                continue
            ppath = root.child("state", "hephaestus", f"{pid}.json")
            if not ppath.exists():
                continue
            try:
                d = _json.loads(ppath.read_text(encoding="utf-8"))
            except Exception:  # noqa: BLE001
                continue
            from olympus.runtime.test_seeds import is_test_proposal
            if is_test_proposal(d):
                continue
            pending.append((pid, d.get("summary", "") or
                             d.get("drift_observed", "")[:80]))
        print(aphrodite.banner(
            "hephaestus pending",
            f"{len(pending)} ratified-but-unapplied proposal(s)"))
        for pid, summary in pending[:30]:
            print(aglaia.murmur(
                f"  {pid:<40} {summary[:70]}"))
        if not pending:
            print(aglaia.murmur(
                "  (nothing pending — Hephaestus has a quiet forge)"))
        return 0

    if sub == "apply":
        if len(argv) < 2:
            print(aglaia.murmur(
                "usage: invoke hephaestus apply <pid> "
                "[--really] [--skip-push] [--skip-pr]"))
            return 2
        pid = argv[1]
        really = "--really" in argv
        skip_push = "--skip-push" in argv
        skip_pr = "--skip-pr" in argv

        # Pre-flight refuse-list
        ppath = root.child("state", "hephaestus", f"{pid}.json")
        if not ppath.exists():
            print(aglaia.murmur(
                f"  ✗ proposal {pid!r} not found at {ppath}"))
            return 1
        try:
            proposal = _json.loads(ppath.read_text(encoding="utf-8"))
        except Exception as exc:  # noqa: BLE001
            print(aglaia.murmur(f"  ✗ proposal unreadable: {exc}"))
            return 1

        # Confirm ratified
        ratified = mnemosyne.recall("action.ratified")
        action_ids = {m.body.get("action_id") for m in ratified}
        if (f"act-{pid}" not in action_ids
                and pid not in action_ids):
            print(aglaia.murmur(
                f"  ✗ proposal {pid!r} is not ratified "
                "(no action.ratified record)"))
            return 1

        # Confirm not already applied
        applied = mnemosyne.recall("prometheus.applied")
        if any(m.body.get("proposal_id") == pid for m in applied
                if not m.body.get("dry_run")):
            print(aglaia.murmur(
                f"  ✗ proposal {pid!r} already applied"))
            return 1

        # Working tree clean?
        if not git_ops.git_clean():
            print(aglaia.murmur(
                "  ✗ working tree is dirty; commit or stash first"))
            return 1

        # Build the apply plan
        target_branch = str(proposal.get("target_branch", "main"))
        if git_ops.is_protected(target_branch):
            pass  # OK: target is allowed to be main (we BRANCH OFF main)
        new_branch = f"prometheus/{pid}"
        if git_ops.branch_exists(new_branch):
            print(aglaia.murmur(
                f"  ✗ branch {new_branch!r} already exists"))
            return 1
        original_branch = git_ops.current_branch()
        has_patch = bool(proposal.get("patch", "").strip())
        title = f"[{proposal.get('risk_class', 'LOW')}] " \
                f"{proposal.get('summary', proposal.get('drift_observed', '')[:60])}"
        body_lines = [
            f"## Proposal `{pid}`",
            "",
            f"**Drift observed**: {proposal.get('drift_observed', '(n/a)')}",
            "",
            f"**Proposed fix**: {proposal.get('proposed_fix', '(n/a)')}",
            "",
            f"**Rationale**: {proposal.get('rationale', '(n/a)')}",
            "",
            f"**Risk class**: {proposal.get('risk_class', 'LOW')}",
            "",
            f"**Raised by**: {proposal.get('raised_by', '(unknown)')}",
            "",
            "---",
            "",
            "_Per Olympus constitution: Hephaestus surfaces drift; Momus "
            "contests; Zeus ratifies on Styx; Prometheus applies as a "
            "branch + PR. The operator merges via the GitHub UI._",
            "",
            f"_Delphi: codex/oracles/delphi/*-{Nyx.now().strftime('%Y-%m-%d')}-*.md_",
        ]
        if not has_patch:
            body_lines.insert(0,
                "**[TRACKING]** This PR has no patch — it documents a "
                "ratified proposal that the operator will implement. "
                "The proposal text is also written to "
                f"`proposals/{pid}.md` as a tracked artifact.")
            body_lines.insert(1, "")
        body = "\n".join(body_lines)

        print(aphrodite.banner(
            "hephaestus apply" + (" [DRY-RUN]" if not really else ""),
            f"proposal {pid} → branch {new_branch}"))
        print(aglaia.section("plan"))
        print(aglaia.murmur(f"  1. git checkout -b {new_branch}"))
        if has_patch:
            print(aglaia.murmur(
                f"  2. git apply <patch>  ({len(proposal['patch'])} chars)"))
        else:
            print(aglaia.murmur(
                f"  2. write proposals/{pid}.md  (tracking artifact)"))
        print(aglaia.murmur(
            f"  3. git commit -m \"{title}\""))
        if not skip_push:
            print(aglaia.murmur(
                f"  4. git push -u origin {new_branch}"))
        if not skip_pr and git_ops.gh_available():
            print(aglaia.murmur(
                f"  5. gh pr create --base {target_branch} "
                f"--head {new_branch}"))
        elif not skip_pr:
            print(aglaia.murmur(
                "  5. (gh CLI missing; skip pr-create)"))
        print(aglaia.murmur(
            f"  6. git checkout {original_branch}"))

        if not really:
            print(aglaia.murmur(
                "  (dry-run — pass --really to execute)"))
            # Still record an audit row so we have evidence of the plan
            mnemosyne.remember(
                kind="prometheus.applied",
                actor="zeus:operator",
                summary=f"DRY-RUN plan for proposal {pid}",
                proposal_id=pid, branch=new_branch,
                target_branch=target_branch,
                has_patch=has_patch, dry_run=True,
            )
            return 0

        # ──── ACTUALLY APPLY ────
        result_log: list[CommandResult] = []  # type: ignore[name-defined]

        def _step(step_name: str, r):
            result_log.append(r)
            badge = "✓" if r.ok else "✗"
            print(aglaia.murmur(f"  {badge} {step_name}"
                                + (f"  {r.error or r.stderr[:80]}"
                                   if not r.ok else "")))
            return r.ok

        if not _step(f"create branch {new_branch}",
                      git_ops.create_branch(new_branch)):
            return 1
        if has_patch:
            if not _step("apply patch",
                          git_ops.apply_patch(proposal["patch"])):
                git_ops.checkout(original_branch)
                return 1
            stage_paths: tuple[str, ...] = ()
        else:
            rel = f"proposals/{pid}.md"
            content_lines = [
                f"# Proposal {pid}",
                "",
                f"_(tracking artifact — generated by Olympus "
                f"`invoke hephaestus apply --really`)_",
                "",
                body,
            ]
            if not _step(f"write {rel}",
                          git_ops.write_file_under_repo(
                              rel, "\n".join(content_lines))):
                git_ops.checkout(original_branch)
                return 1
            stage_paths = (rel,)
        if not _step("commit",
                      git_ops.stage_and_commit(title, *stage_paths)):
            git_ops.checkout(original_branch)
            return 1

        pushed = False
        if not skip_push:
            push_r = git_ops.push_to_remote(new_branch)
            pushed = push_r.ok
            _step(f"push {new_branch}", push_r)
            # Don't abort on push fail — the branch + commit exist locally

        pr_url = ""
        if pushed and not skip_pr and git_ops.gh_available():
            pr_r = git_ops.open_pr(
                title=title, body=body,
                base=target_branch, head=new_branch)
            _step("open PR", pr_r)
            if pr_r.ok:
                pr_url = pr_r.stdout.strip()

        # Return to original branch
        co_r = git_ops.checkout(original_branch)
        _step(f"return to {original_branch}", co_r)

        # Record
        mnemosyne.remember(
            kind="prometheus.applied",
            actor="zeus:operator",
            summary=(f"applied proposal {pid} → branch {new_branch}"
                     + (f"  pr={pr_url}" if pr_url else "")),
            proposal_id=pid,
            branch=new_branch,
            target_branch=target_branch,
            has_patch=has_patch,
            pushed=pushed,
            pr_url=pr_url,
            dry_run=False,
        )
        print(aphrodite.laurel(
            f"applied proposal {pid} → branch {new_branch}"
            + (f" → {pr_url}" if pr_url else "")))
        return 0

    print(aglaia.murmur(
        f"  unknown subcommand {sub!r}; valid: pending, apply"))
    return 2


# CommandResult type forward import for the inner _step closure
from olympus.runtime.git_ops import CommandResult


@hermes.register("chronos", "Chronos — scheduled rituals; "
                             "chronos <rituals|tick|check|ritual>")
def _chronos(argv: list[str]) -> int:
    """Per Delphi 2026-05-19-chronos-arc.md.

    Subcommands:
      chronos rituals             — list configured + next-due times
      chronos tick                — evaluate now; fire matching rituals
      chronos check "<when>"      — would this when-expr fire now? + next 3 due
      chronos ritual add <id> <when> <do>
      chronos ritual remove <id>
    """
    from olympus.runtime.config import load as load_cfg, save as save_cfg
    from olympus.primordials.chronos import (
        chronos, RitualSpec, parse_when, matches_now, next_due,
    )
    from olympus.primordials.nyx import Nyx
    sub = argv[0] if argv else "rituals"

    if sub == "rituals":
        rituals = chronos.load_rituals()
        print(aphrodite.banner(
            "chronos rituals",
            f"{len(rituals)} configured (whitelist: "
            f"{len(__import__('olympus.runtime.errand_whitelist',fromlist=['AUTOMATED_ERRANDS']).AUTOMATED_ERRANDS)})"))
        if not rituals:
            print(aglaia.murmur(
                "  (no rituals — try `invoke chronos ritual add "
                "morning weekday 09:00 today`)"))
            return 0
        now = Nyx.now()
        for r in rituals:
            badge = "✓" if r.enabled else "○"
            nd = next_due(parse_when(r.when), now)
            nd_str = nd.strftime("%Y-%m-%d %H:%M") if nd else "(never)"
            print(aglaia.murmur(
                f"  {badge} {r.id:<24} when={r.when:<18} "
                f"do={r.do:<10} next={nd_str}"))
        return 0

    if sub == "tick":
        fired = chronos.tick()
        print(aphrodite.banner(
            "chronos tick", f"{len(fired)} ritual(s) fired"))
        for f in fired:
            print(aglaia.murmur(
                f"  {f.ritual_id:<24} invoke {f.errand} "
                f"(rc={f.exit_code} {f.elapsed_ms:.0f}ms)"))
            if f.error:
                print(aglaia.murmur(f"    error: {f.error[:120]}"))
        if not fired:
            print(aglaia.murmur(
                "  (no rituals matched the current minute)"))
        return 0

    if sub == "check":
        if len(argv) < 2:
            print(aglaia.murmur(
                'usage: invoke chronos check "<when-expr>"'))
            return 2
        expr = " ".join(argv[1:])
        w = parse_when(expr)
        if not w.valid:
            print(aphrodite.banner(
                "chronos check — invalid", expr))
            print(aglaia.murmur(f"  error: {w.error}"))
            return 1
        now = Nyx.now()
        match = matches_now(w, now)
        print(aphrodite.banner(
            f"chronos check — {expr}",
            f"parsed=valid · matches_now={match}"))
        # Show next 3 due times
        cursor = now
        for i in range(3):
            nd = next_due(w, cursor)
            if nd is None:
                break
            print(aglaia.murmur(
                f"  next #{i+1}: {nd.strftime('%Y-%m-%d %H:%M')}"))
            cursor = nd
        return 0

    if sub == "ritual":
        if len(argv) < 2:
            print(aglaia.murmur(
                "usage: invoke chronos ritual <add|remove> ..."))
            return 2
        op = argv[1]
        if op == "add":
            if len(argv) < 5:
                print(aglaia.murmur(
                    "usage: invoke chronos ritual add <id> "
                    "<when> <do>"))
                print(aglaia.murmur(
                    "  example: invoke chronos ritual add "
                    "morning weekday 09:00 today"))
                return 2
            # `add <id> <when-may-have-spaces> <do>`. The grammar
            # uses up to 2 tokens for when (e.g. "weekday 09:00"),
            # last token is `do`.
            ritual_id = argv[2]
            do_errand = argv[-1]
            when_tokens = argv[3:-1]
            when_expr = " ".join(when_tokens)
            spec = RitualSpec(id=ritual_id, when=when_expr, do=do_errand)
            ok, err = spec.validate()
            if not ok:
                print(aglaia.murmur(f"  invalid spec: {err}"))
                return 1
            cfg = load_cfg()
            existing = {r.get("id") for r in cfg.chronos.rituals}
            if ritual_id in existing:
                print(aglaia.murmur(
                    f"  ritual id {ritual_id!r} already exists; "
                    "remove first"))
                return 1
            cfg.chronos.rituals.append({
                "id": ritual_id, "when": when_expr,
                "do": do_errand, "enabled": True,
            })
            save_cfg(cfg)
            print(aphrodite.laurel(
                f"added ritual '{ritual_id}' → "
                f"when='{when_expr}' do={do_errand}"))
            return 0
        if op == "remove":
            if len(argv) < 3:
                print(aglaia.murmur(
                    "usage: invoke chronos ritual remove <id>"))
                return 2
            ritual_id = argv[2]
            cfg = load_cfg()
            before = len(cfg.chronos.rituals)
            cfg.chronos.rituals = [
                r for r in cfg.chronos.rituals
                if r.get("id") != ritual_id]
            after = len(cfg.chronos.rituals)
            if after == before:
                print(aglaia.murmur(
                    f"  no ritual with id {ritual_id!r}"))
                return 1
            save_cfg(cfg)
            print(aphrodite.laurel(f"removed ritual '{ritual_id}'"))
            return 0
        print(aglaia.murmur(f"  unknown ritual op {op!r}"))
        return 2

    print(aglaia.murmur(
        f"  unknown subcommand {sub!r}; "
        "valid: rituals, tick, check, ritual"))
    return 2


@hermes.register("argos", "Argos colony — fs watcher management; "
                           "argos <scan|watches|watch>")
def _argos(argv: list[str]) -> int:
    """Per Delphi 2026-05-19-argos-eyes-arc.md.

    Subcommands:
      argos scan                    — run colony scan; report fs changes
      argos watches                 — list configured watches
      argos watch add <id> <path> [--glob G] [--action A]
      argos watch remove <id>
    """
    from olympus.runtime.config import load as load_cfg, save as save_cfg
    from olympus.monsters.argos.eyes.eye_filesystem import (
        WatchSpec, ERRAND_WHITELIST,
    )
    sub = argv[0] if argv else "scan"

    if sub == "scan":
        # The colony already auto-registers FS eyes at import time.
        # Forcing a re-import would risk double-registration; instead
        # we deploy the colony as-is and surface fs.* findings.
        from olympus.monsters.argos.colony import colony
        census = colony.deploy(deposit=True)
        fs_phers = [p for p in census.pheromones
                    if p.slice.startswith("filesystem/")]
        other = [p for p in census.pheromones
                 if not p.slice.startswith("filesystem/")]
        print(aphrodite.banner(
            "argos scan",
            f"{census.count} pheromone(s) "
            f"({len(fs_phers)} fs · {len(other)} substrate)"))
        if fs_phers:
            print(aglaia.section("filesystem changes"))
            for p in fs_phers[:20]:
                print(aglaia.murmur(
                    f"  {p.kind:<6} {p.detail[:100]}"))
        return 0

    if sub == "watches":
        cfg = load_cfg()
        watches = cfg.argos.watches or []
        print(aphrodite.banner(
            "argos watches", f"{len(watches)} configured"))
        if not watches:
            print(aglaia.murmur(
                "  (no watches configured — try "
                "`invoke argos watch add <id> <path>`)"))
            return 0
        for w in watches:
            wid = w.get("id", "?")
            path = w.get("path", "?")
            glob = w.get("glob", "*")
            action = w.get("action", "alert")
            enabled = w.get("enabled", True)
            badge = "✓" if enabled else "○"
            print(aglaia.murmur(
                f"  {badge} {wid:<24} {path}  glob={glob}  "
                f"action={action}"))
        return 0

    if sub == "watch":
        if len(argv) < 2:
            print(aglaia.murmur(
                "usage: invoke argos watch <add|remove> ..."))
            return 2
        op = argv[1]
        if op == "add":
            if len(argv) < 4:
                print(aglaia.murmur(
                    "usage: invoke argos watch add <id> <path> "
                    "[--glob G] [--action alert|errand:<name>]"))
                return 2
            wid = argv[2]; path = argv[3]
            glob = "*"; action = "alert"
            i = 4
            while i < len(argv):
                if argv[i] == "--glob" and i + 1 < len(argv):
                    glob = argv[i + 1]; i += 2; continue
                if argv[i] == "--action" and i + 1 < len(argv):
                    action = argv[i + 1]; i += 2; continue
                i += 1
            new_spec = WatchSpec(id=wid, path=path,
                                  glob=glob, action=action)
            ok, err = new_spec.validate()
            if not ok:
                print(aglaia.murmur(f"  invalid spec: {err}"))
                if action.startswith("errand:"):
                    print(aglaia.murmur(
                        f"  errand whitelist: {sorted(ERRAND_WHITELIST)}"))
                return 1
            cfg = load_cfg()
            existing_ids = {w.get("id") for w in cfg.argos.watches}
            if wid in existing_ids:
                print(aglaia.murmur(
                    f"  watch id {wid!r} already exists; remove first"))
                return 1
            cfg.argos.watches.append({
                "id": wid, "path": path, "glob": glob,
                "action": action, "enabled": True,
            })
            save_cfg(cfg)
            print(aphrodite.laurel(f"added watch '{wid}' → {path}"))
            print(aglaia.murmur(
                "  (takes effect on next `invoke argos scan` or daemon "
                "iteration after import-time re-register)"))
            return 0
        if op == "remove":
            if len(argv) < 3:
                print(aglaia.murmur(
                    "usage: invoke argos watch remove <id>"))
                return 2
            wid = argv[2]
            cfg = load_cfg()
            before = len(cfg.argos.watches)
            cfg.argos.watches = [w for w in cfg.argos.watches
                                  if w.get("id") != wid]
            after = len(cfg.argos.watches)
            if after == before:
                print(aglaia.murmur(f"  no watch with id {wid!r}"))
                return 1
            save_cfg(cfg)
            print(aphrodite.laurel(f"removed watch '{wid}'"))
            return 0
        print(aglaia.murmur(f"  unknown watch op {op!r}"))
        return 2

    print(aglaia.murmur(
        f"  unknown subcommand {sub!r}; "
        "valid: scan, watches, watch"))
    return 2


@hermes.register("recall", "Hippocrene — semantic recall over Mnemosyne; "
                            "recall \"<query>\" [-k N] [--kinds K1,K2] "
                            "[--rebuild] [--include-test-seeds] [--stats]")
def _recall(argv: list[str]) -> int:
    """Per Delphi 2026-05-19-hippocrene-arc.md."""
    from olympus.heroes.hippocrene import hippocrene
    k = 5
    only_kinds: list[str] | None = None
    rebuild = False
    include_test_seeds = False
    stats_only = False
    query_parts: list[str] = []
    i = 0
    while i < len(argv):
        a = argv[i]
        if a == "-k" and i + 1 < len(argv):
            try:
                k = int(argv[i + 1])
            except ValueError:
                pass
            i += 2; continue
        if a == "--kinds" and i + 1 < len(argv):
            only_kinds = [s.strip() for s in argv[i + 1].split(",")
                          if s.strip()]
            i += 2; continue
        if a == "--rebuild":
            rebuild = True; i += 1; continue
        if a == "--include-test-seeds":
            include_test_seeds = True; i += 1; continue
        if a == "--stats":
            stats_only = True; i += 1; continue
        query_parts.append(a); i += 1

    if stats_only:
        if not hippocrene._records:
            hippocrene.index(only_kinds=only_kinds,
                              include_test_seeds=include_test_seeds)
        s = hippocrene.stats()
        if _GLOBAL_FLAGS["json"]:
            import dataclasses as _dc
            print(_json.dumps(_dc.asdict(s), default=str, indent=2))
            return 0
        print(aphrodite.banner(
            "recall — Hippocrene stats",
            f"embedder: {s.embedder} · {s.docs_total} docs · "
            f"{s.vocab_size} terms"))
        for kind, count in sorted(s.docs_by_kind.items(),
                                    key=lambda kv: -kv[1]):
            print(aglaia.murmur(f"  {kind:<35} {count:>5}"))
        return 0

    if rebuild:
        n = hippocrene.rebuild(only_kinds=only_kinds,
                                include_test_seeds=include_test_seeds)
        print(aglaia.murmur(f"  re-indexed {n} record(s)"))

    query = " ".join(query_parts).strip()
    if not query:
        print(aglaia.murmur(
            "usage: invoke recall \"<query>\" [-k N] [--kinds K1,K2]"))
        return 2

    results = hippocrene.recall(
        query, k=k, only_kinds=only_kinds,
        include_test_seeds=include_test_seeds)

    if _GLOBAL_FLAGS["json"]:
        import dataclasses as _dc
        print(_json.dumps([_dc.asdict(r) for r in results],
                          default=str, indent=2))
        return 0

    print(aphrodite.banner(
        f"recall — \"{query[:50]}\"",
        f"{len(results)} hit(s)"))
    if not results:
        print(aglaia.murmur("  (no matches)"))
        return 0
    print(aglaia.murmur(
        f"  {'score':<6} {'kind':<32} {'when':<22} summary"))
    print(aglaia.murmur(f"  {'─'*6} {'─'*32} {'─'*22} {'─'*40}"))
    for r in results:
        when = (r.remembered_at or "")[:22]
        summary = (r.summary or "")[:70]
        print(aglaia.murmur(
            f"  {r.score:<6.3f} {r.kind:<32} {when:<22} {summary}"))
    return 0


@hermes.register("vault", "Hades — secrets vault; "
                           "vault <status|deposit|forget|migrate> [name]")
def _vault(argv: list[str]) -> int:
    """Per Delphi 2026-05-19-hades-arc.md. Manages secrets via the OS
    keychain. Constitution: deposit/forget stay CLI-only (Throne can
    only read status)."""
    from olympus.olympians.hades import (
        hades, ENV_OVERRIDES, PLAINTEXT_SENTINEL,
    )
    sub = argv[0] if argv else "status"

    if sub == "status":
        print(aphrodite.banner(
            "vault — Hades strongbox",
            f"backend: {hades.backend_name()} · "
            f"available: {hades.available()}"))
        # Show every known secret name
        names = sorted(set(ENV_OVERRIDES.keys()))
        for name in names:
            st = hades.status(name)
            badge = {
                "env": "✓ env",
                "keychain": "✓ keychain (encrypted)",
                "plaintext": "! PLAINTEXT (run `invoke vault migrate`)",
                "unset": "○ unset",
            }.get(st.location, st.location)
            print(aglaia.murmur(
                f"  {name:<28} {badge}"
                + (f" · {st.bytes_known}b · sha:{st.sha256_prefix}"
                   if st.bytes_known else "")))
        return 0

    if sub == "deposit":
        if len(argv) < 2:
            print(aglaia.murmur(
                "usage: invoke vault deposit <name>"))
            return 1
        name = argv[1]
        if not hades.available():
            print(aglaia.murmur(
                "no keyring backend available; cannot deposit"))
            return 1
        import getpass
        try:
            secret = getpass.getpass(f"value for {name} (input hidden): ")
        except (KeyboardInterrupt, EOFError):
            print(); return 1
        if not secret:
            print(aglaia.murmur("(empty input — refusing)"))
            return 1
        hades.deposit(name, secret)
        print(aphrodite.laurel(
            f"deposited '{name}' to {hades.backend_name()}"))
        return 0

    if sub == "forget":
        if len(argv) < 2:
            print(aglaia.murmur("usage: invoke vault forget <name>"))
            return 1
        name = argv[1]
        ok = hades.forget(name)
        if ok:
            print(aphrodite.laurel(f"forgot '{name}' from keychain"))
        else:
            print(aglaia.murmur(f"'{name}' was not in keychain"))
        return 0

    if sub == "migrate":
        from olympus.runtime.config import migrate_plaintext_to_hades
        result = migrate_plaintext_to_hades()
        print(aphrodite.banner(
            "vault migrate",
            f"migrated: {result['migrated']} · where: {result['where']}"))
        print(aglaia.murmur(f"  {result['reason']}"))
        return 0 if result["migrated"] or "already" in result["where"] else 1

    print(aglaia.murmur(
        f"unknown subcommand: {sub!r}; valid: "
        "status, deposit, forget, migrate"))
    return 1


@hermes.register("spend", "Plutus — LLM cost ledger + budget; "
                            "spend [--today|--7d|--30d|--all|--budget|"
                            "--acknowledge-budget [--reason \"...\"]]")
def _spend(argv: list[str]) -> int:
    """Per Delphi 2026-05-19-plutus-arc.md + 2026-05-19-plutus-budget-arc.md.

    Default: cost report. --budget shows budget status. --acknowledge-budget
    records an operator ack that lifts the LLM-call refusal until the
    next breach."""
    from olympus.heroes.plutus import plutus
    # Per budget arc — handle the budget surfaces first
    if "--acknowledge-budget" in argv:
        reason = ""
        if "--reason" in argv:
            i = argv.index("--reason")
            if i + 1 < len(argv):
                reason = argv[i + 1]
        plutus.acknowledge_breach(reason=reason)
        print(aphrodite.laurel(
            "budget breach acknowledged — LLM calls re-enabled "
            "until next threshold crossing"))
        if reason:
            print(aglaia.murmur(f"  reason: {reason}"))
        return 0
    if "--budget" in argv:
        s = plutus.budget_status()
        if _GLOBAL_FLAGS["json"]:
            print(_json.dumps(s, indent=2))
            return 0
        if not s.get("enabled"):
            print(aphrodite.banner(
                "spend --budget", "budget enforcement: DISABLED"))
            print(aglaia.murmur(
                "  to enable: set plutus.budget.enabled = true in "
                "state/config.json and pick at least one threshold"))
            return 0
        print(aphrodite.banner(
            "spend — budget status",
            f"warn at {s.get('warn_at_pct', 80)}% · over at 100%"))
        for key in ("daily", "weekly", "monthly"):
            e = s.get(key) or {}
            if e.get("state") == "unset":
                continue
            badge = {"ok": "✓", "warn": "!", "over": "✗"}.get(
                e["state"], "?")
            print(aglaia.murmur(
                f"  {badge} {key:<10} ${e['spent']:>7.4f} / "
                f"${e['ceiling']:>7.4f}  ({e['pct']:>5.1f}%)  "
                f"[{e['state']}]"))
        if plutus.is_over_budget():
            if plutus.breach_since_ack():
                print(aglaia.murmur(
                    "  ✗ LLM CALLS REFUSED — "
                    "run `invoke spend --acknowledge-budget`"))
            else:
                print(aglaia.murmur(
                    "  (over budget but acknowledged; LLM calls "
                    "continue until next threshold crossing)"))
        return 0
    window = "all"
    for a in argv:
        if a == "--today":
            window = "today"
        elif a in ("--7d", "--7days"):
            window = "7d"
        elif a in ("--30d", "--30days"):
            window = "30d"
        elif a in ("--24h",):
            window = "24h"
        elif a == "--all":
            window = "all"
    report = plutus.tally(window=window)

    if _GLOBAL_FLAGS["json"]:
        print(_json.dumps(report.to_dict(), default=str, indent=2))
        return 0

    print(aphrodite.banner(
        f"spend — Plutus ledger ({window})",
        f"${report.estimated_usd:.4f} estimated · "
        f"{report.total_calls} call(s) · "
        f"{report.total_input_tokens:,}in / "
        f"{report.total_output_tokens:,}out tokens"))

    if not report.total_calls:
        print(aglaia.murmur("  (no LLM calls in this window)"))
        return 0

    def _table(title: str, rows: dict, max_rows: int = 10) -> None:
        print(aglaia.section(title))
        for key, b in list(rows.items())[:max_rows]:
            print(aglaia.murmur(
                f"  {key:<28} {b.calls:>4}× "
                f"{b.input_tokens:>9,}in {b.output_tokens:>9,}out "
                f"${b.estimated_usd:>8.4f}"))

    _table("by bridge",    report.by_bridge)
    _table("by role",      report.by_role)
    _table("by model",     report.by_model)
    _table("by day (newest first)", report.by_day, max_rows=14)

    if report.unknown_model_calls:
        print(aglaia.murmur(
            f"  note: {report.unknown_model_calls} call(s) against "
            f"unknown model(s) — $0 in estimate. "
            f"Models: {', '.join(report.unknown_models[:5])}"))
    return 0


@hermes.register("throne", "Zeus's Throne — chat in plain English; "
                            "throne [\"<one-shot question>\"] [--voice]")
def _throne(argv: list[str]) -> int:
    """The unified front door. No args → REPL. Args → one-shot.

    Per Delphi 2026-05-19-throne-arc.md (base) +
    2026-05-19-throne-voice-arc.md (--voice flag).
    """
    from olympus.throne.repl import run as repl_run, one_shot

    # Per voice arc: --voice flag pipes responses through `say`
    speak_responses = "--voice" in argv
    if speak_responses:
        argv = [a for a in argv if a != "--voice"]

    if argv:
        question = " ".join(argv)
        rc = one_shot(question)
        if speak_responses and rc == 0:
            # Speak the most recent throne.turn answer
            from olympus.titans.mnemosyne import mnemosyne
            from olympus.runtime.voice import speak, get_backend
            if get_backend().available():
                turns = mnemosyne.recall("throne.turn")
                if turns:
                    speak(turns[-1].body.get("answer_head", ""))
        return rc
    return repl_run(speak_responses=speak_responses)


@hermes.register("agora", "build the operator web UI — agora [--open] [--port N]")
def _agora(argv: list[str]) -> int:
    from olympus.agora import build, open_in_browser
    from olympus.runtime.config import load as load_config
    cfg = load_config()
    port = cfg.agora.port
    host = cfg.agora.host
    open_it = "--open" in argv
    i = 0
    while i < len(argv):
        if argv[i] == "--port" and i + 1 < len(argv):
            port = int(argv[i + 1]); i += 2; continue
        if argv[i] == "--host" and i + 1 < len(argv):
            host = argv[i + 1]; i += 2; continue
        i += 1
    api_base = f"http://{host}:{port}"
    out = build(api_base=api_base, interval_seconds=5.0)
    print(aphrodite.laurel(f"agora built — {out}"))
    print(aglaia.murmur(f"  pages poll {api_base} every 5.0s"))
    print(aglaia.murmur(f"  ensure `invoke serve --port {port}` is running"))
    if open_it:
        open_in_browser(out)
        print(aglaia.murmur("  opened in browser"))
    else:
        print(aglaia.murmur(f"  open with: open {out}"))
    return 0


@hermes.register("doctor", "single-screen health diagnostic (akropolis arc)")
def _doctor(_argv: list[str]) -> int:
    from olympus.runtime.doctor import diagnose
    report = diagnose()
    if _GLOBAL_FLAGS["json"]:
        import dataclasses as _dc
        print(_json.dumps(_dc.asdict(report), default=str, indent=2))
        return 0
    print(aphrodite.banner(
        f"doctor — olympus {report.olympus_version}",
        f"{report.ok_count} ok · {report.warn_count} warn · "
        f"{report.fail_count} fail"))
    print(aglaia.murmur(f"  {report.platform} · py{report.python_version}"))
    rows = [
        (f.name,
         {"ok": "✓", "warn": "!", "fail": "✗"}.get(f.status, "?"),
         f.detail[:80])
        for f in report.findings
    ]
    print(aphrodite.table(("check", "?", "detail"), rows))
    return 0 if report.fail_count == 0 else 1


@hermes.register("bench", "Heracles benchmark — bench [--runner heuristic]")
def _bench(argv: list[str]) -> int:
    from olympus.heroes.heracles import run_canonical_benchmark
    runner = "heuristic"
    i = 0
    while i < len(argv):
        if argv[i] == "--runner" and i + 1 < len(argv):
            runner = argv[i + 1]; i += 2; continue
        i += 1
    report = run_canonical_benchmark(runner=runner)
    if _GLOBAL_FLAGS["json"]:
        import dataclasses as _dc
        print(_json.dumps(_dc.asdict(report), default=str, indent=2))
        return 0
    print(aphrodite.banner(
        f"Heracles — benchmark ({runner})",
        f"{report.passed}/{report.total} pass · "
        f"{report.regressed} regression(s)"))
    rows = [
        (r.task,
         "✓" if r.correct else ("REG" if r.regressed else "✗"),
         f"{r.latency_ms:.2f}ms",
         (r.error or str(r.output))[:50])
        for r in report.results
    ]
    print(aphrodite.table(
        ("task", "?", "latency", "output / error"), rows))
    return 0 if report.passed == report.total else 1


@hermes.register("scale", "Atalanta scalability — scale [--sizes 10,100,1000]")
def _scale(argv: list[str]) -> int:
    from olympus.heroes.atalanta import atalanta
    sizes = [10, 100, 1000]
    op_name = "mnemosyne-recall"
    i = 0
    while i < len(argv):
        if argv[i] == "--sizes" and i + 1 < len(argv):
            sizes = [int(s) for s in argv[i + 1].split(",")]
            i += 2; continue
        if argv[i] == "--op" and i + 1 < len(argv):
            op_name = argv[i + 1]; i += 2; continue
        i += 1
    from olympus.titans.mnemosyne import mnemosyne

    def build_state(n: int) -> str:
        kind = f"scale_test_{n}"
        for j in range(n):
            mnemosyne.remember(
                kind=kind, actor="atalanta:scale-bench",
                summary=f"scale row {j}", row=j,
            )
        return kind

    def run_op(kind: str) -> None:
        _ = mnemosyne.recall(kind)

    report = atalanta.scale(
        op_name, build_state, run_op,
        sizes=sizes, iterations_per_size=10,
    )
    if _GLOBAL_FLAGS["json"]:
        import dataclasses as _dc
        print(_json.dumps(_dc.asdict(report), default=str, indent=2))
        return 0
    print(aphrodite.banner(
        f"Atalanta — scalability ({op_name})",
        f"{len(report.points)} sizes"))
    rows = [
        (str(p.size), f"{p.iterations}",
         f"{p.p50_ms:.2f}", f"{p.p95_ms:.2f}",
         f"{p.p99_ms:.2f}", f"{p.memory_delta_kb:.0f}KB")
        for p in report.points
    ]
    print(aphrodite.table(
        ("size", "iters", "p50ms", "p95ms", "p99ms", "Δmem"), rows))
    return 0


@hermes.register("fault-inject", "Typhon fault — fault-inject <scenario> --confirm [--no-revert]")
def _fault_inject(argv: list[str]) -> int:
    from olympus.monsters.typhon import typhon
    if not argv:
        print(f"usage: invoke fault-inject <scenario> --confirm")
        print(f"  injectable: {', '.join(typhon.injectable())}")
        return 2
    scenario = argv[0]
    confirm = "--confirm" in argv
    no_revert = "--no-revert" in argv
    if not confirm:
        print(aphrodite.wine_dark(
            f"  refusing to inject {scenario!r} without --confirm — "
            "this actually breaks state"))
        return 1
    try:
        injection = typhon.inject(scenario, confirm=True)
    except Exception as exc:  # noqa: BLE001
        print(aphrodite.wine_dark(f"  injection failed: {exc}"))
        return 1
    print(aphrodite.banner(
        f"Typhon — injected {scenario}",
        f"at {injection.injected_at[:19]}"))
    print(aglaia.murmur(f"  detail: {injection.detail}"))
    if no_revert:
        print(aphrodite.wine_dark(
            "  --no-revert: state remains disturbed; revert manually"))
    else:
        injection.revert()
        print(aphrodite.laurel(f"  reverted (state restored)"))
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


_WELCOME_EXEMPT = {
    "setup", "help", "version", "kindle", "describe",
    "bring-forth", "pantheon", "list", "agora",
}


def _maybe_welcome(argv: list[str]) -> bool:
    """If the operator hasn't kindled the hearth yet and isn't running
    an exempt command (setup/help/etc.), print a friendly welcome
    and return True (caller should exit early without dispatching)."""
    if not argv:
        return False
    cmd = argv[0]
    if cmd in _WELCOME_EXEMPT or cmd.startswith("-"):
        return False
    try:
        from olympus.olympians.hestia import hestia
        if hestia.is_lit():
            return False
    except Exception:  # noqa: BLE001
        return False
    # Hestia is unlit AND the operator is trying to do real work.
    sys.stdout.write(
        "\n"
        "═══════════════════════════════════════════════════════════\n"
        "  welcome to Olympus, stranger.\n"
        "═══════════════════════════════════════════════════════════\n"
        "\n"
        "  Olympus is a cognitive substrate built in the shape of\n"
        "  Greek mythology. It hasn't met you yet — Hestia's hearth\n"
        "  is unlit.\n"
        "\n"
        "  To begin (the friendly walk-through, ~5 minutes):\n"
        "      invoke setup\n"
        "\n"
        "  If you're in a hurry:\n"
        "      invoke kindle <name> \"<vocation>\"\n"
        "      invoke session\n"
        "\n"
        "  If you want the full picture first:\n"
        "      cat codex/QUICKSTART.md\n"
        "\n"
    )
    return True


def main(argv: list[str] | None = None) -> int:
    """Entry point. `invoke ...` (pip-installed) and `./scripts/invoke ...`
    both land here."""
    if argv is None:
        argv = sys.argv[1:]
    _load_plugins_once()
    if _maybe_welcome(argv):
        return 0
    return hermes.dispatch(argv)


if __name__ == "__main__":
    sys.exit(main())
