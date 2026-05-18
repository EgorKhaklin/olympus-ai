"""olympus.cli — the single entry point.

Hermes dispatches every named errand. To run a god, ask Hermes:

    invoke prime                  # session prime via Odysseus
    invoke consult chart          # Urania's brain-map
    invoke consult population     # Coeus's tier counts
    invoke consult hymn           # Polyhymnia's Styx hymn
    invoke bring-forth            # Rhea ensures directories
    invoke kindle <name> <vocation>  # Hestia lights the hearth
    invoke remember <kind> <actor> <summary>   # Mnemosyne
    invoke swear <by> <statement>              # Styx
    invoke verify                 # Tisiphone audits Styx
    invoke labors                 # Heracles runs the canonical 12
    invoke pantheon               # full pantheon listing
    invoke blessing               # Thalia's closing
"""
from __future__ import annotations

import pathlib
import sys

from olympus.olympians.hermes import hermes
from olympus.olympians.aphrodite import aphrodite
from olympus.graces.aglaia import aglaia
from olympus.primordials.gaia import root as _gaia_root


# ─────────────────────────────────────────────────────────────────────
# Errands — every public capability is registered here
# ─────────────────────────────────────────────────────────────────────


@hermes.register("prime", "session prime — Odysseus takes bearing")
def _prime(_argv: list[str]) -> int:
    from olympus.titans.rhea import rhea
    from olympus.olympians.hestia import hestia
    from olympus.heroes.odysseus import odysseus
    rhea.bring_forth()
    print(aglaia.section("Olympus — session prime"))
    if not hestia.is_lit():
        print(aphrodite.wine_dark(
            "hearth is unlit — run `invoke kindle <name> <vocation>` first"
        ))
        return 1
    h = hestia.hearth()
    print(aphrodite.laurel(f"hearth lit as '{h.name}' (kindled {h.kindled_at})"))
    print(aglaia.murmur(f"  vocation: {h.vocation}"))
    bearing = odysseus.take_bearing()
    if bearing.last_summary:
        print(aphrodite.lightning(
            f"last memory: {bearing.last_kind} — {bearing.last_summary}"
        ))
    else:
        print(aglaia.murmur("  no prior memories"))
    print(aglaia.murmur(f"  total memories: {bearing.total_memories}"))
    return 0


@hermes.register("bring-forth", "Rhea ensures all required directories exist")
def _bring_forth(_argv: list[str]) -> int:
    from olympus.titans.rhea import rhea
    statuses = rhea.bring_forth()
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


@hermes.register("labors", "Heracles performs the assigned labors")
def _labors(_argv: list[str]) -> int:
    from olympus.heroes.heracles import heracles, CANONICAL_LABORS
    for labor in CANONICAL_LABORS:
        heracles.assign(labor)
    verdicts = heracles.perform()
    rows = [(str(v.labor.number), v.labor.name, v.labor.target,
             "+" if v.survived else "-", v.detail) for v in verdicts]
    print(aphrodite.table(("#", "labor", "target", "result", "detail"), rows))
    failed = sum(1 for v in verdicts if not v.survived)
    if failed:
        print(aphrodite.wine_dark(f"{failed} labor(s) failed"))
        return 1
    print(aphrodite.laurel("all twelve labors survived"))
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
        rows = [(k, str(v)) for k, v in result.items()]
        print(aphrodite.table(("tier", "modules"), rows))
        return 0
    if what == "hymn":
        from olympus.muses.polyhymnia import polyhymnia
        h = polyhymnia.hymn()
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
        for f in b.findings:
            print(f"  · {f}")
        print("\nRecommendations:")
        for r in b.recommendations:
            print(f"  · {r}")
        return 0
    print(aphrodite.wine_dark(f"unknown oracle: {what!r}"))
    return 2


@hermes.register("pantheon", "show the complete pantheon")
def _pantheon(_argv: list[str]) -> int:
    pantheon_md = _gaia_root.child("codex", "PANTHEON.md")
    if not pantheon_md.exists():
        print(aphrodite.wine_dark("codex/PANTHEON.md missing"))
        return 1
    sys.stdout.write(pantheon_md.read_text(encoding="utf-8"))
    return 0


@hermes.register("blessing", "Thalia bestows a closing blessing")
def _blessing(_argv: list[str]) -> int:
    from olympus.muses.thalia_muse import thalia_muse
    from olympus.muses.erato import erato
    print(erato.farewell())
    print(aphrodite.laurel(thalia_muse.blessing()))
    return 0


# ─────────────────────────────────────────────────────────────────────
# Loop + action + meta + correlation + labors errands
# ─────────────────────────────────────────────────────────────────────


@hermes.register("session", "run one cognitive-loop session — optional directive")
def _session(argv: list[str]) -> int:
    from olympus.session import run_session
    directive = " ".join(argv) if argv else None
    r = run_session(directive)
    print(aglaia.section(f"session {r.session_id[:16]}"))
    if r.directive:
        print(aglaia.murmur(f"  directive: {r.directive}"))
    rows = [
        ("HYDRA",      f"{r.hydra_findings} findings ({r.hydra_alerts} alerts, {r.hydra_drifts} drifts)"),
        ("Argos",      f"{r.argos_pheromones} pheromones ({r.argos_alerts} alerts)"),
        ("Athena",     f"brief {r.brief_label!r} — {r.brief_findings} findings, "
                       f"{r.brief_recommendations} recs, confidence={r.brief_confidence:.2f}"),
        ("Hephaestus", f"{r.proposals_count} proposal(s) surfaced"),
        ("Momus",      f"{r.contests_count} contest(s) issued"),
        ("Actions",    f"{r.actions_promoted} promoted "
                       f"({r.actions_autoratified} auto, "
                       f"{r.actions_queued_for_zeus} queued, "
                       f"{r.actions_delphi_pending} delphi)"),
        ("Styx",       f"{r.styx_total} oaths · chain {'intact' if r.styx_intact else 'BROKEN'}"),
    ]
    print(aphrodite.table(("phase", "outcome"), rows))
    if r.error:
        print(aphrodite.wine_dark(f"  ERROR: {r.error}"))
        return 1
    return 0


@hermes.register("action", "action queue — action <review|delphi|ratify|reject>")
def _action(argv: list[str]) -> int:
    from olympus.action import action_queue
    if not argv:
        print("usage: invoke action <review|delphi|ratify <id> [quote]|reject <id> [reason]>")
        return 2
    verb = argv[0]
    if verb == "review":
        pending = action_queue.pending()
        if not pending:
            print(aglaia.murmur("  no actions await Zeus"))
            return 0
        rows = [(a.id[:24], a.risk_class, a.summary[:80]) for a in pending]
        print(aphrodite.table(("id", "risk", "summary"), rows))
        return 0
    if verb == "delphi":
        delphi = action_queue.delphi_pending()
        if not delphi:
            print(aglaia.murmur("  no actions awaiting Delphi"))
            return 0
        rows = [(a.id[:24], a.risk_class, a.summary[:80]) for a in delphi]
        print(aphrodite.table(("id", "risk", "summary"), rows))
        return 0
    if verb == "ratify" and len(argv) >= 2:
        action_id = argv[1]
        quote = " ".join(argv[2:]) if len(argv) > 2 else "ratified via CLI"
        try:
            a = action_queue.ratify(action_id, quote=quote)
            print(aphrodite.laurel(f"ratified {a.id[:24]}"))
            return 0
        except (KeyError, RuntimeError) as exc:
            print(aphrodite.wine_dark(str(exc)))
            return 1
    if verb == "reject" and len(argv) >= 2:
        action_id = argv[1]
        reason = " ".join(argv[2:]) if len(argv) > 2 else "rejected via CLI"
        try:
            a = action_queue.reject(action_id, reason=reason)
            print(aphrodite.laurel(f"rejected {a.id[:24]}"))
            return 0
        except KeyError as exc:
            print(aphrodite.wine_dark(str(exc)))
            return 1
    print(aphrodite.wine_dark(f"unknown action subcommand: {verb!r}"))
    return 2


@hermes.register("meta", "Olympus self-portrait (Olympus reasoning about Olympus)")
def _meta(_argv: list[str]) -> int:
    from olympus.meta import portrait
    print(portrait().as_text())
    return 0


@hermes.register("correlate", "Argos CorrelationEngine — cross-eye patterns over a time window")
def _correlate(argv: list[str]) -> int:
    from olympus.monsters.argos.correlation import correlation
    from olympus.monsters.argos.colony import colony
    window_hours = float(argv[0]) if argv else 24.0
    known_eyes = [e.NAME for e in colony.eyes()]
    report = correlation.correlate(window_hours=window_hours, known_eyes=known_eyes)
    print(aphrodite.banner("Argos correlation",
                           f"window: {window_hours}h · {report.pheromones_considered} pheromone(s)"))
    if report.clusters:
        print(aglaia.subhead(f"Clusters ({len(report.clusters)})"))
        for c in report.clusters[:5]:
            print(f"  · slice {c.slice!r}: {len(c.eyes)} eye(s) "
                  f"({', '.join(c.eyes[:3])}{'...' if len(c.eyes) > 3 else ''}) — "
                  f"intensity sum {c.intensity_sum:.1f}")
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


@hermes.register("console", "Zeus operator console — review and ratify pending actions")
def _console(_argv: list[str]) -> int:
    from olympus.olympians.zeus import zeus
    touched = zeus.console()
    print(aglaia.murmur(f"  Zeus touched {touched} action(s)"))
    return 0


def main(argv: list[str] | None = None) -> int:
    """Entry point. `invoke ...` (pip-installed) and `./scripts/invoke ...`
    both land here."""
    if argv is None:
        argv = sys.argv[1:]
    return hermes.dispatch(argv)


if __name__ == "__main__":
    sys.exit(main())
