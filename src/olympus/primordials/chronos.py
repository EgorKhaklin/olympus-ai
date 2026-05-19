"""olympus.primordials.chronos — the scheduler.

Per Delphi 2026-05-19-chronos-arc.md.

Chronos (Χρόνος) was the personification of time itself — distinct
from Cronus the Titan. In Olympus, Chronos is the scheduler primordial:
sibling to Nyx (clock), Gaia (root), Ananke (necessity).

The operator declares rituals in `state/config.json::chronos.rituals[]`.
The daemon's tick loop calls `chronos.tick()` each iteration; matching
rituals fire (their whitelisted errand runs in-process; output captured
to Mnemosyne under `chronos.fired`).

Grammar (intentionally simple — full cron later if demanded):
    daily HH:MM              every day at HH:MM
    weekday HH:MM            every Mon-Fri at HH:MM
    weekend HH:MM            every Sat-Sun at HH:MM
    <day> HH:MM              specific day: monday..sunday
    monthly <N>              1..28 of each month at 00:00
    monthly <N> HH:MM        1..28 of each month at HH:MM
    every <N>m               every N minutes (5..1440)
    every <N>h               every N hours (1..24)
    hourly                   every hour on the hour
"""
from __future__ import annotations

import datetime as _dt
import io
import json
import re
import time
from contextlib import redirect_stdout
from dataclasses import dataclass, field, asdict
from typing import Any

from olympus.primordials.gaia import root
from olympus.primordials.nyx import Nyx
from olympus.runtime.errand_whitelist import AUTOMATED_ERRANDS


# ─────────────────────────────────────────────────────────────────────
# Data classes
# ─────────────────────────────────────────────────────────────────────


_WEEKDAYS = ("monday", "tuesday", "wednesday", "thursday", "friday",
             "saturday", "sunday")
_WEEKDAY_INDEX = {name: i for i, name in enumerate(_WEEKDAYS)}
# Python: Monday=0, Sunday=6


@dataclass
class WhenSpec:
    """Parsed `when` expression. valid=False with error if unparseable."""
    raw: str
    valid: bool = True
    kind: str = ""           # one of: daily/weekday/weekend/day/monthly/every/hourly
    hour: int = 0
    minute: int = 0
    weekday: int = -1        # 0=Monday .. 6=Sunday; -1 if N/A
    day_of_month: int = -1
    every_minutes: int = 0
    error: str = ""


@dataclass
class RitualSpec:
    """One operator-declared scheduled ritual."""
    id: str
    when: str
    do: str
    enabled: bool = True
    min_interval_seconds: int = 60

    def validate(self) -> tuple[bool, str]:
        if not self.id or not re.match(r"^[a-zA-Z0-9_\-]{1,64}$", self.id):
            return (False, f"ritual id {self.id!r} must be alphanumeric/-/_")
        w = parse_when(self.when)
        if not w.valid:
            return (False, f"when expr {self.when!r}: {w.error}")
        if self.do not in AUTOMATED_ERRANDS:
            return (False, f"errand {self.do!r} not in whitelist "
                          f"({sorted(AUTOMATED_ERRANDS)})")
        return (True, "")


@dataclass
class Fired:
    """One ritual that just fired."""
    ritual_id: str
    errand: str
    fired_at: str
    elapsed_ms: float
    output_head: str = ""
    exit_code: int = 0
    error: str = ""


# ─────────────────────────────────────────────────────────────────────
# `when` parsing
# ─────────────────────────────────────────────────────────────────────


_HHMM_RX = re.compile(r"^([01]?\d|2[0-3]):([0-5]\d)$")


def parse_when(expr: str) -> WhenSpec:
    """Parse a `when` expression. Returns WhenSpec(valid=False) with
    an error string on invalid input; never raises."""
    if not expr or not isinstance(expr, str):
        return WhenSpec(raw=str(expr), valid=False,
                        error="empty or non-string")
    parts = expr.strip().lower().split()

    # hourly
    if parts == ["hourly"]:
        return WhenSpec(raw=expr, kind="hourly")

    # every N{m|h}
    if len(parts) == 2 and parts[0] == "every":
        unit = parts[1]
        m = re.match(r"^(\d+)([mh])$", unit)
        if not m:
            return WhenSpec(raw=expr, valid=False,
                            error="every <N>m or every <N>h")
        n = int(m.group(1))
        unit_kind = m.group(2)
        if unit_kind == "m":
            if not (5 <= n <= 1440):
                return WhenSpec(raw=expr, valid=False,
                                error="every <N>m: N must be 5..1440")
            return WhenSpec(raw=expr, kind="every", every_minutes=n)
        # hours
        if not (1 <= n <= 24):
            return WhenSpec(raw=expr, valid=False,
                            error="every <N>h: N must be 1..24")
        return WhenSpec(raw=expr, kind="every", every_minutes=n * 60)

    # monthly N [HH:MM]
    if parts and parts[0] == "monthly":
        if len(parts) == 2:
            try:
                dom = int(parts[1])
            except ValueError:
                return WhenSpec(raw=expr, valid=False,
                                error="monthly <N>: N not int")
            if not (1 <= dom <= 28):
                return WhenSpec(raw=expr, valid=False,
                                error="monthly N must be 1..28")
            return WhenSpec(raw=expr, kind="monthly",
                            day_of_month=dom, hour=0, minute=0)
        if len(parts) == 3:
            try:
                dom = int(parts[1])
            except ValueError:
                return WhenSpec(raw=expr, valid=False,
                                error="monthly <N> HH:MM: N not int")
            if not (1 <= dom <= 28):
                return WhenSpec(raw=expr, valid=False,
                                error="monthly N must be 1..28")
            m2 = _HHMM_RX.match(parts[2])
            if not m2:
                return WhenSpec(raw=expr, valid=False,
                                error="monthly N HH:MM: bad HH:MM")
            return WhenSpec(raw=expr, kind="monthly",
                            day_of_month=dom,
                            hour=int(m2.group(1)),
                            minute=int(m2.group(2)))
        return WhenSpec(raw=expr, valid=False,
                        error="monthly <N> [HH:MM]")

    # daily HH:MM | weekday HH:MM | weekend HH:MM | <day> HH:MM
    if len(parts) == 2:
        first, hhmm = parts
        m2 = _HHMM_RX.match(hhmm)
        if not m2:
            return WhenSpec(raw=expr, valid=False,
                            error=f"bad HH:MM after {first!r}")
        h, mi = int(m2.group(1)), int(m2.group(2))
        if first in ("daily", "weekday", "weekend"):
            return WhenSpec(raw=expr, kind=first, hour=h, minute=mi)
        if first in _WEEKDAY_INDEX:
            return WhenSpec(raw=expr, kind="day",
                            weekday=_WEEKDAY_INDEX[first],
                            hour=h, minute=mi)
        return WhenSpec(raw=expr, valid=False,
                        error=f"unknown keyword {first!r}")

    return WhenSpec(raw=expr, valid=False,
                    error=f"unrecognized grammar")


def matches_now(spec: WhenSpec, now: _dt.datetime) -> bool:
    """True iff `now` falls in the spec's minute window. For 'every'
    rituals, matching is decided by `Chronos.tick` against last_fired,
    not by matching minute alone — this function returns True for
    'every' specs whenever now's seconds are < 60 (i.e., we're in
    SOME minute; the tick logic handles interval enforcement)."""
    if not spec.valid:
        return False
    if spec.kind == "every":
        return True  # interval logic enforced by tick()
    if spec.kind == "hourly":
        return now.minute == 0
    if spec.kind == "daily":
        return now.hour == spec.hour and now.minute == spec.minute
    if spec.kind == "weekday":
        return (now.weekday() < 5
                and now.hour == spec.hour
                and now.minute == spec.minute)
    if spec.kind == "weekend":
        return (now.weekday() >= 5
                and now.hour == spec.hour
                and now.minute == spec.minute)
    if spec.kind == "day":
        return (now.weekday() == spec.weekday
                and now.hour == spec.hour
                and now.minute == spec.minute)
    if spec.kind == "monthly":
        return (now.day == spec.day_of_month
                and now.hour == spec.hour
                and now.minute == spec.minute)
    return False


def next_due(spec: WhenSpec, now: _dt.datetime) -> _dt.datetime | None:
    """Return the next datetime the ritual would fire (best-effort,
    one-pass; not a calendar walk). None if spec invalid."""
    if not spec.valid:
        return None
    # Search forward minute-by-minute up to a year. Coarse but correct
    # and bounded (525,600 iterations worst case; in practice <1 day).
    cursor = now.replace(second=0, microsecond=0) + _dt.timedelta(minutes=1)
    max_minutes = 366 * 24 * 60
    if spec.kind == "every":
        return cursor + _dt.timedelta(minutes=spec.every_minutes - 1)
    for _ in range(max_minutes):
        if matches_now(spec, cursor):
            return cursor
        cursor += _dt.timedelta(minutes=1)
    return None


# ─────────────────────────────────────────────────────────────────────
# State persistence
# ─────────────────────────────────────────────────────────────────────


def _state_path():
    """Path to last_fired persistence; injectable for tests."""
    return root.child("state", "chronos", "rituals_state.json")


def _load_state() -> dict[str, str]:
    """{ritual_id: iso-ts of last fire}"""
    p = _state_path()
    if not p.exists():
        return {}
    try:
        return json.loads(p.read_text(encoding="utf-8")) or {}
    except Exception:  # noqa: BLE001
        return {}


def _save_state(state: dict[str, str]) -> None:
    p = _state_path()
    p.parent.mkdir(parents=True, exist_ok=True)
    tmp = p.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(state, indent=2, sort_keys=True),
                   encoding="utf-8")
    tmp.replace(p)


# ─────────────────────────────────────────────────────────────────────
# Chronos — the singleton
# ─────────────────────────────────────────────────────────────────────


MAX_FIRES_PER_TICK = 3


class Chronos:
    """The scheduler. Reads rituals from config; fires matching ones."""

    def load_rituals(self) -> list[RitualSpec]:
        """Read state/config.json::chronos.rituals[] and return valid
        RitualSpecs. Invalid specs are skipped with a stderr message."""
        import sys as _sys
        try:
            from olympus.runtime.config import load as load_cfg
            cfg = load_cfg()
        except Exception:  # noqa: BLE001
            return []
        raw = getattr(cfg, "chronos", None)
        if raw is None:
            return []
        rituals_raw = getattr(raw, "rituals", []) or []
        out: list[RitualSpec] = []
        for entry in rituals_raw:
            if not isinstance(entry, dict):
                continue
            try:
                spec = RitualSpec(
                    id=str(entry.get("id", "")),
                    when=str(entry.get("when", "")),
                    do=str(entry.get("do", "")),
                    enabled=bool(entry.get("enabled", True)),
                    min_interval_seconds=int(
                        entry.get("min_interval_seconds", 60)),
                )
            except Exception as exc:  # noqa: BLE001
                _sys.stderr.write(
                    f"[chronos] skipping malformed ritual: {exc}\n")
                continue
            ok, err = spec.validate()
            if not ok:
                _sys.stderr.write(
                    f"[chronos] skipping invalid ritual "
                    f"{spec.id!r}: {err}\n")
                continue
            out.append(spec)
        return out

    def tick(self, now: _dt.datetime | None = None) -> list[Fired]:
        """Evaluate all configured rituals; fire those that match.
        Returns the list of Fired records. Caller may use `now` for
        deterministic testing."""
        now = now or Nyx.now()
        rituals = self.load_rituals()
        if not rituals:
            return []
        state = _load_state()
        fired: list[Fired] = []
        for spec in rituals:
            if not spec.enabled:
                continue
            if len(fired) >= MAX_FIRES_PER_TICK:
                break
            wspec = parse_when(spec.when)
            if not matches_now(wspec, now):
                continue
            last_fired_iso = state.get(spec.id, "")
            if last_fired_iso:
                try:
                    last_dt = _dt.datetime.fromisoformat(
                        last_fired_iso.replace("Z", "+00:00"))
                    if last_dt.tzinfo is None and now.tzinfo is not None:
                        last_dt = last_dt.replace(tzinfo=now.tzinfo)
                    age_s = (now - last_dt).total_seconds()
                    interval = spec.min_interval_seconds
                    # For 'every' rituals, interval is enforced via
                    # the every_minutes setting too
                    if wspec.kind == "every":
                        interval = max(interval, wspec.every_minutes * 60 - 5)
                    if age_s < interval:
                        continue
                except (ValueError, TypeError):
                    pass
            # Mark fired-at BEFORE executing (crash-safe: a partial
            # run won't be re-attempted on restart)
            state[spec.id] = now.isoformat()
            _save_state(state)
            f = self._execute(spec, now)
            fired.append(f)
            self._record(f)
        return fired

    def _execute(self, spec: RitualSpec,
                  fired_at: _dt.datetime) -> Fired:
        """Run the whitelisted errand in-process; capture stdout."""
        started = time.perf_counter()
        out = Fired(
            ritual_id=spec.id, errand=spec.do,
            fired_at=fired_at.isoformat(),
            elapsed_ms=0.0,
        )
        try:
            from olympus.cli import hermes
            errand_obj = hermes._errands.get(spec.do)  # type: ignore[attr-defined]
            if errand_obj is None:
                out.error = f"errand {spec.do!r} not registered"
                return out
            buf = io.StringIO()
            with redirect_stdout(buf):
                rc = errand_obj.fn([])
            out.exit_code = int(rc or 0)
            text = buf.getvalue()
            # Strip ANSI for the captured head
            ansi = re.compile(r"\x1b\[[0-9;]*m")
            out.output_head = ansi.sub("", text)[:1024]
        except SystemExit as exc:
            out.exit_code = int(exc.code or 0)
        except Exception as exc:  # noqa: BLE001
            out.error = f"{type(exc).__name__}: {exc}"
        out.elapsed_ms = (time.perf_counter() - started) * 1000.0
        return out

    def _record(self, f: Fired) -> None:
        from olympus.titans.mnemosyne import mnemosyne
        mnemosyne.remember(
            kind="chronos.fired",
            actor=f"chronos:{f.ritual_id}",
            summary=(f"fired '{f.ritual_id}' → invoke {f.errand} "
                     f"(rc={f.exit_code} {f.elapsed_ms:.0f}ms)"
                     + (f" ERROR={f.error[:60]}" if f.error else "")),
            ritual_id=f.ritual_id, errand=f.errand,
            fired_at=f.fired_at, elapsed_ms=f.elapsed_ms,
            exit_code=f.exit_code, error=f.error,
            output_head=f.output_head,
        )

    def next_due(self, spec: RitualSpec,
                  now: _dt.datetime | None = None) -> _dt.datetime | None:
        """Convenience: when will this ritual fire next?"""
        now = now or Nyx.now()
        return next_due(parse_when(spec.when), now)


chronos = Chronos()


__all__ = [
    "Chronos", "chronos",
    "RitualSpec", "WhenSpec", "Fired",
    "parse_when", "matches_now", "next_due",
    "MAX_FIRES_PER_TICK",
]
