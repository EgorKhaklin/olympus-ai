<div align="center">

# 🜂 SPECS 🜂

**the formal-verification layer**

</div>

---

Per Delphi 2026-05-18-labyrinth-arc.md.

Olympus's constitution lives in three layers, increasing in formality:

1. **Prose** — `codex/COSMOGONY.md`, the human-readable statement of S1–S8.
2. **Tests** — `tests/test_invariant_S*.py`, runtime assertions.
3. **Formal specs** — `codex/specs/*.tla`, mathematical models that
   state what the implementation must guarantee under all interleavings.

The third layer is this directory. It is the deepest layer of the
labyrinth and the most opinionated.

---

## What's here

| spec | what it proves |
|---|---|
| [`styx-append-only.tla`](specs/styx-append-only.tla) | Under any interleaving of N concurrent swearers, the Styx chain remains hash-linked and sequence-monotonic |
| [`hephaestus-pipeline.tla`](specs/hephaestus-pipeline.tla) | No proposal reaches RATIFIED without passing CONTESTED; no HIGH/COMPOSITE proposal reaches RATIFIED without DELPHI_PENDING |
| [`cognitive-flow.tla`](specs/cognitive-flow.tla) | Session phases proceed in order; ERROR short-circuits later phases; every session terminates |

`themis.specs()` exposes them programmatically:

```python
from olympus.titans.themis import themis
for name, meta in themis.specs().items():
    print(name, "→", meta["module_name"], meta["bytes"], "bytes")
```

`invoke specs` shows them at the CLI; `invoke specs <name>` shows one in detail.

---

## Why TLA+

TLA+ (Lamport) is the right tool for *lifecycle and concurrency
invariants*. The questions Olympus actually faces — *"under all
interleavings, does the chain stay linked?"*, *"can a HIGH proposal
ever ratify without Delphi?"* — are state-machine questions. Lean and
Coq are stronger for proving theorems about pure functions; TLA+ is
built for "this state machine, under all interleavings, preserves this
invariant." So TLA+ is what we use.

The specs are **demonstrators**. Writing them is the value; running
TLC against them is optional infrastructure. The act of *naming the
property* — in a language where ambiguity isn't allowed — is what
forces the substrate to be honest about what it promises.

---

## Drift signal

If the Python implementation changes in a way that breaks a spec's
implied contract — for example, allowing a proposal to reach RATIFIED
without going through Momus — that is a **Hephaestus drift signal**.
Either the implementation needs fixing, or the spec needs updating.
Silent divergence is AP6 (understanding-obscuring).

A future arc may wire `invoke verify-specs` to run TLC automatically.
For now, an operator who installs TLC can model-check on demand:

```bash
java -cp tla2tools.jar tlc2.TLC -config StyxAppendOnly.cfg StyxAppendOnly.tla
```

`codex/specs/README.md` has the per-spec config snippets.

---

## What's NOT in TLA+

- **Anything pure-functional.** Hash computation, JSON serialization,
  string formatting — not modeled. Standard Python tests cover these.
- **Performance.** TLA+ doesn't capture wall-clock time or memory.
- **External I/O.** Filesystem, network — modeled only at the
  abstraction of "an event occurred."

The point is *what the substrate is allowed to do*, not *how fast it does it*.

---

*Per Delphi 2026-05-18-labyrinth-arc.md. Themis is the custodian; the
specs make her law more than prose.*
