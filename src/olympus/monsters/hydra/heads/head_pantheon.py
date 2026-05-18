"""head_pantheon — watches codex/PANTHEON.md against disk.

Every god declared in PANTHEON.md must have a Python module. Every
Python module under a cosmogonic tier must be declared in
PANTHEON.md. Drift in either direction is a finding.
"""
from __future__ import annotations

import re

from olympus.monsters.hydra.head import Head, HeadFinding, Severity
from olympus.primordials.gaia import root


TIERS = (
    "primordials", "titans", "olympians", "underworld",
    "fates", "furies", "graces", "muses", "heroes",
)


class HeadPantheon(Head):
    NAME = "pantheon"
    SLICE = "codex/PANTHEON.md"
    IMMORTAL = False

    def observe(self) -> list[HeadFinding]:
        findings: list[HeadFinding] = []
        pantheon_md = self._read("codex", "PANTHEON.md")
        if not pantheon_md:
            findings.append(self._finding(
                self.SLICE, Severity.ALERT,
                "PANTHEON.md is missing",
            ))
            return findings

        # Disk → doc: every .py module in tier dirs should be named in PANTHEON.md
        unnamed: list[str] = []
        for tier in TIERS:
            tier_path = root.child("src", "olympus", tier)
            if not tier_path.exists():
                continue
            for f in tier_path.glob("*.py"):
                if f.name.startswith("_") or f.name == "base.py":
                    continue
                stem = f.stem
                pretty = stem.replace("_muse", "")
                if not re.search(rf"\b{re.escape(pretty)}\b", pantheon_md, re.IGNORECASE):
                    unnamed.append(f"{tier}/{f.name}")

        if unnamed:
            findings.append(self._finding(
                self.SLICE, Severity.DRIFT,
                f"{len(unnamed)} module(s) on disk but not named in PANTHEON.md",
                unnamed=unnamed[:10],
            ))
        else:
            findings.append(self._finding(
                self.SLICE, Severity.INFO,
                "PANTHEON.md is in sync with disk",
            ))
        return findings
