# codex/specs — formal specifications

Per Delphi 2026-05-18-labyrinth-arc.md.

These TLA+ specifications encode the **safety properties** the Python
implementation must guarantee. They are *demonstrators* — the value of
writing them is in stating, mathematically, what the implementation
must hold; running TLC against them is optional and operator-installed.

| spec | what it proves |
|---|---|
| [`styx-append-only.tla`](styx-append-only.tla) | Under any interleaving of N concurrent swearers, the chain remains hash-linked and seq-monotonic |
| [`hephaestus-pipeline.tla`](hephaestus-pipeline.tla) | No proposal reaches RATIFIED without passing CONTESTED; no HIGH/COMPOSITE without DELPHI_PENDING |
| [`cognitive-flow.tla`](cognitive-flow.tla) | Session phases proceed in order; ERROR short-circuits later phases; every session terminates |

## Running TLC

TLA+ Toolbox / TLC is optional. If you want to model-check:

```bash
# install: https://lamport.azurewebsites.net/tla/tla.html
java -cp tla2tools.jar tlc2.TLC -config StyxAppendOnly.cfg StyxAppendOnly.tla
```

A minimal `.cfg` is documented at the bottom of each `.tla` file.

## Why TLA+ and not Lean / Coq

TLA+ operates at the right level for *lifecycle and concurrency
safety* — the questions Olympus actually faces. Lean and Coq are
better for proving theorems about pure functions; TLA+ is built for
"does this state machine, under all interleavings, preserve this
invariant." Olympus's invariants are state-machine invariants. TLA+
is the right tool.

## Drift signal

If the Python implementation changes in a way that breaks a spec's
implied contract — for example, allowing a proposal to reach RATIFIED
without going through Momus — that is a Hephaestus drift signal.
Add a test that fails until the spec or the implementation is
realigned.
