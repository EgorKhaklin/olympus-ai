"""Momus — personification of mockery and criticism.

Momus was the god of unfair criticism, banished from Olympus for
finding fault with every other deity's work — he mocked Aphrodite's
sandals for squeaking. In Olympus he is the Anti-Architect: the
adversarial reviewer of Hephaestus's proposals. Where Hephaestus
proposes, Momus contests.

His banishment from Olympus is the point. He cannot rule; he can only
critique. His role is structural: every Hephaestus proposal goes
through Momus's eight anti-pattern catalog (AP1–AP8) before it can
be brought to Zeus.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Sequence


@dataclass(frozen=True)
class AntiPattern:
    id: str             # AP1..AP8
    name: str
    description: str
    refusal: str        # the form of refusal Momus issues


ANTI_PATTERNS: tuple[AntiPattern, ...] = (
    AntiPattern(
        "AP1", "self-observation without ground-touch",
        "A proposal that justifies itself only by what the system says about itself, "
        "with no observable consequence outside the cognitive layer.",
        "REJECT — name a measurable consequence outside Olympus first.",
    ),
    AntiPattern(
        "AP2", "scope creep via bundle",
        "A proposal that bundles a small fix with a large structural change, hoping "
        "the structural change rides through under the small fix's authorization.",
        "REJECT — split into two proposals; each routed on its own risk class.",
    ),
    AntiPattern(
        "AP3", "instance-level rule for class-level drift",
        "A proposal that adds a specific instance check (this file, this version) "
        "instead of a structural invariant.",
        "REJECT — promote to a class-shape invariant or accept the drift.",
    ),
    AntiPattern(
        "AP4", "premature constitutional elevation",
        "A proposal that wants to amend MISSION / COSMOGONY when a DOMAIN-side "
        "fix would suffice.",
        "REJECT — try the smaller change first.",
    ),
    AntiPattern(
        "AP5", "decline-and-surface violation",
        "A proposal that silently expands scope rather than declining + naming "
        "the trigger that would unfreeze the expansion.",
        "REJECT — explicitly decline; name the missing trigger.",
    ),
    AntiPattern(
        "AP6", "vocation-adjacent silent strengthening",
        "A proposal that subtly strengthens surveillance, centralization, or "
        "retention while claiming to do something else.",
        "REJECT — vocation S8 takes precedence; refuse on those grounds.",
    ),
    AntiPattern(
        "AP7", "ledger-balance without honesty",
        "A proposal that rebases past commitments to make current numbers look "
        "good — the books balance, the truth doesn't.",
        "REJECT — log the cost, do not balance the ledger by edit.",
    ),
    AntiPattern(
        "AP8", "decorative work claiming structural value",
        "A proposal that adds a watcher / eye / test that observes nothing "
        "load-bearing, just to appear comprehensive.",
        "REJECT — every new observer must name what would change if it spoke.",
    ),
)


class Momus:
    """The Anti-Architect. Critic-of-record."""

    def catalog(self) -> tuple[AntiPattern, ...]:
        return ANTI_PATTERNS

    def by_id(self, ap_id: str) -> AntiPattern | None:
        for ap in ANTI_PATTERNS:
            if ap.id == ap_id.upper():
                return ap
        return None

    def contest(self, proposal_summary: str, ap_ids: Sequence[str]) -> list[AntiPattern]:
        """Given a list of anti-pattern ids, return the catalog entries —
        used to render an adversarial review."""
        return [self.by_id(a) for a in ap_ids if self.by_id(a)]


momus = Momus()
