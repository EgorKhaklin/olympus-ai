"""ant_delphi_outcome — pheromones for Delphis lacking §VII cross-refs.

Slice: each Delphi file under `delphi/2026-*.md`.

Local rule: if a Delphi is CLOSED but its §VII Outcome does not name a
CHANGELOG version or link a journal file, deposit a `drift` pheromone
onto the brain-map node for that Delphi.

This is the Architect-reflection finding that  closed manually.
The ant exists so any future regression is surfaced automatically: as
soon as a Delphi is created, the ant will track it; as soon as it
gets a §VII cross-ref, the ant stops complaining (no pheromone next
pass).

Decentralization note: this ant does NOT decide what to do about the
finding. It just deposits the observation. Other ants (or human
operators reading the bloom) interpret the pattern.
"""

from __future__ import annotations

import re

from monsters.argos.base import (
    Ant, EyeFinding, KIND_DRIFT, KIND_INFO, DECAY_HALF_LIFE_HOURS_DEFAULT,
)


# Pattern for "§VII Outcome that names a v8.X version OR links a journal/ path"
_VII_SECTION_RE = re.compile(r"^## VII\. Outcome\b", re.MULTILINE)
_HAS_LINK_RE = re.compile(r"(CHANGELOG|## v8\.|journal/)")


class AntDelphiOutcome(Eye):
    NAME = "ant_delphi_outcome"
    DESCRIPTION = "Pheromones Delphis whose §VII lacks CHANGELOG/journal links."

    def scan(self) -> list[EyeFinding]:
        findings: list[EyeFinding] = []
        delphi_dir = self.root / "delphi"
        if not delphi_dir.is_dir():
            return findings
        for path in sorted(delphi_dir.glob("2026-*.md")):
            text = self._read("delphi", path.name) or ""
            # Find §VII section
            m = _VII_SECTION_RE.search(text)
            if not m:
                # No §VII at all — not closed yet, skip
                continue
            vii_body = text[m.end():]
            # Skip if Delphi is still OPEN (no decision yet)
            if "DECIDED" not in text and "Status:** CLOSED" not in text:
                continue
            if _HAS_LINK_RE.search(vii_body):
                # Has a cross-ref; quiet
                continue
            # Drift: closed Delphi lacks §VII cross-ref
            slug = path.stem  # "2026-05-13-arc-e-..."
            findings.append(EyeFinding(
                node_id=f"delphi:{slug}",
                intensity=2.5,
                kind=KIND_DRIFT,
                evidence={
                    "message": "§VII Outcome lacks CHANGELOG/journal cross-ref",
                    "file": f"delphi/{path.name}",
                    "fix_hint": "append '**See:** CHANGELOG ## vX.Y · journal/YYYY-MM-DD.md'",
                },
                half_life_hours=DECAY_HALF_LIFE_HOURS_DEFAULT,
            ))
        return findings
