"""Mnemosyne — titaness of memory, mother of the Muses.

Mnemosyne is memory itself: not the storage but the *discipline* of
remembering accurately. The nine Muses (one per art) are her daughters
by Zeus — each Muse a specific kind of remembering. In Olympus,
Mnemosyne is the audit-of-record discipline.

The substrate-level immutability primitive is Styx (oaths). Mnemosyne
is the higher-level pattern: every load-bearing decision writes to an
append-only record, and the record fully reconstructs operation
without joining elsewhere.
"""
from __future__ import annotations

import json
import pathlib
from dataclasses import dataclass, asdict, field
from typing import Any

from primordials.gaia import root
from primordials.nyx import Nyx


@dataclass
class Memory:
    """A single load-bearing memory — what happened, when, why."""
    kind: str             # decision / observation / oath / transition / ...
    actor: str            # who did this
    summary: str          # one-line description
    body: dict[str, Any] = field(default_factory=dict)
    remembered_at: str = ""

    def __post_init__(self) -> None:
        if not self.remembered_at:
            self.remembered_at = Nyx.now().isoformat()


class Mnemosyne:
    """The audit-of-record discipline. Each kind of record gets its
    own append-only file under titans/mnemosyne_*.jsonl."""

    BASE = "titans/mnemosyne"

    def __init__(self, base_path: pathlib.Path | None = None) -> None:
        self.base_path = base_path or root.child(self.BASE)
        self.base_path.mkdir(parents=True, exist_ok=True)

    def _file_for(self, kind: str) -> pathlib.Path:
        safe = "".join(c for c in kind if c.isalnum() or c == "_")[:64]
        return self.base_path / f"{safe}.jsonl"

    def remember(self, kind: str, actor: str, summary: str,
                 **body: Any) -> Memory:
        """Record a load-bearing memory. Append-only."""
        m = Memory(kind=kind, actor=actor, summary=summary, body=body)
        with self._file_for(kind).open("a", encoding="utf-8") as f:
            f.write(json.dumps(asdict(m), default=str) + "\n")
        return m

    def recall(self, kind: str, actor: str | None = None) -> list[Memory]:
        """Read back memories of a given kind, optionally filtered by actor."""
        path = self._file_for(kind)
        if not path.exists():
            return []
        out: list[Memory] = []
        with path.open("r", encoding="utf-8") as f:
            for line in f:
                if not line.strip():
                    continue
                d = json.loads(line)
                if actor is None or d.get("actor") == actor:
                    out.append(Memory(**d))
        return out

    def kinds(self) -> list[str]:
        """All registered memory kinds."""
        return sorted(f.stem for f in self.base_path.glob("*.jsonl"))


mnemosyne = Mnemosyne()
