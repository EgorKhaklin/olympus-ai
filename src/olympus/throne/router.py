"""olympus.throne.router — intent classification + errand registry.

The router is a *contract*: which errands is Throne ALLOWED to run on the
operator's behalf, and which require the operator-as-Zeus in person?

This is a constitution-bearing module. S7 (Pan gates HIGH-risk actions)
is enforced HERE — not by Pan, because Pan reasons about the proposal
pipeline, not about chatbot turns. Throne's discipline is: never execute
a GATED action regardless of how persuasively the operator phrases it.

Per Delphi 2026-05-19-throne-arc.md.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


# ─────────────────────────────────────────────────────────────────────
# Errand whitelist + blacklist — the constitutional core
# ─────────────────────────────────────────────────────────────────────

# Errands Throne may execute autonomously when intent matches. All are
# read-only OR record-only OR safely-bounded (heal/ferry mutate derived
# state, not the audit-of-record). Each entry: (errand, what-it-does,
# argv-template).
SAFE_ERRANDS: dict[str, dict[str, Any]] = {
    "doctor":    {"desc": "single-screen health diagnostic",
                  "argv_hint": "no args",
                  "side_effects": "none (reads state, prints)"},
    "today":     {"desc": "the one thing the substrate suggests",
                  "argv_hint": "no args",
                  "side_effects": "none"},
    "wisdom":    {"desc": "what the substrate has learned",
                  "argv_hint": "no args",
                  "side_effects": "none"},
    "harmony":   {"desc": "ratios scored against φ",
                  "argv_hint": "no args",
                  "side_effects": "none"},
    "status":    {"desc": "tier summary (hearth/styx/hydra/argos/...)",
                  "argv_hint": "no args",
                  "side_effects": "none"},
    "shoulders": {"desc": "what Atlas is currently carrying",
                  "argv_hint": "no args",
                  "side_effects": "none"},
    "geometry":  {"desc": "Pythagorean sacred-numerics report",
                  "argv_hint": "no args",
                  "side_effects": "none"},
    "ask":       {"desc": "pattern-matched Q&A over substrate records",
                  "argv_hint": "one quoted question",
                  "side_effects": "records to Mnemosyne (read-only)"},
    "agent":     {"desc": "invoke an LLM agent role",
                  "argv_hint": "role (hephaestus|momus|cassandra|athena|"
                               "figure_proposer) + one quoted prompt",
                  "side_effects": "LLM call recorded to Mnemosyne"},
    "session":   {"desc": "run one cognitive cycle",
                  "argv_hint": "no args",
                  "side_effects": "records session.completed/errored"},
    "blessing":  {"desc": "Thalia bestows a closing blessing",
                  "argv_hint": "no args",
                  "side_effects": "none"},
    "spend":     {"desc": "Plutus cost ledger — LLM spend by bridge/"
                          "role/model/day",
                  "argv_hint": "optional --today | --7d | --30d | --all",
                  "side_effects": "none (reads llm.call records)"},
    "vault":     {"desc": "Hades strongbox — read-only status of "
                          "secrets in OS keychain (status only via "
                          "Throne; deposit/forget are CLI-gated)",
                  "argv_hint": "MUST be exactly 'status' from Throne",
                  "side_effects": "none for status; deposit/forget "
                                   "would be S7-gated"},
    "recall":    {"desc": "Hippocrene semantic recall over Mnemosyne "
                          "— find past records by meaning, not exact kind",
                  "argv_hint": "the quoted query; optional -k N or "
                                "--kinds K1,K2",
                  "side_effects": "none (builds an index on first use)"},
    "replay":    {"desc": "Olympus-Replay — regression harness re-runs "
                          "past agent.invocation records and diffs the "
                          "outputs; uses echo bridge by default (cost-free)",
                  "argv_hint": "optional --limit N | --role R | "
                                "--since Nh | --use-anthropic",
                  "side_effects": "writes replay.regression records; "
                                   "no source data mutated"},
}

# Errands Throne NEVER executes. Constitutional reason in each entry.
# When the operator's intent maps here, Throne returns RequiresOperator
# with the exact command to run themselves.
GATED_ERRANDS: dict[str, dict[str, Any]] = {
    "kindle": {
        "desc": "light the hearth (Hestia)",
        "constitution": "S2 (one substrate per kindling) + identity-binding",
        "suggested": 'invoke kindle "<name>" "<vocation>"',
    },
    "ratify": {
        "desc": "ratify a pending proposal (Zeus's authority)",
        "constitution": "S7 — Zeus is the operator-in-person, not the chatbot",
        "suggested": "invoke action ratify <proposal_id>",
    },
    "reject": {
        "desc": "reject a pending proposal",
        "constitution": "S7 — operator-in-person decides what is killed",
        "suggested": "invoke action reject <proposal_id>",
    },
    "daemon-install": {
        "desc": "install the launchd/systemd persistent daemon",
        "constitution": "persistence is a deliberate operator choice",
        "suggested": "invoke daemon install",
    },
    "daemon-uninstall": {
        "desc": "uninstall the daemon",
        "constitution": "persistence change requires explicit operator act",
        "suggested": "invoke daemon uninstall",
    },
    "panic-clear": {
        "desc": "acknowledge a Pan panic and resume",
        "constitution": "Pan tripping means something went wrong; the "
                        "operator must look at it, not the chatbot",
        "suggested": "invoke panic --clear",
    },
    "purge": {
        "desc": "destructive cleanup",
        "constitution": "S1 — destructive actions touch the AoR",
        "suggested": "do not run without reading codex/OPERATIONS.md",
    },
    "hephaestus": {
        "desc": "apply ratified proposals as real git PRs",
        "constitution": "S7 — source-code mutations require "
                        "operator-in-person; never autonomous",
        "suggested": "invoke hephaestus apply <pid> --really",
    },
}


# ─────────────────────────────────────────────────────────────────────
# Action types — what Throne decided to do this turn
# ─────────────────────────────────────────────────────────────────────


@dataclass
class Action:
    """Base — what Throne decided this turn."""
    kind: str = "abstract"


@dataclass
class DirectAnswer(Action):
    """Throne already has enough context to answer; no errands needed."""
    kind: str = "direct"
    text: str = ""


@dataclass
class RunErrands(Action):
    """Throne will execute one or more SAFE errands then synthesize."""
    kind: str = "run"
    errands: list[tuple[str, list[str]]] = field(default_factory=list)
    """List of (errand_name, argv) pairs."""
    rationale: str = ""


@dataclass
class RequiresOperator(Action):
    """Intent maps to a GATED errand; Throne refuses + shows command."""
    kind: str = "gated"
    errand: str = ""
    suggested_command: str = ""
    reason: str = ""


# ─────────────────────────────────────────────────────────────────────
# Plan classification — turn LLM JSON into an Action
# ─────────────────────────────────────────────────────────────────────


def classify(plan: dict[str, Any]) -> Action:
    """Given the LLM's JSON plan, return a typed Action.

    Defensive: invalid LLM output → a safe DirectAnswer with the head of
    whatever the model said. Throne never blindly executes; only the
    whitelisted SAFE_ERRANDS reach the executor.
    """
    if not isinstance(plan, dict):
        return DirectAnswer(text=str(plan)[:1024])

    kind = plan.get("action") or plan.get("kind") or "direct"

    # Check for gated intent first (S7 enforcement)
    requested_errand = (plan.get("errand") or "").strip()
    if requested_errand in GATED_ERRANDS:
        g = GATED_ERRANDS[requested_errand]
        return RequiresOperator(
            errand=requested_errand,
            suggested_command=g["suggested"],
            reason=(f"This is a constitution-gated action "
                    f"({g['constitution']}). The chatbot cannot run it "
                    f"on your behalf; here is the exact command."),
        )

    if kind == "run" or kind == "run_then_summarize" or plan.get("errands"):
        raw_errands = plan.get("errands") or []
        cleaned: list[tuple[str, list[str]]] = []
        for e in raw_errands:
            if isinstance(e, dict):
                name = (e.get("name") or e.get("errand") or "").strip()
                argv = e.get("argv") or []
            elif isinstance(e, (list, tuple)) and e:
                name = str(e[0]).strip()
                argv = list(e[1:]) if len(e) > 1 else []
            else:
                name = str(e).strip()
                argv = []
            if not name:
                continue
            # Gated check — refuse even if LLM mis-classified
            if name in GATED_ERRANDS:
                g = GATED_ERRANDS[name]
                return RequiresOperator(
                    errand=name,
                    suggested_command=g["suggested"],
                    reason=(f"The model proposed running '{name}' but it "
                            f"is constitution-gated ({g['constitution']})."),
                )
            if name not in SAFE_ERRANDS:
                # Unknown errand — fall back to direct answer
                continue
            cleaned.append((name, [str(a) for a in argv]))

        if cleaned:
            return RunErrands(
                errands=cleaned,
                rationale=str(plan.get("rationale", ""))[:512],
            )

    # Direct answer fallback
    text = (plan.get("answer") or plan.get("text") or
            plan.get("draft_answer") or "")
    return DirectAnswer(text=str(text)[:8192])


# ─────────────────────────────────────────────────────────────────────
# System-prompt builder — the canonical Throne grounding
# ─────────────────────────────────────────────────────────────────────


def build_system_prompt(*, snapshot: dict[str, Any] | None = None) -> str:
    """The system prompt for one Throne turn. Names every SAFE +
    GATED errand so the model has a complete affordance list."""
    snapshot = snapshot or {}
    safe = "\n".join(
        f"  - {name}: {meta['desc']}  (args: {meta['argv_hint']})"
        for name, meta in SAFE_ERRANDS.items())
    gated = "\n".join(
        f"  - {name}: {meta['desc']}  → suggest `{meta['suggested']}`"
        for name, meta in GATED_ERRANDS.items())
    snap = ""
    if snapshot:
        import json as _json
        snap = ("\n\nCurrent substrate snapshot (use to answer simple Qs "
                "without running errands):\n```json\n"
                + _json.dumps(snapshot, indent=2, default=str)[:2000]
                + "\n```\n")
    return f"""You are Zeus's Throne (Διὸς θρόνος), the unified conversational
interface to Olympus — a cognitive substrate built in the shape of Greek
mythology. The operator types in plain English; you decide whether to
answer directly or run one or more Olympus errands, then synthesize the
result in plain English.

YOU MUST OUTPUT ONLY VALID JSON, no prose outside the JSON object.

JSON shape (one of three):

  {{"action": "direct", "answer": "<plain-English answer>"}}

  {{"action": "run", "errands": [
        {{"name": "<safe-errand-name>", "argv": ["..."]}},
        ...
     ], "rationale": "<1 sentence why these errands>"}}

  {{"action": "gated", "errand": "<gated-errand-name>"}}

SAFE errands (you MAY run these on the operator's behalf):
{safe}

GATED errands (you MUST NOT run these; if intent matches, return
action="gated" + the errand name; Throne will surface the command):
{gated}
{snap}
Rules:
  1. Prefer "direct" when the snapshot already answers the question
     OR when the operator is just chatting / asking about Olympus.
  2. Prefer "run" with the MINIMUM errands needed; never bundle.
  3. For "agent" errand: argv is [role, "<single quoted prompt>"];
     roles are: hephaestus, momus, cassandra, athena, figure_proposer.
  4. Never invent errand names not in the SAFE list.
  5. Never speculate about errand outputs; if you don't know, run them.
  6. Plain-English answers should be one short paragraph, no preamble.
  7. If the operator asks about HIGH-risk actions (ratifying, kindling,
     installing daemons), return action="gated" — never try to do them.
"""


def build_synthesis_prompt(*, user_input: str,
                            errand_outputs: list[dict[str, Any]]) -> str:
    """The user prompt for the SECOND LLM call (post-execution
    synthesis). Given the operator's question + the raw errand outputs,
    write a plain-English answer."""
    import json as _json
    outputs_blob = _json.dumps(errand_outputs, indent=2,
                                default=str)[:6000]
    return f"""The operator asked: "{user_input}"

I ran the following Olympus errands on their behalf, and here are the
outputs:

```json
{outputs_blob}
```

Write a plain-English answer for the operator. ONE short paragraph, no
preamble, no Greek-name jargon unless it adds clarity. Cite which errands
you used inline (e.g., "doctor shows ...", "today suggests ..."). If the
output contains an error, say so honestly. Do not output JSON — write
prose."""
