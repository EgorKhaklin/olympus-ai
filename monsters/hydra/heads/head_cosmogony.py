"""head_cosmogony — watches codex/COSMOGONY.md for invariant drift.

The constitution must always name S1 through S8. If any disappears,
this head emits ALERT — the substrate is no longer constitutionally
covered.
"""
from __future__ import annotations

from monsters.hydra.head import Head, HeadFinding, Severity
from titans.themis import themis


class HeadCosmogony(Head):
    NAME = "cosmogony"
    SLICE = "codex/COSMOGONY.md"
    IMMORTAL = False

    def observe(self) -> list[HeadFinding]:
        findings: list[HeadFinding] = []
        for inv in themis.all():
            if not themis.cosmogony_mentions(inv.id):
                findings.append(self._finding(
                    self.SLICE, Severity.ALERT,
                    f"COSMOGONY.md no longer names invariant {inv.id} ({inv.name})",
                    invariant_id=inv.id,
                ))
        if not findings:
            findings.append(self._finding(
                self.SLICE, Severity.INFO,
                "all eight substrate invariants present in COSMOGONY.md",
                invariant_count=len(themis.all()),
            ))
        return findings
