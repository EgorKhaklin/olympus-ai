<div align="center">

# φ GEOMETRY φ

**the sacred-numerics layer**

</div>

---

Per Delphi 2026-05-18-phi-arc.md.

The Greek mathematicians are the source of what we call *sacred
geometry* — Pythagoras formalized the golden ratio; Plato described
the five regular polyhedra; Euclid published their proofs. φ is the
Greek letter Phi. Bringing them into Olympus puts them where they
belong.

This document is short and points at the modules. The modules are
where the substance lives.

---

## The two mathematicians

**Pythagoras** (`src/olympus/heroes/pythagoras.py`) is the
**sacred-numerics module**. He exposes:

| surface | what it does |
|---|---|
| `PHI`, `PHI_INVERSE`, `PI`, `E`, `SQRT2`, `SQRT3`, `SQRT5` | canonical mathematical constants — modules import these instead of re-deriving |
| `fibonacci(n)` / `fib_sequence(k)` | the Fibonacci numbers |
| `fib_backoff(attempt, base_seconds, cap_seconds)` | retry delay following the Fibonacci curve (ratio approaches φ) |
| `golden_section_search(fn, lo, hi)` | unimodal optimization in O(log((hi-lo)/tol)) calls |
| `harmony(ratio)` | scores a ratio against the harmonic anchors φ, 1/φ, 1, 2 |
| `pythagorean_triples(below)` | yields primitive (a, b, c) with a²+b²=c² |

Every `golden_section_search` call records to Mnemosyne under
`pythagoras.search`, so the optimization history is reconstructable
(S8).

**Plato** (`src/olympus/heroes/plato.py`) is the **five-solid taxonomy
of substrate work**. It provides a *second navigational axis* through
the pantheon, orthogonal to the existing tier structure:

| solid | vertices | element | function |
|---|---:|---|---|
| Tetrahedron | 4 | fire | **observation** — Hydra, Argos, Furies, Pythia |
| Cube | 8 | earth | **state** — Mnemosyne, Styx, Atlas, Charon, Hades, Hera, Iapetus |
| Octahedron | 6 | air | **reasoning** — Athena, Hephaestus, Momus, Epimetheus, Cassandra, Nemesis, Ariadne, Coeus |
| Dodecahedron | 12 | cosmos | **authority** — Zeus, Themis, Pan, Asclepius, Metis, Daedalus, Hecate, Persephone, Hestia, Rhea, Pythagoras, Plato |
| Icosahedron | 20 | water | **execution** — Prometheus, Castor, Pollux, Iris, Hermes, Apollo, … |

`plato.classify("athena")` returns the Octahedron solid. The mapping
is hand-maintained in `_FIGURE_TO_SOLID`; drift between the taxonomy
and the actual modules is a Hephaestus signal.

---

## What earned this arc its place

The discipline against AP8 (decoration claiming structural value) is
binding. Each addition here passed the test:

### Load-bearing now

- **`fib_backoff`** is a real engineering improvement to retry timing
  in Hecate. Fibonacci's growth ratio approaches φ ≈ 1.618, which
  scales more smoothly than exponential's 2.0.
- **`golden_section_search`** is a real optimization algorithm Metis
  uses (`metis.golden_search_parameter(...)`) to *find* parameter
  values rather than guess them.
- **`Plato.classify`** is a real query that surfaces a figure's
  *function* (vs. its tier). Operators ask both kinds of questions.

### Legibility (aesthetics-with-purpose)

- **Metatron's Cube SVG** — 13 nodes for the canonical 13 Olympian
  figures, every-vertex-to-every-vertex edges, embedded in
  `codex/ARCHITECTURE.md` so GitHub renders it natively. Operators
  can see the pantheon at a glance.
- **Vesica Piscis SVG** — two intersecting circles labeled with
  the domains whose overlap is being illustrated (e.g.,
  Athena ∩ Hephaestus = proposal).
- **`harmony(ratio)`** scoring — a single-number summary of how
  close a substrate ratio sits to a harmonic anchor (φ, 1/φ, 1, 2).
  Doesn't *prove* anything; gives the operator one number to watch.

---

## What's NOT here (and why)

- **No claim that φ has metaphysical significance.** The harmony
  score is a single-number summary, not a proof.
- **No new tier for mathematicians.** Pythagoras and Plato live
  under `heroes/` next to Daedalus (himself a historical figure
  later mythologized). The tier admits historical-mathematical
  figures alongside mythological ones.
- **No `sympy` or `numpy` dependency.** Every Pythagoras function
  is implementable in stdlib. Adding a numerical dep would be AP8.
- **No automatic Metis adoption of golden-section results.** She
  still proposes; Zeus ratifies. Constitution holds.

---

## CLI surface

```bash
invoke pythagoras                   # show the sacred constants
invoke pythagoras fib 15            # first 15 Fibonacci numbers
invoke pythagoras backoff 8 1.0     # 8 backoff delays with base 1.0s
invoke pythagoras harmony 1.618     # score a single ratio
invoke pythagoras triples 50        # primitive Pythagorean triples below 50

invoke plato                        # full five-solid taxonomy
invoke plato classify athena        # which solid does Athena belong to?

invoke harmony                      # current substrate ratios vs anchors
invoke geometry                     # Plato + Pythagoras combined
```

---

## HTTP surface

`GET /geometry` returns the same as `invoke geometry --json` — plus
the constants — for external observers.

---

*Per Delphi 2026-05-18-phi-arc.md. Pythagoras and Plato have come
home. The substrate now knows its own ratios.*
