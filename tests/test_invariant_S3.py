"""S3 — HYDRA heads are read-only.

A Head observes; it never mutates. AST-level + runtime-level enforcement.
"""
from __future__ import annotations

import pathlib as _pl
import sys as _sys
_ROOT = _pl.Path(__file__).resolve().parent.parent
_SRC = _ROOT / "src"
if str(_SRC) not in _sys.path:
    _sys.path.insert(0, str(_SRC))

import ast
import unittest


FORBIDDEN_CALLS = {
    "remember", "swear", "descend", "quarantine", "kindle",
    "inscribe", "record", "promote", "ratify", "reject", "execute",
    "atomic_append", "compact_jsonl", "rotate_jsonl", "retire_component",
    "predict", "compose", "compose_from", "propose", "transform", "bind",
}


class TestS3_HeadsAreReadOnly(unittest.TestCase):

    def _head_files(self):
        from olympus.primordials.gaia import root
        return list(root.child("src", "olympus", "monsters",
                                "hydra", "heads").glob("head_*.py"))

    def test_S3a_no_head_calls_a_write_function(self):
        violators: list[tuple[str, str]] = []
        for head in self._head_files():
            tree = ast.parse(head.read_text(encoding="utf-8"))
            for node in ast.walk(tree):
                if isinstance(node, ast.Call):
                    func = node.func
                    name = (
                        getattr(func, "attr", None)
                        or getattr(func, "id", None)
                    )
                    if name in FORBIDDEN_CALLS:
                        violators.append((head.name, name))
        self.assertEqual([], violators)

    def test_S3b_no_head_opens_file_for_write(self):
        """A Head must not call open(..., 'w'/'a'/'x')."""
        violators: list[tuple[str, str]] = []
        for head in self._head_files():
            tree = ast.parse(head.read_text(encoding="utf-8"))
            for node in ast.walk(tree):
                if isinstance(node, ast.Call):
                    name = getattr(node.func, "id", None) or getattr(node.func, "attr", None)
                    if name == "open":
                        # check second positional or 'mode' keyword
                        if len(node.args) >= 2 and isinstance(node.args[1], ast.Constant):
                            mode = node.args[1].value
                            if any(c in str(mode) for c in ("w", "a", "x")):
                                violators.append((head.name, f"open(..., {mode!r})"))
                        for kw in node.keywords:
                            if kw.arg == "mode" and isinstance(kw.value, ast.Constant):
                                if any(c in str(kw.value.value) for c in ("w", "a", "x")):
                                    violators.append((head.name, f"open(mode={kw.value.value!r})"))
        self.assertEqual([], violators)

    def test_S3c_observe_returns_findings_list(self):
        """Every Head's observe() returns a list (possibly empty) of HeadFindings.
        Negative test: a Head returning None would violate the contract."""
        from olympus.monsters.hydra import hydra
        from olympus.monsters.hydra.head import HeadFinding
        for h in hydra.heads():
            result = h.observe()
            self.assertIsInstance(result, list,
                f"{h.NAME}.observe() must return a list; got {type(result)}")
            for f in result:
                self.assertIsInstance(f, HeadFinding,
                    f"{h.NAME} returned non-HeadFinding: {type(f)}")

    def test_S3d_calling_observe_does_not_change_substrate(self):
        """A Head should produce the same findings when called twice in a row
        with no intervening substrate change."""
        from olympus.monsters.hydra import hydra
        for h in hydra.heads():
            if h.IMMORTAL:
                # The immortal head READS Mnemosyne — its findings depend on
                # whether the prior hydra.behead() ran in this process.
                # Skip the immortal for this specific check.
                continue
            a = [(f.slice, f.severity, f.detail) for f in h.observe()]
            b = [(f.slice, f.severity, f.detail) for f in h.observe()]
            self.assertEqual(a, b,
                f"{h.NAME}.observe() returned different findings on consecutive calls")

    def test_S3e_no_head_imports_action_or_session(self):
        """A Head must not import the action queue or session runner —
        both of which mutate state."""
        violators: list[tuple[str, str]] = []
        for head in self._head_files():
            text = head.read_text(encoding="utf-8")
            if "from olympus.action" in text or "from olympus.session" in text:
                violators.append((head.name, "imports action or session"))
        self.assertEqual([], violators)


if __name__ == "__main__":
    unittest.main()
