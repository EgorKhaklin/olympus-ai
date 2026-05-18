"""ant_test_gap — surfaces Python modules without test files.

Acceleration ant. Slice: each `*.py` under `olympus_web/` and
`monsters.hydra/` (excluding `test_*.py`, `__init__.py`, and other
test-tree leaves). For each module, check whether a corresponding
`test_<name>.py` exists in the same package or in a sibling tests
location.

Local rule: missing test file = `drift` pheromone at intensity 4.0
(uniform — gaps are gaps; no scaling). Acceleration value: hands the
operator a concrete TODO list of "fill these gaps to ship the next
feature confidently."

Read-only contract (G17): the ant does not create test stubs; it
only surfaces the absence.

Authorized by `delphi/2026-05-13-arc-e-acceleration-consciousness-cohort-e10.md`.
"""

from __future__ import annotations

from monsters.argos.base import Eye, EyeFinding, KIND_DRIFT
from monsters.argos.scan_filters import is_olympus_source


# Module-scan roots. We deliberately keep this list small: scanning
# monsters.argos/ would flag every ant as "missing tests", which is
# noise — structural-invariants cover the ant cohort uniformly.
SCAN_DIRS = ("olympus_web", "monsters.hydra")

# Test prefix: in Olympus the convention is `test_*.py` colocated.
TEST_PREFIX = "test_"


def _is_module_file(path) -> bool:
    """True iff path is a real Olympus source module (not test, not
    pkg marker, not under venv/site-packages — see scan_filters)."""
    if not is_olympus_source(path):
        return False
    if path.suffix != ".py":
        return False
    if path.name.startswith(TEST_PREFIX):
        return False
    return True


class AntTestGap(Eye):
    NAME = "ant_test_gap"
    DESCRIPTION = "Pheromones modules under olympus_web/ + monsters.hydra/ without test_<name>.py."

    def scan(self) -> list[EyeFinding]:
        findings: list[EyeFinding] = []
        for sd in SCAN_DIRS:
            base = self.root / sd
            if not base.is_dir():
                continue
            for path in sorted(base.rglob("*.py")):
                #  / B1: scan_filters.is_olympus_source rejects
                # venv/, site-packages/, __pycache__/, etc.
                if not _is_module_file(path):
                    continue
                # Look for test_<name>.py in the SAME directory
                expected = path.parent / f"{TEST_PREFIX}{path.name}"
                if expected.is_file():
                    continue
                rel = path.relative_to(self.root)
                expected_rel = expected.relative_to(self.root)
                findings.append(EyeFinding(
                    node_id=f"module:{rel}",
                    intensity=4.0,
                    kind=KIND_DRIFT,
                    evidence={
                        "message": (
                            f"{rel} has no colocated test file "
                            f"({expected_rel} missing)"
                        ),
                        "module": str(rel),
                        "has_test_file": False,
                        "expected_test_path": str(expected_rel),
                        "fix_hint": (
                            "create a test_<name>.py at the expected "
                            "path, or document why the module is "
                            "test-free in DEVNOTES/style.md"
                        ),
                    },
                    half_life_hours=168.0,    # week-scale
                ))
        return findings
