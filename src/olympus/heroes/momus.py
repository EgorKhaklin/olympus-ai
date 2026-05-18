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
        "AP6", "understanding-obscuring",
        "A proposal that makes the agent's decision-making harder to reconstruct "
        "from the substrate's own records: opaque heuristics with no logged "
        "rationale, external calls without recorded context, abstractions that "
        "hide reasoning paths, decisions taken without an authorizing oath.",
        "REJECT — S8 takes precedence; the operator must be able to ask "
        "'why did the agent do that?' and answer it from Mnemosyne + Styx alone.",
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

    # ─────────────────────────────────────────────────────────
    # Auto-contest: read a proposal in context of the brief and decide
    # which APs apply, by heuristic.
    # ─────────────────────────────────────────────────────────

    def contest_via_brief(self, proposal: object, brief: object) -> list[str]:
        """Returns a list of AP ids that fire for this proposal in the
        context of the brief. Heuristic rules — not exhaustive, but
        enough to give Momus a meaningful voice in the loop."""
        ap_ids: list[str] = []
        drift = (getattr(proposal, "drift_observed", "") or "").lower()
        fix = (getattr(proposal, "proposed_fix", "") or "").lower()
        risk = (getattr(proposal, "risk_class", "") or "").upper()
        rationale = (getattr(proposal, "rationale", "") or "").lower()

        findings = getattr(brief, "findings", [])
        recommendations = getattr(brief, "recommendations", [])
        confidence = getattr(brief, "confidence", 0.0)

        # AP1 — self-observation without ground-touch
        #   Fires when the proposal references no concrete artifact outside
        #   the cognitive layer (e.g., 'something feels off in the brief')
        if not any(token in drift for token in [
            "slice", "file", "path", "module", "code", "test", "log",
            ".py", ".md", "olympus/",
        ]):
            ap_ids.append("AP1")

        # AP2 — scope creep via bundle
        #   Fires when the fix sentence contains an 'and' joining two
        #   distinct verbs.
        verb_pairs = (
            ("rewrite", "refactor"), ("delete", "rename"), ("add", "remove"),
            ("amend", "ship"), ("migrate", "redesign"),
        )
        if any(a in fix and b in fix for a, b in verb_pairs):
            ap_ids.append("AP2")

        # AP3 — instance-level rule for class-level drift
        #   Fires when the fix names a specific file/version (vs. a pattern)
        if any(tok in fix for tok in [".py:", "line ", "this specific"]):
            ap_ids.append("AP3")

        # AP4 — premature constitutional elevation
        #   Fires when the fix touches COSMOGONY / S1-S8 and the brief
        #   doesn't already corroborate (≥2 sources on the same slice)
        if any(t in fix for t in ["cosmogony", "constitution", "s1", "s2",
                                   "s3", "s4", "s5", "s6", "s7", "s8"]):
            if confidence < 0.7:
                ap_ids.append("AP4")

        # AP5 — decline-and-surface violation
        #   Fires when a HIGH/COMPOSITE proposal is recommended for
        #   autonomous action.
        if risk in {"HIGH", "COMPOSITE"} and "auto" in fix:
            ap_ids.append("AP5")

        # AP6 — understanding-obscuring (the S8 contest)
        #   Fires when the proposal would reduce reconstructability
        if any(t in fix for t in ["remove logging", "drop the record",
                                   "skip mnemosyne", "bypass styx",
                                   "skip the journal"]):
            ap_ids.append("AP6")

        # AP7 — ledger-balance without honesty
        #   Fires when the fix mentions rebasing/squashing audit-of-record
        if any(t in fix for t in ["rebase", "squash chronicle", "edit the chronicle"]):
            ap_ids.append("AP7")

        # AP8 — decorative work claiming structural value
        #   Fires when the proposal adds an observer (eye/head) but
        #   the rationale doesn't name what would change if it spoke.
        if any(t in fix for t in ["add eye", "add head", "new observer"]):
            if "would change" not in rationale and "if" not in rationale:
                ap_ids.append("AP8")

        return ap_ids


momus = Momus()
