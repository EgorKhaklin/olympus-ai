"""head_oaths — watches the cadence of new Styx oaths.

Olympus operations should produce oaths. A long stretch with no new
oaths means either no activity, or activity that is bypassing the
oath ledger. Both are drift.
"""
from __future__ import annotations

import datetime

from olympus.monsters.hydra.head import Head, HeadFinding, Severity
from olympus.underworld.styx import styx
from olympus.titans.cronus import Cronus


SILENCE_THRESHOLD_HOURS = 72.0


class HeadOaths(Head):
    NAME = "oaths"
    SLICE = "underworld/styx (cadence)"
    IMMORTAL = False

    def observe(self) -> list[HeadFinding]:
        oaths = styx._read_all()
        if not oaths:
            return [self._finding(
                self.SLICE, Severity.INFO,
                "no oaths sworn yet",
            )]
        last_ts = oaths[-1]["ts"]
        age = Cronus.age_seconds(last_ts) / 3600.0
        if age > SILENCE_THRESHOLD_HOURS:
            return [self._finding(
                self.SLICE, Severity.DRIFT,
                f"{age:.1f}h since the last oath",
                last_ts=last_ts, hours_since=age,
            )]
        return [self._finding(
            self.SLICE, Severity.INFO,
            f"oaths current ({age:.1f}h since last)",
            total=len(oaths),
        )]
