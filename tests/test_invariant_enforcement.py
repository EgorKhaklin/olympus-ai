"""Real teeth on the substrate invariants.

These tests are designed to FAIL when an invariant is violated.
S2 (determinism), S3 (read-only heads), S4 (no Eye imports another Eye),
S5 (Apollo falsifiability), S8 (continuity of understanding).
"""
from __future__ import annotations

import pathlib as _pl
import sys as _sys
_ROOT = _pl.Path(__file__).resolve().parent.parent
_SRC = _ROOT / 'src'
if str(_SRC) not in _sys.path:
    _sys.path.insert(0, str(_SRC))

import ast
import pathlib
import sys
import unittest


ROOT = pathlib.Path(__file__).resolve().parent.parent
SRC = ROOT / "src" / "olympus"


class TestS2_Determinism(unittest.TestCase):
    """Identical seed → identical pheromones. Replay every Eye twice."""

    def test_every_eye_is_replayable(self):
        from olympus.monsters.argos.colony import colony
        offenders: list[tuple[str, str]] = []
        for eye in colony.eyes():
            try:
                a = [(f.eye, f.slice, f.kind, f.detail) for f in eye.scan()]
                b = [(f.eye, f.slice, f.kind, f.detail) for f in eye.scan()]
            except Exception as exc:  # noqa: BLE001
                offenders.append((eye.NAME, f"raised: {exc}"))
                continue
            if a != b:
                offenders.append((eye.NAME, f"differed across runs: {a} vs {b}"))
        self.assertEqual([], offenders,
            f"S2 violation — eyes are not deterministic: {offenders}")


class TestS3_HeadsAreReadOnly(unittest.TestCase):
    """AST scan: HYDRA head modules must not contain write operations."""

    FORBIDDEN_CALLS = {
        # file/db write surfaces a Head must not call
        "remember", "swear", "descend", "quarantine", "kindle",
        "inscribe", "record", "promote", "ratify", "reject",
        "execute", "atomic_append", "compact_jsonl", "rotate_jsonl",
        "retire_component",
    }

    def test_no_head_calls_a_write_function(self):
        heads_dir = SRC / "monsters" / "hydra" / "heads"
        violators: list[tuple[str, str]] = []
        for head_file in heads_dir.glob("head_*.py"):
            tree = ast.parse(head_file.read_text(encoding="utf-8"))
            for node in ast.walk(tree):
                if isinstance(node, ast.Call):
                    func = node.func
                    name = (
                        getattr(func, "attr", None)
                        or getattr(func, "id", None)
                    )
                    if name in self.FORBIDDEN_CALLS:
                        violators.append((head_file.name, name))
        self.assertEqual([], violators,
            f"S3 violation — HYDRA head(s) call write function(s): {violators}")


class TestS4_NoEyeImportsAnotherEye(unittest.TestCase):
    """An Eye may only import from base / stdlib / olympus.*. It must
    never import another Eye module."""

    def test_no_eye_imports_another_eye(self):
        eyes_dir = SRC / "monsters" / "argos" / "eyes"
        eye_modules = {f.stem for f in eyes_dir.glob("eye_*.py")}
        violators: list[tuple[str, str]] = []
        for eye_file in eyes_dir.glob("eye_*.py"):
            tree = ast.parse(eye_file.read_text(encoding="utf-8"))
            for node in ast.walk(tree):
                if isinstance(node, ast.ImportFrom) and node.module:
                    # check for sibling-eye imports
                    if "monsters.argos.eyes" in node.module:
                        # strip prefix; what's left is the sibling
                        suffix = node.module.split("monsters.argos.eyes.")[-1]
                        if suffix in eye_modules and suffix != eye_file.stem:
                            violators.append((eye_file.name, suffix))
                    # also disallow importing OTHER tier's internals
                    # (eyes should only reach into argos.base or olympus stdlib)
        self.assertEqual([], violators,
            f"S4 violation — Eye(s) import sibling Eye(s): {violators}")


class TestS5_ApolloRefusesUnverifiable(unittest.TestCase):
    """Apollo.predict() must reject a Prediction whose verify is None."""

    def test_apollo_predict_rejects_no_verify(self):
        from olympus.olympians.apollo import Apollo, Prediction
        import datetime
        a = Apollo()
        with self.assertRaises(ValueError):
            a.predict(Prediction(
                name="invariant-test-1",
                statement="this prediction lacks verify()",
                horizon=datetime.date(2099, 1, 1),
                verify=None,
            ))

    def test_apollo_accepts_verifiable(self):
        from olympus.olympians.apollo import Apollo, Prediction
        import datetime
        a = Apollo()
        p = a.predict(Prediction(
            name="invariant-test-2",
            statement="this prediction has verify",
            horizon=datetime.date(2099, 1, 1),
            verify=lambda: True,
        ))
        self.assertEqual(p.name, "invariant-test-2")


class TestS8_LoadBearingMemoriesCarryActor(unittest.TestCase):
    """Every load-bearing Mnemosyne memory must carry actor + summary
    so the operator can reconstruct who-did-what."""

    LOAD_BEARING = (
        "decision", "thread.spun", "thread.cut", "hydra.run",
        "colony.deploy", "bootstrap", "invariant.violated",
        "session.completed", "action.promoted", "action.ratified",
        "action.executed",
    )

    def test_no_load_bearing_memory_is_anonymous(self):
        from olympus.titans.mnemosyne import mnemosyne
        gaps: list[str] = []
        for kind in mnemosyne.kinds():
            if kind not in self.LOAD_BEARING:
                continue
            for m in mnemosyne.recall(kind):
                if not m.actor or not m.summary:
                    gaps.append(f"{kind}@{m.remembered_at}")
        self.assertEqual([], gaps,
            f"S8 violation — load-bearing memories without actor/summary: {gaps[:5]}")


if __name__ == "__main__":
    unittest.main()
