"""head_lifecycle — watches Iapetus's lifecycle registry.

Components stuck in QUIESCING for too long, components born and never
activated, components ended without proper cleanup — these are
lifecycle drift Iapetus reports and this head surfaces.
"""
from __future__ import annotations

from olympus.monsters.hydra.head import Head, HeadFinding, Severity
from olympus.titans.iapetus import iapetus, LifecyclePhase


class HeadLifecycle(Head):
    NAME = "lifecycle"
    SLICE = "titans/iapetus (lifecycle states)"
    IMMORTAL = False

    def observe(self) -> list[HeadFinding]:
        findings: list[HeadFinding] = []
        quiescing = iapetus.by_phase(LifecyclePhase.QUIESCING)
        if quiescing:
            findings.append(self._finding(
                self.SLICE, Severity.DRIFT,
                f"{len(quiescing)} component(s) stuck in QUIESCING",
                components=[lc.component for lc in quiescing],
            ))
        unborn = iapetus.by_phase(LifecyclePhase.UNBORN)
        if unborn:
            findings.append(self._finding(
                self.SLICE, Severity.INFO,
                f"{len(unborn)} component(s) registered but UNBORN",
                components=[lc.component for lc in unborn],
            ))
        active = iapetus.by_phase(LifecyclePhase.ACTIVE)
        findings.append(self._finding(
            self.SLICE, Severity.INFO,
            f"{len(active)} component(s) ACTIVE",
            active_count=len(active),
        ))
        return findings
