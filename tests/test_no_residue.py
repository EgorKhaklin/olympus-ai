"""Zero-tolerance residue test.

The kindling commitment: zero mentions of any pre-Olympus framework,
zero legacy version refs, zero unintended cross-contamination.

This test is the enforcement."""
from __future__ import annotations

import pathlib
import re
import sys
import unittest

ROOT = pathlib.Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


# Forbidden in any active file (not in archive or this test itself).
FORBIDDEN_PATTERNS = (
    (re.compile(r"\bpolaris\b", re.IGNORECASE), "polaris"),
    (re.compile(r"\bmycelium\b", re.IGNORECASE), "mycelium"),
    (re.compile(r"\bsanctum\b", re.IGNORECASE), "sanctum"),
    (re.compile(r"\bv[89]\.[0-9]+\b"), "legacy version v8.x/v9.x"),
    (re.compile(r"\bv[89]\.[0-9]+\.[0-9]+\b"), "legacy version v8.x.y/v9.x.y"),
    (re.compile(r"\bPolaris\b"), "Polaris"),
    (re.compile(r"\bPOLARIS\b"), "POLARIS"),
)

EXEMPT = {"tests/test_no_residue.py"}

SKIP_DIRS = {".git", "__pycache__", "node_modules", ".venv", "venv"}

SCANNABLE_SUFFIXES = (".py", ".sh", ".md", ".json", ".yml", ".yaml",
                      ".toml", ".txt", ".cfg", ".ini")


def _files() -> list[pathlib.Path]:
    out: list[pathlib.Path] = []
    for p in ROOT.rglob("*"):
        if not p.is_file():
            continue
        if any(part in SKIP_DIRS for part in p.parts):
            continue
        if p.suffix not in SCANNABLE_SUFFIXES:
            continue
        rel = p.relative_to(ROOT).as_posix()
        if rel in EXEMPT:
            continue
        out.append(p)
    return out


class TestNoResidue(unittest.TestCase):

    def test_no_legacy_residue_in_active_files(self):
        violations: list[tuple[str, int, str, str]] = []
        for p in _files():
            try:
                lines = p.read_text(encoding="utf-8").splitlines()
            except UnicodeDecodeError:
                continue
            for i, line in enumerate(lines, 1):
                for pattern, label in FORBIDDEN_PATTERNS:
                    if pattern.search(line):
                        rel = p.relative_to(ROOT).as_posix()
                        violations.append((rel, i, label, line.strip()[:100]))
                        break
        if violations:
            msg = "Legacy residue found:\n" + "\n".join(
                f"  {r}:{n}  [{label}]  {l}"
                for r, n, label, l in violations[:30]
            )
            if len(violations) > 30:
                msg += f"\n  ... and {len(violations) - 30} more"
            self.fail(msg)


if __name__ == "__main__":
    unittest.main()
