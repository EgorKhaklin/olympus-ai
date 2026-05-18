"""Deme base — the civic-observer pattern.

Each Deme is a named member of the polis tier. Demes summarize at a
higher level than Eyes — they read multiple slices and produce one
finding."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from primordials.nyx import Nyx


@dataclass
class DemeFinding:
    deme: str
    role: str
    summary: str
    detail: dict[str, Any] = field(default_factory=dict)
    seen_at: str = ""

    def __post_init__(self) -> None:
        if not self.seen_at:
            self.seen_at = Nyx.now().isoformat()


class Deme:
    NAME: str = "unnamed-deme"
    ROLE: str = "unspecified"

    def observe(self) -> DemeFinding:
        raise NotImplementedError
