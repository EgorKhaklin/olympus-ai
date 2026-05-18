"""head_substrate — watches the filesystem layout against Rhea's
required-directories list.

If a required directory disappears, the substrate is no longer whole.
Rhea can re-bring-forth, but the head emits ALERT first so the
operator knows it happened.
"""
from __future__ import annotations

from monsters.hydra.head import Head, HeadFinding, Severity
from titans.rhea import rhea
from primordials.gaia import root


class HeadSubstrate(Head):
    NAME = "substrate"
    SLICE = "filesystem layout"
    IMMORTAL = False

    def observe(self) -> list[HeadFinding]:
        missing: list[str] = []
        for rel in rhea.REQUIRED_DIRS:
            if not root.child(rel).is_dir():
                missing.append(rel)
        if missing:
            return [self._finding(
                self.SLICE, Severity.ALERT,
                f"{len(missing)} required director(y/ies) missing",
                missing=missing,
            )]
        return [self._finding(
            self.SLICE, Severity.INFO,
            f"all {len(rhea.REQUIRED_DIRS)} required directories present",
        )]
