"""olympus.runtime.agents — the agent layer.

Per Delphi 2026-05-18-oikoumene-arc.md. This is the module that
answers Zeus's question *"how do actual LLM agents inhabit this
substrate?"*

The answer: **by becoming a named figure.** Every LLM call is made
*as* some Greek role — *as-Hephaestus*, *as-Momus*, *as-Cassandra*,
*as-Athena*, or *as-figure-proposer*. The role determines the system
prompt (the figure's docstring + the constitution + the AP catalog
where relevant), the user prompt (the specific context for this
call), the output schema (what shape the response must take), and
the destination (where the parsed output feeds back into the
substrate's pipeline).

Crucially: the substrate enforces **the same constitution** on agent
outputs as on internal-heuristic outputs. An agent's "proposal" is a
Hephaestus proposal; it goes through Momus → Delphi → Zeus. An
agent's "contest" is an additional AP-id list; it augments but does
not replace the heuristic Momus. The model thinks in the mythology;
the substrate enforces the constitution.
"""
from __future__ import annotations

import json
import re
from dataclasses import dataclass, field, asdict
from typing import Any, Callable

from olympus.primordials.gaia import root
from olympus.primordials.nyx import Nyx
from olympus.titans.mnemosyne import mnemosyne


# ─────────────────────────────────────────────────────────
# Shared bits — the constitution every agent sees in its prompt
# ─────────────────────────────────────────────────────────


CONSTITUTION_PRIMER = """\
You operate inside Olympus, a cognitive substrate built in the shape
of Greek mythology. Your role is a single named figure. You think in
the mythology and the constitution; you do not act outside them.

The eight substrate invariants — these always hold:
  S1 Mnemosyne — every load-bearing decision writes to an append-only record.
  S2 Argos — no randomness in observation.
  S3 HYDRA — read-only observation; watchers never mutate.
  S4 Argos — eyes are decentralized; no eye imports another.
  S5 Apollo — predictions carry a verify() callable.
  S6 Delphi — MEDIUM/HIGH-risk strategic decisions get a written debate.
  S7 Bounded autonomy — LOW is autonomous; MEDIUM proposes; HIGH/COMPOSITE
     require Zeus authorization sworn on Styx.
  S8 Continuity of Understanding — every action reconstructible from
     substrate records alone.

The eight anti-patterns Momus contests (AP1-AP8):
  AP1 self-observation without ground-touch
  AP2 scope creep via bundle
  AP3 instance-level rule for class-level drift
  AP4 premature constitutional elevation
  AP5 decline-and-surface violation
  AP6 understanding-obscuring
  AP7 ledger-balance without honesty
  AP8 decorative work claiming structural value

Your output will be parsed by the substrate. Follow the output schema
exactly. If you cannot honor the schema, return a structured error
explaining why; do not invent fields.
"""


# ─────────────────────────────────────────────────────────
# Agent role
# ─────────────────────────────────────────────────────────


@dataclass
class AgentResult:
    """Generic structured result of an agent call. Specific roles
    may attach extra fields via `extra`."""
    role: str
    bridge: str
    raw_text: str
    parsed: dict[str, Any] = field(default_factory=dict)
    error: str = ""
    confidence: float = 0.0
    elapsed_ms: float = 0.0
    completed_at: str = ""

    def __post_init__(self) -> None:
        if not self.completed_at:
            self.completed_at = Nyx.now().isoformat()


@dataclass
class AgentRole:
    """One canonical role an LLM can inhabit."""
    name: str                     # 'hephaestus' / 'momus' / ...
    figure: str                   # the Greek figure this maps to
    description: str              # one-line role description
    system_template: str          # the figure-specific system prompt template
    parse: Callable[[str], dict[str, Any]]  # response → structured dict

    def render_system(self, *,
                       constitution: str = CONSTITUTION_PRIMER) -> str:
        """Compose the full system prompt."""
        return self.system_template.format(constitution=constitution).strip()


# ─────────────────────────────────────────────────────────
# Parsers — each role's expected JSON shape
# ─────────────────────────────────────────────────────────


def _json_block(text: str) -> dict[str, Any]:
    """Extract the first JSON object from a response. Tolerant of
    Markdown code fences and leading prose."""
    if not text:
        return {}
    # Strip Markdown code fences
    fence_match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```",
                              text, re.DOTALL)
    if fence_match:
        candidate = fence_match.group(1)
    else:
        # Find the first { ... last } span
        start = text.find("{")
        end = text.rfind("}")
        if start < 0 or end <= start:
            return {}
        candidate = text[start:end + 1]
    try:
        result = json.loads(candidate)
        if isinstance(result, dict):
            return result
        return {"_parse_error": "JSON was not an object",
                "_raw": candidate[:200]}
    except json.JSONDecodeError as exc:
        return {"_parse_error": str(exc), "_raw": candidate[:200]}


def parse_hephaestus(text: str) -> dict[str, Any]:
    d = _json_block(text)
    if not d:
        return {"_empty": True}
    # Expected fields: summary, drift_observed, proposed_fix,
    # rationale, risk_class, confidence
    return {
        "summary":         str(d.get("summary", ""))[:200],
        "drift_observed":  str(d.get("drift_observed", ""))[:400],
        "proposed_fix":    str(d.get("proposed_fix", ""))[:400],
        "rationale":       str(d.get("rationale", ""))[:400],
        "risk_class":      str(d.get("risk_class", "LOW")).upper(),
        "confidence":      float(d.get("confidence", 0.5)),
    }


def parse_momus(text: str) -> dict[str, Any]:
    d = _json_block(text)
    return {
        "ap_ids":      [str(x).upper() for x in d.get("ap_ids", [])],
        "reasoning":   str(d.get("reasoning", ""))[:600],
        "confidence":  float(d.get("confidence", 0.5)),
    }


def parse_cassandra(text: str) -> dict[str, Any]:
    d = _json_block(text)
    return {
        "vindicated_slices": [str(s) for s in d.get("vindicated_slices", [])],
        "still_safe_to_dismiss": [str(s) for s in
                                   d.get("still_safe_to_dismiss", [])],
        "reasoning": str(d.get("reasoning", ""))[:600],
        "confidence": float(d.get("confidence", 0.5)),
    }


def parse_athena(text: str) -> dict[str, Any]:
    d = _json_block(text)
    return {
        "insights":   [str(s) for s in d.get("insights", [])][:10],
        "themes":     [str(s) for s in d.get("themes", [])][:5],
        "reasoning":  str(d.get("reasoning", ""))[:600],
        "confidence": float(d.get("confidence", 0.5)),
    }


def parse_figure_proposer(text: str) -> dict[str, Any]:
    d = _json_block(text)
    return {
        "figure_name":           str(d.get("figure_name", "")),
        "tier":                  str(d.get("tier", "heroes")).lower(),
        "mythological_grounding": str(d.get("mythological_grounding", ""))[:400],
        "cognitive_role":        str(d.get("cognitive_role", ""))[:400],
        "ap_self_check":         str(d.get("ap_self_check", ""))[:400],
        "skeleton":              str(d.get("skeleton", ""))[:2000],
        "confidence":            float(d.get("confidence", 0.5)),
    }


# ─────────────────────────────────────────────────────────
# Role registry — the five canonical agent shapes
# ─────────────────────────────────────────────────────────


_SYSTEM_HEPHAESTUS = """\
You are Hephaestus, the smith — the Architect of Olympus. You read
the substrate's recent state (briefs, alerts, rejection memory) and
surface drift: where is the substrate slipping from its own constitution?

{constitution}

Output a JSON object with these exact fields:
  summary         (one-line proposal name; ≤200 chars)
  drift_observed  (where the drift is — mention a slice/file/path/module name; ≤400 chars)
  proposed_fix    (concrete change; describe the action; ≤400 chars)
  rationale       (why this matters; ≤400 chars)
  risk_class      (one of LOW / MEDIUM / HIGH / COMPOSITE)
  confidence      (0.0..1.0; how strongly you stand behind this)

Do not propose anything that would violate S1-S8. Mention slice/file/
module by name (the substrate enforces AP1 ground-touch via heuristic).
"""

_SYSTEM_MOMUS = """\
You are Momus, the banished anti-architect of Olympus. You contest
Hephaestus's proposals via the AP1-AP8 catalog. You cannot rule; you
can only critique. Banishment is the point.

{constitution}

Given a proposal (rendered below in the user prompt), return a JSON
object:
  ap_ids      (list of AP ids that fire, e.g. ["AP1", "AP8"]; empty if clean)
  reasoning   (per-AP justification, ≤600 chars total)
  confidence  (0.0..1.0)

If the proposal is clean, return an empty ap_ids list. Do not invent
APs; only the eight catalog entries are valid.
"""

_SYSTEM_CASSANDRA = """\
You are Cassandra, the prophetess of Troy, cursed never to be
believed. You review dismissed warnings: was the dismissal sound,
or has the substrate's later experience vindicated the original concern?

{constitution}

Given the list of dismissed warnings (rendered below), return a JSON object:
  vindicated_slices         (slices where evidence shows the dismissal was wrong)
  still_safe_to_dismiss     (slices where dismissal remains correct)
  reasoning                 (≤600 chars)
  confidence                (0.0..1.0)
"""

_SYSTEM_ATHENA = """\
You are Athena, goddess of wisdom and strategy. You synthesize the
substrate's findings into a brief that surfaces cross-session insight.

{constitution}

Given recent findings + history (rendered below), return a JSON object:
  insights    (list of one-sentence claims; up to 10)
  themes      (list of one-word theme tags; up to 5)
  reasoning   (≤600 chars)
  confidence  (0.0..1.0)
"""

_SYSTEM_FIGURE_PROPOSER = """\
You are Hephaestus, in figure-proposal mode. You propose a NEW Greek
figure to be added to Olympus — a figure that would close a real
substrate gap, NOT decorative completion. The proposal will be
contested by Momus (AP1-AP8) and require Zeus ratification.

{constitution}

Output a JSON object:
  figure_name              (the Greek name, lowercase)
  tier                     (primordials / titans / olympians / underworld / fates / furies / graces / muses / heroes / monsters)
  mythological_grounding   (why this figure exists in Greek myth — be specific; ≤400 chars)
  cognitive_role           (what load-bearing role they fill in Olympus; ≤400 chars)
  ap_self_check            (your honest AP1-AP8 audit of THIS proposal; ≤400 chars)
  skeleton                 (Python module skeleton — class + singleton + docstring;
                            this is suggestion, the operator decides whether to copy it; ≤2000 chars)
  confidence               (0.0..1.0)

Refuse: figures already present in the pantheon, decorative additions
(AP8), figures whose role overlaps an existing module without distinct value.
"""


ROLES: dict[str, AgentRole] = {
    "hephaestus": AgentRole(
        name="hephaestus", figure="Hephaestus",
        description="surface drift; produce a Hephaestus proposal",
        system_template=_SYSTEM_HEPHAESTUS,
        parse=parse_hephaestus,
    ),
    "momus": AgentRole(
        name="momus", figure="Momus",
        description="contest a proposal via AP1-AP8",
        system_template=_SYSTEM_MOMUS,
        parse=parse_momus,
    ),
    "cassandra": AgentRole(
        name="cassandra", figure="Cassandra",
        description="review dismissed warnings for vindication",
        system_template=_SYSTEM_CASSANDRA,
        parse=parse_cassandra,
    ),
    "athena": AgentRole(
        name="athena", figure="Athena",
        description="synthesize findings + history into a brief",
        system_template=_SYSTEM_ATHENA,
        parse=parse_athena,
    ),
    "figure_proposer": AgentRole(
        name="figure_proposer", figure="Hephaestus (figure-proposal mode)",
        description="propose a new Greek figure to extend the pantheon",
        system_template=_SYSTEM_FIGURE_PROPOSER,
        parse=parse_figure_proposer,
    ),
}


def role(name: str) -> AgentRole:
    """Return the registered AgentRole. Raises KeyError if unknown."""
    return ROLES[name.lower()]


def known_roles() -> list[str]:
    return sorted(ROLES.keys())


# ─────────────────────────────────────────────────────────
# Run — the main entry point
# ─────────────────────────────────────────────────────────


def run(role_name: str, user_prompt: str, *,
        max_tokens: int = 2048,
        check_pan: bool = True) -> AgentResult:
    """Invoke the named agent role with `user_prompt`. Returns the
    structured AgentResult.

    Pan is consulted first (just like ratification); if Pan is in
    panic, agent calls are refused. This keeps the LLM bridge under
    the same circuit breaker as everything else.
    """
    from olympus.runtime.llm_bridge import bridge

    # Pan check — agent calls are constitutional; they obey the breaker
    if check_pan:
        try:
            from olympus.olympians.pan import pan, PanicError
            try:
                pan.guard_ratification(action_id=f"agent:{role_name}")
            except PanicError as exc:
                return AgentResult(
                    role=role_name, bridge="(blocked)",
                    raw_text="",
                    error=f"Pan refused: {exc.detail}",
                )
        except ImportError:
            pass

    try:
        r = role(role_name)
    except KeyError:
        return AgentResult(
            role=role_name, bridge="(unknown)",
            raw_text="",
            error=f"unknown role {role_name!r}; "
                  f"known: {', '.join(known_roles())}",
        )

    system = r.render_system()
    b = bridge()

    # Per Delphi 2026-05-19-grounding-arc.md: every agent call gets a
    # role-specific grounding block prepended. The block contains real
    # Pantheon roster + recent Mnemosyne records so the LLM cites real
    # things instead of fabricating paths/identifiers.
    from olympus.runtime.grounding import (
        build_grounding_for_role, apply_grounding,
    )
    grounding_block = build_grounding_for_role(role_name)
    if grounding_block:
        grounded_user = (
            "GROUNDING (verified at call time — cite ONLY paths and "
            "record-ids present in this block; if you cite a path "
            "absent here, the substrate will verify it and downgrade "
            "your confidence on fabrication):\n\n"
            "```json\n" + grounding_block + "\n```\n\n"
            "---\n\nQUESTION:\n" + user_prompt
        )
    else:
        grounded_user = user_prompt

    response = b.call(system=system, user=grounded_user,
                       max_tokens=max_tokens, role=role_name)

    if response.error:
        return AgentResult(
            role=role_name, bridge=b.name,
            raw_text=response.text, error=response.error,
            elapsed_ms=response.elapsed_ms,
        )

    parsed = r.parse(response.text)
    # Verify cited paths; downgrade confidence on fabrication; record
    # the check to Mnemosyne under `agent.grounding_check`.
    parsed = apply_grounding(role=role_name,
                              response_text=response.text,
                              parsed=parsed)
    confidence = float(parsed.get("confidence", 0.0))
    result = AgentResult(
        role=role_name, bridge=b.name,
        raw_text=response.text, parsed=parsed,
        confidence=confidence,
        elapsed_ms=response.elapsed_ms,
    )

    mnemosyne.remember(
        kind="agent.invocation",
        actor=f"agent:{role_name}",
        summary=(f"{role_name} via {b.name}: "
                 f"confidence={confidence:.2f} "
                 f"({response.elapsed_ms:.0f}ms)"
                 + (f" parse={parsed.get('_parse_error', '')[:40]}"
                    if "_parse_error" in parsed else "")),
        role=role_name,
        bridge=b.name,
        confidence=confidence,
        parsed=parsed,
        elapsed_ms=response.elapsed_ms,
    )
    return result


# ─────────────────────────────────────────────────────────
# Recursion path — LLM-driven new-figure proposal
# ─────────────────────────────────────────────────────────


def propose_figure(*, directive: str | None = None,
                    write_proposal: bool = True) -> dict[str, Any]:
    """Ask the figure-proposer role to suggest a new Greek figure.
    The result becomes a HIGH-risk Hephaestus proposal file at
    state/hephaestus/proposals/figure-<id>.json. The substrate does
    NOT auto-create the Python file — the operator does, after the
    proposal passes the standard pipeline (Momus + Delphi + Zeus).
    """
    from olympus.heroes.plato import plato
    # Render a useful user prompt — give the LLM the current pantheon
    # so it doesn't propose duplicates
    classified = sorted(plato.classified_figures())
    pantheon_text = ", ".join(classified[:60])
    user_prompt = (
        (directive or "Propose a Greek figure that fills a real "
                       "substrate gap.")
        + "\n\nCurrent pantheon (first 60 figures): " + pantheon_text
        + "\n\nRespond with the JSON object the schema requires."
    )

    result = run("figure_proposer", user_prompt, max_tokens=3000)
    if result.error:
        return {"ok": False, "error": result.error, "result": asdict(result)}

    proposal = result.parsed
    figure_name = proposal.get("figure_name", "")
    if not figure_name:
        return {"ok": False,
                "error": "agent did not return a figure_name",
                "result": asdict(result)}

    # Refuse duplicates
    if figure_name.lower() in {f.lower() for f in classified}:
        return {"ok": False,
                "error": (f"figure {figure_name!r} already present in "
                          f"pantheon"),
                "result": asdict(result)}

    pid = f"figure-{Nyx.now().strftime('%Y%m%dT%H%M%SZ')}-{figure_name.lower()}"
    record = {
        "id": pid,
        "drift_observed": (f"agent proposes new figure "
                            f"{figure_name!r} in tier "
                            f"{proposal.get('tier', '?')!r}: "
                            f"{proposal.get('cognitive_role', '')[:200]}"),
        "summary": (f"propose new figure {figure_name!r} "
                    f"({proposal.get('tier', '?')})"),
        "proposed_fix": (f"create src/olympus/{proposal.get('tier', '?')}/"
                          f"{figure_name.lower()}.py with the agent's "
                          f"skeleton (operator review required)"),
        "rationale": proposal.get("mythological_grounding", ""),
        "risk_class": "HIGH",
        "raised_by": f"agent:figure_proposer (via {result.bridge})",
        "raised_at": Nyx.now().isoformat(),
        "agent_confidence": result.confidence,
        "ap_self_check": proposal.get("ap_self_check", ""),
        "suggested_skeleton": proposal.get("skeleton", ""),
        "requires_delphi": True,
    }

    proposal_path = ""
    if write_proposal:
        proposals_dir = root.child("state", "hephaestus", "proposals")
        proposals_dir.mkdir(parents=True, exist_ok=True)
        target = proposals_dir / f"{pid}.json"
        target.write_text(json.dumps(record, indent=2), encoding="utf-8")
        proposal_path = str(target)

    mnemosyne.remember(
        kind="agent.figure-proposal",
        actor="agent:figure_proposer",
        summary=(f"agent proposed new figure {figure_name!r} "
                 f"(risk_class=HIGH, requires Delphi + Zeus)"),
        figure_name=figure_name,
        tier=proposal.get("tier", ""),
        proposal_id=pid,
        proposal_path=proposal_path,
        confidence=result.confidence,
        bridge=result.bridge,
    )
    return {"ok": True, "proposal_id": pid,
            "proposal_path": proposal_path,
            "figure_name": figure_name,
            "tier": proposal.get("tier", ""),
            "confidence": result.confidence,
            "result": asdict(result)}


# ─────────────────────────────────────────────────────────
# Calibration — agent confidence vs realized outcome
# ─────────────────────────────────────────────────────────


def calibration(role_name: str | None = None) -> dict[str, Any]:
    """Per-role calibration scoring. Returns:
      total_invocations    — how many times this role was called
      avg_confidence       — mean confidence
      parse_failure_rate   — fraction with `_parse_error`
      error_rate           — fraction where the agent itself errored

    More sophisticated calibration (confidence-vs-actual-outcome)
    requires linking agent results to downstream substrate outcomes
    and is left for future arcs — this is the bare-bones baseline."""
    invocations = mnemosyne.recall("agent.invocation")
    if role_name:
        invocations = [m for m in invocations
                        if (m.body or {}).get("role") == role_name.lower()]
    if not invocations:
        return {
            "role": role_name or "all",
            "total_invocations": 0,
            "avg_confidence": 0.0,
            "parse_failure_rate": 0.0,
            "error_rate": 0.0,
        }
    confidences: list[float] = []
    parse_failures = 0
    errors = 0
    for m in invocations:
        body = m.body or {}
        confidences.append(float(body.get("confidence", 0.0)))
        parsed = body.get("parsed") or {}
        if isinstance(parsed, dict) and "_parse_error" in parsed:
            parse_failures += 1
        # If the agent.invocation summary contains "ERROR", count it
        if "ERROR" in (m.summary or ""):
            errors += 1
    n = len(invocations)
    return {
        "role": role_name or "all",
        "total_invocations": n,
        "avg_confidence": (sum(confidences) / n) if confidences else 0.0,
        "parse_failure_rate": parse_failures / n,
        "error_rate": errors / n,
    }
