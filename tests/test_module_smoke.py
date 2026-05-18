"""Smoke tests — every implemented Olympus module imports and its
public interface is exercisable.

If a god is registered in PANTHEON.md but a typo broke its imports,
this fails."""
from __future__ import annotations

import sys
import pathlib
import unittest

ROOT = pathlib.Path(__file__).resolve().parent.parent
if str(ROOT / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "src"))


class TestPrimordials(unittest.TestCase):
    def test_chaos_is_void(self):
        from olympus.primordials.chaos import Chaos, void, is_void
        self.assertIs(Chaos(), Chaos())  # singleton
        self.assertTrue(is_void(void))
        self.assertFalse(bool(void))

    def test_gaia_resolves_root(self):
        from olympus.primordials.gaia import root
        self.assertTrue(root.root.is_dir())
        self.assertTrue(root.exists("codex/COSMOGONY.md"))

    def test_eros_is_deterministic(self):
        from olympus.primordials.eros import Eros
        self.assertEqual(Eros.begotten_id("x", "s"), Eros.begotten_id("x", "s"))


class TestTitans(unittest.TestCase):
    def test_themis_lists_eight(self):
        from olympus.titans.themis import themis
        self.assertEqual(len(themis.all()), 8)
        for i in range(1, 9):
            self.assertIsNotNone(themis.by_id(f"S{i}"))

    def test_cronus_has_cadences(self):
        from olympus.titans.cronus import cronus
        for name in ("moment", "hour", "day", "week"):
            self.assertIsNotNone(cronus.cadence(name))

    def test_hyperion_counters(self):
        from olympus.titans.hyperion import hyperion
        v = hyperion.incr("test.smoke")
        self.assertEqual(hyperion.incr("test.smoke"), v + 1)

    def test_iapetus_lifecycle_refuses_regression(self):
        from olympus.titans.iapetus import iapetus, LifecyclePhase
        lc = iapetus.register("smoke-test-component")
        lc.advance_to(LifecyclePhase.NASCENT)
        lc.advance_to(LifecyclePhase.ACTIVE)
        with self.assertRaises(ValueError):
            lc.advance_to(LifecyclePhase.NASCENT)


class TestOlympians(unittest.TestCase):
    def test_aphrodite_table_renders(self):
        from olympus.olympians.aphrodite import aphrodite
        out = aphrodite.table(("a", "b"), [("1", "2"), ("3", "4")])
        self.assertIn("a", out)
        self.assertIn("3", out)

    def test_hermes_dispatch_with_no_errands_returns_help(self):
        from olympus.olympians.hermes import Hermes
        h = Hermes()
        # Empty argv → help → returns 0
        self.assertEqual(h.dispatch([]), 0)

    def test_artemis_records_percentiles(self):
        from olympus.olympians.artemis import Artemis
        a = Artemis(capacity=10)
        for v in [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]:
            a.mark("smoke", v)
        q = a.quiver("smoke")
        self.assertIsNotNone(q)
        self.assertAlmostEqual(q.percentile(50), 5.5, delta=0.5)

    def test_athena_composes_and_recalls(self):
        from olympus.olympians.athena import athena
        athena.compose("smoke-label", findings=[{"x": 1}], recommendations=["do y"])
        latest = athena.latest("smoke-label")
        self.assertIsNotNone(latest)
        self.assertIn("do y", latest.recommendations)


class TestUnderworld(unittest.TestCase):
    def test_styx_swears_and_verifies(self):
        from olympus.underworld.styx import styx
        oath = styx.swear("test", "smoke oath")
        self.assertEqual(oath.seq, oath.seq)  # exists
        intact, _ = styx.verify()
        self.assertTrue(intact, "Fresh chain must verify intact")

    def test_lethe_forgets_after_zero_ttl(self):
        from olympus.underworld.lethe import lethe
        lethe.forget("smoke-key", "value", ttl=0.001)
        import time; time.sleep(0.01)
        self.assertIsNone(lethe.remembered("smoke-key"))

    def test_persephone_cycle(self):
        from olympus.underworld.persephone import Cycle, persephone
        c = persephone.cycle(Cycle("smoke", 6, 6))
        self.assertIn(c.state_at(), {"above", "below"})


class TestFatesFuriesGracesMuses(unittest.TestCase):
    def test_clotho_spins(self):
        from olympus.fates.clotho import spin
        t = spin("smoke", spun_for="test", seed="fixed")
        self.assertTrue(t.id.startswith("smoke-"))

    def test_lachesis_caps(self):
        from olympus.fates.lachesis import lachesis, Quota
        lachesis.allot(Quota("smoke-q", ceiling=10.0))
        self.assertTrue(lachesis.measure("smoke-q", 5.0))
        self.assertTrue(lachesis.measure("smoke-q", 5.0))
        self.assertFalse(lachesis.measure("smoke-q", 0.01))

    def test_alecto_raises_alert(self):
        from olympus.furies.alecto import alecto
        a = alecto.raise_alert("S1", "smoke alert")
        self.assertEqual(a.invariant_id, "S1")

    def test_aglaia_crowns(self):
        from olympus.graces.aglaia import aglaia
        out = aglaia.crown("smoke")
        self.assertIn("smoke", out)

    def test_clio_writes_a_journal_line(self):
        from olympus.muses.clio import clio
        f = clio.inscribe("smoke", "test inscription")
        self.assertTrue(f.exists())

    def test_polyhymnia_composes_hymn(self):
        from olympus.muses.polyhymnia import polyhymnia
        hymn = polyhymnia.hymn()
        self.assertGreaterEqual(hymn.total_oaths, 0)


class TestHeroes(unittest.TestCase):
    def test_heracles_performs(self):
        from olympus.heroes.heracles import Heracles, Labor
        h = Heracles()
        h.assign(Labor(1, "smoke labor", "tests", lambda: True))
        verdicts = h.perform()
        self.assertTrue(any(v.survived for v in verdicts))

    def test_momus_catalog_has_eight(self):
        from olympus.heroes.momus import momus
        self.assertEqual(len(momus.catalog()), 8)
        for i in range(1, 9):
            self.assertIsNotNone(momus.by_id(f"AP{i}"))

    def test_theseus_explores(self):
        from olympus.heroes.theseus import theseus
        # theseus.explore on an existing tier returns at least one module
        out = theseus.explore("primordials")
        self.assertGreater(len(out), 0)


class TestMonsters(unittest.TestCase):
    def test_sphinx_riddle_roundtrip(self):
        from olympus.monsters.sphinx import sphinx
        r = sphinx.pose("What walks on four legs in the morning?", "man")
        self.assertTrue(sphinx.solve(r, "man"))
        self.assertFalse(sphinx.solve(r, "lion"))

    def test_cerberus_three_heads(self):
        from olympus.monsters.cerberus import cerberus, Gate
        cerberus.post(Gate(
            name="smoke-gate",
            authenticate=lambda c: c == "ok",
            authorize=lambda c: True,
            verify=lambda p: True,
        ))
        self.assertTrue(cerberus.admit("smoke-gate", "ok").allowed)
        self.assertFalse(cerberus.admit("smoke-gate", "bad").allowed)

    def test_minotaur_caps_depth(self):
        from olympus.monsters.minotaur import Minotaur, MinotaurDepthExceeded
        m = Minotaur(max_depth=3)
        # Build a structure deep enough to trip the cap
        deep = {"a": {"b": {"c": {"d": {"e": 1}}}}}
        with self.assertRaises(MinotaurDepthExceeded):
            list(m.descend(deep))

    def test_typhon_names_scenarios(self):
        from olympus.monsters.typhon import typhon
        self.assertGreater(len(typhon.scenarios()), 0)
        self.assertIsNotNone(typhon.by_name("styx-broken"))


if __name__ == "__main__":
    unittest.main()
