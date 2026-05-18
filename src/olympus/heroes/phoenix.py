"""Phoenix — the firebird of cyclical death and rebirth.

In myth: the Phoenix lives long, burns itself in a great fire, and
rises from the ashes — the same bird, renewed. Adopted into Greek
myth from older traditions, it became the canonical symbol of
cyclical regeneration.

In Olympus, Phoenix is the **cyclical-regeneration primitive**.
Distinct from:

  - **Asclepius** — rebuilds *derived* state (Iris HTML, Pan state
    file, directory structure)
  - **Charon** — archives *completed* state (released burdens move
    to Hades)
  - **Prometheus** — improves substrate per registered handlers

Phoenix identifies state that has *completed a lifecycle* and is
*due to be reborn*. She does not act. She surfaces "candidates for
rebirth" under `phoenix.candidate`; Hephaestus can then propose,
Momus contest, Zeus ratify.

Per Delphi 2026-05-18-aegis-arc.md.
"""
from __future__ import annotations

import datetime
from dataclasses import dataclass, field, asdict
from typing import Any

from olympus.primordials.nyx import Nyx
from olympus.titans.mnemosyne import mnemosyne


@dataclass
class RebirthCandidate:
    """One thing that completed its lifecycle and may want to begin again."""
    kind: str                # 'retired_prophecy' | 'hung_burden' | 'stale_graduation' | 'recurring_panic'
    subject: str             # identifier of the thing
    reason: str              # why it's a candidate
    last_seen: str = ""
    confidence: float = 0.5  # 0..1 — how strongly Phoenix thinks rebirth is appropriate
    proposed_action: str = ""


@dataclass
class RebirthReport:
    started_at: str
    ended_at: str = ""
    candidates: list[RebirthCandidate] = field(default_factory=list)
    already_known: int = 0

    @property
    def total(self) -> int:
        return len(self.candidates)


class Phoenix:
    """The firebird. Identifies state due for renewal."""

    DEFAULT_PROPHECY_STALENESS_DAYS = 30.0
    DEFAULT_HUNG_BURDEN_HOURS = 48.0

    def consider(self, *,
                  prophecy_staleness_days: float = DEFAULT_PROPHECY_STALENESS_DAYS,
                  hung_burden_hours: float = DEFAULT_HUNG_BURDEN_HOURS,
                  ) -> RebirthReport:
        """Walk recent state; identify rebirth candidates; record them."""
        report = RebirthReport(started_at=Nyx.now().isoformat())
        now = Nyx.now()

        already_known: set[tuple[str, str]] = set()
        for m in mnemosyne.recall("phoenix.candidate"):
            body = m.body or {}
            # Records written before the body-key rename used "kind";
            # the body-key rename for new records is "candidate_kind".
            kind_str = body.get("candidate_kind") or body.get("kind", "")
            k = (kind_str, body.get("subject", ""))
            if k != ("", ""):
                already_known.add(k)
        report.already_known = len(already_known)

        # ─── Candidate 1: retired prophecies whose retirement
        # rationale no longer applies (i.e., the prophecy hasn't been
        # re-attempted since retirement)
        retired = mnemosyne.recall("prophecy.retired")
        for r in retired:
            body = r.body or {}
            name = body.get("prediction", "")
            if not name:
                continue
            if ("retired_prophecy", name) in already_known:
                continue
            # Has any verification happened after the retirement?
            retired_dt = self._parse(r.remembered_at)
            if retired_dt is None:
                continue
            since_retired = now - retired_dt
            if since_retired.days >= prophecy_staleness_days:
                report.candidates.append(RebirthCandidate(
                    kind="retired_prophecy",
                    subject=name,
                    reason=(f"prediction {name!r} retired "
                            f"{since_retired.days} days ago; "
                            f"the conditions that retired it may "
                            f"have shifted"),
                    last_seen=r.remembered_at,
                    confidence=0.5,
                    proposed_action=(f"re-instate {name!r} with "
                                     f"updated verify() callable"),
                ))

        # ─── Candidate 2: hung Atlas burdens whose owner has gone
        # silent (no completed session matches)
        bears = mnemosyne.recall("atlas.bear")
        releases = mnemosyne.recall("atlas.release")
        released_ids = {(r.body or {}).get("id", "") for r in releases}
        completed_sessions = {
            (s.body or {}).get("session_id", "")
            for s in mnemosyne.recall("session.completed")
        }
        for b in bears:
            body = b.body or {}
            bid = body.get("id", "")
            if not bid or bid in released_ids:
                continue
            owner = body.get("owner", "")
            op = body.get("op", "")
            started_at = body.get("started_at", b.remembered_at)
            started_dt = self._parse(started_at)
            if started_dt is None:
                continue
            age_hours = (now - started_dt).total_seconds() / 3600.0
            if age_hours < hung_burden_hours:
                continue
            if ("hung_burden", bid) in already_known:
                continue
            # If the burden's owner appears in completed_sessions, the
            # work finished but the burden wasn't released — eligible
            session_owner = (op == "session" and owner in
                              completed_sessions)
            report.candidates.append(RebirthCandidate(
                kind="hung_burden",
                subject=bid,
                reason=(f"burden {op} for {owner!r} aged "
                        f"{age_hours:.1f}h without release"
                        + (" (session.completed exists)"
                           if session_owner else "")),
                last_seen=started_at,
                confidence=0.8 if session_owner else 0.5,
                proposed_action=(f"Asclepius hung-burden check + "
                                  f"Atlas release with outcome='reborn'"),
            ))

        # ─── Candidate 3: graduated prophecies that haven't been
        # verified recently — the substrate has stopped exercising them
        graduated = mnemosyne.recall("prophecy.graduated")
        verifications_by_pred: dict[str, str] = {}
        for v in mnemosyne.recall("prophecy.verified"):
            name = (v.body or {}).get("prediction", "")
            if name:
                verifications_by_pred[name] = v.remembered_at
        for g in graduated:
            body = g.body or {}
            name = body.get("prediction", "")
            if not name:
                continue
            if ("stale_graduation", name) in already_known:
                continue
            last_v = verifications_by_pred.get(name)
            if last_v is None:
                continue  # graduated but never verified again — odd; skip
            last_dt = self._parse(last_v)
            if last_dt is None:
                continue
            silence_days = (now - last_dt).days
            if silence_days >= prophecy_staleness_days:
                report.candidates.append(RebirthCandidate(
                    kind="stale_graduation",
                    subject=name,
                    reason=(f"graduated prophecy {name!r} hasn't been "
                            f"verified in {silence_days} day(s) — "
                            f"cycle has stopped engaging"),
                    last_seen=last_v,
                    confidence=0.6,
                    proposed_action=(f"re-trigger verification of "
                                     f"{name!r} or check if its "
                                     f"verify() callable still exists"),
                ))

        # Persist new candidates. Note: RebirthCandidate.kind would
        # collide with mnemosyne.remember(kind=...) on **unpack, so
        # rename the field in the body to candidate_kind.
        for c in report.candidates:
            body = asdict(c)
            body["candidate_kind"] = body.pop("kind", "")
            mnemosyne.remember(
                kind="phoenix.candidate",
                actor="phoenix",
                summary=(f"{c.kind} for {c.subject[:32]}: {c.reason[:100]}"),
                **body,
            )

        mnemosyne.remember(
            kind="phoenix.pass",
            actor="phoenix",
            summary=(f"rebirth scan: {report.total} new candidate(s); "
                     f"{report.already_known} already known"),
            new_candidates=report.total,
            already_known=report.already_known,
        )
        report.ended_at = Nyx.now().isoformat()
        return report

    @staticmethod
    def _parse(ts: str) -> datetime.datetime | None:
        try:
            return datetime.datetime.fromisoformat(ts)
        except (ValueError, TypeError):
            return None


phoenix = Phoenix()
