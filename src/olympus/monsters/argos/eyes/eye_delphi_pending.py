"""eye_delphi_pending — counts Delphi files that look unresolved
(no decision recorded)."""
from __future__ import annotations

from olympus.monsters.argos.base import Eye, EyeFinding, KIND_INFO, KIND_DRIFT
from olympus.primordials.gaia import root


class EyeDelphiPending(Eye):
    NAME = "eye_delphi_pending"
    SLICE = "oracles/delphi/"

    def scan(self) -> list[EyeFinding]:
        delphi_path = root.child("oracles", "delphi")
        if not delphi_path.exists():
            return [self._finding(KIND_INFO, "oracles/delphi/ missing")]
        files = sorted(delphi_path.glob("*.md"))
        if not files:
            return [self._finding(KIND_INFO, "no Delphi files yet")]
        unresolved: list[str] = []
        for f in files:
            text = f.read_text(encoding="utf-8")
            if "Zeus decision" in text and "Position" not in text:
                unresolved.append(f.name)
        if unresolved:
            return [self._finding(KIND_DRIFT,
                f"{len(unresolved)} Delphi file(s) appear unresolved",
                intensity=3.0, unresolved=unresolved)]
        return [self._finding(KIND_INFO,
            f"{len(files)} Delphi file(s); none pending")]
