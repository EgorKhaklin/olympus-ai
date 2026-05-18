"""head_immortal — the one head that cannot be killed.

In myth, Heracles cut every head of the Hydra, and two regrew for
each cut — except one, the immortal head, which he buried under a
great stone. The mortal heads can be replaced; the immortal one is
the structural guarantee.

In Olympus, the immortal head watches the other heads. If any
mortal head has gone silent — no findings emitted in the last run —
the immortal head emits ALERT. This is the meta-watcher: the head
that ensures the watcher tier is still operating.
"""
from __future__ import annotations

from monsters.hydra.head import Head, HeadFinding, Severity
from titans.mnemosyne import mnemosyne


class HeadImmortal(Head):
    NAME = "immortal"
    SLICE = "the watcher tier itself"
    IMMORTAL = True

    def observe(self) -> list[HeadFinding]:
        # Read the most recent hydra.run memory to know which heads
        # reported findings. If a mortal head emitted nothing in the
        # last run, that's surfaced here.
        runs = mnemosyne.recall("hydra.run", "hydra")
        if not runs:
            return [self._finding(
                self.SLICE, Severity.INFO,
                "no prior HYDRA run recorded; nothing to watch yet",
            )]
        last = runs[-1]
        head_counts: dict[str, int] = last.body.get("head_counts", {})
        silent = [name for name, n in head_counts.items()
                  if n == 0 and name != self.NAME]
        if silent:
            return [self._finding(
                self.SLICE, Severity.ALERT,
                f"{len(silent)} mortal head(s) emitted no findings last run",
                silent_heads=silent,
            )]
        return [self._finding(
            self.SLICE, Severity.INFO,
            f"all {len(head_counts) - 1} mortal heads reported last run",
            head_counts=head_counts,
        )]
