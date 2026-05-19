"""olympus.throne.repl — interactive terminal REPL for the Throne.

`invoke throne` (no args) enters this loop. Each turn:
  - operator types a line
  - Throne.respond() runs
  - the answer + (if any) suggested_command + actions_taken are printed
  - the loop continues until q/quit/exit/EOF

Multi-turn history is kept in-memory only (not persisted across REPL
sessions; Mnemosyne already records every turn under `throne.turn`).
"""
from __future__ import annotations

import sys
from typing import Callable, Iterable

from olympus.throne.throne import Throne, ThroneResponse, Turn, throne


_BANNER = """\
╔════════════════════════════════════════════════════════════╗
║  Zeus's Throne (Διὸς θρόνος)                              ║
║  ask anything in plain English — q to exit                ║
╚════════════════════════════════════════════════════════════╝"""


_HELP = """\
You can type anything. Examples:
  · how's everything?
  · what should I look at today?
  · ask hephaestus what's drifting
  · show me what the substrate has learned
  · should I worry about the atlas warning?

HIGH-risk actions (ratify, kindle, panic-clear) are NOT runnable from
the Throne by constitutional design. If your intent maps to one,
Throne will refuse and show you the exact CLI command to run yourself.

Commands: q/quit/exit (leave) · ? (this help) · history (recent turns)
"""


def run(*,
        input_provider: Callable[[str], str] | None = None,
        output: Callable[[str], None] | None = None,
        throne_instance: Throne | None = None,
        max_history: int = 10,
        speak_responses: bool = False) -> int:
    """The REPL loop. Returns 0 on clean exit.

    Injectable for tests:
      - input_provider: callable taking the prompt str, returning the user line
      - output: callable taking a string to print
      - throne_instance: a Throne (default: module singleton)
      - speak_responses: per Throne-Voice arc, pipe each response
        through the active TTS backend
    """
    inp = input_provider or input
    out = output or print
    t = throne_instance if throne_instance is not None else throne()

    out(_BANNER)
    if speak_responses:
        out("  (voice mode — responses will be spoken)")
    out("type ? for help\n")

    history: list[Turn] = []
    while True:
        try:
            line = inp("  you ▸ ").strip()
        except (KeyboardInterrupt, EOFError):
            out("")
            break

        if not line:
            continue
        if line.lower() in {"q", "quit", "exit", ":q"}:
            out("  (leaving the throne — Mnemosyne retains every turn)")
            break
        if line in {"?", "help"}:
            out(_HELP)
            continue
        if line.lower() == "history":
            _print_history(history, out, max_history=max_history)
            continue
        # Voice toggles inside the REPL
        if line.lower() in {"/voice on", ":voice on"}:
            speak_responses = True
            out("  (voice mode ON)")
            continue
        if line.lower() in {"/voice off", ":voice off", "/quiet"}:
            speak_responses = False
            out("  (voice mode OFF)")
            continue

        history.append(Turn(role="operator", text=line))
        resp = t.respond(line, history=history)
        history.append(Turn(role="throne", text=resp.answer))
        _print_response(resp, out)

        # Voice output: speak the answer in the background
        if speak_responses and resp.answer:
            try:
                from olympus.runtime.voice import speak as _speak
                _speak(resp.answer)
            except Exception:  # noqa: BLE001
                pass

    return 0


def _print_response(r: ThroneResponse, out: Callable[[str], None]) -> None:
    """Render one ThroneResponse to the terminal."""
    out("")
    out("  throne ▸")
    for line in (r.answer or "").splitlines() or [""]:
        out(f"    {line}")
    meta_bits: list[str] = []
    if r.actions_taken:
        meta_bits.append("ran: " + ", ".join(r.actions_taken))
    if r.suggested_command:
        meta_bits.append(f"command: {r.suggested_command}")
    meta_bits.append(f"{r.elapsed_ms:.0f}ms via {r.bridge}")
    out("    ── " + " · ".join(meta_bits))
    out("")


def _print_history(history: list[Turn], out: Callable[[str], None],
                    *, max_history: int) -> None:
    if not history:
        out("  (no turns yet)")
        return
    out("")
    for t in history[-max_history:]:
        prefix = "  you ▸" if t.role == "operator" else "  throne ▸"
        snippet = t.text[:200].replace("\n", " ")
        out(f"{prefix} {snippet}")
    out("")


# ─────────────────────────────────────────────────────────────────────
# One-shot mode (invoke throne "..." with args)
# ─────────────────────────────────────────────────────────────────────


def one_shot(user_input: str, *,
              output: Callable[[str], None] | None = None,
              throne_instance: Throne | None = None) -> int:
    """Single turn, print, exit. Returns 0 on success, 1 on error."""
    out = output or print
    t = throne_instance if throne_instance is not None else throne()
    out(_BANNER)
    out("")
    out(f"  you ▸ {user_input}")
    resp = t.respond(user_input)
    _print_response(resp, out)
    return 0 if not resp.error else 1
