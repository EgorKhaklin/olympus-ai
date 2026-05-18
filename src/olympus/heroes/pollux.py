"""Pollux — the immortal twin of the Dioscuri.

In myth: Pollux was a boxer, son of Zeus by Leda, immortal where
Castor was mortal. When Castor died, Pollux shared his immortality;
Zeus placed them in the heavens together.

In Olympus, Pollux is the **comparator**. Castor produces shadow
session reports; Pollux compares one report against another (or
against production state) and surfaces structured differences.

Symmetric design — comparison is commutative; deltas are computed
field by field over a known set of session-report keys.

Per Delphi 2026-05-18-recursion-arc.md.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from olympus.primordials.nyx import Nyx
from olympus.titans.mnemosyne import mnemosyne


@dataclass
class Difference:
    """One field-level diff between two reports."""
    field: str
    left: Any
    right: Any


@dataclass
class ComparisonReport:
    compared_at: str
    left_label: str
    right_label: str
    differences: list[Difference] = field(default_factory=list)
    same_fields: list[str] = field(default_factory=list)
    only_in_left: list[str] = field(default_factory=list)
    only_in_right: list[str] = field(default_factory=list)

    @property
    def differs(self) -> bool:
        return bool(self.differences or self.only_in_left
                    or self.only_in_right)


# Keys that meaningfully compare across two session reports. Lifecycle
# timestamps and ids vary between runs by design — they're skipped.
_COMPARABLE_KEYS: tuple[str, ...] = (
    "hydra_findings", "argos_pheromones", "proposals_count",
    "proposals_auto", "proposals_queued", "proposals_delphi",
    "prophecies_verified", "prophecies_accepted",
    "prophecies_rejected", "fury_alerts",
    "delta_hydra_change", "delta_argos_change",
    "delta_new_alerts", "delta_resolved_alerts",
    "recurring_slices", "newly_alerted_slices", "resolved_slices",
    "insights",
)


class Pollux:
    """The comparator twin."""

    def compare(self,
                left: dict[str, Any],
                right: dict[str, Any],
                *,
                left_label: str = "left",
                right_label: str = "right",
                keys: tuple[str, ...] | None = None,
                ) -> ComparisonReport:
        """Diff two session-report dicts. Returns a ComparisonReport."""
        keys = keys or _COMPARABLE_KEYS
        report = ComparisonReport(
            compared_at=Nyx.now().isoformat(),
            left_label=left_label, right_label=right_label,
        )
        for k in keys:
            in_left = k in left
            in_right = k in right
            if in_left and in_right:
                lv, rv = left.get(k), right.get(k)
                if self._equal(lv, rv):
                    report.same_fields.append(k)
                else:
                    report.differences.append(Difference(
                        field=k, left=lv, right=rv,
                    ))
            elif in_left and not in_right:
                report.only_in_left.append(k)
            elif in_right and not in_left:
                report.only_in_right.append(k)
            # else: in neither — silent
        mnemosyne.remember(
            kind="pollux.comparison",
            actor="pollux",
            summary=(f"compared {left_label!r} vs {right_label!r}: "
                     f"{len(report.differences)} diffs · "
                     f"{len(report.same_fields)} same · "
                     f"{len(report.only_in_left)} L-only · "
                     f"{len(report.only_in_right)} R-only"),
            left_label=left_label, right_label=right_label,
            differences=[
                {"field": d.field, "left": d.left, "right": d.right}
                for d in report.differences
            ],
            same_fields=report.same_fields,
            only_in_left=report.only_in_left,
            only_in_right=report.only_in_right,
        )
        return report

    @staticmethod
    def _equal(a: Any, b: Any) -> bool:
        # Lists compare as ordered for now (sessions emit deterministic
        # orderings); operators wanting set-equality should use
        # frozenset before comparing.
        if isinstance(a, list) and isinstance(b, list):
            return a == b
        return a == b


pollux = Pollux()
