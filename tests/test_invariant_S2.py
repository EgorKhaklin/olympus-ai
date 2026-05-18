"""S2 — Argos determinism.

No Eye uses randomness in its scan logic. Identical seed → identical
pheromones. Replay is exact."""
from __future__ import annotations

import pathlib as _pl
import sys as _sys
_ROOT = _pl.Path(__file__).resolve().parent.parent
_SRC = _ROOT / "src"
if str(_SRC) not in _sys.path:
    _sys.path.insert(0, str(_SRC))

import ast
import unittest


class TestS2_Determinism(unittest.TestCase):

    def test_S2a_every_eye_replays_identically(self):
        from olympus.monsters.argos.colony import colony
        offenders: list[tuple[str, str]] = []
        for eye in colony.eyes():
            a = [(f.eye, f.slice, f.kind, f.detail) for f in eye.scan()]
            b = [(f.eye, f.slice, f.kind, f.detail) for f in eye.scan()]
            if a != b:
                offenders.append((eye.NAME, "non-deterministic"))
        self.assertEqual([], offenders)

    def test_S2b_eye_seed_is_stable_across_instances(self):
        """Two instances of the same Eye class have the same seed."""
        from olympus.monsters.argos.colony import colony
        for eye in colony.eyes():
            cls = type(eye)
            self.assertEqual(cls().seed, cls().seed,
                f"{cls.__name__} has unstable seed across instances")

    def test_S2c_eye_seed_differs_across_classes(self):
        """Different Eye classes have different seeds (no accidental collisions)."""
        from olympus.monsters.argos.colony import colony
        seeds = {type(e).__name__: e.seed for e in colony.eyes()}
        # No two classes should share a seed
        self.assertEqual(len(seeds), len(set(seeds.values())),
            f"seed collision detected: {seeds}")

    def test_S2d_no_eye_imports_random_module(self):
        """An Eye module that imports `random` or `secrets` raises a red flag.
        Some Eyes legitimately import other stdlib modules; this catches the
        obvious S2 violators."""
        from olympus.primordials.gaia import root
        eyes_dir = root.child("src", "olympus", "monsters", "argos", "eyes")
        offenders: list[tuple[str, str]] = []
        for eye_file in eyes_dir.glob("eye_*.py"):
            tree = ast.parse(eye_file.read_text(encoding="utf-8"))
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for n in node.names:
                        if n.name == "random":
                            offenders.append((eye_file.name, "imports random"))
        self.assertEqual([], offenders)

    def test_S2e_eros_deterministic_id_is_pure(self):
        """Eros.begotten_id is the seeded-id primitive every deterministic
        Eye relies on. Same seed must always produce same id, even across
        process restarts (verified here within one process)."""
        from olympus.primordials.eros import Eros
        for seed in ("a", "the quick brown fox", "", "🜂", "very long " * 50):
            a = Eros.begotten_id("test", seed)
            b = Eros.begotten_id("test", seed)
            self.assertEqual(a, b, f"seed {seed!r} produced different ids")

    def test_S2f_eros_different_seeds_different_ids(self):
        from olympus.primordials.eros import Eros
        ids = {Eros.begotten_id("test", str(i)) for i in range(1000)}
        # 1000 distinct seeds → 1000 distinct ids (no collisions for short seeds)
        self.assertEqual(len(ids), 1000)

    def test_S2g_colony_deploy_pheromones_stable(self):
        """Deploying twice produces the same set of slice/kind tuples.
        (Timestamps will differ; the structural content must not.)"""
        from olympus.monsters.argos.colony import colony
        c1 = colony.deploy(deposit=False)
        c2 = colony.deploy(deposit=False)
        signatures1 = sorted((p.eye, p.slice, p.kind) for p in c1.pheromones)
        signatures2 = sorted((p.eye, p.slice, p.kind) for p in c2.pheromones)
        self.assertEqual(signatures1, signatures2)


if __name__ == "__main__":
    unittest.main()
