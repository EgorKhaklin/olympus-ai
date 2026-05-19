"""olympus.runtime.grounding — make LLM agents cite real things.

Per Delphi 2026-05-19-grounding-arc.md.

The problem this closes: agents reason fluently *in* the mythology
(citing S5, AP7, etc. correctly) but fabricate filesystem paths and
record identifiers because nobody is grounding them in the actual
substrate state. Hephaestus cited `strategic/delphi/debates/*.md`
during the throne demo; that path does not exist anywhere.

What grounding does:

  1. **Per-call context injection** — `build_grounding_for_role(role)`
     assembles a role-specific block (real Pantheon roster, recent
     Mnemosyne records, AP catalog, etc.) that is prepended to the
     user prompt at call time. Hard token budget per role.

  2. **Post-call verification** — `cited_paths_in_text(response)` +
     `verify_cited_paths(paths)` checks every path the model cited.
     Fabricated paths are surfaced as `fabricated_paths` on the
     result and the agent's confidence is downgraded by 0.2.

  3. **Audit-of-record** — every grounding build + every verification
     is recorded to Mnemosyne under `agent.grounding_check`. Future
     calibration scoring can correlate fabrication-rate with bridge,
     model, and prompt-shape.

Constitutional posture:
  - S1: every check → Mnemosyne
  - S6: fabrication → confidence penalty (real consequence, not theater)
  - S8: grounding contexts are JSON-serializable; reproducible
  - AP1: ~200 LOC; agents.py wiring is ~15 added lines
"""
from __future__ import annotations

import hashlib
import json
import pathlib
import re
from dataclasses import dataclass, field, asdict
from typing import Any

from olympus.primordials.gaia import root
from olympus.primordials.nyx import Nyx
from olympus.titans.mnemosyne import mnemosyne


# ─────────────────────────────────────────────────────────────────────
# Data classes
# ─────────────────────────────────────────────────────────────────────


@dataclass
class GroundedRead:
    """Result of reading a file with grounding-discipline."""
    path: str                       # the relpath the caller requested
    exists: bool                    # was a file actually read?
    content_head: str = ""          # first N chars (default 2000)
    sha256: str = ""                # full-content hash if read
    bytes_total: int = 0
    error: str = ""                 # why we couldn't read (if !exists)


@dataclass
class GroundedCheck:
    """Result of verifying one cited path. JSON-safe."""
    cited: str                      # the path as cited by the agent
    normalized: str                 # the resolved relpath (if resolvable)
    exists: bool
    reason: str = ""                # why exists is False, when False


# ─────────────────────────────────────────────────────────────────────
# Safety: project-root whitelist (no .. escape, no symlink escape)
# ─────────────────────────────────────────────────────────────────────


_PROJECT_ROOT = root.root.resolve()


def _is_within_root(p: pathlib.Path) -> bool:
    """True iff p resolves to a path under the project root."""
    try:
        resolved = p.resolve()
    except (OSError, RuntimeError):
        return False
    try:
        resolved.relative_to(_PROJECT_ROOT)
        return True
    except ValueError:
        return False


# ─────────────────────────────────────────────────────────────────────
# Reading: grounded file access
# ─────────────────────────────────────────────────────────────────────


def read_file_grounded(relpath: str, *,
                        head_chars: int = 2000) -> GroundedRead:
    """Read a file relative to the project root. Whitelisted: rejects
    absolute paths outside root, rejects '..' escapes, rejects symlinks
    pointing outside root. Never raises."""
    if not relpath:
        return GroundedRead(path="", exists=False,
                             error="empty path")
    # Normalize relative paths against root
    candidate = pathlib.Path(relpath)
    if candidate.is_absolute():
        # Allow absolute paths only if they're under root
        target = candidate
    else:
        target = _PROJECT_ROOT / candidate
    if not _is_within_root(target):
        return GroundedRead(path=relpath, exists=False,
                             error="resolves outside project root")
    try:
        if not target.exists():
            return GroundedRead(path=relpath, exists=False,
                                 error="file not found")
        if not target.is_file():
            return GroundedRead(path=relpath, exists=False,
                                 error="not a regular file")
        data = target.read_bytes()
        text = data.decode("utf-8", errors="replace")
        return GroundedRead(
            path=str(target.relative_to(_PROJECT_ROOT)),
            exists=True,
            content_head=text[:head_chars],
            sha256=hashlib.sha256(data).hexdigest(),
            bytes_total=len(data),
        )
    except Exception as exc:  # noqa: BLE001
        return GroundedRead(path=relpath, exists=False,
                             error=f"{type(exc).__name__}: {exc}")


# ─────────────────────────────────────────────────────────────────────
# Mnemosyne recall — JSON-safe wrapper
# ─────────────────────────────────────────────────────────────────────


def recall_grounded(kind: str, *, limit: int = 10) -> list[dict[str, Any]]:
    """Return the last N records for `kind` as JSON-safe dicts. Used
    by `build_grounding_for_role` to attach real history to the LLM
    prompt."""
    if limit < 1:
        return []
    try:
        records = mnemosyne.recall(kind)
    except Exception:  # noqa: BLE001
        return []
    out: list[dict[str, Any]] = []
    for m in records[-limit:]:
        out.append({
            "kind": m.kind,
            "actor": m.actor,
            "summary": m.summary,
            "remembered_at": m.remembered_at,
            # Body fields can be sensitive; expose head only
            "body_keys": sorted((m.body or {}).keys())[:10],
        })
    return out


# ─────────────────────────────────────────────────────────────────────
# Citation extraction + verification
# ─────────────────────────────────────────────────────────────────────


# Match path-shaped substrings: at least one slash, ends with a short
# extension OR begins with a known project subdir. Allows `*`/`?` so
# glob citations (`codex/oracles/delphi/*.md`) are caught too.
_PATH_RX = re.compile(
    r"(?:[a-zA-Z0-9_\-./*?]+/)+[a-zA-Z0-9_\-*?]+(?:\.[a-zA-Z0-9*?]{1,5})?"
)

# Known project top-level directories (used to distinguish path-like
# strings from URL fragments, Greek names, etc.)
_PROJECT_DIRS = frozenset({
    "src", "codex", "tests", "state", "scripts", "examples",
})


def cited_paths_in_text(text: str) -> list[str]:
    """Extract path-shaped substrings the agent cited. Conservative:
    requires either an extension OR a known top-level project dir."""
    if not text:
        return []
    seen: set[str] = set()
    out: list[str] = []
    for match in _PATH_RX.finditer(text):
        candidate = match.group(0).strip(".,;:)")
        # Filter out URLs (anything with ://)
        if "://" in candidate:
            continue
        # Filter out version-like tokens
        if re.match(r"^\d+(?:\.\d+)+$", candidate):
            continue
        # Require either a project-dir prefix OR a recognizable extension
        head = candidate.split("/", 1)[0]
        has_ext = bool(re.search(r"\.[a-zA-Z]{1,5}$", candidate))
        if head not in _PROJECT_DIRS and not has_ext:
            continue
        if candidate in seen:
            continue
        seen.add(candidate)
        out.append(candidate)
    return out


def verify_cited_paths(paths: list[str]) -> list[GroundedCheck]:
    """For each cited path, return a GroundedCheck."""
    out: list[GroundedCheck] = []
    for cited in paths:
        candidate = pathlib.Path(cited)
        target = (_PROJECT_ROOT / candidate
                  if not candidate.is_absolute() else candidate)
        if not _is_within_root(target):
            out.append(GroundedCheck(
                cited=cited, normalized="",
                exists=False,
                reason="resolves outside project root"))
            continue
        normalized = ""
        try:
            normalized = str(target.resolve().relative_to(_PROJECT_ROOT))
        except (OSError, ValueError):
            pass
        # A path with a glob (`*`, `?`) is considered "exists" if at
        # least one match resolves; treat literal glob as not-fabricated
        # if any siblings match.
        if any(c in cited for c in "*?"):
            try:
                matches = list(_PROJECT_ROOT.glob(cited))
            except (OSError, ValueError):
                matches = []
            out.append(GroundedCheck(
                cited=cited, normalized=normalized,
                exists=bool(matches),
                reason=("no glob matches" if not matches else "")))
            continue
        exists = target.exists()
        out.append(GroundedCheck(
            cited=cited, normalized=normalized,
            exists=exists,
            reason=("file not found" if not exists else "")))
    return out


# ─────────────────────────────────────────────────────────────────────
# Per-role grounding builders
# ─────────────────────────────────────────────────────────────────────


_BUDGET_CHARS = 3000  # per-role grounding cap


def _fit_to_budget(blob: dict[str, Any]) -> str:
    """JSON-serialize blob, trimming list-valued fields from the tail
    until the serialized length fits the budget. Always emits valid
    JSON (we never slice the serialized string mid-token)."""
    s = json.dumps(blob, indent=2, default=str)
    if len(s) <= _BUDGET_CHARS:
        return s
    # Walk the lists and pop the OLDEST entries (front of list) until fit
    trimmed = json.loads(s)
    list_keys = [k for k, v in trimmed.items() if isinstance(v, list)]
    if not list_keys:
        # No lists to trim; truncate the longest string field
        for k in sorted(trimmed.keys(),
                         key=lambda k: len(str(trimmed[k])),
                         reverse=True):
            if isinstance(trimmed[k], str) and len(trimmed[k]) > 200:
                trimmed[k] = trimmed[k][:200] + "…(trimmed)"
                s = json.dumps(trimmed, indent=2, default=str)
                if len(s) <= _BUDGET_CHARS:
                    return s
        return s[:_BUDGET_CHARS - 20] + "\n  …(over-budget)\n}"
    # Trim list keys round-robin until under budget
    safety_iterations = 200
    while len(s) > _BUDGET_CHARS and safety_iterations > 0:
        progress = False
        for k in list_keys:
            if trimmed[k]:
                trimmed[k].pop(0)
                progress = True
                s = json.dumps(trimmed, indent=2, default=str)
                if len(s) <= _BUDGET_CHARS:
                    return s
        if not progress:
            break
        safety_iterations -= 1
    return s


def _pantheon_roster() -> list[str]:
    """Best-effort: list of figure names from the pantheon."""
    try:
        from olympus.pantheon import roster
        return [f.name for f in roster()][:120]
    except Exception:  # noqa: BLE001
        # Fallback: parse codex/PANTHEON.md headings
        r = read_file_grounded("codex/PANTHEON.md", head_chars=20000)
        if not r.exists:
            return []
        names: list[str] = []
        for line in r.content_head.splitlines():
            m = re.match(r"^##+\s+([A-Z][a-zA-Z]+)", line.strip())
            if m:
                names.append(m.group(1))
        return names[:120]


def _build_hephaestus_grounding() -> str:
    roster = _pantheon_roster()
    recent_sessions = recall_grounded("session.completed", limit=8)
    recent_errors = recall_grounded("session.errored", limit=5)
    recent_proposals = recall_grounded("proposal.raised", limit=5)
    blob = {
        "pantheon": roster[:60],
        "recent_session_completed": recent_sessions,
        "recent_session_errored": recent_errors,
        "recent_proposal_raised": recent_proposals,
    }
    return _fit_to_budget(blob)


def _build_momus_grounding() -> str:
    recent_proposals = recall_grounded("proposal.raised", limit=8)
    ap_catalog_read = read_file_grounded(
        "codex/AP-CATALOG.md", head_chars=1800)
    blob = {
        "ap_catalog_head": (ap_catalog_read.content_head
                            if ap_catalog_read.exists
                            else "(catalog file not found)"),
        "recent_proposal_raised": recent_proposals,
    }
    return _fit_to_budget(blob)


def _build_cassandra_grounding() -> str:
    dismissed = recall_grounded("warning.dismissed", limit=10)
    pheromones = recall_grounded("argos.pheromone", limit=8)
    blob = {
        "recent_warning_dismissed": dismissed,
        "recent_argos_pheromone": pheromones,
    }
    return _fit_to_budget(blob)


def _build_athena_grounding() -> str:
    sessions = recall_grounded("session.completed", limit=10)
    proposals = recall_grounded("proposal.raised", limit=5)
    blob = {
        "recent_session_completed": sessions,
        "recent_proposal_raised": proposals,
    }
    return _fit_to_budget(blob)


def _build_figure_proposer_grounding() -> str:
    roster = _pantheon_roster()
    blob = {
        "existing_figures": roster,
        "note": ("If your proposed figure's role overlaps with any "
                  "of these, you MUST justify why it is distinct or "
                  "withdraw the proposal."),
    }
    return _fit_to_budget(blob)


_ROLE_BUILDERS = {
    "hephaestus":      _build_hephaestus_grounding,
    "momus":           _build_momus_grounding,
    "cassandra":       _build_cassandra_grounding,
    "athena":          _build_athena_grounding,
    "figure_proposer": _build_figure_proposer_grounding,
}


def build_grounding_for_role(role: str) -> str:
    """Return the role-specific grounding block as a JSON-shaped
    string. Empty string for unknown roles (caller may treat as
    grounding-not-required)."""
    fn = _ROLE_BUILDERS.get(role)
    if fn is None:
        return ""
    try:
        return fn()
    except Exception as exc:  # noqa: BLE001
        return json.dumps({"_grounding_error": str(exc)})


# ─────────────────────────────────────────────────────────────────────
# Audit recording
# ─────────────────────────────────────────────────────────────────────


def record_grounding_check(*, role: str, cited_paths: list[str],
                            checks: list[GroundedCheck],
                            confidence_penalty: float = 0.0) -> None:
    """Persist the grounding-verification outcome under
    `agent.grounding_check`. Operator can recall to audit fabrication
    rate per role / bridge / model."""
    fabricated = [c.cited for c in checks if not c.exists]
    mnemosyne.remember(
        kind="agent.grounding_check",
        actor=f"grounding:{role}",
        summary=(f"{role}: {len(cited_paths)} cited · "
                 f"{len(fabricated)} fabricated · "
                 f"penalty={confidence_penalty:.2f}"),
        role=role,
        cited_count=len(cited_paths),
        fabricated_count=len(fabricated),
        fabricated_paths=fabricated[:20],
        all_checks=[asdict(c) for c in checks][:20],
        confidence_penalty=confidence_penalty,
    )


# ─────────────────────────────────────────────────────────────────────
# Convenience: full grounding pipeline (used by agents.py::run)
# ─────────────────────────────────────────────────────────────────────


CONFIDENCE_PENALTY_PER_FABRICATION = 0.2


def apply_grounding(*, role: str, response_text: str,
                     parsed: dict[str, Any]) -> dict[str, Any]:
    """Post-call: verify cited paths, update parsed with fabrication
    facts, record the check. Returns the updated parsed dict (mutated
    + returned for chaining)."""
    cited = cited_paths_in_text(response_text)
    checks = verify_cited_paths(cited)
    fabricated = [c.cited for c in checks if not c.exists]
    penalty = (CONFIDENCE_PENALTY_PER_FABRICATION
               if fabricated else 0.0)

    # Always expose the facts to the operator
    parsed["cited_paths"] = cited
    parsed["fabricated_paths"] = fabricated
    parsed["grounding_penalty"] = penalty

    # Downgrade confidence (clamped to [0, 1])
    if penalty and "confidence" in parsed:
        try:
            base = float(parsed["confidence"])
            parsed["confidence"] = max(0.0, min(1.0, base - penalty))
        except (TypeError, ValueError):
            pass

    record_grounding_check(role=role, cited_paths=cited,
                            checks=checks,
                            confidence_penalty=penalty)
    return parsed
