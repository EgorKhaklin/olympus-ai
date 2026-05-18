"""Styx — the river of unbreakable oaths.

The gods swore their most binding oaths on the waters of Styx. A god
who broke a Stygian oath was struck unconscious for a year and exiled
from divine assembly for nine more. Olympus's Styx is the immutable
oath ledger: once written, an oath cannot be revised. It is the
substrate-level audit-of-record commitment.

Mnemosyne (the Titan of memory) provides the application-level AoR
discipline. Styx is the primitive beneath it: cryptographic, immutable,
chain-locked.
"""
from __future__ import annotations

import hashlib
import json
import pathlib
from dataclasses import dataclass, asdict
from typing import Any

from olympus.primordials.gaia import root
from olympus.primordials.nyx import Nyx


@dataclass
class Oath:
    seq: int
    ts: str
    sworn_by: str
    statement: str
    payload_hash: str
    prev_hash: str
    self_hash: str

    @staticmethod
    def _digest(*parts: str) -> str:
        return hashlib.sha256("|".join(parts).encode("utf-8")).hexdigest()


class Styx:
    """Append-only oath chain. Each oath hashes its predecessor; tampering
    is detectable by re-hashing the chain."""

    LEDGER = "state/styx.jsonl"

    def __init__(self, ledger_path: pathlib.Path | None = None) -> None:
        self.ledger_path = ledger_path or root.child(self.LEDGER)
        self.ledger_path.parent.mkdir(parents=True, exist_ok=True)

    def _read_all(self) -> list[dict[str, Any]]:
        if not self.ledger_path.exists():
            return []
        with self.ledger_path.open("r", encoding="utf-8") as f:
            return [json.loads(line) for line in f if line.strip()]

    def swear(self, sworn_by: str, statement: str, payload: Any = None) -> Oath:
        """Append an oath. Returns the sworn record."""
        chain = self._read_all()
        seq = len(chain)
        prev_hash = chain[-1]["self_hash"] if chain else "GENESIS"
        ts = Nyx.now().isoformat()
        payload_hash = Oath._digest(json.dumps(payload, sort_keys=True, default=str)) if payload is not None else "void"
        self_hash = Oath._digest(str(seq), ts, sworn_by, statement, payload_hash, prev_hash)
        oath = Oath(seq, ts, sworn_by, statement, payload_hash, prev_hash, self_hash)
        with self.ledger_path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(asdict(oath)) + "\n")
        return oath

    def oaths_of(self, sworn_by: str) -> list[dict[str, Any]]:
        """All oaths sworn by `sworn_by`."""
        return [o for o in self._read_all() if o["sworn_by"] == sworn_by]

    def verify(self) -> tuple[bool, int | None]:
        """Re-hash the chain. Returns (intact, first_bad_seq).
        If intact is True, the chain has not been tampered with."""
        prev = "GENESIS"
        for o in self._read_all():
            expected = Oath._digest(
                str(o["seq"]), o["ts"], o["sworn_by"],
                o["statement"], o["payload_hash"], prev,
            )
            if expected != o["self_hash"] or o["prev_hash"] != prev:
                return False, o["seq"]
            prev = o["self_hash"]
        return True, None


styx = Styx()
swear = styx.swear
oath_of = styx.oaths_of
