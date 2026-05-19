"""olympus.runtime.test_seeds — the source of truth for "is this a test seed?".

Per Delphi 2026-05-19-tartarus-arc.md.

Investigation showed that 4 of the 5 substrate-surfaced gaps share one
root cause: tests write records that pollute production-facing metrics.
The substrate has been crying about its own health based on test residue.

This module is the **one place** that defines what "test-seed" means.
Production layers (wisdom, doctor, healer, oracles) import from here.
Tests are still recorded fully to Mnemosyne (S1 holds); only
production-facing aggregates filter them out.

Design discipline:
  - Conservative — false negatives preferred over false positives.
    If we're not SURE it's a test seed, treat it as production.
  - Class-level rules (not per-record). Adding a new test class
    should NOT require new patterns here unless the convention drifts.
  - Operator-readable rules. The patterns are written so a human
    can audit "does this look like test residue?" at a glance.
"""
from __future__ import annotations

import re
from typing import Any


# ─────────────────────────────────────────────────────────────────────
# Actor / owner patterns
# ─────────────────────────────────────────────────────────────────────

# An actor/owner is a test seed if any of these are true:
#   - ends with '-test'  (e.g., "charon-test", "asclepius-test")
#   - ends with ':test'  (some heroes append role with colon)
#   - contains 'test-'   (e.g., "test-owner", "test-plutus")
#   - is exactly 'test'
#   - starts with 'test-' / 'test_'  (e.g., "test_seed")

_ACTOR_RX = re.compile(
    r"(^test[_-]|[_-]test$|:test$|test-[a-z]+|^test$)",
    re.IGNORECASE,
)


def is_test_actor(actor: str | None) -> bool:
    """True iff actor looks like a test fixture/seed source."""
    if not actor:
        return False
    return bool(_ACTOR_RX.search(str(actor)))


def is_test_owner(owner: str | None) -> bool:
    """Same shape as is_test_actor — Atlas burden owners use the same
    naming convention as Mnemosyne actors."""
    return is_test_actor(owner)


# ─────────────────────────────────────────────────────────────────────
# Proposal-shape predicates (looks at the dict, not the actor)
# ─────────────────────────────────────────────────────────────────────


def is_test_proposal(proposal: dict[str, Any] | None) -> bool:
    """A Hephaestus proposal dict is a test seed if its content is
    obviously synthetic. Investigation found three reliable signatures:

      1. proposed_fix is exactly 'test' or 'n/a'
      2. rationale contains 'test' AND drift_observed ends with ': test'
      3. id contains 'test-' (test-specific id namespacing)
    """
    if not isinstance(proposal, dict):
        return False
    fix = str(proposal.get("proposed_fix", "")).strip().lower()
    if fix in {"test", "n/a", "test."}:
        return True
    rationale = str(proposal.get("rationale", "")).lower()
    drift = str(proposal.get("drift_observed", "")).lower()
    if "test" in rationale and drift.rstrip().endswith(": test"):
        return True
    pid = str(proposal.get("id", ""))
    if "test-" in pid or pid.startswith("test"):
        return True
    return False


# ─────────────────────────────────────────────────────────────────────
# Mnemosyne record predicate (the union)
# ─────────────────────────────────────────────────────────────────────


def is_test_record(memory: Any) -> bool:
    """True iff a Mnemosyne `Memory` should be excluded from
    production-facing aggregates. Looks at actor + body shape."""
    if memory is None:
        return False
    if is_test_actor(getattr(memory, "actor", "")):
        return True
    body = getattr(memory, "body", {}) or {}
    # Sessions: directive contains 'test' marker
    directive = str(body.get("directive", "")).lower()
    if "test:" in directive or directive.startswith("test ") \
       or directive == "test":
        return True
    # Proposals embedded in records
    if "proposed_fix" in body and is_test_proposal(body):
        return True
    return False


# ─────────────────────────────────────────────────────────────────────
# Convenience: filter helpers for the production layers
# ─────────────────────────────────────────────────────────────────────


def filter_out_test_records(records: list) -> list:
    """Return only records that are NOT test seeds. Used by wisdom +
    doctor production aggregates."""
    return [r for r in records if not is_test_record(r)]


def filter_out_test_proposals(proposals: list[dict]) -> list[dict]:
    """Return only proposals that are NOT test seeds."""
    return [p for p in proposals if not is_test_proposal(p)]


__all__ = [
    "is_test_actor", "is_test_owner", "is_test_proposal",
    "is_test_record",
    "filter_out_test_records", "filter_out_test_proposals",
]
