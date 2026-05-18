"""Head — the base class every HYDRA head extends.

A Head observes one slice of the substrate. It does not write. It does
not import other Heads. Its only output is a list of HeadFinding
records, which the host (Hydra) collects.

The S3 substrate invariant says HYDRA heads are read-only. Any Head
that writes is a bug.
"""
from __future__ import annotations

import enum
from dataclasses import dataclass, field
from typing import Any

from primordials.gaia import root
from primordials.nyx import Nyx


class Severity(str, enum.Enum):
    INFO = "info"          # noted, no action
    DRIFT = "drift"        # measurable, not yet broken
    ALERT = "alert"        # broken; needs decision


@dataclass
class HeadFinding:
    head: str               # name of the emitting Head
    slice: str              # what part of the substrate
    severity: Severity
    detail: str
    evidence: dict[str, Any] = field(default_factory=dict)
    observed_at: str = ""

    def __post_init__(self) -> None:
        if not self.observed_at:
            self.observed_at = Nyx.now().isoformat()


class Head:
    """Base class for any HYDRA head. Subclasses implement observe()."""

    NAME: str = "unnamed-head"
    SLICE: str = "unspecified"
    IMMORTAL: bool = False     # set True only on the one immortal head

    def observe(self) -> list[HeadFinding]:
        """Return findings. MUST NOT mutate any state. Override in
        subclasses."""
        raise NotImplementedError

    # ─────────────────────────────────────────────────────────────
    # Helpers available to every head
    # ─────────────────────────────────────────────────────────────

    def _read(self, *parts: str) -> str:
        """Read a project-relative file. Returns "" if missing."""
        p = root.child(*parts)
        if not p.exists():
            return ""
        return p.read_text(encoding="utf-8")

    def _finding(self, slice: str, severity: Severity, detail: str,
                 **evidence: Any) -> HeadFinding:
        return HeadFinding(
            head=self.NAME, slice=slice, severity=severity,
            detail=detail, evidence=evidence,
        )
