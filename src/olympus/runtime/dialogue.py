"""olympus.runtime.dialogue — pattern-matched Q&A over substrate records.

`invoke ask "<question>"` answers operator questions in plain English
*from the substrate's own records*. NOT an LLM — pattern-matched
against query templates. Limited, but honest: every answer cites the
Mnemosyne kind(s) it drew from, so the operator can verify.

The templates are intentionally simple. The point is to give the
operator a fast read on common questions without spinning up multiple
`invoke` commands. For anything more nuanced, the operator falls
back to the dedicated errands or reads the JSONL directly.

Per Delphi 2026-05-18-labyrinth-arc.md.
"""
from __future__ import annotations

import datetime
import re
from dataclasses import dataclass, field
from typing import Callable

from olympus.primordials.nyx import Nyx
from olympus.titans.mnemosyne import mnemosyne


@dataclass
class Answer:
    """One answer — text body + sources."""
    question: str
    matched_template: str
    text: str
    sources: list[str] = field(default_factory=list)
    answered_at: str = ""

    def __post_init__(self) -> None:
        if not self.answered_at:
            self.answered_at = Nyx.now().isoformat()


# ─────────────────────────────────────────────────────────
# Pattern definitions — each is (regex, template-name, answer-fn)
# ─────────────────────────────────────────────────────────


def _ans_what_happened(_match: re.Match) -> tuple[str, list[str]]:
    """What happened recently."""
    sources: list[str] = []
    sessions = mnemosyne.recall("session.completed")[-5:]
    sources.append("session.completed")
    ratifications = mnemosyne.recall("action.ratified")[-3:]
    sources.append("action.ratified")
    panics = [m for m in mnemosyne.recall("pan.transition")
              if (m.body or {}).get("transition") == "enter"]
    sources.append("pan.transition")
    lines = [f"Last {len(sessions)} session(s):"]
    for s in sessions:
        body = s.body or {}
        lines.append(
            f"  · {s.remembered_at[:19]} — "
            f"hydra={body.get('hydra_findings', 0)} "
            f"argos={body.get('argos_pheromones', 0)} "
            f"proposals={body.get('proposals_count', 0)}"
        )
    if ratifications:
        lines.append("")
        lines.append(f"Last {len(ratifications)} ratification(s):")
        for r in ratifications:
            lines.append(f"  · {r.remembered_at[:19]} — {r.summary[:80]}")
    if panics:
        lines.append("")
        lines.append(f"Total panic-entries on record: {len(panics)}")
    return "\n".join(lines), sources


def _ans_what_worried(_match: re.Match) -> tuple[str, list[str]]:
    """What are we worried about."""
    sources: list[str] = []
    vinds = mnemosyne.recall("cassandra.vindicated")
    sources.append("cassandra.vindicated")
    from olympus.olympians.pan import pan
    panic_state = pan.evaluate()
    sources.append("pan.transition (current)")
    lines = []
    if panic_state.panicked:
        lines.append(f"Pan is in PANIC: {panic_state.detail}")
    else:
        lines.append("Pan: calm (no current panic).")
    lines.append("")
    if vinds:
        lines.append(f"Cassandra has recorded {len(vinds)} vindication(s) "
                     f"— warnings dismissed that later recurred:")
        for v in vinds[-5:]:
            body = v.body or {}
            lines.append(f"  · slice {body.get('slice', '?')!r} "
                         f"({body.get('dismissal_kind', '?')}, "
                         f"{body.get('recurrences_after_dismissal', 0)}x)")
    else:
        lines.append("Cassandra has no vindications on record yet — "
                     "no dismissed warnings have come back.")
    return "\n".join(lines), sources


def _ans_loop_health(_match: re.Match) -> tuple[str, list[str]]:
    """How is the loop / daemon."""
    from olympus.titans.atlas import atlas
    sources = ["atlas.bear / atlas.release"]
    shoulders = atlas.shoulders(recent_releases=5)
    lines = [f"Atlas is carrying {shoulders.current_count} burden(s) right now."]
    if shoulders.current:
        for b in shoulders.current[:5]:
            lines.append(f"  · {b.op} (started {b.started_at[:19]}, "
                         f"owner {b.owner[:20]})")
    if shoulders.recently_released:
        lines.append("")
        lines.append("Recently released:")
        for b in shoulders.recently_released:
            lines.append(f"  · {b.op} → {b.outcome} "
                         f"(at {b.released_at[:19]})")
    return "\n".join(lines), sources


def _ans_who_is(match: re.Match) -> tuple[str, list[str]]:
    """Who is X — describe a named figure."""
    name = (match.group("name") or "").strip().lower()
    from olympus.primordials.gaia import root as _root
    # Try every tier
    tiers = ("primordials", "titans", "olympians", "underworld",
             "fates", "furies", "graces", "muses", "heroes", "monsters")
    candidates: list[tuple[str, str]] = []
    for tier in tiers:
        tier_path = _root.child("src", "olympus", tier)
        if not tier_path.exists():
            continue
        # plain file
        f = tier_path / f"{name}.py"
        if f.exists():
            candidates.append((tier, str(f)))
        # subpackage
        sub = tier_path / name / "__init__.py"
        if sub.exists():
            candidates.append((tier, str(sub)))
    if not candidates:
        return (f"No named figure matches {name!r}. "
                f"Try `invoke list` to see all registered modules."), []
    sources: list[str] = []
    lines = []
    for tier, path in candidates:
        lines.append(f"{name.capitalize()} lives in `{tier}/` at `{path}`.")
        sources.append(path)
        # First docstring line
        try:
            with open(path, "r", encoding="utf-8") as fh:
                content = fh.read()
            ds_start = content.find('"""')
            if ds_start >= 0:
                ds_end = content.find('"""', ds_start + 3)
                if ds_end > ds_start:
                    ds = content[ds_start + 3:ds_end].strip()
                    first = ds.split("\n")[0].strip()
                    lines.append(f"  {first}")
        except Exception:  # noqa: BLE001
            pass
    return "\n".join(lines), sources


def _ans_what_learned(_match: re.Match) -> tuple[str, list[str]]:
    """What has the substrate learned."""
    from olympus.wisdom import wisdom
    w = wisdom()
    sources = ["wisdom (aggregated from many kinds)"]
    lines = [f"Sessions total: {w.sessions_total}"]
    if w.insights:
        lines.append("")
        lines.append("Insights:")
        for i in w.insights[:10]:
            lines.append(f"  · {i}")
    if w.recurring_slices:
        lines.append("")
        lines.append("Recurring slices:")
        for s in w.recurring_slices[:5]:
            lines.append(f"  · {s}")
    return "\n".join(lines), sources


def _ans_help(_match: re.Match) -> tuple[str, list[str]]:
    """List available question patterns."""
    lines = [
        "I can answer these question shapes (pattern-matched):",
        "",
        "  what happened (today | recently | this week)",
        "  what are we worried about",
        "  how is the loop / daemon",
        "  who is <name>           (e.g. 'who is pan')",
        "  what has the substrate learned",
        "  help / how does this work",
        "",
        "For anything else, use `invoke help` to see all errands.",
    ]
    return "\n".join(lines), []


# Ordered: first match wins. Specific before general.
_PATTERNS: list[tuple[re.Pattern, str, Callable]] = [
    (re.compile(r"^(help|how does this work|what can you)", re.I),
     "help", _ans_help),
    (re.compile(r"^what.*(happen(ed)?|recent|this week|today)", re.I),
     "what-happened", _ans_what_happened),
    (re.compile(r"^what.*(worried|worrying|concern|wrong)", re.I),
     "what-worried", _ans_what_worried),
    (re.compile(r"^how.*(loop|daemon|atlas|carrying|in flight)", re.I),
     "loop-health", _ans_loop_health),
    (re.compile(r"^who\s+(is|are)\s+(?P<name>[a-z_][a-z0-9_]*)", re.I),
     "who-is", _ans_who_is),
    (re.compile(r"^what.*(learn|wisdom|know|insights)", re.I),
     "what-learned", _ans_what_learned),
]


def ask(question: str) -> Answer:
    """Match the question against templates; return an Answer. If no
    template matches, returns a fallback answer pointing at `help`."""
    q = (question or "").strip()
    if not q:
        return Answer(question=q, matched_template="empty",
                      text="(no question asked)")
    for pattern, name, fn in _PATTERNS:
        match = pattern.search(q)
        if match:
            text, sources = fn(match)
            answer = Answer(question=q, matched_template=name,
                            text=text, sources=sources)
            mnemosyne.remember(
                kind="dialogue.ask",
                actor="dialogue",
                summary=f"matched template {name!r}: {q[:60]}",
                template=name, question=q,
                source_count=len(sources),
            )
            return answer

    # No pattern matched
    fallback = (
        f"I don't have a pattern for: {q!r}\n\n"
        f"Try `invoke ask help` to see what I can answer."
    )
    answer = Answer(question=q, matched_template="none",
                    text=fallback)
    mnemosyne.remember(
        kind="dialogue.ask",
        actor="dialogue",
        summary=f"no template matched: {q[:60]}",
        template="none", question=q, source_count=0,
    )
    return answer
