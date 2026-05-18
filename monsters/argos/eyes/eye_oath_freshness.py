"""eye_oath_freshness — watches the cadence of new Styx oaths."""
from __future__ import annotations

from monsters.argos.base import Eye, EyeFinding, KIND_INFO, KIND_DRIFT
from underworld.styx import styx
from titans.cronus import Cronus


STALE_HOURS = 168.0   # one week


class EyeOathFreshness(Eye):
    NAME = "eye_oath_freshness"
    SLICE = "underworld/styx (cadence)"

    def scan(self) -> list[EyeFinding]:
        oaths = styx._read_all()
        if not oaths:
            return [self._finding(KIND_INFO, "no oaths sworn yet")]
        age = Cronus.age_seconds(oaths[-1]["ts"]) / 3600.0
        if age > STALE_HOURS:
            return [self._finding(KIND_DRIFT,
                f"{age:.0f}h since the last oath", intensity=3.0,
                hours_since=age)]
        return [self._finding(KIND_INFO,
            f"oath cadence active ({age:.1f}h since last)", total=len(oaths))]
