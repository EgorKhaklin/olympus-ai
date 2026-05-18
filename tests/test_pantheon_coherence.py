"""Pantheon coherence — every named god in PANTHEON.md exists; every
module under the cosmogonic tiers is named in PANTHEON.md.

These tests are the substrate's own self-audit. Run them before any
ship that adds, renames, or removes a god."""
from __future__ import annotations

import re
import sys
import pathlib
import unittest

# Make repo root importable
ROOT = pathlib.Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


# Names that PANTHEON.md asserts exist as Python modules in the tier.
# Drawn from PANTHEON.md tables; if you add a god, update both.
EXPECTED = {
    "primordials": ["chaos", "gaia", "nyx", "eros", "tartarus"],
    "titans":      ["mnemosyne", "themis", "cronus", "hyperion",
                    "rhea", "oceanus", "iapetus", "coeus"],
    "olympians":   ["zeus", "hera", "poseidon", "demeter", "athena",
                    "artemis", "ares", "aphrodite", "hephaestus",
                    "hermes", "dionysus", "hestia"],
    "underworld":  ["hades", "persephone", "hecate", "styx", "lethe"],
    "fates":       ["clotho", "lachesis", "atropos"],
    "furies":      ["alecto", "megaera", "tisiphone"],
    "graces":      ["aglaia", "euphrosyne", "thalia"],
    "muses":       ["calliope", "clio", "erato", "euterpe", "melpomene",
                    "polyhymnia", "terpsichore", "thalia_muse", "urania"],
    "heroes":      ["heracles", "perseus", "theseus", "odysseus",
                    "orpheus", "atalanta", "momus"],
    "monsters":    ["cerberus", "sphinx", "medusa", "chimera",
                    "minotaur", "typhon"],
}


class TestPantheonCoherence(unittest.TestCase):
    """Each expected module exists on disk in the right tier."""

    def test_every_god_has_a_module(self):
        missing: list[tuple[str, str]] = []
        for tier, names in EXPECTED.items():
            for name in names:
                p = ROOT / tier / f"{name}.py"
                if not p.exists():
                    missing.append((tier, name))
        self.assertEqual([], missing,
            f"Pantheon-coherence: gods declared in PANTHEON.md but missing on disk: {missing}")

    def test_pantheon_doc_mentions_every_god(self):
        pantheon_md = (ROOT / "PANTHEON.md").read_text(encoding="utf-8")
        missing: list[str] = []
        for names in EXPECTED.values():
            for name in names:
                pretty = name.replace("_muse", "")
                pattern = rf"\b{re.escape(pretty)}\b"
                if not re.search(pattern, pantheon_md, re.IGNORECASE):
                    missing.append(name)
        self.assertEqual([], missing,
            f"Pantheon-coherence: gods on disk but not mentioned in PANTHEON.md: {missing}")

    def test_apollo_is_a_subpackage(self):
        apollo = ROOT / "olympians" / "apollo"
        self.assertTrue(apollo.exists() and apollo.is_dir(),
            "Apollo lives as a subpackage at olympians/apollo/")
        self.assertTrue((apollo / "__init__.py").exists(),
            "Apollo subpackage needs __init__.py")

    def test_hydra_has_heads_dir(self):
        heads = ROOT / "monsters" / "hydra" / "heads"
        self.assertTrue(heads.exists() and heads.is_dir())
        head_files = sorted(f.name for f in heads.glob("head_*.py"))
        self.assertGreaterEqual(len(head_files), 9,
            f"HYDRA must have at least 9 mortal heads; found {len(head_files)}: {head_files}")

    def test_argos_has_four_subtiers(self):
        argos = ROOT / "monsters" / "argos"
        for sub in ("eyes", "satyrs", "demes", "phalanges"):
            self.assertTrue((argos / sub).is_dir(),
                f"Argos must have {sub}/ subdir")


if __name__ == "__main__":
    unittest.main()
