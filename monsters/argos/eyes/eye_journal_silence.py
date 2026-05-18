"""eye_journal_silence — surfaces when Clio has been silent too long."""
from __future__ import annotations

import datetime

from monsters.argos.base import Eye, EyeFinding, KIND_INFO, KIND_DRIFT
from primordials.gaia import root


SILENCE_THRESHOLD_DAYS = 14


class EyeJournalSilence(Eye):
    NAME = "eye_journal_silence"
    SLICE = "codex/journal/"

    def scan(self) -> list[EyeFinding]:
        journal_path = root.child("codex", "journal")
        if not journal_path.exists():
            return [self._finding(KIND_INFO, "codex/journal/ does not exist")]
        entries = sorted(journal_path.glob("*.md"))
        if not entries:
            return [self._finding(KIND_INFO, "no journal entries yet")]
        try:
            latest = datetime.datetime.strptime(entries[-1].stem, "%Y-%m-%d").date()
        except ValueError:
            return [self._finding(KIND_INFO,
                f"unusual journal filename: {entries[-1].name}")]
        days_since = (datetime.date.today() - latest).days
        if days_since > SILENCE_THRESHOLD_DAYS:
            return [self._finding(KIND_DRIFT,
                f"{days_since} days since last journal inscription",
                intensity=min(8.0, days_since / 7.0),
                latest_date=str(latest), days_since=days_since)]
        return [self._finding(KIND_INFO,
            f"journal current ({days_since}d since last)",
            entries=len(entries))]
