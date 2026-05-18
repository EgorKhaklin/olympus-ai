"""eye_styx_chain_intact — re-verify the Styx oath chain."""
from __future__ import annotations

from monsters.argos.base import Eye, EyeFinding, KIND_INFO, KIND_ALERT
from underworld.styx import styx


class EyeStyxChainIntact(Eye):
    NAME = "eye_styx_chain_intact"
    SLICE = "underworld/styx.jsonl"

    def scan(self) -> list[EyeFinding]:
        intact, bad_seq = styx.verify()
        if not intact:
            return [self._finding(KIND_ALERT,
                f"styx chain tampered at seq={bad_seq}", intensity=10.0,
                first_bad_seq=bad_seq)]
        return [self._finding(KIND_INFO,
            f"styx chain intact across {len(styx._read_all())} oath(s)")]
