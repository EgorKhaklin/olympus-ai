"""olympus.runtime.plugins — entry-point-based plugin loader.

Third-party Python packages register additional substrate components
via standard PEP 621 entry_points. Olympus discovers them at runtime
(via `importlib.metadata`) and wires them into the relevant registries.

Supported groups:

  olympus.prometheus_handlers  — Prometheus.register(name, fn)
  olympus.asclepius_healers    — Asclepius.register(name, fn)
  olympus.argos_eyes           — Argos colony eye registration
  olympus.apollo_predictions   — Apollo.predict(prediction)
  olympus.cli_errands          — Hermes.register(name, summary, fn)

Plugins must follow the same discipline as built-in modules — Mnemosyne
audit-of-record, S1–S8 invariants, Momus AP1–AP8. A plugin that
violates an invariant will be caught by the Furies; ratification of
its proposals goes through Momus + Delphi.

Per Delphi 2026-05-18-recursion-arc.md.
"""
from __future__ import annotations

import importlib.metadata
from dataclasses import dataclass, field
from typing import Any, Callable


GROUPS = (
    "olympus.prometheus_handlers",
    "olympus.asclepius_healers",
    "olympus.argos_eyes",
    "olympus.apollo_predictions",
    "olympus.cli_errands",
)


@dataclass
class LoadedPlugin:
    group: str
    name: str
    target: str
    succeeded: bool
    detail: str = ""


@dataclass
class PluginManifest:
    discovered_at: str = ""
    loaded: list[LoadedPlugin] = field(default_factory=list)
    failed: list[LoadedPlugin] = field(default_factory=list)

    @property
    def total_loaded(self) -> int:
        return len(self.loaded)

    @property
    def total_failed(self) -> int:
        return len(self.failed)


# ─────────────────────────────────────────────────────────
# Discovery + registration
# ─────────────────────────────────────────────────────────


def discover() -> list[importlib.metadata.EntryPoint]:
    """Return every entry-point that registers under any olympus.*
    group. Pure read — does not import the target modules."""
    out: list[importlib.metadata.EntryPoint] = []
    try:
        # Python 3.10+ supports .select(group=...)
        all_eps = importlib.metadata.entry_points()
        for group in GROUPS:
            try:
                if hasattr(all_eps, "select"):
                    eps = all_eps.select(group=group)
                else:
                    # Python 3.9 returns a dict
                    eps = all_eps.get(group, [])  # type: ignore[attr-defined]
            except Exception:  # noqa: BLE001
                eps = []
            for ep in eps:
                out.append(ep)
    except Exception:  # noqa: BLE001
        pass
    return out


def load_all(*, record_to_mnemosyne: bool = True) -> PluginManifest:
    """Discover, import, and register every plugin entry-point.
    Returns a PluginManifest. Failures (import or registration) are
    captured per-plugin and never abort the load pass."""
    from olympus.primordials.nyx import Nyx
    manifest = PluginManifest(discovered_at=Nyx.now().isoformat())

    for ep in discover():
        target = f"{ep.value}"
        try:
            fn = ep.load()
        except Exception as exc:  # noqa: BLE001
            manifest.failed.append(LoadedPlugin(
                group=ep.group, name=ep.name, target=target,
                succeeded=False,
                detail=f"import-failed: {type(exc).__name__}: {exc}",
            ))
            continue

        try:
            _register(ep.group, ep.name, fn)
            manifest.loaded.append(LoadedPlugin(
                group=ep.group, name=ep.name, target=target,
                succeeded=True,
                detail="registered",
            ))
        except Exception as exc:  # noqa: BLE001
            manifest.failed.append(LoadedPlugin(
                group=ep.group, name=ep.name, target=target,
                succeeded=False,
                detail=f"register-failed: {type(exc).__name__}: {exc}",
            ))

    if record_to_mnemosyne:
        from olympus.titans.mnemosyne import mnemosyne
        mnemosyne.remember(
            kind="plugins.loaded",
            actor="plugin-loader",
            summary=(f"plugin discovery: {manifest.total_loaded} loaded, "
                     f"{manifest.total_failed} failed"),
            loaded=[{"group": p.group, "name": p.name, "target": p.target}
                    for p in manifest.loaded],
            failed=[{"group": p.group, "name": p.name, "target": p.target,
                     "detail": p.detail}
                    for p in manifest.failed],
        )
    return manifest


def _register(group: str, name: str, fn: Any) -> None:
    """Wire a loaded entry-point object into its target registry."""
    if group == "olympus.prometheus_handlers":
        from olympus.heroes.prometheus import prometheus
        if not callable(fn):
            raise TypeError(f"prometheus handler {name!r} must be callable")
        prometheus.register(name, fn)
        return

    if group == "olympus.asclepius_healers":
        from olympus.olympians.asclepius import asclepius
        if not callable(fn):
            raise TypeError(f"asclepius healer {name!r} must be callable")
        asclepius.register(name, fn)
        return

    if group == "olympus.argos_eyes":
        from olympus.monsters.argos.colony import colony
        # `fn` could be an Eye class or an Eye instance
        eye = fn() if isinstance(fn, type) else fn
        # The colony registers via .register or by appending to ._eyes
        if hasattr(colony, "register"):
            colony.register(eye)  # type: ignore[attr-defined]
        else:
            colony._eyes.append(eye)  # type: ignore[attr-defined]
        return

    if group == "olympus.apollo_predictions":
        from olympus.olympians.apollo import Apollo  # type: ignore
        # `fn` is expected to be a Prediction or a factory returning one
        prediction = fn() if callable(fn) else fn
        # Use module-level singleton if present
        try:
            from olympus.olympians.apollo.oracle import apollo as apollo_singleton
            apollo_singleton.predict(prediction)
        except Exception as exc:  # noqa: BLE001
            raise RuntimeError(f"apollo.predict failed: {exc}") from exc
        return

    if group == "olympus.cli_errands":
        from olympus.olympians.hermes import hermes
        # `fn` may be a (summary, callable) tuple or just a callable
        if isinstance(fn, tuple) and len(fn) == 2:
            summary, handler = fn
        else:
            summary = f"plugin errand: {name}"
            handler = fn
        if not callable(handler):
            raise TypeError(f"cli errand {name!r} handler must be callable")
        hermes.register(name, summary)(handler)
        return

    raise ValueError(f"unknown plugin group {group!r}")
