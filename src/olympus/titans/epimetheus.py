"""Epimetheus — titan of afterthought, brother of Prometheus.

Their names are paired and opposite. *Pro-metheus* is forethought;
*epi-metheus* is the recognition that comes after. In the myths, he is
the one who accepts Pandora despite Prometheus's warning — the
embodiment of "we should have seen this coming."

In Olympus he closes the loop that Prometheus opened. Prometheus
*acts*; Epimetheus *reviews*. For every ratified action, every
prophecy verification, every Prometheus handler run, and every session
error, Epimetheus produces a structured hindsight record naming what
was *expected* versus what *actually* happened, with a concise English
*lesson*.

Read-only. Writes only to Mnemosyne (S1, S8 reconstructable). No
ground-touch; no privilege escalation. Per Delphi
2026-05-18-missing-figures-arc.md (zero Momus dings).
"""
from __future__ import annotations

import datetime
from dataclasses import dataclass, field, asdict
from typing import Any

from olympus.primordials.nyx import Nyx
from olympus.titans.mnemosyne import mnemosyne


@dataclass
class HindsightRecord:
    """One structured hindsight — what we thought, what happened, what
    we'd do differently."""
    subject_kind: str          # 'action' | 'prophecy' | 'session' | 'handler'
    subject_id: str            # the identifier of the thing reflected on
    expected: str              # English sentence
    actual: str                # English sentence
    lesson: str                # concise takeaway
    surprising: bool           # True iff actual != expected
    reflected_at: str = ""
    source_ts: str = ""        # when the underlying event was recorded

    def __post_init__(self) -> None:
        if not self.reflected_at:
            self.reflected_at = Nyx.now().isoformat()


@dataclass
class ReflectionReport:
    started_at: str
    ended_at: str = ""
    lookback_hours: float = 24.0
    records: list[HindsightRecord] = field(default_factory=list)

    @property
    def total(self) -> int:
        return len(self.records)

    @property
    def surprising(self) -> int:
        return sum(1 for r in self.records if r.surprising)


# ─────────────────────────────────────────────────────────
# Helpers — parse timestamps; compute lookback cutoff
# ─────────────────────────────────────────────────────────


def _parse(ts: str) -> datetime.datetime | None:
    try:
        return datetime.datetime.fromisoformat(ts)
    except (ValueError, TypeError):
        return None


def _within(ts: str, cutoff: datetime.datetime | None) -> bool:
    if cutoff is None:
        return True
    dt = _parse(ts)
    return dt is not None and dt >= cutoff


# ─────────────────────────────────────────────────────────
# Epimetheus
# ─────────────────────────────────────────────────────────


class Epimetheus:
    """The afterthought-bringer. Reads Mnemosyne; produces hindsights."""

    def reflect(self, lookback_hours: float = 24.0) -> ReflectionReport:
        """Look back at the last N hours and produce hindsight records
        for every event of the relevant kinds. Idempotent: re-running
        produces (mostly) the same records — Epimetheus does not
        deduplicate, since each call is itself a recorded reflection."""
        report = ReflectionReport(
            started_at=Nyx.now().isoformat(),
            lookback_hours=lookback_hours,
        )

        cutoff: datetime.datetime | None = None
        if lookback_hours > 0:
            now = Nyx.now()
            cutoff = now - datetime.timedelta(hours=lookback_hours)

        # Ratified actions — expected: drift gets resolved
        for m in mnemosyne.recall("action.ratified"):
            if not _within(m.remembered_at, cutoff):
                continue
            report.records.append(self._reflect_action(m))

        # Prophecies — expected: prediction matches verify()
        for m in mnemosyne.recall("prophecy.verified"):
            if not _within(m.remembered_at, cutoff):
                continue
            report.records.append(self._reflect_prophecy(m))

        # Session errors — expected: clean run
        for m in mnemosyne.recall("session.errored"):
            if not _within(m.remembered_at, cutoff):
                continue
            report.records.append(self._reflect_session_error(m))

        # Prometheus handler failures — expected: handler succeeds
        for m in mnemosyne.recall("prometheus.handler"):
            if not _within(m.remembered_at, cutoff):
                continue
            body = m.body or {}
            if body.get("succeeded") is False:
                report.records.append(self._reflect_handler_failure(m))

        # Record the pass itself
        mnemosyne.remember(
            kind="epimetheus.pass",
            actor="epimetheus",
            summary=(f"hindsight pass: {report.total} record(s), "
                     f"{report.surprising} surprising"),
            total=report.total,
            surprising=report.surprising,
            lookback_hours=lookback_hours,
        )

        # And record each individual hindsight (so it's queryable later)
        for h in report.records:
            mnemosyne.remember(
                kind="epimetheus.hindsight",
                actor=f"epimetheus:{h.subject_kind}",
                summary=h.lesson,
                **asdict(h),
            )

        report.ended_at = Nyx.now().isoformat()
        return report

    def reflect_on_action(self, action_id: str) -> HindsightRecord | None:
        """Look back at a specific action by id. Returns None if not
        found in Mnemosyne."""
        for m in mnemosyne.recall("action.ratified"):
            body = m.body or {}
            if body.get("id") == action_id or body.get("action_id") == action_id:
                return self._reflect_action(m)
        return None

    def hindsights(self, limit: int = 50) -> list[HindsightRecord]:
        """Every hindsight ever recorded, newest first."""
        out: list[HindsightRecord] = []
        for m in mnemosyne.recall("epimetheus.hindsight"):
            body = m.body or {}
            # Reconstruct from stored fields; ignore fields we don't know about.
            try:
                out.append(HindsightRecord(
                    subject_kind=body.get("subject_kind", ""),
                    subject_id=body.get("subject_id", ""),
                    expected=body.get("expected", ""),
                    actual=body.get("actual", ""),
                    lesson=body.get("lesson", ""),
                    surprising=bool(body.get("surprising", False)),
                    reflected_at=body.get("reflected_at",
                                          m.remembered_at),
                    source_ts=body.get("source_ts", ""),
                ))
            except TypeError:
                continue
        return list(reversed(out))[:limit]

    # ─────────────────────────────────────────────────────────
    # Per-subject reflections — each is a small pattern
    # ─────────────────────────────────────────────────────────

    @staticmethod
    def _reflect_action(m: Any) -> HindsightRecord:
        body = m.body or {}
        drift = body.get("drift_signature") or body.get("signature") or "—"
        action_id = body.get("id") or body.get("action_id") or "—"
        summary = m.summary or "(no summary)"
        expected = f"action would resolve drift {drift!r}"
        # Note: actual resolution can only be confirmed by a subsequent
        # session running clean against the same slice; here we record
        # the action as completed-as-ratified pending future evidence.
        actual = f"action ratified and queued: {summary}"
        lesson = (f"track future findings on the slice from drift {drift!r}; "
                  f"if it recurs within 7 days, the ratification did not "
                  f"settle the underlying concern.")
        return HindsightRecord(
            subject_kind="action",
            subject_id=str(action_id),
            expected=expected,
            actual=actual,
            lesson=lesson,
            surprising=False,
            source_ts=m.remembered_at,
        )

    @staticmethod
    def _reflect_prophecy(m: Any) -> HindsightRecord:
        body = m.body or {}
        name = body.get("prediction", "—")
        accepted = body.get("accepted")
        horizon = body.get("horizon", "")
        statement = body.get("statement", "")
        if accepted is True:
            expected = (f"prediction {name!r} would hold at horizon {horizon}")
            actual = "verify() returned True — prediction held"
            lesson = (f"prediction {name!r} confirmed; consider whether the "
                      f"belief encoded in {statement!r} is now strong enough "
                      f"to use as a precondition elsewhere.")
            surprising = False
        elif accepted is False:
            expected = (f"prediction {name!r} would hold at horizon {horizon}")
            actual = "verify() returned False — prediction did not hold"
            lesson = (f"prediction {name!r} failed; re-examine the model that "
                      f"produced this claim. If 3+ failures, Prometheus will "
                      f"retire it.")
            surprising = True
        else:
            expected = "prophecy verification produced a boolean"
            actual = f"verify() returned {accepted!r} (non-boolean)"
            lesson = ("prediction verify() should return True or False; "
                      "investigate the predicate definition.")
            surprising = True
        return HindsightRecord(
            subject_kind="prophecy",
            subject_id=str(name),
            expected=expected,
            actual=actual,
            lesson=lesson,
            surprising=surprising,
            source_ts=m.remembered_at,
        )

    @staticmethod
    def _reflect_session_error(m: Any) -> HindsightRecord:
        body = m.body or {}
        session_id = body.get("session_id", "—")
        error = body.get("error", "(no detail)")
        expected = "session completes without raising"
        actual = f"session raised: {error}"
        lesson = (f"trace the phase that raised; add a Furies check or "
                  f"a recovery path so the substrate degrades gracefully "
                  f"rather than aborting.")
        return HindsightRecord(
            subject_kind="session",
            subject_id=str(session_id),
            expected=expected,
            actual=actual,
            lesson=lesson,
            surprising=True,
            source_ts=m.remembered_at,
        )

    @staticmethod
    def _reflect_handler_failure(m: Any) -> HindsightRecord:
        body = m.body or {}
        handler = body.get("handler", "—")
        summary = m.summary or "(no summary)"
        expected = f"Prometheus handler {handler!r} would succeed"
        actual = f"handler raised: {summary}"
        lesson = (f"the handler's input assumptions did not hold; add a "
                  f"precondition or make the failure non-fatal so other "
                  f"handlers continue.")
        return HindsightRecord(
            subject_kind="handler",
            subject_id=str(handler),
            expected=expected,
            actual=actual,
            lesson=lesson,
            surprising=True,
            source_ts=m.remembered_at,
        )


epimetheus = Epimetheus()
