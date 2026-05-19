"""olympus.runtime.setup — the interactive welcome wizard.

Per Delphi 2026-05-18-xenia-arc.md. This is the load-bearing answer
to Zeus's question *"how does a stranger become an operator?"*

Design:
  - Idempotent — re-running is safe; shows current state, asks "change?"
  - Metacognitive — every step explains WHAT is happening and WHY
  - Testable — injectable `input_provider` so tests pass canned answers
  - Mythology-aware — frames each step in the substrate's own terms

The wizard never silently configures anything dangerous. Picking the
anthropic LLM provider triggers a test call BEFORE the config is
saved — no surprise broken setups.
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Callable

from olympus.primordials.nyx import Nyx
from olympus.runtime import config as cfg_module
from olympus.titans.mnemosyne import mnemosyne


# Type aliases
Asker = Callable[[str, str], str]   # (prompt, default) -> answer


def _default_asker(prompt: str, default: str = "") -> str:
    """Production input asker. Shows the default in brackets; empty
    answer accepts the default."""
    suffix = f" [{default}]" if default else ""
    answer = input(f"{prompt}{suffix}: ").strip()
    return answer or default


def _yes_no(asker: Asker, prompt: str, default: bool = True) -> bool:
    d = "Y/n" if default else "y/N"
    while True:
        raw = asker(f"{prompt} ({d})", "y" if default else "n").lower()
        if raw in ("y", "yes", "true", "1"):
            return True
        if raw in ("n", "no", "false", "0"):
            return False
        # Accept the default on empty (already handled by asker)


# ─────────────────────────────────────────────────────────
# Step functions — each returns a "completed step" record
# ─────────────────────────────────────────────────────────


@dataclass
class StepResult:
    name: str
    changed: bool = False
    detail: str = ""


@dataclass
class SetupReport:
    started_at: str
    ended_at: str = ""
    steps: list[StepResult] = None
    config_path: str = ""

    def __post_init__(self):
        if self.steps is None:
            self.steps = []


def _print(text: str = "") -> None:
    """Wrapped print so tests can capture if they want; default
    prints to stdout."""
    print(text)


def _hr() -> None:
    _print("─" * 64)


def _banner(title: str, subtitle: str = "") -> None:
    _print()
    _hr()
    _print(f"  {title}")
    if subtitle:
        _print(f"  {subtitle}")
    _hr()


def _welcome() -> None:
    _banner("Welcome to Olympus",
             "a cognitive substrate built in the shape of Greek mythology")
    _print()
    _print("  Olympus is not just \"with greek-named modules.\" It IS the")
    _print("  mythology. Each tier has a structural role:")
    _print()
    _print("    primordials  — chaos, gaia, nyx, eros, tartarus, ananke")
    _print("    titans       — mnemosyne, themis, atlas, metis, …")
    _print("    olympians    — zeus, athena, hephaestus, pan, asclepius, …")
    _print("    underworld   — hades, styx, lethe, charon, …")
    _print("    + fates, furies, graces, muses, heroes, monsters")
    _print()
    _print("  This wizard will configure your deployment in ~5 steps.")
    _print("  Re-running is safe — it shows what's already set.")
    _print()


def _step_kindle(*, asker: Asker, current: cfg_module.Config) -> StepResult:
    _banner("Step 1 / 6 · Kindle the hearth",
             "this names your deployment")
    _print()
    _print("  Hestia is the goddess of the hearth — the sacred boundary")
    _print("  that marks 'this is my Olympus instance.' Every cognitive")
    _print("  loop runs under this name. Choose something descriptive.")
    _print()
    name = asker("  name", current.kindled or "my-olympus")
    vocation = asker("  vocation (what is this Olympus for?)",
                      current.vocation or "personal cognitive substrate")
    changed = (name != current.kindled or vocation != current.vocation)
    if changed:
        current.kindled = name
        current.vocation = vocation
        # Also kindle Hestia if she isn't lit
        try:
            from olympus.olympians.hestia import hestia
            if not hestia.is_lit():
                hestia.kindle(name=name, vocation=vocation)
                detail = f"kindled '{name}' (Hestia is lit)"
            else:
                detail = f"saved '{name}' (Hestia was already lit)"
        except Exception as exc:  # noqa: BLE001
            detail = f"saved name; Hestia kindle failed: {exc}"
    else:
        detail = f"unchanged: {name!r}"
    _print(f"  → {detail}")
    return StepResult(name="kindle", changed=changed, detail=detail)


def _step_llm(*, asker: Asker,
               current: cfg_module.Config) -> StepResult:
    _banner("Step 2 / 6 · LLM provider",
             "the substrate is safe-by-default; LLM is optional")
    _print()
    _print("  Olympus runs WITHOUT an LLM. The default 'echo' provider")
    _print("  is a deterministic stub — useful for tests and for trying")
    _print("  out the substrate. To get real agent reasoning, configure")
    _print("  Anthropic (Claude). All LLM calls are recorded to Mnemosyne.")
    _print()
    _print("  Choices:")
    _print("    1. echo       — no network, no cost (recommended to start)")
    _print("    2. anthropic  — Claude (needs ANTHROPIC_API_KEY)")
    _print("    3. skip       — leave as-is")
    _print()
    current_choice = current.llm.provider or "echo"
    choice = asker("  choice (1/2/3 or name)", current_choice).lower()
    # Normalize
    if choice in ("1", "echo"):
        choice = "echo"
    elif choice in ("2", "anthropic"):
        choice = "anthropic"
    elif choice in ("3", "skip"):
        return StepResult(name="llm", changed=False,
                           detail=f"left as {current.llm.provider!r}")
    else:
        _print(f"  → unrecognized choice {choice!r}; leaving as "
                 f"{current.llm.provider!r}")
        return StepResult(name="llm", changed=False,
                           detail="unrecognized; unchanged")

    if choice == "echo":
        if current.llm.provider != "echo":
            current.llm.provider = "echo"
            current.llm.anthropic_api_key = ""
            return StepResult(name="llm", changed=True,
                               detail="set to echo (safe default)")
        return StepResult(name="llm", changed=False,
                           detail="already echo")

    # anthropic — prompt for key, TEST CALL before saving
    masked = (current.llm.anthropic_api_key[:6] + "…"
              if current.llm.anthropic_api_key else "(not set)")
    _print(f"  current ANTHROPIC_API_KEY: {masked}")
    key = asker("  ANTHROPIC_API_KEY (paste, or blank to keep)",
                current.llm.anthropic_api_key or "")
    if not key:
        return StepResult(name="llm", changed=False,
                           detail="anthropic chosen but no key; unchanged")
    # Test call
    _print()
    _print("  testing the connection (one tiny call)…")
    try:
        import os as _os
        prior = _os.environ.get("ANTHROPIC_API_KEY")
        _os.environ["ANTHROPIC_API_KEY"] = key
        from olympus.runtime.llm_bridge import AnthropicBridge
        resp = AnthropicBridge().call(
            system="ping", user="say 'pong' and nothing else",
            max_tokens=16, role="setup-probe",
        )
        if prior is None:
            del _os.environ["ANTHROPIC_API_KEY"]
        else:
            _os.environ["ANTHROPIC_API_KEY"] = prior
        if resp.error:
            _print(f"  ✗ test call failed: {resp.error[:200]}")
            _print(f"  → leaving config UNCHANGED (your key was not saved)")
            return StepResult(name="llm", changed=False,
                               detail=f"test failed: {resp.error[:80]}")
        _print(f"  ✓ test call succeeded (model={resp.model})")
    except Exception as exc:  # noqa: BLE001
        _print(f"  ✗ test call raised: {exc}")
        _print(f"  → leaving config UNCHANGED (your key was not saved)")
        return StepResult(name="llm", changed=False,
                           detail=f"test raised: {exc}")

    current.llm.provider = "anthropic"
    current.llm.anthropic_api_key = key
    return StepResult(name="llm", changed=True,
                       detail=f"set to anthropic (key tested ok)")


def _step_daemon(*, asker: Asker,
                  current: cfg_module.Config) -> StepResult:
    _banner("Step 3 / 6 · Daemon (the continuous self-improvement loop)",
             "optional — runs invoke session + improve on a cadence")
    _print()
    _print("  The daemon runs in the background (launchd on macOS,")
    _print("  systemd on Linux) and triggers one cognitive pass every")
    _print("  N minutes. You can install now, or later via:")
    _print("    invoke daemon install --interval 600")
    _print()
    install = _yes_no(asker, "  install daemon now",
                       default=current.daemon.installed)
    if not install:
        return StepResult(name="daemon", changed=False,
                           detail="not installed (operator deferred)")
    interval_raw = asker("  iteration interval (seconds)",
                          str(current.daemon.interval_seconds))
    try:
        interval = int(interval_raw)
    except ValueError:
        interval = 600
    try:
        from olympus.runtime import daemon as _daemon_mod
        result = _daemon_mod.install(interval_seconds=interval,
                                       dry_run=False)
        current.daemon.installed = True
        current.daemon.interval_seconds = interval
        return StepResult(name="daemon", changed=True,
                           detail=f"installed on {result.get('platform')}; "
                                  f"interval={interval}s")
    except Exception as exc:  # noqa: BLE001
        return StepResult(name="daemon", changed=False,
                           detail=f"install failed: {exc}")


def _step_agora(*, asker: Asker,
                 current: cfg_module.Config) -> StepResult:
    _banner("Step 4 / 6 · Web UI port",
             "Agora is the operator's interactive dashboard")
    _print()
    _print("  Agora serves HTML pages from the HTTP API. Default port")
    _print("  is 8765 (localhost-only). Change only if you have a")
    _print("  conflict.")
    _print()
    port_raw = asker("  Agora port", str(current.agora.port))
    try:
        port = int(port_raw)
    except ValueError:
        port = 8765
    changed = port != current.agora.port
    current.agora.port = port
    return StepResult(name="agora", changed=changed,
                       detail=f"port = {port}")


def _step_first_session(*, asker: Asker,
                          current: cfg_module.Config,
                          run_session_fn: Callable = None,
                          ) -> StepResult:
    _banner("Step 5 / 6 · First session",
             "one cognitive pass to confirm everything works")
    _print()
    if not _yes_no(asker, "  run a session now", default=True):
        return StepResult(name="first-session", changed=False,
                           detail="skipped")
    try:
        if run_session_fn is None:
            from olympus.session import run_session
            run_session_fn = run_session
        report = run_session_fn(directive="setup-wizard probe")
        ok = report.error is None
        if ok:
            _print(f"  ✓ session {report.session_id[:16]} completed")
            _print(f"    hydra={report.hydra_findings} "
                     f"argos={report.argos_pheromones} "
                     f"proposals={report.proposals_count}")
        else:
            _print(f"  ✗ session errored: {report.error}")
        return StepResult(name="first-session", changed=ok,
                           detail=f"session ok={ok}")
    except Exception as exc:  # noqa: BLE001
        return StepResult(name="first-session", changed=False,
                           detail=f"raised: {exc}")


def _step_summary(*, current: cfg_module.Config,
                    report: SetupReport) -> StepResult:
    _banner("Step 6 / 6 · Summary",
             f"setup complete — config saved to {report.config_path}")
    _print()
    _print(f"  hearth:        {current.kindled} — {current.vocation}")
    _print(f"  LLM provider:  {current.llm.provider or '(unset; echo)'}")
    if current.llm.provider == "anthropic":
        masked = current.llm.anthropic_api_key[:6] + "…"
        _print(f"    API key:     {masked}")
    _print(f"  daemon:        "
             f"{'installed' if current.daemon.installed else 'not installed'}"
             f" (interval={current.daemon.interval_seconds}s)")
    _print(f"  Agora port:    {current.agora.port}")
    _print()
    _print("  Next steps:")
    _print("    invoke status            # quick health snapshot")
    _print("    invoke doctor            # full diagnostic")
    _print("    invoke today             # one concrete thing to look at")
    _print("    invoke agora --open      # open the web UI")
    _print()
    return StepResult(name="summary", changed=False,
                       detail="setup complete")


# ─────────────────────────────────────────────────────────
# Public entry point
# ─────────────────────────────────────────────────────────


def run_setup(*, asker: Asker | None = None,
               run_session_fn: Callable | None = None,
               quiet: bool = False) -> SetupReport:
    """Run the interactive setup wizard. Returns a SetupReport.

    `asker` is the function prompted for each input; defaults to a
    real `input()`-based asker. Tests inject canned answers.
    `quiet=True` suppresses the welcome banner (useful for tests).
    """
    if asker is None:
        asker = _default_asker

    if not quiet:
        _welcome()

    current = cfg_module.load()
    report = SetupReport(started_at=Nyx.now().isoformat())

    for step_fn, kwargs in (
        (_step_kindle,        {}),
        (_step_llm,           {}),
        (_step_daemon,        {}),
        (_step_agora,         {}),
        (_step_first_session, {"run_session_fn": run_session_fn}),
    ):
        try:
            result = step_fn(asker=asker, current=current, **kwargs)
        except Exception as exc:  # noqa: BLE001
            result = StepResult(
                name=step_fn.__name__.lstrip("_").replace("_", "-"),
                changed=False,
                detail=f"step raised: {type(exc).__name__}: {exc}",
            )
        report.steps.append(result)
        mnemosyne.remember(
            kind="setup.step",
            actor="setup-wizard",
            summary=f"{result.name}: {result.detail[:100]}",
            step=result.name, changed=result.changed,
            detail=result.detail,
        )

    # Save the final config + run the summary step
    try:
        from olympus import __version__ as _v
    except ImportError:
        _v = "unknown"
    current.version = _v
    current.setup_completed_at = Nyx.now().isoformat()
    cfg_module.save(current)
    report.config_path = str(cfg_module._path())

    summary_result = _step_summary(current=current, report=report)
    report.steps.append(summary_result)

    report.ended_at = Nyx.now().isoformat()
    mnemosyne.remember(
        kind="setup.completed",
        actor="setup-wizard",
        summary=(f"setup complete — {sum(1 for s in report.steps if s.changed)} "
                 f"changes; config at {report.config_path}"),
        kindled=current.kindled,
        llm_provider=current.llm.provider,
        daemon_installed=current.daemon.installed,
        agora_port=current.agora.port,
    )
    return report


def is_setup_complete() -> bool:
    """Has the operator run the wizard at least once?"""
    cfg = cfg_module.load()
    return bool(cfg.setup_completed_at)
