"""Heracles — strongest of mortal heroes, completer of twelve labors.

Heracles was set twelve impossible tasks by King Eurystheus. He
completed every one. In Olympus, Heracles is the kill-test runner:
a battery of twelve adversarial scenarios, each meant to break a
specific substrate invariant. A run is successful only when all
twelve are completed without breakage.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, Any


@dataclass
class Labor:
    """One of the twelve. Named after the original myth."""
    number: int
    name: str            # canonical name (e.g., "Nemean Lion")
    target: str          # which Olympus surface this attacks
    fn: Callable[[], bool]   # runner; True = survived, False = broke


@dataclass
class Verdict:
    labor: Labor
    survived: bool
    detail: str


class Heracles:
    """The twelve-labor kill-test runner."""

    def __init__(self) -> None:
        self._labors: dict[int, Labor] = {}

    def assign(self, labor: Labor) -> None:
        """Register a labor. Number must be 1..12."""
        if not 1 <= labor.number <= 12:
            raise ValueError(f"labor number must be 1..12; got {labor.number}")
        self._labors[labor.number] = labor

    def perform(self) -> list[Verdict]:
        """Run all assigned labors. Returns one Verdict per labor."""
        verdicts: list[Verdict] = []
        for n in range(1, 13):
            labor = self._labors.get(n)
            if labor is None:
                continue
            try:
                survived = bool(labor.fn())
                detail = "survived" if survived else "broke"
            except Exception as exc:
                survived = False
                detail = f"raised: {type(exc).__name__}: {exc}"
            verdicts.append(Verdict(labor=labor, survived=survived, detail=detail))
        return verdicts


heracles = Heracles()


# The canonical twelve labors. Each is a real substrate kill-test:
# survives iff the substrate's promise still holds in code.


def _labor_nemean_lion() -> bool:
    """HYDRA must have eight mortal heads + one immortal."""
    from olympus.monsters.hydra import hydra
    heads = hydra.heads()
    mortal = sum(1 for h in heads if not h.IMMORTAL)
    immortal = sum(1 for h in heads if h.IMMORTAL)
    return mortal == 8 and immortal == 1


def _labor_lernaean_hydra() -> bool:
    """HYDRA must observe — beheading produces ≥1 finding from every head."""
    from olympus.monsters.hydra import hydra
    report = hydra.behead()
    return all(len(report.by_head.get(h.NAME, [])) >= 1 for h in hydra.heads())


def _labor_ceryneian_hind() -> bool:
    """Artemis's quiver must record + summarize percentiles."""
    from olympus.olympians.artemis import Artemis
    a = Artemis(capacity=100)
    for v in range(1, 101):
        a.mark("labor.hind", float(v))
    s = a.quiver("labor.hind").summary()
    return 45 < s["p50"] < 55 and s["count"] == 100


def _labor_erymanthian_boar() -> bool:
    """Ares must accept and run a registered assault end-to-end."""
    from olympus.olympians.ares import Ares
    a = Ares()
    a.declare_war(
        name="labor.boar",
        description="trivial refusal",
        fn=lambda: (_ for _ in ()).throw(RuntimeError("refused")),
        expected_outcome="raised",
    )
    return a.battle("labor.boar")["verdict"] == "passed"


def _labor_augean_stables() -> bool:
    """Lethe must forget what's been written after its TTL."""
    import time
    from olympus.underworld.lethe import Lethe
    l = Lethe()
    l.forget("labor.augean", "muck", ttl=0.01)
    time.sleep(0.05)
    return l.remembered("labor.augean") is None


def _labor_stymphalian_birds() -> bool:
    """Argos must deploy and produce at least one pheromone per registered eye."""
    from olympus.monsters.argos.colony import colony
    census = colony.deploy()
    return census.count >= len(colony.eyes())


def _labor_cretan_bull() -> bool:
    """Poseidon's pub/sub must deliver events to subscribers in order."""
    from olympus.olympians.poseidon import Poseidon
    p = Poseidon()
    received: list[int] = []
    p.subscribe("labor.bull", lambda e: received.append(e))
    for i in range(5):
        p.publish("labor.bull", i)
    return received == [0, 1, 2, 3, 4]


def _labor_mares_of_diomedes() -> bool:
    """Atropos must end a thread cleanly and record it in Mnemosyne."""
    from olympus.fates.atropos import atropos
    from olympus.titans.mnemosyne import mnemosyne
    cleanup_ran = []
    atropos.cut("labor.mares", cleanup=lambda: cleanup_ran.append(True),
                reason="labor-test")
    cuts = mnemosyne.recall("thread.cut")
    return cleanup_ran == [True] and any(
        c.body.get("thread_id") == "labor.mares" for c in cuts
    )


def _labor_belt_of_hippolyta() -> bool:
    """Hera must record bindings as append-only and read them back."""
    from olympus.olympians.hera import hera
    b = hera.bind(name="labor.belt", left="left", right="right",
                  role="labor-binding")
    bindings = hera.bindings()
    return any(x.name == "labor.belt" and x.left == "left" for x in bindings)


def _labor_cattle_of_geryon() -> bool:
    """Demeter must accumulate then reap a harvest."""
    from olympus.olympians.demeter import Demeter
    d = Demeter()
    for v in range(10):
        d.gather("labor.geryon", v)
    h = d.reap("labor.geryon")
    return h.size == 10


def _labor_apples_of_hesperides() -> bool:
    """Apollo MUST refuse a prediction without verify() (S5 invariant)."""
    from olympus.olympians.apollo import Apollo, Prediction
    import datetime
    a = Apollo()
    try:
        a.predict(Prediction(
            name="labor.apples",
            statement="this prediction has no verify()",
            horizon=datetime.date(2099, 1, 1),
            verify=None,
        ))
        return False  # accepted what S5 forbids
    except ValueError:
        return True


def _labor_cerberus() -> bool:
    """Cerberus must refuse a caller who fails any of three heads."""
    from olympus.monsters.cerberus import Cerberus, Gate
    c = Cerberus()
    c.post(Gate(
        name="labor.cerberus",
        authenticate=lambda caller: caller == "valid",
        authorize=lambda caller: True,
        verify=lambda payload: True,
    ))
    good = c.admit("labor.cerberus", "valid").allowed
    bad = c.admit("labor.cerberus", "intruder").allowed
    return good is True and bad is False


CANONICAL_LABORS = [
    Labor(1,  "Nemean Lion",          "monsters/hydra",           _labor_nemean_lion),
    Labor(2,  "Lernaean Hydra",       "monsters/hydra",           _labor_lernaean_hydra),
    Labor(3,  "Ceryneian Hind",       "olympians/artemis",        _labor_ceryneian_hind),
    Labor(4,  "Erymanthian Boar",     "olympians/ares",           _labor_erymanthian_boar),
    Labor(5,  "Augean Stables",       "underworld/lethe",         _labor_augean_stables),
    Labor(6,  "Stymphalian Birds",    "monsters/argos",           _labor_stymphalian_birds),
    Labor(7,  "Cretan Bull",          "olympians/poseidon",       _labor_cretan_bull),
    Labor(8,  "Mares of Diomedes",    "fates/atropos",            _labor_mares_of_diomedes),
    Labor(9,  "Belt of Hippolyta",    "olympians/hera",           _labor_belt_of_hippolyta),
    Labor(10, "Cattle of Geryon",     "olympians/demeter",        _labor_cattle_of_geryon),
    Labor(11, "Apples of Hesperides", "olympians/apollo",         _labor_apples_of_hesperides),
    Labor(12, "Cerberus",             "monsters/cerberus",        _labor_cerberus),
]
