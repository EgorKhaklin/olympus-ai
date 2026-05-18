"""Ephoros — the overseer.

The ephors were Spartan magistrates who watched the kings for
constitutional compliance. In Olympus, Ephoros watches the Delphi
archive for protocol compliance: every recorded decision should be
sworn on Styx."""
from __future__ import annotations

from monsters.argos.demes.base import Deme, DemeFinding
from primordials.gaia import root
from underworld.styx import styx


class Ephoros(Deme):
    NAME = "ephoros"
    ROLE = "the overseer — protocol compliance"

    def observe(self) -> DemeFinding:
        delphi_dir = root.child("oracles", "delphi")
        if not delphi_dir.exists():
            return DemeFinding(deme=self.NAME, role=self.ROLE,
                summary="oracles/delphi/ does not exist; nothing to watch")
        delphi_files = list(delphi_dir.glob("*.md"))
        oaths = styx._read_all()
        decision_oaths = [o for o in oaths if "delphi" in o["statement"].lower()
                          or "decision" in o["statement"].lower()]
        return DemeFinding(
            deme=self.NAME, role=self.ROLE,
            summary=(f"{len(delphi_files)} Delphi file(s); "
                     f"{len(decision_oaths)} decision-oath(s) on Styx"),
            detail={
                "delphi_files": len(delphi_files),
                "decision_oaths": len(decision_oaths),
            },
        )


ephoros = Ephoros()
