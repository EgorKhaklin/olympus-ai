"""head_journal — watches codex/journal/ for silence.

Clio inscribes daily decisions. If too many days pass with no
inscription, the operator is either not sessioning, or the agent
is sessioning silently. Either is worth surfacing.
"""
from __future__ import annotations

import datetime

from olympus.monsters.hydra.head import Head, HeadFinding, Severity
from olympus.primordials.gaia import root


SILENCE_THRESHOLD_DAYS = 7


class HeadJournal(Head):
    NAME = "journal"
    SLICE = "codex/journal/"
    IMMORTAL = False

    def observe(self) -> list[HeadFinding]:
        journal_path = root.child("codex", "journal")
        if not journal_path.exists():
            return [self._finding(
                self.SLICE, Severity.DRIFT,
                "codex/journal/ does not exist",
            )]
        entries = sorted(journal_path.glob("*.md"))
        if not entries:
            return [self._finding(
                self.SLICE, Severity.INFO,
                "no journal entries yet",
            )]
        try:
            latest_date = datetime.datetime.strptime(entries[-1].stem, "%Y-%m-%d").date()
        except ValueError:
            return [self._finding(
                self.SLICE, Severity.DRIFT,
                f"latest journal entry has non-standard name: {entries[-1].name}",
            )]
        days_since = (datetime.date.today() - latest_date).days
        if days_since > SILENCE_THRESHOLD_DAYS:
            return [self._finding(
                self.SLICE, Severity.DRIFT,
                f"{days_since} days since last journal inscription",
                latest_date=str(latest_date),
                days_since=days_since,
            )]
        return [self._finding(
            self.SLICE, Severity.INFO,
            f"journal current ({days_since}d since last)",
            entries=len(entries),
        )]
