"""olympus.runtime.replay — regression harness over past agent.invocation.

Per Delphi 2026-05-19-olympus-replay-arc.md (Decade #10 — closer).

Selects past `agent.invocation` records, pairs them with their
`llm.call` partners (by prompt_hash + role + time-proximity), re-runs
through the current code path, and classifies each replay as one of:
  - stable    — parsed keys match, risk_class same, confidence ±0.3
  - drift     — schema match but values shifted
  - broken    — raised, parse-error, or unrecognized schema
  - skipped   — no paired llm.call OR test-seed
  - over-budget — Arc 20 bridge guard refused

EchoBridge is default — replays cost nothing. `--use-anthropic` opts
into real LLM calls and respects Arc 20's budget enforcement.
"""
from __future__ import annotations

import datetime as _dt
import time
from dataclasses import dataclass, field, asdict
from typing import Any, Iterable

from olympus.primordials.nyx import Nyx
from olympus.titans.mnemosyne import mnemosyne
from olympus.runtime.test_seeds import is_test_record


# ─────────────────────────────────────────────────────────────────────
# Bounds + classification thresholds
# ─────────────────────────────────────────────────────────────────────


MAX_LIMIT = 200
CONFIDENCE_DRIFT_THRESHOLD = 0.3
LIST_DRIFT_RATIO = 0.5    # > 50% shrink/growth = drift
PER_REPLAY_TIMEOUT_S = 30


# ─────────────────────────────────────────────────────────────────────
# Data classes
# ─────────────────────────────────────────────────────────────────────


@dataclass
class ReplayPlan:
    """How a replay batch should be configured."""
    limit: int = 20
    role: str | None = None
    since_hours: float | None = None
    bridge: str = "echo"       # "echo" | "anthropic" | "scripted"
    include_test_seeds: bool = False


@dataclass
class ReplayCandidate:
    """One agent.invocation paired with its llm.call source prompt."""
    agent_record_id: str       # synthetic id (kind + index)
    role: str
    user_prompt: str           # from llm.call.user_head
    original_parsed: dict[str, Any]
    original_confidence: float
    original_bridge: str
    original_at: str


@dataclass
class ReplayResult:
    """The outcome of one replay."""
    candidate_id: str
    role: str
    classification: str        # stable | drift | broken | skipped | over-budget
    new_parsed: dict[str, Any] = field(default_factory=dict)
    new_confidence: float = 0.0
    new_bridge: str = ""
    diffs: list[str] = field(default_factory=list)
    elapsed_ms: float = 0.0
    error: str = ""


@dataclass
class ReplayReport:
    """Aggregate of a replay batch."""
    started_at: str
    finished_at: str = ""
    bridge_used: str = ""
    total: int = 0
    stable: int = 0
    drift: int = 0
    broken: int = 0
    skipped: int = 0
    over_budget: int = 0
    by_role: dict[str, dict[str, int]] = field(default_factory=dict)
    drift_examples: list[ReplayResult] = field(default_factory=list)
    broken_examples: list[ReplayResult] = field(default_factory=list)
    elapsed_ms: float = 0.0


# ─────────────────────────────────────────────────────────────────────
# Candidate selection — pair agent.invocation with its llm.call
# ─────────────────────────────────────────────────────────────────────


_AGENT_ROLES = ("hephaestus", "momus", "cassandra", "athena",
                "figure_proposer")


def plan_replays(plan: ReplayPlan) -> list[ReplayCandidate]:
    """Build the list of replay candidates per plan filters."""
    if plan.limit < 1:
        return []
    limit = min(plan.limit, MAX_LIMIT)
    role_filter = (plan.role or "").strip() or None
    if role_filter and role_filter not in _AGENT_ROLES:
        return []   # unknown role

    cutoff: _dt.datetime | None = None
    if plan.since_hours is not None and plan.since_hours > 0:
        now = Nyx.now()
        cutoff = now - _dt.timedelta(hours=plan.since_hours)

    # Build llm.call lookup by (role, prompt_hash) → record
    llm_calls = mnemosyne.recall("llm.call")
    by_role_hash: dict[tuple[str, str], Any] = {}
    for c in llm_calls:
        body = c.body or {}
        if not plan.include_test_seeds and is_test_record(c):
            continue
        role = str(body.get("role", ""))
        if role not in _AGENT_ROLES:
            continue
        if role_filter and role != role_filter:
            continue
        ph = str(body.get("prompt_hash", ""))
        if not ph:
            continue
        # Keep the most recent llm.call per (role, prompt_hash)
        existing = by_role_hash.get((role, ph))
        if existing is None or (
                str(c.remembered_at) > str(existing.remembered_at)):
            by_role_hash[(role, ph)] = c

    agent_invocs = mnemosyne.recall("agent.invocation")
    # Newest first
    invocs_sorted = list(reversed(agent_invocs))
    candidates: list[ReplayCandidate] = []
    for idx, inv in enumerate(invocs_sorted):
        if len(candidates) >= limit:
            break
        if not plan.include_test_seeds and is_test_record(inv):
            continue
        body = inv.body or {}
        role = str(body.get("role", ""))
        if role not in _AGENT_ROLES:
            continue
        if role_filter and role != role_filter:
            continue
        # Time filter
        if cutoff is not None and inv.remembered_at:
            try:
                ts = _dt.datetime.fromisoformat(
                    inv.remembered_at.replace("Z", "+00:00"))
                if ts.tzinfo is None and cutoff.tzinfo is not None:
                    ts = ts.replace(tzinfo=cutoff.tzinfo)
                if ts < cutoff:
                    continue
            except (ValueError, TypeError):
                pass
        # Find paired llm.call by prompt_hash (in linked record if present)
        # The agent.invocation body doesn't carry prompt_hash directly;
        # match via the closest llm.call for this role recorded around
        # the same time.
        paired = _find_paired_llm_call(inv, by_role_hash, role)
        if paired is None:
            # Skip candidates we can't pair — we don't fabricate prompts
            continue
        user_prompt = str((paired.body or {}).get("user_head", ""))
        if not user_prompt:
            continue
        candidates.append(ReplayCandidate(
            agent_record_id=f"agent.invocation#{idx}",
            role=role,
            user_prompt=user_prompt,
            original_parsed=dict(body.get("parsed", {})),
            original_confidence=float(body.get("confidence", 0.0)),
            original_bridge=str(body.get("bridge", "")),
            original_at=str(inv.remembered_at),
        ))
    return candidates


def _find_paired_llm_call(invocation, by_role_hash, role):
    """Find the llm.call that produced this agent.invocation.
    Strategy: same role, recorded within 60 seconds before invocation.
    """
    inv_ts = invocation.remembered_at or ""
    candidates = []
    for (r, ph), c in by_role_hash.items():
        if r != role:
            continue
        c_ts = c.remembered_at or ""
        # Allow some slack — llm.call is recorded before the
        # invocation completes, so the call should be a few seconds
        # earlier. Just pick the closest in time.
        candidates.append((abs_diff(c_ts, inv_ts), c))
    if not candidates:
        return None
    candidates.sort(key=lambda x: x[0])
    if candidates[0][0] is None or candidates[0][0] > 120.0:
        # No close match
        return None
    return candidates[0][1]


def abs_diff(a: str, b: str) -> float | None:
    try:
        ta = _dt.datetime.fromisoformat(a.replace("Z", "+00:00"))
        tb = _dt.datetime.fromisoformat(b.replace("Z", "+00:00"))
        if ta.tzinfo is None and tb.tzinfo is not None:
            ta = ta.replace(tzinfo=tb.tzinfo)
        if tb.tzinfo is None and ta.tzinfo is not None:
            tb = tb.replace(tzinfo=ta.tzinfo)
        return abs((ta - tb).total_seconds())
    except (ValueError, TypeError):
        return None


# ─────────────────────────────────────────────────────────────────────
# Replay execution
# ─────────────────────────────────────────────────────────────────────


def replay_one(candidate: ReplayCandidate,
                plan: ReplayPlan) -> ReplayResult:
    """Re-run one candidate; classify; record to Mnemosyne."""
    started = time.perf_counter()
    out = ReplayResult(
        candidate_id=candidate.agent_record_id,
        role=candidate.role,
        classification="skipped",
        new_bridge=plan.bridge,
    )
    try:
        # Bridge selection: import lazily so env-var-driven default
        # bridges can be overridden by the plan
        from olympus.runtime import llm_bridge as bridge_mod
        if plan.bridge == "echo":
            from olympus.runtime.llm_bridge import EchoBridge
            chosen = EchoBridge()
        elif plan.bridge == "anthropic":
            from olympus.runtime.llm_bridge import AnthropicBridge
            chosen = AnthropicBridge()
        else:
            # Unknown bridge → fall through to default
            chosen = bridge_mod.bridge()

        # Inject the bridge for this call only, run the agent
        from olympus.runtime import agents as agents_mod
        original_bridge_fn = bridge_mod.bridge
        bridge_mod.bridge = lambda: chosen   # type: ignore[assignment]
        try:
            result = agents_mod.run(
                candidate.role, candidate.user_prompt,
                check_pan=False)
        finally:
            bridge_mod.bridge = original_bridge_fn
    except Exception as exc:  # noqa: BLE001
        out.classification = "broken"
        out.error = f"{type(exc).__name__}: {exc}"
        out.elapsed_ms = (time.perf_counter() - started) * 1000.0
        _record(out, candidate)
        return out

    # Check for bridge errors (e.g., budget breach)
    if getattr(result, "error", ""):
        if "budget" in result.error.lower():
            out.classification = "over-budget"
        else:
            out.classification = "broken"
        out.error = result.error[:200]
        out.elapsed_ms = (time.perf_counter() - started) * 1000.0
        _record(out, candidate)
        return out

    out.new_parsed = dict(result.parsed or {})
    out.new_confidence = float(getattr(result, "confidence", 0.0))
    out.classification, out.diffs = _classify(
        candidate.original_parsed,
        candidate.original_confidence,
        out.new_parsed,
        out.new_confidence,
    )
    out.elapsed_ms = (time.perf_counter() - started) * 1000.0
    _record(out, candidate)
    return out


def _classify(old_parsed: dict, old_conf: float,
              new_parsed: dict, new_conf: float
              ) -> tuple[str, list[str]]:
    """Classify the diff. Returns (classification, diffs)."""
    if not new_parsed:
        return ("broken", ["new parsed is empty"])
    # Schema check: old keys present in new?
    # We ignore grounding-added keys (cited_paths, fabricated_paths,
    # grounding_penalty) since those are added by the grounding arc
    # post-processing, not the agent itself
    grounding_keys = {"cited_paths", "fabricated_paths",
                       "grounding_penalty"}
    old_keys = set(old_parsed.keys()) - grounding_keys
    new_keys = set(new_parsed.keys()) - grounding_keys
    missing = old_keys - new_keys
    if missing:
        return ("broken",
                [f"schema regression: missing keys {sorted(missing)}"])

    diffs: list[str] = []
    # Risk-class drift (Hephaestus)
    if "risk_class" in old_parsed and "risk_class" in new_parsed:
        if str(old_parsed["risk_class"]) != str(new_parsed["risk_class"]):
            diffs.append(
                f"risk_class: {old_parsed['risk_class']} → "
                f"{new_parsed['risk_class']}")
    # Confidence drift
    try:
        delta = abs(float(new_conf) - float(old_conf))
        if delta > CONFIDENCE_DRIFT_THRESHOLD:
            diffs.append(
                f"confidence: {old_conf:.2f} → {new_conf:.2f} "
                f"(Δ {delta:.2f})")
    except (TypeError, ValueError):
        pass
    # List drift
    for k in old_keys & new_keys:
        old_v, new_v = old_parsed.get(k), new_parsed.get(k)
        if isinstance(old_v, list) and isinstance(new_v, list):
            ov, nv = len(old_v), len(new_v)
            base = max(ov, 1)
            if abs(ov - nv) / base > LIST_DRIFT_RATIO:
                diffs.append(f"{k} length: {ov} → {nv}")
    if diffs:
        return ("drift", diffs)
    return ("stable", [])


def _record(result: ReplayResult,
             candidate: ReplayCandidate) -> None:
    """One regression record per replay."""
    mnemosyne.remember(
        kind="replay.regression",
        actor="replay-harness",
        summary=(f"{candidate.role}: {result.classification} "
                 f"({result.elapsed_ms:.0f}ms)"
                 + (f" — {result.diffs[0][:80]}"
                    if result.diffs else "")),
        candidate_id=candidate.agent_record_id,
        role=candidate.role,
        classification=result.classification,
        diffs=result.diffs[:10],
        old_confidence=candidate.original_confidence,
        new_confidence=result.new_confidence,
        new_bridge=result.new_bridge,
        elapsed_ms=result.elapsed_ms,
        error=result.error,
    )


# ─────────────────────────────────────────────────────────────────────
# Batch
# ─────────────────────────────────────────────────────────────────────


def replay_many(plan: ReplayPlan) -> ReplayReport:
    """Run the full plan; return the aggregate."""
    started = time.perf_counter()
    report = ReplayReport(
        started_at=Nyx.now().isoformat(),
        bridge_used=plan.bridge,
    )
    candidates = plan_replays(plan)
    for cand in candidates:
        r = replay_one(cand, plan)
        report.total += 1
        _bump(report, r.classification)
        _bump_role(report, cand.role, r.classification)
        if r.classification == "drift" and len(report.drift_examples) < 10:
            report.drift_examples.append(r)
        elif (r.classification == "broken"
              and len(report.broken_examples) < 10):
            report.broken_examples.append(r)
    report.finished_at = Nyx.now().isoformat()
    report.elapsed_ms = (time.perf_counter() - started) * 1000.0
    return report


def _bump(report: ReplayReport, classification: str) -> None:
    key = classification.replace("-", "_")
    if hasattr(report, key):
        setattr(report, key, getattr(report, key) + 1)


def _bump_role(report: ReplayReport, role: str,
                classification: str) -> None:
    if role not in report.by_role:
        report.by_role[role] = {
            "stable": 0, "drift": 0, "broken": 0,
            "skipped": 0, "over_budget": 0,
        }
    key = classification.replace("-", "_")
    if key in report.by_role[role]:
        report.by_role[role][key] += 1


__all__ = [
    "ReplayPlan", "ReplayCandidate", "ReplayResult", "ReplayReport",
    "plan_replays", "replay_one", "replay_many",
    "CONFIDENCE_DRIFT_THRESHOLD", "LIST_DRIFT_RATIO", "MAX_LIMIT",
]
