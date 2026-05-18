"""Legio Substrate — Legatus Dependentia.

Republican phalanx #8 (added ). Guards Olympus's contract
with the external world: what it depends on, what versions, where
the Rust toolchain lives. Without substrate scrutiny, dependency
drift accumulates silently until a fresh checkout fails.

Doctrine: **CUNEUS** (wedge formation).

The wedge-lead is `ant_substrate_catalog`. If the catalog itself
(`DEVNOTES/substrate.md`) is missing primitives, the rest of the
swarm's substrate signals are unmoored. Only when the lead is
silent do the follower ants (in-use Python imports + Rust
toolchain) deploy. Trigger-driven cascade: if substrate.md is
broken, fix substrate.md first; then re-scan downstream.

Originally established as a "Hydra head" in
`delphi/2026-05-13-arc-e-hydra-nine-heads-completion.md`. In
 the Hydra mythology was relocated to HYDRA watchers
(`delphi/2026-05-13-hydra-mythology-relocation-to-watchers.md`);
this phalanx is now organizationally Republican rather than
mythologically a Hydra head.
"""

from monsters.argos.phalanges.base import Phalanx, Tactic, TacticConfig
from monsters.argos.eyes.ant_substrate_catalog import AntSubstrateCatalog
from monsters.argos.eyes.ant_dependency_in_use import AntDependencyInUse
from monsters.argos.eyes.ant_rust_toolchain import AntRustToolchain


class LegioSubstrate(Phalanx):
    NAME    = "phalanx_substrate"
    DOMAIN  = "substrate"
    LEGATUS = "Legatus Dependentia"
    ANTS    = [AntSubstrateCatalog, AntDependencyInUse, AntRustToolchain]
    TACTIC  = TacticConfig(
        tactic=Tactic.CUNEUS,
        lead=AntSubstrateCatalog,
    )
