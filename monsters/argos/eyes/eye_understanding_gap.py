"""eye_understanding_gap — structural enforcement of S8.

S8 (Continuity of Understanding) says every load-bearing action must be
reconstructible from the substrate's own records. This Eye reads
Mnemosyne and flags load-bearing kinds (decision / oath / proposal /
transition) whose entries are missing rationale, actor, or summary.
"""
from __future__ import annotations

from monsters.argos.base import Eye, EyeFinding, KIND_INFO, KIND_DRIFT


# Memory kinds Olympus treats as load-bearing — these MUST carry enough
# detail for the operator to reconstruct why.
LOAD_BEARING_KINDS = (
    "decision",
    "thread.spun",
    "thread.cut",
    "hydra.run",
    "colony.deploy",
    "bootstrap",
    "invariant.violated",
)


class EyeUnderstandingGap(Eye):
    NAME = "eye_understanding_gap"
    SLICE = "titans/mnemosyne (rationale coverage)"

    def scan(self) -> list[EyeFinding]:
        from titans.mnemosyne import mnemosyne

        gap_count = 0
        opaque: list[str] = []
        total = 0
        for kind in mnemosyne.kinds():
            if kind not in LOAD_BEARING_KINDS:
                continue
            for m in mnemosyne.recall(kind):
                total += 1
                # A memory is reconstructible iff it carries actor + summary.
                if not m.actor or not m.summary:
                    gap_count += 1
                    opaque.append(f"{kind}@{m.remembered_at}")

        if total == 0:
            return [self._finding(KIND_INFO,
                "no load-bearing memories yet to audit",
                load_bearing_kinds=list(LOAD_BEARING_KINDS))]

        if gap_count:
            return [self._finding(KIND_DRIFT,
                f"{gap_count} of {total} load-bearing memor{'ies' if total != 1 else 'y'} "
                f"lack actor or summary — S8 violation",
                intensity=min(8.0, gap_count / max(total, 1) * 10.0),
                total=total, gaps=gap_count, sample=opaque[:5])]

        return [self._finding(KIND_INFO,
            f"all {total} load-bearing memor{'ies' if total != 1 else 'y'} are reconstructible",
            total=total)]
