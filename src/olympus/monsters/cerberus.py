"""Cerberus — three-headed dog who guards the gates of the underworld.

Cerberus allowed the dead in but never out. In Olympus, Cerberus is
the perimeter check: he validates that a caller is permitted to cross
a named boundary before allowing the call through.

Each head checks one dimension: authentication, authorization, integrity.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Callable


@dataclass
class Gate:
    """A named boundary Cerberus watches."""
    name: str
    authenticate: Callable[[str], bool]    # who-they-are
    authorize:    Callable[[str], bool]    # what-they-can-do
    verify:       Callable[[bytes], bool]  # what-they-brought-is-intact


@dataclass
class Verdict:
    gate: str
    caller: str
    allowed: bool
    head_blocked: str | None       # "authenticate" / "authorize" / "verify" / None


class Cerberus:
    """Three-headed guardian."""

    def __init__(self) -> None:
        self._gates: dict[str, Gate] = {}

    def post(self, gate: Gate) -> None:
        self._gates[gate.name] = gate

    def admit(self, gate_name: str, caller: str, payload: bytes = b"") -> Verdict:
        """Check all three heads. Returns Verdict; first failing head
        wins."""
        gate = self._gates.get(gate_name)
        if gate is None:
            return Verdict(gate=gate_name, caller=caller, allowed=False,
                           head_blocked="no-such-gate")
        if not gate.authenticate(caller):
            return Verdict(gate=gate_name, caller=caller, allowed=False,
                           head_blocked="authenticate")
        if not gate.authorize(caller):
            return Verdict(gate=gate_name, caller=caller, allowed=False,
                           head_blocked="authorize")
        if not gate.verify(payload):
            return Verdict(gate=gate_name, caller=caller, allowed=False,
                           head_blocked="verify")
        return Verdict(gate=gate_name, caller=caller, allowed=True, head_blocked=None)


cerberus = Cerberus()
