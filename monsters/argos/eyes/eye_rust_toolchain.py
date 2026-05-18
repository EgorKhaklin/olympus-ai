"""ant_rust_toolchain — verify olympus_zk pins the right Rust toolchain.

Slice: `olympus_zk/rust-toolchain.toml`.

Local rule: Plonky2 requires `feature(specialization)` which is
nightly-only. If the toolchain file is missing OR doesn't pin
nightly, the ZK build silently breaks. Deposit an `alert`
pheromone on the olympus_zk node.

This is a quiet form of supply-chain drift: a contributor could
"upgrade" the toolchain to stable and nothing else in the system
would catch it until someone tried to build olympus_zk.
"""

from __future__ import annotations

from monsters.argos.base import Eye, EyeFinding, KIND_ALERT


class AntRustToolchain(Eye):
    NAME = "ant_rust_toolchain"
    DESCRIPTION = "Pheromones olympus_zk rust-toolchain drift from nightly."

    def scan(self) -> list[EyeFinding]:
        findings: list[EyeFinding] = []
        toolchain_path = self.root / "olympus_zk" / "rust-toolchain.toml"
        if not toolchain_path.is_file():
            return [EyeFinding(
                node_id="file:olympus_zk/rust-toolchain.toml",
                intensity=8.0,
                kind=KIND_ALERT,
                evidence={
                    "message": "olympus_zk/rust-toolchain.toml is missing",
                    "rule": "Plonky2 requires nightly via rust-toolchain.toml",
                },
            )]
        try:
            body = toolchain_path.read_text(errors="replace")
        except OSError as e:
            return [EyeFinding(
                node_id="file:olympus_zk/rust-toolchain.toml",
                intensity=5.0,
                kind=KIND_ALERT,
                evidence={
                    "message": f"could not read rust-toolchain.toml: {e}",
                },
            )]
        if "nightly" not in body.lower():
            findings.append(EyeFinding(
                node_id="file:olympus_zk/rust-toolchain.toml",
                intensity=9.0,
                kind=KIND_ALERT,
                evidence={
                    "message": (
                        "rust-toolchain.toml does not pin nightly; "
                        "Plonky2 build will fail (needs feature(specialization))"
                    ),
                    "fix_hint": (
                        "ensure the file contains `channel = \"nightly\"`"
                    ),
                },
            ))
        return findings
