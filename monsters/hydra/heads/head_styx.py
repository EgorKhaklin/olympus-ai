"""head_styx — watches the oath chain for tampering.

The Styx ledger is append-only and chain-hashed. If a cryptographic
re-verification fails, this head emits ALERT — the constitution's
own substrate is broken.
"""
from __future__ import annotations

from monsters.hydra.head import Head, HeadFinding, Severity
from underworld.styx import styx


class HeadStyx(Head):
    NAME = "styx"
    SLICE = "underworld/styx.jsonl"
    IMMORTAL = False

    def observe(self) -> list[HeadFinding]:
        intact, bad_seq = styx.verify()
        if not intact:
            return [self._finding(
                self.SLICE, Severity.ALERT,
                f"styx chain tampered at seq={bad_seq}",
                first_bad_seq=bad_seq,
            )]
        oath_count = len(styx._read_all())
        return [self._finding(
            self.SLICE, Severity.INFO,
            f"styx chain intact across {oath_count} oath(s)",
            oath_count=oath_count,
        )]
