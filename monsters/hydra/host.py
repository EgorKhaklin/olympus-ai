"""Hydra — the host that orchestrates the eight mortal heads + immortal.

The host calls each head's observe() and aggregates findings. It does
NOT call any LLM. The heads return structured data; what the operator
or agent does with the data is downstream of Hydra.
"""
from __future__ import annotations

from dataclasses import dataclass, field, asdict
from typing import Type

from monsters.hydra.head import Head, HeadFinding, Severity
from titans.mnemosyne import mnemosyne
from olympians.poseidon import poseidon


@dataclass
class HydraReport:
    findings: list[HeadFinding] = field(default_factory=list)
    by_head: dict[str, list[HeadFinding]] = field(default_factory=dict)

    @property
    def total(self) -> int:
        return len(self.findings)

    @property
    def alerts(self) -> list[HeadFinding]:
        return [f for f in self.findings if f.severity == Severity.ALERT]

    @property
    def drifts(self) -> list[HeadFinding]:
        return [f for f in self.findings if f.severity == Severity.DRIFT]


class Hydra:
    """Eight mortal heads + one immortal. The host runs them, in
    deterministic order, collecting findings."""

    STREAM = "hydra.findings"

    def __init__(self) -> None:
        self._heads: list[Head] = []

    def attach(self, head: Head) -> None:
        """Attach a head. There must be exactly one IMMORTAL head."""
        self._heads.append(head)

    def heads(self) -> list[Head]:
        return list(self._heads)

    def mortal_count(self) -> int:
        return sum(1 for h in self._heads if not h.IMMORTAL)

    def immortal(self) -> Head | None:
        for h in self._heads:
            if h.IMMORTAL:
                return h
        return None

    def behead(self) -> HydraReport:
        """Run every head's observe(). Aggregates findings.

        Records the run in Mnemosyne; broadcasts each finding on
        Poseidon's `hydra.findings` stream so Furies can react."""
        report = HydraReport()
        for head in self._heads:
            findings = head.observe()
            report.findings.extend(findings)
            report.by_head[head.NAME] = findings
            for f in findings:
                poseidon.publish(self.STREAM, f)
        mnemosyne.remember(
            kind="hydra.run",
            actor="hydra",
            summary=f"observed {report.total} findings across "
                    f"{len(self._heads)} heads ({report.alerts} alerts, "
                    f"{report.drifts} drifts)",
            head_counts={h.NAME: len(report.by_head.get(h.NAME, []))
                         for h in self._heads},
        )
        return report


hydra = Hydra()


# ─────────────────────────────────────────────────────────────────
# The default head roster: 8 mortal + 1 immortal.
# Deployments may attach their own heads; these are the defaults
# Olympus ships with.
# ─────────────────────────────────────────────────────────────────


def _attach_defaults() -> None:
    from monsters.hydra.heads.head_cosmogony import HeadCosmogony
    from monsters.hydra.heads.head_pantheon import HeadPantheon
    from monsters.hydra.heads.head_styx import HeadStyx
    from monsters.hydra.heads.head_journal import HeadJournal
    from monsters.hydra.heads.head_oaths import HeadOaths
    from monsters.hydra.heads.head_lifecycle import HeadLifecycle
    from monsters.hydra.heads.head_substrate import HeadSubstrate
    from monsters.hydra.heads.head_apollo import HeadApollo
    from monsters.hydra.heads.head_immortal import HeadImmortal

    for cls in (HeadCosmogony, HeadPantheon, HeadStyx, HeadJournal,
                HeadOaths, HeadLifecycle, HeadSubstrate, HeadApollo,
                HeadImmortal):
        hydra.attach(cls())


_attach_defaults()
