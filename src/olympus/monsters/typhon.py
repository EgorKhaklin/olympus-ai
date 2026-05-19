"""Typhon — father of all monsters, the storm-giant.

Typhon was so terrible that the Olympians fled at his approach.
Zeus alone faced him and sealed him under Mount Etna. In Olympus,
Typhon is the catastrophic-failure scenario library — he names the
worst-case scenarios every deployment should prepare for.

Typhon does not fire automatically. He must be invoked, and Ares
runs his scenarios as adversarial assaults.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Scenario:
    """A catastrophic scenario. Naming it is the first step toward
    surviving it."""
    name: str
    description: str
    affected: tuple[str, ...]   # which Olympus tiers it touches
    survival_strategy: str


SCENARIOS: tuple[Scenario, ...] = (
    Scenario(
        "filesystem-full",
        "Gaia has no remaining space. No write succeeds.",
        ("primordials", "underworld", "titans"),
        "Reads + Lethe (in-memory) continue. Hades drops new shades. "
        "Operator must free space; pre-ship gate detects this and refuses.",
    ),
    Scenario(
        "styx-broken",
        "The oath chain is tampered with. Tisiphone detects bad seq.",
        ("underworld", "furies", "titans"),
        "Treat all post-tamper oaths as suspect. Restore from offsite "
        "copy of styx.jsonl. No new oaths until intact.",
    ),
    Scenario(
        "hera-bindings-lost",
        "The bindings registry is deleted. Components lose their named "
        "relationships.",
        ("olympians",),
        "Rebuild from source — every binding has a constructor in source. "
        "Lost bindings do not break code; they break the catalog.",
    ),
    Scenario(
        "hydra-head-blind",
        "A head is hung; emits no findings for >24h.",
        ("monsters", "furies"),
        "Alecto fires after 24h silence. Cerberus refuses traffic through "
        "gates the blind head was meant to guard.",
    ),
    Scenario(
        "argos-poisoning",
        "An Eye deposits adversarial pheromones at high rate.",
        ("monsters",),
        "Lachesis (quota) caps per-Eye deposit rate. Excess goes to "
        "Tartarus. Operator audits the offending Eye's source.",
    ),
    Scenario(
        "delphi-prompt-injection",
        "A delphi/ file contains prompt-injection disguised as decision.",
        ("oracles",),
        "Delphi files are NEVER read by the agent as instructions. The "
        "agent reads them as data and renders them to the operator.",
    ),
    Scenario(
        "hephaestus-overreach",
        "Hephaestus proposes constitutional amendment without Delphi.",
        ("olympians", "oracles"),
        "Momus AP4 refusal. Themis enforces: any MISSION / COSMOGONY "
        "edit requires a Delphi reference in the commit message.",
    ),
)


class Typhon:
    """Catastrophic-failure catalog + fault injector (akropolis arc).

    Each injection has a reverter; `typhon.inject(scenario,
    confirm=True)` performs the disturbance and returns an Injection
    handle. Test-time only — production uses Hygieia for inspection
    and Asclepius/Pan for recovery."""

    def scenarios(self) -> tuple[Scenario, ...]:
        return SCENARIOS

    def by_name(self, name: str) -> Scenario | None:
        for s in SCENARIOS:
            if s.name == name:
                return s
        return None

    def injectable(self) -> list[str]:
        """The set of injectable scenario keys (akropolis arc)."""
        return sorted(_INJECTORS.keys())

    def inject(self, scenario: str, *, confirm: bool = False,
                **kwargs) -> "Injection":
        """Inject a fault. confirm=True is required — this actually
        breaks substrate state."""
        if not confirm:
            raise RuntimeError(
                f"typhon.inject({scenario!r}) requires confirm=True — "
                "this actually breaks substrate state. CLI: "
                "`invoke fault-inject <scenario> --confirm`"
            )
        injector = _INJECTORS.get(scenario)
        if injector is None:
            raise KeyError(
                f"unknown scenario {scenario!r}; "
                f"injectable: {self.injectable()}"
            )
        return injector(**kwargs)


# ─────────────────────────────────────────────────────────
# Fault-injection support — Injection handle + concrete injectors
# ─────────────────────────────────────────────────────────


from dataclasses import field  # noqa: E402 (used below)


@dataclass
class Injection:
    """One active fault injection. Call .revert() to undo."""
    scenario: str
    detail: str
    injected_at: str = ""
    reverter: object | None = None      # Callable[[], None]
    reverted: bool = False

    def __post_init__(self) -> None:
        from olympus.primordials.nyx import Nyx
        from olympus.titans.mnemosyne import mnemosyne
        if not self.injected_at:
            self.injected_at = Nyx.now().isoformat()
        mnemosyne.remember(
            kind="typhon.injection",
            actor="typhon",
            summary=f"injected {self.scenario}: {self.detail[:80]}",
            scenario=self.scenario, detail=self.detail,
            injected_at=self.injected_at,
        )

    def revert(self) -> None:
        if self.reverted:
            return
        from olympus.primordials.nyx import Nyx
        from olympus.titans.mnemosyne import mnemosyne
        try:
            if self.reverter is not None:
                self.reverter()
            self.reverted = True
            mnemosyne.remember(
                kind="typhon.recovery",
                actor="typhon",
                summary=f"reverted {self.scenario}",
                scenario=self.scenario, ok=True,
                reverted_at=Nyx.now().isoformat(),
            )
        except Exception as exc:  # noqa: BLE001
            mnemosyne.remember(
                kind="typhon.recovery",
                actor="typhon",
                summary=f"revert FAILED for {self.scenario}: {exc}",
                scenario=self.scenario, ok=False,
                error=f"{type(exc).__name__}: {exc}",
                reverted_at=Nyx.now().isoformat(),
            )
            raise


def _inj_delete_pan_state() -> Injection:
    """Delete state/pan/state.json. Asclepius's healer regenerates."""
    from olympus.primordials.gaia import root
    pan_state = root.child("state", "pan", "state.json")
    backup = pan_state.read_text(encoding="utf-8") \
             if pan_state.exists() else None
    if backup is not None:
        pan_state.unlink()

    def revert() -> None:
        if backup is not None:
            pan_state.parent.mkdir(parents=True, exist_ok=True)
            pan_state.write_text(backup, encoding="utf-8")

    return Injection(
        scenario="delete-pan-state",
        detail=f"deleted {pan_state}; backup held in-memory",
        reverter=revert,
    )


def _inj_seed_fake_violations(n: int = 5) -> Injection:
    """Write n fake invariant.violated rows. Should trip Pan if the
    threshold is crossed within the window."""
    from olympus.titans.mnemosyne import mnemosyne
    for i in range(n):
        mnemosyne.remember(
            kind="invariant.violated",
            actor="typhon:fault-injector",
            summary=f"injected fake violation {i}",
            invariant_id="S1", evidence={"injected": True},
        )

    def revert() -> None:
        # Mnemosyne is append-only — we cannot delete the rows.
        # Instead, clear Pan so the substrate continues normally.
        from olympus.olympians.pan import pan
        pan.clear(by="typhon:revert",
                   reason="fault injection reverted")

    return Injection(
        scenario="seed-fake-violations",
        detail=(f"wrote {n} invariant.violated rows; revert clears "
                f"Pan (rows persist as audit-of-record)"),
        reverter=revert,
    )


def _inj_break_styx_chain() -> Injection:
    """Corrupt the last line of state/styx.jsonl — Tisiphone's verify
    should detect the break."""
    from olympus.primordials.gaia import root
    styx_path = root.child("state", "styx.jsonl")
    if not styx_path.exists():
        raise RuntimeError("styx.jsonl missing — nothing to corrupt")
    original = styx_path.read_text(encoding="utf-8")
    lines = original.splitlines()
    if not lines:
        raise RuntimeError("styx.jsonl empty — nothing to corrupt")
    import json as _json
    last = _json.loads(lines[-1])
    last["self_hash"] = "0" * 64
    lines[-1] = _json.dumps(last, default=str)
    styx_path.write_text("\n".join(lines) + "\n", encoding="utf-8")

    def revert() -> None:
        styx_path.write_text(original, encoding="utf-8")

    return Injection(
        scenario="break-styx-chain",
        detail=("bogus self_hash on last line of state/styx.jsonl; "
                "revert restores the original file"),
        reverter=revert,
    )


_INJECTORS: dict[str, object] = {
    "delete-pan-state":      _inj_delete_pan_state,
    "seed-fake-violations":  _inj_seed_fake_violations,
    "break-styx-chain":      _inj_break_styx_chain,
}


typhon = Typhon()
