"""Brief — render Apollo's predictions into a human-readable brief.

The brief structure is simple by design — Apollo's predictions speak
for themselves; the brief just lays them out."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable

from olympus.olympians.apollo.oracle import Prediction


@dataclass
class Brief:
    title: str = "Apollo's brief"
    predictions: list[Prediction] = field(default_factory=list)
    acceptance_rate: float | None = None


def render_brief(predictions: Iterable[Prediction], *,
                 title: str = "Apollo's brief") -> str:
    """Render a list of predictions into a plain-text brief."""
    preds = list(predictions)
    lines: list[str] = [
        f"# {title}",
        "",
        f"_{len(preds)} prediction(s)_",
        "",
    ]
    for p in preds:
        status = (
            "PENDING" if p.accepted is None
            else ("ACCEPTED" if p.accepted else "REJECTED")
        )
        lines.append(f"## {p.name}  [{status}]")
        lines.append(f"  · *horizon:* {p.horizon}")
        lines.append(f"  · *issued:* {p.issued_at}")
        lines.append("")
        lines.append(p.statement)
        lines.append("")
    return "\n".join(lines)
