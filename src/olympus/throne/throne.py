"""olympus.throne.throne — the Throne core.

`Throne.respond(input)` is the one method that matters. Everything else
is testable surface: snapshot building, errand execution, Mnemosyne
recording. Per Delphi 2026-05-19-throne-arc.md.

Design notes:
  - At most TWO LLM calls per turn:
      1. routing call (LLM emits a plan as JSON)
      2. synthesis call (LLM writes plain-English answer from outputs)
    Direct-answer plans skip call #2.
  - SAFE errands are executed in-process by importing and running each
    errand's CLI handler. This guarantees identical behavior to
    `invoke <errand>` — no parallel implementation.
  - Each turn is recorded to Mnemosyne under `throne.turn`. The
    `llm.call` records from the bridge are the per-LLM-call detail.
"""
from __future__ import annotations

import io
import json
import re
import time
from dataclasses import dataclass, field, asdict
from typing import Any, Callable

from olympus.primordials.nyx import Nyx
from olympus.titans.mnemosyne import mnemosyne
from olympus.runtime.llm_bridge import bridge as _default_bridge, LLMBridge
from olympus.throne.router import (
    SAFE_ERRANDS, GATED_ERRANDS,
    Action, DirectAnswer, RunErrands, RequiresOperator,
    classify, build_system_prompt, build_synthesis_prompt,
)


# ─────────────────────────────────────────────────────────────────────
# Data classes
# ─────────────────────────────────────────────────────────────────────


@dataclass
class Turn:
    """One half-turn (operator says X / throne replies Y)."""
    role: str               # "operator" or "throne"
    text: str
    at: str = ""

    def __post_init__(self) -> None:
        if not self.at:
            self.at = Nyx.now().isoformat()


@dataclass
class ThroneResponse:
    """Returned by Throne.respond — what to show the operator."""
    answer: str                                # plain-English reply
    actions_taken: list[str] = field(default_factory=list)
    suggested_command: str | None = None       # set when refusing GATED
    sources: list[str] = field(default_factory=list)
    elapsed_ms: float = 0.0
    bridge: str = ""
    plan_raw: str = ""                         # the model's raw plan JSON
    error: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


# ─────────────────────────────────────────────────────────────────────
# Snapshot — small frozen context attached to the routing call
# ─────────────────────────────────────────────────────────────────────


def build_snapshot() -> dict[str, Any]:
    """A compact, JSON-safe snapshot of substrate state for the
    routing prompt. Small on purpose — Throne is glue, not Athena."""
    out: dict[str, Any] = {"at": Nyx.now().isoformat()}
    try:
        from olympus.primordials.hestia import hestia
        h = hestia.spark()
        out["hearth"] = {"lit": h.lit, "name": h.name,
                          "vocation": h.vocation}
    except Exception as exc:  # noqa: BLE001
        out["hearth"] = {"error": str(exc)}
    try:
        from olympus.olympians.styx import styx
        out["styx_oaths"] = styx.tally().get("total", 0)
    except Exception:  # noqa: BLE001
        pass
    try:
        from olympus.olympians.pan import pan
        ps = pan.evaluate()
        out["pan"] = {"panicked": ps.panicked, "detail": ps.detail[:120]}
    except Exception:  # noqa: BLE001
        pass
    return out


# ─────────────────────────────────────────────────────────────────────
# Errand execution — run a CLI errand and capture stdout
# ─────────────────────────────────────────────────────────────────────


def _run_errand(name: str, argv: list[str]) -> dict[str, Any]:
    """Execute one SAFE errand in-process. Captures stdout. Returns
    {ok, errand, argv, stdout_head, exit_code, elapsed_ms, error}.

    We import cli.hermes and use the registered handler — the SAME
    code path as `invoke <errand>` — so behavior is identical."""
    started = time.perf_counter()
    out: dict[str, Any] = {
        "ok": False, "errand": name, "argv": list(argv),
        "stdout_head": "", "exit_code": -1, "elapsed_ms": 0.0,
        "error": "",
    }
    if name not in SAFE_ERRANDS:
        out["error"] = f"errand {name!r} is not in SAFE_ERRANDS"
        return out
    try:
        from olympus.cli import hermes
        errand_obj = hermes._errands.get(name)  # type: ignore[attr-defined]
        if errand_obj is None:
            out["error"] = f"no handler registered for errand {name!r}"
            return out
        handler = errand_obj.fn
        # Capture stdout
        import contextlib
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            exit_code = handler(list(argv))
        out["exit_code"] = int(exit_code or 0)
        out["ok"] = (out["exit_code"] == 0)
        # Strip ANSI for the captured head
        stdout = buf.getvalue()
        ansi = re.compile(r"\x1b\[[0-9;]*m")
        out["stdout_head"] = ansi.sub("", stdout)[:4000]
    except SystemExit as exc:
        out["exit_code"] = int(exc.code or 0)
        out["ok"] = (out["exit_code"] == 0)
    except Exception as exc:  # noqa: BLE001
        out["error"] = f"{type(exc).__name__}: {exc}"
    out["elapsed_ms"] = (time.perf_counter() - started) * 1000.0
    return out


# ─────────────────────────────────────────────────────────────────────
# Plan parsing — extract JSON from LLM text
# ─────────────────────────────────────────────────────────────────────


_JSON_BLOCK = re.compile(r"\{.*\}", re.DOTALL)


def _extract_plan(llm_text: str) -> dict[str, Any]:
    """The model is asked to emit pure JSON, but sometimes wraps it in
    prose or code fences. Defensive parse."""
    s = (llm_text or "").strip()
    # Strip code fences
    if s.startswith("```"):
        s = s.strip("`")
        # Remove leading 'json' if present
        if s.lower().startswith("json"):
            s = s[4:].strip()
    try:
        return json.loads(s)
    except json.JSONDecodeError:
        pass
    m = _JSON_BLOCK.search(s)
    if m:
        try:
            return json.loads(m.group(0))
        except json.JSONDecodeError:
            return {"action": "direct", "answer": llm_text[:2000]}
    return {"action": "direct", "answer": llm_text[:2000]}


# ─────────────────────────────────────────────────────────────────────
# Throne — the orchestrator
# ─────────────────────────────────────────────────────────────────────


class Throne:
    """The unified front door. One method matters: `respond(input)`."""

    def __init__(self, *, llm: LLMBridge | None = None,
                 max_routing_tokens: int = 1024,
                 max_synthesis_tokens: int = 1024) -> None:
        self._llm = llm  # if None, resolved each turn via bridge()
        self.max_routing_tokens = max_routing_tokens
        self.max_synthesis_tokens = max_synthesis_tokens

    def _get_llm(self) -> LLMBridge:
        return self._llm if self._llm is not None else _default_bridge()

    # ─────────────────────────────────────────────────────────────
    # The one method that matters
    # ─────────────────────────────────────────────────────────────

    def respond(self, user_input: str,
                 history: list[Turn] | None = None) -> ThroneResponse:
        """One operator turn → one throne response.

        history is optional context (prior turns); not used in routing
        prompt for now (kept small to control cost). Future: feed last
        few turns into the system prompt.
        """
        started = time.perf_counter()
        user_input = (user_input or "").strip()
        if not user_input:
            return ThroneResponse(
                answer="(empty input — try asking 'how's it going?')",
                bridge=self._get_llm().name,
            )

        snapshot = build_snapshot()
        llm = self._get_llm()

        # Step 1 — routing call
        try:
            routing = llm.call(
                system=build_system_prompt(snapshot=snapshot),
                user=user_input,
                max_tokens=self.max_routing_tokens,
                role="throne-routing",
            )
        except Exception as exc:  # noqa: BLE001
            resp = ThroneResponse(
                answer=(f"(throne could not reach the LLM: "
                         f"{type(exc).__name__}: {exc}. "
                         f"Falling back: try `invoke doctor`.)"),
                bridge=llm.name,
                error=str(exc),
                elapsed_ms=(time.perf_counter() - started) * 1000.0,
            )
            self._record_turn(user_input, resp, plan={}, action=None,
                               outputs=[])
            return resp

        plan = _extract_plan(routing.text)
        action = classify(plan)

        # Step 2 — dispatch on Action type
        if isinstance(action, DirectAnswer):
            resp = ThroneResponse(
                answer=action.text or "(no answer)",
                actions_taken=[],
                bridge=llm.name,
                plan_raw=routing.text[:2000],
                elapsed_ms=(time.perf_counter() - started) * 1000.0,
            )
            self._record_turn(user_input, resp, plan=plan, action=action,
                               outputs=[])
            return resp

        if isinstance(action, RequiresOperator):
            resp = ThroneResponse(
                answer=(f"{action.reason}\n\nRun this yourself:\n"
                         f"  {action.suggested_command}"),
                actions_taken=[],
                suggested_command=action.suggested_command,
                bridge=llm.name,
                plan_raw=routing.text[:2000],
                elapsed_ms=(time.perf_counter() - started) * 1000.0,
            )
            self._record_turn(user_input, resp, plan=plan, action=action,
                               outputs=[])
            return resp

        # RunErrands — execute each, collect outputs, synthesize
        assert isinstance(action, RunErrands)
        outputs: list[dict[str, Any]] = []
        actions_taken: list[str] = []
        for ename, argv in action.errands:
            out = _run_errand(ename, argv)
            outputs.append(out)
            actions_taken.append(ename + (
                " " + " ".join(argv) if argv else ""))

        # Step 3 — synthesis call (one more LLM round)
        try:
            synth = llm.call(
                system=("You are Zeus's Throne. Write a plain-English "
                        "answer for the operator based on errand outputs. "
                        "Be concise; cite each errand inline. No JSON, no "
                        "preamble."),
                user=build_synthesis_prompt(
                    user_input=user_input,
                    errand_outputs=outputs),
                max_tokens=self.max_synthesis_tokens,
                role="throne-synthesis",
            )
            answer = synth.text.strip()
        except Exception as exc:  # noqa: BLE001
            # Errands ran successfully but synthesis failed — show raw
            answer = (f"(synthesis call failed: {exc}. Raw outputs:)\n\n"
                       + json.dumps(outputs, default=str, indent=2)[:2000])

        sources = [f"errand:{a}" for a in actions_taken]
        resp = ThroneResponse(
            answer=answer or "(no answer)",
            actions_taken=actions_taken,
            sources=sources,
            bridge=llm.name,
            plan_raw=routing.text[:2000],
            elapsed_ms=(time.perf_counter() - started) * 1000.0,
        )
        self._record_turn(user_input, resp, plan=plan, action=action,
                           outputs=outputs)
        return resp

    # ─────────────────────────────────────────────────────────────
    # Mnemosyne recording — every turn → audit-of-record
    # ─────────────────────────────────────────────────────────────

    def _record_turn(self, user_input: str, resp: ThroneResponse, *,
                      plan: dict[str, Any], action: Action | None,
                      outputs: list[dict[str, Any]]) -> None:
        action_kind = action.kind if action else "none"
        mnemosyne.remember(
            kind="throne.turn",
            actor="throne",
            summary=(f"throne turn: in={len(user_input)}c "
                     f"action={action_kind} "
                     f"errands={len(resp.actions_taken)} "
                     f"out={len(resp.answer)}c "
                     f"{resp.elapsed_ms:.0f}ms"
                     + (f" GATED={resp.suggested_command}"
                        if resp.suggested_command else "")),
            user_input_head=user_input[:512],
            answer_head=resp.answer[:512],
            action_kind=action_kind,
            actions_taken=resp.actions_taken,
            suggested_command=resp.suggested_command,
            bridge=resp.bridge,
            elapsed_ms=resp.elapsed_ms,
            errand_output_count=len(outputs),
            plan_keys=list(plan.keys()) if isinstance(plan, dict) else [],
            error=resp.error,
        )


# ─────────────────────────────────────────────────────────────────────
# Module-level singleton
# ─────────────────────────────────────────────────────────────────────


_THRONE: Throne | None = None


def throne() -> Throne:
    """Get the singleton Throne (uses the default bridge resolution
    per-call so config changes are honored)."""
    global _THRONE
    if _THRONE is None:
        _THRONE = Throne()
    return _THRONE
