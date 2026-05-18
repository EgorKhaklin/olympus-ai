"""Demarchos — the deme-leader.

The demarchos was the official head of a Greek deme who kept the
citizen roll. In Olympus, Demarchos keeps the roll of registered
Eyes and Heads."""
from __future__ import annotations

from monsters.argos.demes.base import Deme, DemeFinding


class Demarchos(Deme):
    NAME = "demarchos"
    ROLE = "the deme-leader / roll-keeper"

    def observe(self) -> DemeFinding:
        from monsters.argos.colony import colony
        from monsters.hydra.host import hydra
        eyes = colony.eyes()
        heads = hydra.heads()
        return DemeFinding(
            deme=self.NAME, role=self.ROLE,
            summary=f"the roll holds {len(eyes)} eye(s) and {len(heads)} head(s)",
            detail={
                "eye_names": [e.NAME for e in eyes],
                "head_names": [h.NAME for h in heads],
                "mortal_heads": hydra.mortal_count(),
                "immortal_head": hydra.immortal().NAME if hydra.immortal() else None,
            },
        )


demarchos = Demarchos()
