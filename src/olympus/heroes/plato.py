"""Plato — philosopher of the five regular solids.

In history: Plato (5th-4th century BCE) described the five regular
convex polyhedra in *Timaeus*. Each was associated with a classical
element. The mapping has held in mathematics ever since:

  Tetrahedron   (4 vertices)  — fire
  Cube          (8 vertices)  — earth
  Octahedron    (6 vertices)  — air
  Dodecahedron  (12 vertices) — cosmos (the universe itself)
  Icosahedron   (20 vertices) — water

In Olympus, Plato is the **five-solid taxonomy of substrate work**.
This is a *second navigational axis* through the pantheon, orthogonal
to the existing tier structure. Tier asks *"what kind of figure is
this?"* (Olympian, Titan, Hero, …). Function asks *"what does this
figure do?"* (observation, state, reasoning, authority, execution).

The mapping is **hand-maintained**, like Daedalus's `_COGNITIVE_FLOW`
edge list. Drift between this taxonomy and the actual modules is a
Hephaestus signal; the taxonomy should be updated when functions
change.

Per Delphi 2026-05-18-phi-arc.md.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Solid:
    """One of the five Platonic solids."""
    name: str             # 'tetrahedron' / 'cube' / ...
    vertices: int
    element: str          # 'fire' / 'earth' / 'air' / 'cosmos' / 'water'
    function: str         # 'observation' / 'state' / 'reasoning' / ...
    description: str


SOLIDS: tuple[Solid, ...] = (
    Solid(
        name="tetrahedron", vertices=4, element="fire",
        function="observation",
        description=("the watchers — figures that observe substrate "
                     "state and emit findings without mutating it"),
    ),
    Solid(
        name="cube", vertices=8, element="earth",
        function="state",
        description=("the keepers — figures that hold the substrate's "
                     "ground truth: append-only ledgers, queues, bindings"),
    ),
    Solid(
        name="octahedron", vertices=6, element="air",
        function="reasoning",
        description=("the thinkers — figures that read observations and "
                     "ground truth, then produce briefs, proposals, "
                     "and hindsights"),
    ),
    Solid(
        name="dodecahedron", vertices=12, element="cosmos",
        function="authority",
        description=("the deciders — figures that ratify, refuse, "
                     "panic, heal, or otherwise carry constitutional "
                     "authority"),
    ),
    Solid(
        name="icosahedron", vertices=20, element="water",
        function="execution",
        description=("the actors — figures that turn ratified decisions "
                     "into observable change, plus the surfaces that "
                     "let outside observers read the substrate"),
    ),
)


# ─────────────────────────────────────────────────────────
# The canonical figure → solid mapping. Hand-maintained.
# When a new figure is added or a figure's function changes, this
# list updates. Drift is a Hephaestus signal.
# ─────────────────────────────────────────────────────────


_FIGURE_TO_SOLID: dict[str, str] = {
    # ─── Tetrahedron — observation ────────────────────────
    "hydra":      "tetrahedron",
    "argos":      "tetrahedron",
    "alecto":     "tetrahedron",    # Fury — observation-level
    "megaera":    "tetrahedron",
    "tisiphone":  "tetrahedron",
    "pythia":     "tetrahedron",    # observes the world

    # ─── Cube — state (ground truth) ──────────────────────
    "mnemosyne":  "cube",
    "styx":       "cube",
    "atlas":      "cube",
    "charon":     "cube",
    "hades":      "cube",
    "hera":       "cube",           # bindings registry
    "iapetus":    "cube",           # lifecycle state machine
    "lethe":      "cube",           # ephemeral cache
    "cronus":     "cube",           # calendar / scheduling cadence = state
    "oceanus":    "cube",           # I/O boundary = state

    # ─── Octahedron — reasoning ───────────────────────────
    "athena":     "octahedron",
    "hephaestus": "octahedron",
    "momus":      "octahedron",     # anti-architect = reasoning
    "epimetheus": "octahedron",
    "cassandra":  "octahedron",
    "nemesis":    "octahedron",     # counterfactual reasoner
    "ariadne":    "octahedron",     # causal-chain reasoner
    "coeus":      "octahedron",     # investigation

    # ─── Dodecahedron — authority ─────────────────────────
    "zeus":       "dodecahedron",
    "themis":     "dodecahedron",
    "pan":        "dodecahedron",   # circuit breaker = authority
    "asclepius":  "dodecahedron",   # healer
    "metis":      "dodecahedron",   # advisor
    "daedalus":   "dodecahedron",   # cartographer of authority
    "hecate":     "dodecahedron",   # crossroads = authority of recovery
    "persephone": "dodecahedron",   # cyclical authority
    "hestia":     "dodecahedron",   # hearth — identity seal
    "rhea":       "dodecahedron",   # bootstrap — bringing-forth authority
    "pythagoras": "dodecahedron",   # numerical authority
    "plato":      "dodecahedron",   # this very taxonomy
    "hygieia":    "dodecahedron",   # wellness authority (cohesion)
    "phoenix":    "dodecahedron",   # cyclical-renewal authority

    # ─── Icosahedron — execution + presentation ───────────
    "prometheus": "icosahedron",    # bounded auto-improver
    "castor":     "icosahedron",    # shadow runner
    "pollux":     "icosahedron",    # comparator
    "iris":       "icosahedron",    # presentation
    "hermes":     "icosahedron",    # CLI dispatch / messenger
    "hyperion":   "icosahedron",    # observability emit
    "demeter":    "icosahedron",    # batch ingestion
    "poseidon":   "icosahedron",    # data flow
    "apollo":     "icosahedron",    # prophecy verification
    "artemis":    "icosahedron",    # precision metrics
    "ares":       "icosahedron",    # adversarial assault
    "aphrodite":  "icosahedron",    # terminal aesthetics
    "dionysus":   "icosahedron",    # state transitions
    "heracles":   "icosahedron",    # twelve labors
    "perseus":    "icosahedron",    # reflection persona
    "theseus":    "icosahedron",    # brain-map
    "odysseus":   "icosahedron",    # session-resume
    "orpheus":    "icosahedron",    # archive retrieval
    "atalanta":   "icosahedron",    # benchmark runner
    "calliope":   "icosahedron",    # epic poetry
    "clio":       "icosahedron",    # history writer
    "erato":      "icosahedron",    # love
    "euterpe":    "icosahedron",    # music
    "melpomene":  "icosahedron",    # tragedy
    "polyhymnia": "icosahedron",    # sacred hymns
    "terpsichore":"icosahedron",    # dance
    "thalia":     "icosahedron",    # comedy / grace
    "thalia_muse":"icosahedron",    # muse
    "urania":     "icosahedron",    # astronomy
    "aglaia":     "icosahedron",    # grace
    "euphrosyne": "icosahedron",    # mirth
    "clotho":     "icosahedron",    # spinner
    "lachesis":   "icosahedron",    # allotter
    "atropos":    "icosahedron",    # cutter

    # ─── Primordials — fall outside the five classical elements; ──
    # they're the substrate of the substrate. Classify by function.
    "chaos":      "cube",           # void / null
    "gaia":       "cube",           # filesystem root = state
    "nyx":        "cube",           # time = state
    "eros":       "cube",           # id generation = state primitive
    "tartarus":   "cube",           # quarantine = state
    "ananke":     "cube",           # deterministic seed = state primitive
    "tiresias":   "octahedron",     # ground-truth tracker = reasoning

    # ─── Monsters not above — observation-tier mostly ─────
    "cerberus":   "tetrahedron",    # perimeter gate watches
    "sphinx":     "tetrahedron",    # challenge-response gate
    "medusa":     "tetrahedron",    # snapshot primitive
    "chimera":    "octahedron",     # composite-test runner = reasoning
    "minotaur":   "icosahedron",    # recursive walker = execution
    "typhon":     "tetrahedron",    # catastrophic catalog = observation
}


# ─────────────────────────────────────────────────────────
# Plato class
# ─────────────────────────────────────────────────────────


class Plato:
    """The taxonomy. classify() returns the solid for a given figure
    name; cosmos() returns the full mapping; solid() returns the Solid
    metadata."""

    def solids(self) -> tuple[Solid, ...]:
        return SOLIDS

    def solid(self, name: str) -> Solid | None:
        target = name.lower()
        for s in SOLIDS:
            if s.name == target:
                return s
        return None

    def classify(self, figure_name: str) -> Solid | None:
        """Return the Solid this figure is classified under, or None
        if it's not in the taxonomy."""
        name = figure_name.lower()
        # Strip the "thalia_muse" disambiguator etc.
        solid_name = _FIGURE_TO_SOLID.get(name)
        if solid_name is None:
            return None
        return self.solid(solid_name)

    def cosmos(self) -> dict[str, dict[str, str]]:
        """Return the full mapping {figure → {solid, element, function}}."""
        out: dict[str, dict[str, str]] = {}
        for figure, solid_name in _FIGURE_TO_SOLID.items():
            s = self.solid(solid_name)
            if s is None:
                continue
            out[figure] = {
                "solid": s.name,
                "element": s.element,
                "function": s.function,
            }
        return out

    def members(self, solid_name: str) -> list[str]:
        """Return every figure currently classified under this solid."""
        target = solid_name.lower()
        return sorted(f for f, s in _FIGURE_TO_SOLID.items()
                      if s == target)

    def classified_figures(self) -> list[str]:
        """All figures the taxonomy knows about (sorted)."""
        return sorted(_FIGURE_TO_SOLID.keys())


plato = Plato()
