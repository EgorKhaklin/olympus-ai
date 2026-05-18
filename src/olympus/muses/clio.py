"""Clio — Muse of history.

Clio holds the scrolls of history. In Olympus she writes and reads
the chronicle: the daily journal where decisions, learnings, and
shipped work are noted.

The labyrinth arc promotes Clio from passive inscriber to **narrative
auto-writer**. `clio.narrate(window_days)` composes a structured
digest from Mnemosyne records — what happened, what changed, what was
decided, what slipped through. The digest lands in `codex/journal/
<date>-clio-digest.md`, readable in 5 minutes.

She is not an LLM; the narrative is template-shaped from real records.
Where she summarizes, she cites — every claim references a Mnemosyne
kind so the operator can verify.
"""
from __future__ import annotations

import datetime
import pathlib
from dataclasses import dataclass, field

from olympus.primordials.gaia import root
from olympus.primordials.nyx import Nyx
from olympus.titans.mnemosyne import mnemosyne


@dataclass
class Digest:
    """One narrative digest — what the substrate did over a window."""
    window_days: int
    composed_at: str
    sessions_run: int = 0
    proposals_ratified: int = 0
    proposals_rejected: int = 0
    prophecies_accepted: int = 0
    prophecies_rejected: int = 0
    panics_entered: int = 0
    vindications: int = 0
    improvement_passes: int = 0
    pythia_consultations: int = 0
    counterfactuals_run: int = 0
    headlines: list[str] = field(default_factory=list)
    path: str = ""


class Clio:
    """Reader and writer of codex/journal/. Now also narrative composer."""

    JOURNAL = "codex/journal"

    def __init__(self) -> None:
        self.journal_path = root.child(self.JOURNAL)
        self.journal_path.mkdir(parents=True, exist_ok=True)

    def _today_file(self) -> pathlib.Path:
        return self.journal_path / f"{Nyx.now().strftime('%Y-%m-%d')}.md"

    def inscribe(self, kind: str, text: str) -> pathlib.Path:
        """Append a line to today's journal under a `kind` (decision/
        learning/observation/etc.)."""
        f = self._today_file()
        if not f.exists():
            f.write_text(f"# {Nyx.now().strftime('%Y-%m-%d')}\n\n",
                         encoding="utf-8")
        with f.open("a", encoding="utf-8") as fh:
            ts = Nyx.now().strftime("%H:%M")
            fh.write(f"- **{kind}** {ts} — {text}\n")
        return f

    def days(self) -> list[pathlib.Path]:
        return sorted(self.journal_path.glob("*.md"))

    # ─────────────────────────────────────────────────────────
    # Narrative — auto-written digest (labyrinth arc)
    # ─────────────────────────────────────────────────────────

    def narrate(self, *, window_days: int = 7,
                write: bool = True) -> Digest:
        """Compose a digest of the last `window_days`. If write=True,
        persist to codex/journal/<date>-clio-digest.md."""
        cutoff = Nyx.now() - datetime.timedelta(days=window_days)

        def _recent(kind: str) -> list:
            return [m for m in mnemosyne.recall(kind)
                    if self._within(m.remembered_at, cutoff)]

        sessions = _recent("session.completed")
        ratified = _recent("action.ratified")
        rejected = _recent("action.rejected")
        prophecies = _recent("prophecy.verified")
        prophecies_yes = [p for p in prophecies
                          if (p.body or {}).get("accepted") is True]
        prophecies_no = [p for p in prophecies
                         if (p.body or {}).get("accepted") is False]
        panics = [m for m in _recent("pan.transition")
                  if (m.body or {}).get("transition") == "enter"]
        vinds = _recent("cassandra.vindicated")
        improvements = _recent("prometheus.pass")
        pythias = _recent("pythia.consultation")
        cfs = _recent("nemesis.counterfactual")

        digest = Digest(
            window_days=window_days,
            composed_at=Nyx.now().isoformat(),
            sessions_run=len(sessions),
            proposals_ratified=len(ratified),
            proposals_rejected=len(rejected),
            prophecies_accepted=len(prophecies_yes),
            prophecies_rejected=len(prophecies_no),
            panics_entered=len(panics),
            vindications=len(vinds),
            improvement_passes=len(improvements),
            pythia_consultations=len(pythias),
            counterfactuals_run=len(cfs),
        )

        # Headlines — pick the load-bearing recent events
        if panics:
            last = panics[-1]
            digest.headlines.append(
                f"Pan entered panic at "
                f"{last.remembered_at[:19]} — "
                f"{(last.body or {}).get('detail', '(no detail)')[:100]}"
            )
        if vinds:
            digest.headlines.append(
                f"Cassandra vindicated {len(vinds)} previously-dismissed "
                f"warning(s)"
            )
        if prophecies_no:
            for p in prophecies_no[-3:]:
                name = (p.body or {}).get("prediction", "")
                digest.headlines.append(
                    f"Apollo rejected prediction {name!r}"
                )
        if ratified:
            digest.headlines.append(
                f"Zeus ratified {len(ratified)} proposal(s); "
                f"latest: {ratified[-1].summary[:80]}"
            )

        # Render and (optionally) write
        body = self._render(digest, sessions, ratified, rejected,
                            panics, vinds, prophecies)
        if write:
            out_path = self.journal_path / (
                f"{Nyx.now().strftime('%Y-%m-%d')}-clio-digest.md"
            )
            out_path.write_text(body, encoding="utf-8")
            digest.path = str(out_path)

        # Record the pass
        mnemosyne.remember(
            kind="clio.narrate",
            actor="clio",
            summary=(f"digest composed for last {window_days}d: "
                     f"{digest.sessions_run} session(s), "
                     f"{digest.proposals_ratified} ratified, "
                     f"{digest.panics_entered} panic(s), "
                     f"{digest.vindications} vindication(s)"),
            window_days=window_days,
            sessions_run=digest.sessions_run,
            proposals_ratified=digest.proposals_ratified,
            panics_entered=digest.panics_entered,
            vindications=digest.vindications,
            path=digest.path,
        )
        return digest

    @staticmethod
    def _within(ts: str, cutoff: datetime.datetime) -> bool:
        try:
            dt = datetime.datetime.fromisoformat(ts)
            return dt >= cutoff
        except (ValueError, TypeError):
            return False

    @staticmethod
    def _render(digest: Digest, sessions, ratified, rejected,
                panics, vinds, prophecies) -> str:
        date_str = Nyx.now().strftime("%Y-%m-%d")
        lines = [
            f"# Olympus — Clio's digest, {date_str}",
            "",
            f"*Window: last {digest.window_days} day(s). Composed "
            f"{digest.composed_at[:19]}.*",
            "",
            "## Headlines",
            "",
        ]
        if digest.headlines:
            for h in digest.headlines:
                lines.append(f"- {h}")
        else:
            lines.append("- *(no load-bearing events this window — "
                         "quiet substrate is healthy substrate)*")
        lines.extend([
            "",
            "## Activity",
            "",
            f"- **{digest.sessions_run}** session(s) completed "
            f"(`session.completed`)",
            f"- **{digest.proposals_ratified}** proposal(s) ratified, "
            f"**{digest.proposals_rejected}** rejected "
            f"(`action.ratified` / `action.rejected`)",
            f"- **{digest.improvement_passes}** Prometheus improvement "
            f"pass(es) (`prometheus.pass`)",
            f"- **{digest.pythia_consultations}** Pythia consultation(s) "
            f"(`pythia.consultation`)",
            f"- **{digest.counterfactuals_run}** Nemesis counterfactual"
            f"(s) (`nemesis.counterfactual`)",
            "",
            "## Forecasting",
            "",
            f"- **{digest.prophecies_accepted}** prediction(s) accepted",
            f"- **{digest.prophecies_rejected}** prediction(s) rejected",
            "",
            "## Health",
            "",
            f"- **{digest.panics_entered}** Pan panic(s) entered "
            f"(`pan.transition`)",
            f"- **{digest.vindications}** Cassandra vindication(s) "
            f"(`cassandra.vindicated`)",
            "",
        ])
        if ratified:
            lines.extend(["## Most recent ratifications", ""])
            for r in ratified[-5:]:
                lines.append(f"- `{r.remembered_at[:19]}` — {r.summary}")
            lines.append("")
        if rejected:
            lines.extend(["## Most recent rejections", ""])
            for r in rejected[-5:]:
                lines.append(f"- `{r.remembered_at[:19]}` — {r.summary}")
            lines.append("")
        if vinds:
            lines.extend(["## Cassandra vindications", ""])
            for v in vinds[-5:]:
                slice_ = (v.body or {}).get("slice", "?")
                kind = (v.body or {}).get("dismissal_kind", "?")
                rec = (v.body or {}).get("recurrences_after_dismissal", 0)
                lines.append(f"- `{slice_}` dismissed ({kind}); "
                             f"recurred {rec}x")
            lines.append("")
        lines.extend([
            "---",
            "",
            "*Written by Clio, Muse of history. Every claim above is "
            "verifiable from `state/mnemosyne/*.jsonl` records of the "
            "named kinds. S8 (Continuity of Understanding) preserved.*",
            "",
        ])
        return "\n".join(lines)


clio = Clio()
