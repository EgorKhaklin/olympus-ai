"""olympus.heroes.plutus — the cost ledger.

Per Delphi 2026-05-19-plutus-arc.md.

Plutus (Greek: Πλοῦτος) was the god of wealth and abundance, son of
Demeter, often shown carrying a cornucopia. In Olympus, **Plutus is
the cost accountant** — he reads `llm.call` records from Mnemosyne and
adds up token spend, estimating USD against a model-pricing table.

Plutus does NOT create the records (every LLM bridge already does);
he only reads + aggregates. The audit-of-record (S1) is unchanged.

Public API:

    from olympus.heroes.plutus import plutus, CostReport

    r = plutus.tally()                    # all-time
    r = plutus.tally(window="today")      # today only
    r = plutus.tally(window="7d")         # last 7 days

    print(r.estimated_usd)                # float
    print(r.by_role["hephaestus"])        # {calls, in, out, usd}

    plutus.estimate_dollars(in_tokens=2000,
                             out_tokens=500,
                             model="claude-opus-4-7")  # → 0.0225
"""
from __future__ import annotations

import datetime as _dt
from collections import defaultdict
from dataclasses import dataclass, field, asdict
from typing import Any

from olympus.primordials.nyx import Nyx
from olympus.titans.mnemosyne import mnemosyne


# ─────────────────────────────────────────────────────────────────────
# Pricing table — USD per 1M tokens (input, output)
# ─────────────────────────────────────────────────────────────────────

# Cached pricing as of 2026-04-29 (claude-api skill catalog). Keep in
# sync via the live Models API when the operator runs `invoke spend
# --refresh-pricing` (future arc).
PRICING: dict[str, tuple[float, float]] = {
    # Claude 4 family
    "claude-opus-4-7":    (5.00, 25.00),
    "claude-opus-4-6":    (5.00, 25.00),
    "claude-opus-4-5":    (5.00, 25.00),
    "claude-sonnet-4-6":  (3.00, 15.00),
    "claude-sonnet-4-5":  (3.00, 15.00),
    "claude-haiku-4-5":   (1.00,  5.00),
    # Older Claude 3.x families (best-effort estimates)
    "claude-3-7-sonnet":  (3.00, 15.00),
    "claude-3-5-sonnet":  (3.00, 15.00),
    "claude-3-5-haiku":   (0.80,  4.00),
    "claude-3-opus":      (15.0, 75.00),
    # Local / stub
    "echo-1":             (0.00,  0.00),
    "echo":               (0.00,  0.00),
}

UNKNOWN_MODEL_KEY = "(unknown)"


def _budget_signature(status: dict[str, Any]) -> str:
    """Hashable signature of the budget config that produced `status`.
    Acks made under a different signature are stale and ignored — this
    enables config edits (and test fixtures with isolated configs) to
    invalidate prior acks automatically."""
    parts: list[str] = [str(status.get("enabled", False)),
                         str(status.get("warn_at_pct", 0))]
    for key in ("daily", "weekly", "monthly"):
        e = status.get(key) or {}
        parts.append(f"{key}:{e.get('ceiling', 0)}")
    return "|".join(parts)

# Window definitions in seconds
_WINDOW_SECONDS: dict[str, float | None] = {
    "all":     None,
    "today":   None,    # special: matches today's date
    "1h":      3600.0,
    "24h":     86400.0,
    "7d":      7 * 86400.0,
    "30d":    30 * 86400.0,
}


# ─────────────────────────────────────────────────────────────────────
# Data classes
# ─────────────────────────────────────────────────────────────────────


@dataclass
class CostBreakdown:
    """One axis of the cost report (per bridge / role / model / day)."""
    calls: int = 0
    input_tokens: int = 0
    output_tokens: int = 0
    estimated_usd: float = 0.0


@dataclass
class CostReport:
    """Aggregate cost report across `llm.call` records."""
    window: str = "all"
    snapshot_at: str = ""
    total_calls: int = 0
    total_input_tokens: int = 0
    total_output_tokens: int = 0
    estimated_usd: float = 0.0
    by_bridge: dict[str, CostBreakdown] = field(default_factory=dict)
    by_role: dict[str, CostBreakdown] = field(default_factory=dict)
    by_model: dict[str, CostBreakdown] = field(default_factory=dict)
    by_day: dict[str, CostBreakdown] = field(default_factory=dict)
    unknown_model_calls: int = 0
    unknown_models: list[str] = field(default_factory=list)
    pricing_used: dict[str, tuple[float, float]] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.snapshot_at:
            self.snapshot_at = Nyx.now().isoformat()

    def to_dict(self) -> dict[str, Any]:
        """JSON-safe dict (CostBreakdown → dict)."""
        return {
            "window": self.window,
            "snapshot_at": self.snapshot_at,
            "total_calls": self.total_calls,
            "total_input_tokens": self.total_input_tokens,
            "total_output_tokens": self.total_output_tokens,
            "estimated_usd": round(self.estimated_usd, 4),
            "by_bridge": {k: asdict(v) for k, v in self.by_bridge.items()},
            "by_role":   {k: asdict(v) for k, v in self.by_role.items()},
            "by_model":  {k: asdict(v) for k, v in self.by_model.items()},
            "by_day":    {k: asdict(v) for k, v in self.by_day.items()},
            "unknown_model_calls": self.unknown_model_calls,
            "unknown_models": self.unknown_models,
            "pricing_used": {k: list(v) for k, v in self.pricing_used.items()},
        }


# ─────────────────────────────────────────────────────────────────────
# Pricing math
# ─────────────────────────────────────────────────────────────────────


def estimate_dollars(*, input_tokens: int, output_tokens: int,
                      model: str) -> float:
    """Return USD estimate for one call. 0.0 for unknown models."""
    p = PRICING.get(model)
    if p is None:
        return 0.0
    in_per_m, out_per_m = p
    return ((input_tokens / 1_000_000.0) * in_per_m
            + (output_tokens / 1_000_000.0) * out_per_m)


# ─────────────────────────────────────────────────────────────────────
# Window filtering
# ─────────────────────────────────────────────────────────────────────


def _record_in_window(remembered_at: str, window: str,
                       *, now: _dt.datetime | None = None) -> bool:
    """Is this record's timestamp inside the requested window?"""
    if window == "all":
        return True
    if not remembered_at:
        return False
    try:
        ts = _dt.datetime.fromisoformat(remembered_at.replace("Z", "+00:00"))
    except (ValueError, TypeError):
        return False
    now = now or Nyx.now()
    # Treat naive timestamps as UTC-aware to match Nyx
    if ts.tzinfo is None and now.tzinfo is not None:
        ts = ts.replace(tzinfo=now.tzinfo)
    if window == "today":
        return ts.date() == now.date()
    seconds = _WINDOW_SECONDS.get(window)
    if seconds is None:
        return True
    delta = (now - ts).total_seconds()
    return 0 <= delta <= seconds


def _day_key(remembered_at: str) -> str:
    """YYYY-MM-DD key for the by_day rollup."""
    try:
        ts = _dt.datetime.fromisoformat(remembered_at.replace("Z", "+00:00"))
        return ts.strftime("%Y-%m-%d")
    except (ValueError, TypeError):
        return "unknown-date"


# ─────────────────────────────────────────────────────────────────────
# Plutus — the singleton
# ─────────────────────────────────────────────────────────────────────


class Plutus:
    """The cost accountant. Reads-only over `llm.call` records."""

    PRICING = PRICING  # exposed for introspection
    UNKNOWN_MODEL_KEY = UNKNOWN_MODEL_KEY
    WINDOWS = tuple(_WINDOW_SECONDS.keys())

    def estimate_dollars(self, *, input_tokens: int,
                          output_tokens: int,
                          model: str) -> float:
        """Public wrapper around the module-level estimator."""
        return estimate_dollars(input_tokens=input_tokens,
                                 output_tokens=output_tokens,
                                 model=model)

    # ───────────────────────────────────────────────────────────────
    # Budget enforcement (Delphi 2026-05-19-plutus-budget-arc.md)
    # ───────────────────────────────────────────────────────────────

    def budget_status(self) -> dict[str, Any]:
        """Snapshot of where current spend sits against operator-declared
        ceilings. Returns dict: {enabled, daily, weekly, monthly} where
        each window has {spent, ceiling, pct, state} and state is one
        of: 'ok' | 'warn' | 'over' | 'unset'."""
        try:
            from olympus.runtime.config import load as load_cfg
            cfg = load_cfg()
            b = cfg.plutus.budget
        except Exception:  # noqa: BLE001
            return {"enabled": False}
        if not b.enabled:
            return {"enabled": False}
        out: dict[str, Any] = {"enabled": True,
                                 "warn_at_pct": b.warn_at_pct}
        for window, ceiling, key in (
                ("today", b.daily_usd, "daily"),
                ("7d", b.weekly_usd, "weekly"),
                ("30d", b.monthly_usd, "monthly")):
            if ceiling <= 0:
                out[key] = {"spent": 0.0, "ceiling": 0.0,
                             "pct": 0.0, "state": "unset"}
                continue
            r = self.tally(window=window)
            spent = round(r.estimated_usd, 4)
            pct = round(100.0 * spent / ceiling, 1) if ceiling > 0 else 0.0
            if pct >= 100.0:
                state = "over"
            elif pct >= b.warn_at_pct:
                state = "warn"
            else:
                state = "ok"
            out[key] = {"spent": spent, "ceiling": ceiling,
                         "pct": pct, "state": state}
        return out

    def is_over_budget(self) -> bool:
        """True iff ANY enabled threshold is over 100%."""
        s = self.budget_status()
        if not s.get("enabled"):
            return False
        for key in ("daily", "weekly", "monthly"):
            entry = s.get(key) or {}
            if entry.get("state") == "over":
                return True
        return False

    def acknowledge_breach(self, *, reason: str = "") -> None:
        """Record an operator acknowledgment. Clears the
        breach-since-ack flag until the NEXT crossing."""
        from olympus.titans.mnemosyne import mnemosyne
        s = self.budget_status()
        mnemosyne.remember(
            kind="plutus.budget_ack",
            actor="zeus:operator",
            summary=("operator acknowledged budget breach"
                     + (f" — {reason[:80]}" if reason else "")),
            reason=reason,
            status_at_ack=s,
        )

    def breach_since_ack(self) -> bool:
        """True iff the substrate is currently over budget AND no
        valid acknowledgment exists. An ack is VALID iff it was made
        under the SAME budget config as the current state; if ceilings
        have changed (e.g., operator edited config, or a test fixture
        installed a different config), prior acks are stale and ignored.
        Among valid acks, the latest counts: spend that grew past the
        ack's spend re-triggers breach."""
        from olympus.titans.mnemosyne import mnemosyne
        if not self.is_over_budget():
            return False
        current = self.budget_status()
        current_sig = _budget_signature(current)
        acks = mnemosyne.recall("plutus.budget_ack")
        valid_acks = [a for a in acks
                      if _budget_signature(
                          (a.body or {}).get("status_at_ack") or {}
                      ) == current_sig]
        if not valid_acks:
            return True
        latest_ack = valid_acks[-1]
        ack_status = (latest_ack.body or {}).get("status_at_ack") or {}
        if not ack_status.get("enabled"):
            return True
        for key in ("daily", "weekly", "monthly"):
            curr = (current.get(key) or {}).get("spent", 0.0)
            ackd = (ack_status.get(key) or {}).get("spent", 0.0)
            ceiling = (current.get(key) or {}).get("ceiling", 0.0)
            if ceiling <= 0:
                continue
            if curr > ceiling and curr > ackd:
                return True
        return False

    def tally(self, window: str = "all", *,
              max_by_day_keys: int = 30) -> CostReport:
        """Aggregate `llm.call` Mnemosyne records into a CostReport.

        window: "all" | "today" | "1h" | "24h" | "7d" | "30d"
        """
        if window not in _WINDOW_SECONDS:
            raise ValueError(
                f"unknown window {window!r}; "
                f"valid: {sorted(_WINDOW_SECONDS.keys())}"
            )

        report = CostReport(window=window)
        bridge_acc: dict[str, CostBreakdown] = defaultdict(CostBreakdown)
        role_acc:   dict[str, CostBreakdown] = defaultdict(CostBreakdown)
        model_acc:  dict[str, CostBreakdown] = defaultdict(CostBreakdown)
        day_acc:    dict[str, CostBreakdown] = defaultdict(CostBreakdown)
        unknown_models: set[str] = set()

        try:
            records = mnemosyne.recall("llm.call")
        except Exception:  # noqa: BLE001
            records = []

        now = Nyx.now()
        for m in records:
            if not _record_in_window(m.remembered_at, window, now=now):
                continue
            body = m.body or {}
            bridge = str(body.get("bridge", "(unknown-bridge)"))
            role = str(body.get("role", "") or "(none)")
            model = str(body.get("model", "") or UNKNOWN_MODEL_KEY)
            try:
                in_tokens = int(body.get("input_tokens", 0) or 0)
                out_tokens = int(body.get("output_tokens", 0) or 0)
            except (TypeError, ValueError):
                in_tokens, out_tokens = 0, 0

            usd = estimate_dollars(input_tokens=in_tokens,
                                    output_tokens=out_tokens,
                                    model=model)
            if model not in PRICING:
                report.unknown_model_calls += 1
                unknown_models.add(model)

            # Add to each axis
            for acc, key in ((bridge_acc, bridge),
                              (role_acc, role),
                              (model_acc, model),
                              (day_acc, _day_key(m.remembered_at))):
                b = acc[key]
                b.calls += 1
                b.input_tokens += in_tokens
                b.output_tokens += out_tokens
                b.estimated_usd += usd

            report.total_calls += 1
            report.total_input_tokens += in_tokens
            report.total_output_tokens += out_tokens
            report.estimated_usd += usd

        # Materialize defaultdicts → plain dicts (sorted for stable output)
        report.by_bridge = dict(sorted(bridge_acc.items(),
                                        key=lambda kv: -kv[1].estimated_usd))
        report.by_role = dict(sorted(role_acc.items(),
                                      key=lambda kv: -kv[1].estimated_usd))
        report.by_model = dict(sorted(model_acc.items(),
                                       key=lambda kv: -kv[1].estimated_usd))
        # by_day: keep only the most recent N keys, sorted descending
        sorted_days = sorted(day_acc.items(), reverse=True)
        report.by_day = dict(sorted_days[:max_by_day_keys])
        report.unknown_models = sorted(unknown_models)
        report.pricing_used = {k: v for k, v in PRICING.items()
                               if k in report.by_model}
        return report


# Module-level singleton
plutus = Plutus()


__all__ = [
    "Plutus", "plutus", "PRICING",
    "CostReport", "CostBreakdown",
    "estimate_dollars", "UNKNOWN_MODEL_KEY",
]
