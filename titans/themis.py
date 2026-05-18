"""Themis — titaness of divine law, custom, and natural order.

Themis is the personification of right order, sacred law that pre-dates
the Olympians. She gave humans the Oracle at Delphi before Apollo took
it over. In Olympus, Themis is the constitution: she enumerates the
substrate invariants (S1–S8) and answers "is this allowed?"

The COSMOGONY.md file names the substrate invariants in human-readable
form. This module makes them machine-checkable.
"""
from __future__ import annotations

import re
import pathlib
from dataclasses import dataclass
from typing import Callable

from primordials.gaia import root


@dataclass(frozen=True)
class Invariant:
    """A substrate invariant."""
    id: str            # e.g., "S1"
    name: str          # short name
    statement: str     # human-readable claim
    enforcement: str   # how it's checked


# The eight substrate invariants. Domain-specific invariants (C1–CN)
# live in DOMAIN.md (deployment-side) and are not enumerated here.
SUBSTRATE_INVARIANTS: tuple[Invariant, ...] = (
    Invariant(
        id="S1", name="Mnemosyne — append-only audit-of-record",
        statement="Every load-bearing decision writes to an append-only record.",
        enforcement="Styx chain hash + per-kind JSONL append in titans/mnemosyne/",
    ),
    Invariant(
        id="S2", name="Argos — deterministic substrate",
        statement="No Argos Eye uses randomness in its scan logic.",
        enforcement="Eye.seed must be set; identical seed → identical pheromones",
    ),
    Invariant(
        id="S3", name="HYDRA — read-only observation",
        statement="HYDRA Heads never mutate state.",
        enforcement="Head.observe() returns findings; no writes from this module",
    ),
    Invariant(
        id="S4", name="Argos — decentralization",
        statement="No Eye imports another Eye. No host calls anything.",
        enforcement="Static analysis: imports under monsters/argos/eyes/ may only "
                    "reach monsters/argos/base and stdlib",
    ),
    Invariant(
        id="S5", name="Apollo — falsifiability",
        statement="Every Apollo prediction is a predicate that can be checked.",
        enforcement="Apollo predicates carry a `verify()` callable returning bool",
    ),
    Invariant(
        id="S6", name="Delphi — strategic-decision discipline",
        statement="MEDIUM and HIGH-risk decisions are recorded in oracles/delphi/.",
        enforcement="Pre-ship gate verifies a Delphi exists for any HIGH ship",
    ),
    Invariant(
        id="S7", name="Bounded autonomy",
        statement="LOW autonomous, MEDIUM proposal, HIGH requires Zeus authorization.",
        enforcement="Zeus.can_perform(risk_class) reads Styx oaths for HIGH/COMPOSITE",
    ),
    Invariant(
        id="S8", name="Anti-coercion vocation",
        statement="Olympus refuses changes that strengthen surveillance / centralization / "
                  "unbounded retention. Changes that weaken operator leverage are accepted.",
        enforcement="Constitutional — checked at proposal time by Hephaestus + Momus debate",
    ),
)


class Themis:
    """Custodian of the substrate constitution."""

    def all(self) -> tuple[Invariant, ...]:
        return SUBSTRATE_INVARIANTS

    def by_id(self, sid: str) -> Invariant | None:
        for inv in SUBSTRATE_INVARIANTS:
            if inv.id == sid:
                return inv
        return None

    def cosmogony_path(self) -> pathlib.Path:
        return root.child("codex", "COSMOGONY.md")

    def cosmogony_mentions(self, invariant_id: str) -> bool:
        """True iff the constitutional document mentions this invariant id."""
        path = self.cosmogony_path()
        if not path.exists():
            return False
        text = path.read_text(encoding="utf-8")
        return bool(re.search(rf"\b{re.escape(invariant_id)}\b", text))


themis = Themis()
