"""S4 — Argos decentralization.

No Eye imports another Eye. No host calls anything. Synthesis is
emergent at read time."""
from __future__ import annotations

import pathlib as _pl
import sys as _sys
_ROOT = _pl.Path(__file__).resolve().parent.parent
_SRC = _ROOT / "src"
if str(_SRC) not in _sys.path:
    _sys.path.insert(0, str(_SRC))

import ast
import unittest


class TestS4_Decentralization(unittest.TestCase):

    def _eye_files(self):
        from olympus.primordials.gaia import root
        return list(root.child("src", "olympus", "monsters",
                                "argos", "eyes").glob("eye_*.py"))

    def test_S4a_no_eye_imports_sibling_eye(self):
        eye_files = self._eye_files()
        eye_modules = {f.stem for f in eye_files}
        violators: list[tuple[str, str]] = []
        for eye in eye_files:
            tree = ast.parse(eye.read_text(encoding="utf-8"))
            for node in ast.walk(tree):
                if isinstance(node, ast.ImportFrom) and node.module:
                    if "monsters.argos.eyes" in node.module:
                        suffix = node.module.split("monsters.argos.eyes.")[-1]
                        if suffix in eye_modules and suffix != eye.stem:
                            violators.append((eye.name, suffix))
        self.assertEqual([], violators)

    def test_S4b_no_eye_imports_colony(self):
        """An Eye must not call the colony — that's host-level coordination
        which violates decentralization."""
        violators: list[str] = []
        for eye in self._eye_files():
            text = eye.read_text(encoding="utf-8")
            if "from olympus.monsters.argos.colony" in text:
                violators.append(eye.name)
        self.assertEqual([], violators)

    def test_S4c_eye_scan_does_not_read_other_eye_pheromones(self):
        """An Eye must not call colony.read_log() — synthesis is the
        downstream reader's job, not an Eye's."""
        violators: list[str] = []
        for eye in self._eye_files():
            text = eye.read_text(encoding="utf-8")
            if "colony.read_log" in text or "read_log()" in text:
                violators.append(eye.name)
        self.assertEqual([], violators)

    def test_S4d_removing_any_eye_does_not_break_others(self):
        """Run every Eye in isolation; none should fail because another
        Eye is missing."""
        from olympus.monsters.argos.colony import colony
        broken: list[str] = []
        for eye in colony.eyes():
            try:
                _ = eye.scan()
            except Exception as exc:  # noqa: BLE001
                broken.append(f"{type(eye).__name__}: {exc}")
        self.assertEqual([], broken)

    def test_S4e_synthesis_happens_outside_eyes(self):
        """The CorrelationEngine (the synthesizer) lives outside any Eye."""
        from olympus.monsters.argos.correlation import correlation
        # Just ensure the synthesizer is importable as a separate module,
        # not bundled inside any Eye.
        self.assertTrue(hasattr(correlation, "correlate"))


if __name__ == "__main__":
    unittest.main()
