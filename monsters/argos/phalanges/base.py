"""Argos phalanxs — Roman cohort organization for Phase E6.

A **Phalanx** is the unit of swarm organization. Each Phalanx has:

  - A **Legatus** (general), conceptually one of HYDRA's 7 watcher
    domains: schema, cognitive, security, mission, adversary,
    performance, trajectory.
  - A **cohort of ants** (1+ phalanxnaires) under its banner.
  - A **default tactic** declaring how the cohort deploys.

The colony runner iterates `ALL_PHALANGES`, deploys each via its tactic,
and deposits findings to the Pheromone log. The deposit's
`deposited_by` field is still the *ant* name (AoR preservation);
the phalanx identity travels in the evidence JSONB.

Contract ((legacy arc) G10 + G11):

  - **G10** — every ant belongs to exactly one Phalanx. No orphans,
    no double-counting.
  - **G11** — ants do NOT import from `monsters.argos.phalanges`. The
    knowledge flow is one-way: Phalanx knows its ants; ants do not
    know their Phalanx. This is the reverse-direction of G6 and is
    necessary so a Phalanx-level refactor never touches ant code.

Authorized by `delphi/2026-05-13-arc-e-phalanx-structure-with-tactics.md`.

The five tactics correspond to genuine Roman military doctrines.
Their software meanings are documented in each `_deploy_*` function.
"""

from __future__ import annotations

import dataclasses
import enum
import pathlib
from typing import Callable, ClassVar

from monsters.argos.base import Eye, EyeFinding


class Tactic(enum.Enum):
    """The five tactical doctrines a Legatus may choose."""
    TESTUDO       = "testudo"        # all ants run; output aggregated
    TRIPLEX_ACIES = "triplex_acies"  # tiered escalation
    CUNEUS        = "cuneus"         # lead + followers cascade
    VEXILLATIO    = "vexillatio"     # operator-directed focused detachment
    AUXILIA       = "auxilia"        # cross-phalanx ally borrowing


@dataclasses.dataclass
class TacticConfig:
    """Per-phalanx tactic parameterization. Most fields are None
    unless the phalanx has chosen a tactic that requires them."""
    tactic: Tactic

    # For TRIPLEX_ACIES: ordered list of tiers; each tier is a list
    # of Eye classes from this phalanx's cohort. Empty tiers are
    # allowed (phalanx may grow them later).
    tiers: list[list[type[Ant]]] | None = None

    # For CUNEUS: the lead ant. Must be a member of this phalanx's ANTS.
    lead: type[Eye] | None = None

    # For VEXILLATIO: a predicate (EyeFinding) → bool that selects
    # which findings the cohort emits. Defaults to "all" if None.
    focus_predicate: Callable[[EyeFinding], bool] | None = None

    # For AUXILIA: names of other phalanxs whose ants may be borrowed.
    auxilia_pool: list[str] | None = None

    def validate(self, cohort: list[type[Ant]]) -> None:
        """Raise ValueError if the config is inconsistent with the cohort."""
        if self.tactic == Tactic.TRIPLEX_ACIES:
            if not self.tiers or len(self.tiers) < 2:
                raise ValueError(
                    f"TRIPLEX_ACIES requires >=2 tiers; got {self.tiers!r}"
                )
            flat = [a for tier in self.tiers for a in tier]
            if set(flat) != set(cohort):
                raise ValueError(
                    "TRIPLEX_ACIES tiers must partition the cohort"
                )
        if self.tactic == Tactic.CUNEUS:
            if self.lead is None or self.lead not in cohort:
                raise ValueError(
                    "CUNEUS requires a lead ant that is in the cohort"
                )


class Phalanx:
    """Base class for all Phalanges under monsters.argos/phalanxs/.

    Subclasses MUST declare:
      - NAME       — module name (e.g., "phalanx_schema")
      - DOMAIN     — HYDRA watcher domain (e.g., "schema")
      - LEGATUS    — display name (e.g., "Legatus Schema")
      - ANTS       — list of Eye subclasses commanded
      - TACTIC     — TacticConfig declaring default doctrine

    Subclasses MUST NOT:
      - Override `deploy()` unless adding new tactics (extend Tactic enum first)
      - Import any other Phalanx module (per G11-adjacent: phalanxs are siblings)
      - Call any LLM API (G8 extends to phalanxs)
    """

    NAME:    ClassVar[str] = "phalanx_base"
    DOMAIN:  ClassVar[str] = "(none)"
    LEGATUS: ClassVar[str] = "(unnamed)"
    ANTS:    ClassVar[list[type[Ant]]] = []
    TACTIC:  ClassVar[TacticConfig] = TacticConfig(tactic=Tactic.TESTUDO)

    def __init__(self, root: pathlib.Path):
        self.root = root
        # Validate the phalanx's tactic against its cohort at construction
        # time. Catches misconfiguration before the colony runs.
        self.TACTIC.validate(self.ANTS)

    def deploy(self, **kwargs) -> list[tuple[type[Eye], list[EyeFinding]]]:
        """Dispatch to the tactic-specific deployer. Returns list of
        (EyeClass, findings) tuples so the colony runner preserves
        deposited_by = ant.NAME for AoR."""
        return _DISPATCHERS[self.TACTIC.tactic](self, **kwargs)


# --------------------------------------------------------------------------
# Tactic implementations. Each takes a Phalanx instance and returns a list
# of (EyeClass, list-of-findings) pairs. The colony runner serializes
# the findings into Pheromone rows.
# --------------------------------------------------------------------------

def _deploy_testudo(phalanx: Phalanx, **_kwargs) -> list[tuple[type[Eye], list[EyeFinding]]]:
    """TESTUDO — every ant in the cohort scans. Output is the union
    of all findings, returned per-ant so each ant's deposit retains
    its own deposited_by name.

    Roman context: every shield raised, cohort moves as one. The
    formation is maximally defensive — no domain blind spots — but
    also maximally communicative: every ant always speaks. Use when
    coverage matters more than economy.
    """
    return [(AntCls, AntCls(phalanx.root).scan()) for AntCls in phalanx.ANTS]


def _deploy_triplex_acies(phalanx: Phalanx, **_kwargs) -> list[tuple[type[Eye], list[EyeFinding]]]:
    """TRIPLEX ACIES — three battle lines deployed in sequence.

    Tier 1 (hastati) ants run first. If any fire, Tier 2 (principes)
    is deployed against the same surface. If any of those fire, Tier 3
    (triarii) is deployed. Stops at the first silent tier.

    Roman context: hastati are young aggressive front-line; principes
    are veterans; triarii are elite reserves committed only at crisis.
    In software: cheap-fast checks first, escalating to expensive
    deep checks only when warranted. Use when checks form a natural
    cost gradient.
    """
    if not phalanx.TACTIC.tiers:
        return []
    results: list[tuple[type[Eye], list[EyeFinding]]] = []
    for tier in phalanx.TACTIC.tiers:
        tier_any_fired = False
        for AntCls in tier:
            findings = AntCls(phalanx.root).scan()
            results.append((AntCls, findings))
            if findings:
                tier_any_fired = True
        if not tier_any_fired:
            break  # silent tier; no escalation
    return results


def _deploy_cuneus(phalanx: Phalanx, **_kwargs) -> list[tuple[type[Eye], list[EyeFinding]]]:
    """CUNEUS — wedge formation: the lead pierces; followers exploit.

    The designated lead ant scans first. If it is silent, the
    cohort does not deploy further (the gap was not found). If
    the lead fires, every other ant in the cohort scans.

    Roman context: a veteran centurion at the point of the wedge
    drives into the enemy line; the rest of the formation pours
    through the breach. In software: one strong signal triggers
    a fuller investigation. Use when one ant reliably detects
    the presence of trouble and others detail it.
    """
    lead = phalanx.TACTIC.lead
    if lead is None:
        return _deploy_testudo(phalanx)
    lead_findings = lead(phalanx.root).scan()
    results: list[tuple[type[Eye], list[EyeFinding]]] = [(lead, lead_findings)]
    if not lead_findings:
        return results
    for AntCls in phalanx.ANTS:
        if AntCls is lead:
            continue
        results.append((AntCls, AntCls(phalanx.root).scan()))
    return results


def _deploy_vexillatio(phalanx: Phalanx, focus_predicate=None, **_kwargs) -> list[tuple[type[Eye], list[EyeFinding]]]:
    """VEXILLATIO — operator-directed detachment for a focused mission.

    All ants scan, but the cohort emits only findings matching the
    focus predicate (defaults to the phalanx's TACTIC.focus_predicate
    if the caller didn't supply one).

    Roman context: a Roman general could send a vexillatio (literally,
    a unit carrying a vexillum standard) on a focused mission outside
    the phalanx's usual scope. In software: operators invoke the
    phalanx with a narrow `--focus` argument; the cohort scans
    normally but emits only what matches. Use for deep-dive
    investigations without standing up a new colony pass.
    """
    pred = focus_predicate or phalanx.TACTIC.focus_predicate
    results: list[tuple[type[Eye], list[EyeFinding]]] = []
    for AntCls in phalanx.ANTS:
        findings = AntCls(phalanx.root).scan()
        if pred is not None:
            findings = [f for f in findings if pred(f)]
        results.append((AntCls, findings))
    return results


def _deploy_auxilia(phalanx: Phalanx, ally_phalanxs: list["Phalanx"] | None = None, **_kwargs) -> list[tuple[type[Eye], list[EyeFinding]]]:
    """AUXILIA — borrow phalanxnaires from allied phalanxs.

    Runs this phalanx's own cohort plus the ants of any supplied
    ally phalanxs. The borrowed ants still get credited via
    deposited_by = ant.NAME, but the evidence JSONB will record
    the host phalanx that called them (`host_legio`).

    Roman context: auxilia troops were allied soldiers who fought
    alongside phalanxs on specific campaigns. In software:
    cross-domain investigations where one phalanx needs another's
    expertise without permanent restructuring. Use sparingly —
    overuse re-centralizes the swarm.
    """
    results: list[tuple[type[Eye], list[EyeFinding]]] = []
    for AntCls in phalanx.ANTS:
        results.append((AntCls, AntCls(phalanx.root).scan()))
    if ally_phalanxs:
        allowed = set(phalanx.TACTIC.auxilia_pool or [])
        for ally in ally_phalanxs:
            if ally.NAME not in allowed:
                continue  # honor declared pool
            for AntCls in ally.ANTS:
                results.append((AntCls, AntCls(phalanx.root).scan()))
    return results


_DISPATCHERS: dict[Tactic, Callable[..., list[tuple[type[Eye], list[EyeFinding]]]]] = {
    Tactic.TESTUDO:       _deploy_testudo,
    Tactic.TRIPLEX_ACIES: _deploy_triplex_acies,
    Tactic.CUNEUS:        _deploy_cuneus,
    Tactic.VEXILLATIO:    _deploy_vexillatio,
    Tactic.AUXILIA:       _deploy_auxilia,
}
