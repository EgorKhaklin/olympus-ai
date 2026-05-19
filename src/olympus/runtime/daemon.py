"""olympus.runtime.daemon — the long-running self-improvement daemon.

Until now, scripts/loop.sh was the loop runner but had no supervisor.
This module is the operationalization:

  - `daemon.run(interval, max_iterations)` — the foreground entry
    point. Suitable for systemd Type=simple or launchd KeepAlive.
  - `daemon.install()` / `daemon.uninstall()` — generate and load
    the OS unit (launchd plist on macOS, systemd unit on Linux).
  - `daemon.status()` — query whether the unit is loaded and running.

The unit files are generated from templates at scripts/daemon/. The
generation step substitutes the absolute paths so the unit works
regardless of where the operator placed the repo.

Logs go to state/daemon.log (the unit also redirects stdout/stderr
there). Each loop iteration writes one structured line: iso-ts,
session_id, phase counts, duration_ms.

Per Delphi 2026-05-18-compass-rose-arc.md.
"""
from __future__ import annotations

import json
import os
import pathlib
import platform
import shutil
import subprocess
import sys
import time
from dataclasses import dataclass, field
from typing import Any

from olympus.primordials.gaia import root
from olympus.primordials.nyx import Nyx


# ─────────────────────────────────────────────────────────
# Paths + defaults
# ─────────────────────────────────────────────────────────


LABEL = "com.olympus.daemon"
DEFAULT_INTERVAL_SECONDS = 600
LAUNCHD_PLIST_NAME = f"{LABEL}.plist"
SYSTEMD_UNIT_NAME = "olympus-daemon.service"
TEMPLATE_DIR = "scripts/daemon"
LOG_PATH = "state/daemon.log"


@dataclass
class DaemonStatus:
    platform: str
    installed: bool
    running: bool
    unit_path: str = ""
    detail: str = ""
    pid: int | None = None


@dataclass
class IterationLog:
    iteration: int
    ts: str
    duration_ms: float
    session_ok: bool
    improve_ok: bool
    panicked: bool
    detail: dict[str, Any] = field(default_factory=dict)


# ─────────────────────────────────────────────────────────
# Foreground loop — the actual daemon body
# ─────────────────────────────────────────────────────────


def _log_line(payload: dict[str, Any]) -> None:
    """Append one structured log line to state/daemon.log."""
    path = root.child(*LOG_PATH.split("/"))
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(payload, default=str) + "\n")


def run(*, interval_seconds: float = DEFAULT_INTERVAL_SECONDS,
        max_iterations: int = -1,
        on_iteration: Any | None = None) -> None:
    """Run the self-improvement loop. max_iterations < 0 = forever.
    Catches SIGINT for clean shutdown."""
    from olympus.session import run_session
    from olympus.heroes.prometheus import prometheus
    from olympus.olympians.pan import pan

    i = 0
    _log_line({"event": "daemon.start",
               "ts": Nyx.now().isoformat(),
               "interval_seconds": interval_seconds,
               "max_iterations": max_iterations,
               "pid": os.getpid()})

    try:
        while max_iterations < 0 or i < max_iterations:
            i += 1
            start = time.perf_counter()
            session_ok = False
            improve_ok = False
            session_summary = ""
            improve_summary = ""

            # Pre-iteration: evaluate Pan
            pan_state = pan.evaluate()
            if pan_state.panicked:
                # In panic: skip session + improve. Log and sleep.
                _log_line({
                    "event": "daemon.skipped",
                    "ts": Nyx.now().isoformat(),
                    "iteration": i,
                    "reason": "pan-panic",
                    "pan_detail": pan_state.detail,
                })
                time.sleep(interval_seconds)
                continue

            # Per Delphi 2026-05-19-chronos-arc.md: fire scheduled
            # rituals each tick BEFORE the session (so a ritual that
            # triggers `today` runs before the regular session work).
            try:
                from olympus.primordials.chronos import chronos
                chronos_fired = chronos.tick()
                if chronos_fired:
                    _log_line({
                        "event": "daemon.chronos",
                        "ts": Nyx.now().isoformat(),
                        "iteration": i,
                        "fired_count": len(chronos_fired),
                        "fired": [f.ritual_id for f in chronos_fired],
                    })
            except Exception as exc:  # noqa: BLE001
                _log_line({
                    "event": "daemon.chronos_raised",
                    "ts": Nyx.now().isoformat(),
                    "iteration": i,
                    "error": str(exc),
                })

            try:
                report = run_session(directive=None)
                session_ok = report.error is None
                session_summary = (
                    f"session={report.session_id[:12]} "
                    f"hydra={report.hydra_findings} "
                    f"argos={report.argos_pheromones} "
                    f"proposals={report.proposals_count}"
                )
            except Exception as exc:  # noqa: BLE001
                session_summary = f"session-raised: {exc}"

            try:
                impr = prometheus.improve()
                improve_ok = (impr.handlers_succeeded ==
                              impr.handlers_invoked)
                improve_summary = (f"improve={impr.handlers_succeeded}/"
                                   f"{impr.handlers_invoked}")
            except Exception as exc:  # noqa: BLE001
                improve_summary = f"improve-raised: {exc}"

            # Labyrinth-arc extras — periodic deep work
            extras: dict[str, str] = {}
            try:
                # Every 6th iteration: Clio narrates a weekly digest
                if i % 6 == 0:
                    from olympus.muses.clio import clio
                    digest = clio.narrate(window_days=7)
                    extras["clio"] = (f"digest written "
                                       f"({digest.sessions_run} sessions, "
                                       f"{digest.proposals_ratified} ratified)")
            except Exception as exc:  # noqa: BLE001
                extras["clio"] = f"failed: {type(exc).__name__}: {exc}"

            try:
                # Every 12th iteration: Nemesis runs a counterfactual
                # (bounded — max 1 per pass to keep iteration time
                # reasonable)
                if i % 12 == 0:
                    from olympus.heroes.nemesis import nemesis
                    nrep = nemesis.consider(max_per_pass=1,
                                              cleanup_shadows=True)
                    extras["nemesis"] = (f"{nrep.total} counterfactual(s) "
                                          f"({nrep.actions_considered} "
                                          f"considered)")
            except Exception as exc:  # noqa: BLE001
                extras["nemesis"] = f"failed: {type(exc).__name__}: {exc}"

            duration_ms = (time.perf_counter() - start) * 1000.0
            entry = IterationLog(
                iteration=i, ts=Nyx.now().isoformat(),
                duration_ms=duration_ms,
                session_ok=session_ok, improve_ok=improve_ok,
                panicked=False,
                detail={"session": session_summary,
                        "improve": improve_summary,
                        **extras},
            )
            _log_line({"event": "daemon.iteration", **entry.__dict__})
            if on_iteration is not None:
                try:
                    on_iteration(entry)
                except Exception:  # noqa: BLE001
                    pass

            if max_iterations < 0 or i < max_iterations:
                time.sleep(interval_seconds)
    except KeyboardInterrupt:
        _log_line({"event": "daemon.signal", "ts": Nyx.now().isoformat(),
                   "signal": "SIGINT", "iterations_completed": i})
    finally:
        _log_line({"event": "daemon.stop",
                   "ts": Nyx.now().isoformat(),
                   "iterations_completed": i})


# ─────────────────────────────────────────────────────────
# Install / uninstall — OS-specific
# ─────────────────────────────────────────────────────────


def _invoke_path() -> str:
    """Absolute path to the invoke script."""
    return str(root.child("scripts", "invoke"))


def _olympus_home() -> str:
    return str(root.root)


def _log_path_absolute() -> str:
    return str(root.child(*LOG_PATH.split("/")))


def _render_template(name: str, *, interval_seconds: int) -> str:
    tmpl_path = root.child(TEMPLATE_DIR, name)
    text = tmpl_path.read_text(encoding="utf-8")
    return (text
            .replace("{LABEL}", LABEL)
            .replace("{INVOKE_PATH}", _invoke_path())
            .replace("{OLYMPUS_HOME}", _olympus_home())
            .replace("{INTERVAL_SECONDS}", str(interval_seconds))
            .replace("{LOG_PATH}", _log_path_absolute()))


def _launchd_target_path() -> pathlib.Path:
    return pathlib.Path.home() / "Library" / "LaunchAgents" / LAUNCHD_PLIST_NAME


def _systemd_target_path() -> pathlib.Path:
    return (pathlib.Path.home() / ".config" / "systemd" / "user" /
            SYSTEMD_UNIT_NAME)


def install(*, interval_seconds: int = DEFAULT_INTERVAL_SECONDS,
            dry_run: bool = False) -> dict[str, Any]:
    """Generate and install the OS unit. Idempotent — re-install is
    safe (re-writes the file, reloads the unit)."""
    sysname = platform.system()
    if sysname == "Darwin":
        return _install_launchd(interval_seconds=interval_seconds,
                                dry_run=dry_run)
    if sysname == "Linux":
        return _install_systemd(interval_seconds=interval_seconds,
                                dry_run=dry_run)
    return {
        "platform": sysname,
        "installed": False,
        "detail": f"unsupported platform {sysname!r}; "
                  "use scripts/loop.sh in cron instead",
    }


def _install_launchd(*, interval_seconds: int,
                     dry_run: bool) -> dict[str, Any]:
    rendered = _render_template("com.olympus.daemon.plist.tmpl",
                                interval_seconds=interval_seconds)
    target = _launchd_target_path()
    if dry_run:
        return {"platform": "Darwin", "installed": False,
                "would_write": str(target), "rendered_bytes": len(rendered),
                "preview": rendered[:200]}
    target.parent.mkdir(parents=True, exist_ok=True)
    # Idempotent: unload any prior version, write new, load
    if target.exists() and shutil.which("launchctl"):
        subprocess.run(["launchctl", "unload", str(target)],
                       capture_output=True, check=False)
    target.write_text(rendered, encoding="utf-8")
    if shutil.which("launchctl"):
        load = subprocess.run(["launchctl", "load", str(target)],
                              capture_output=True, text=True, check=False)
        detail = f"loaded: {load.stdout.strip() or 'ok'}"
        if load.returncode != 0:
            detail = f"load failed: {load.stderr.strip()}"
    else:
        detail = "written but launchctl not found (cannot load)"
    return {"platform": "Darwin", "installed": True,
            "unit_path": str(target), "detail": detail,
            "interval_seconds": interval_seconds}


def _install_systemd(*, interval_seconds: int,
                     dry_run: bool) -> dict[str, Any]:
    rendered = _render_template("olympus-daemon.service.tmpl",
                                interval_seconds=interval_seconds)
    target = _systemd_target_path()
    if dry_run:
        return {"platform": "Linux", "installed": False,
                "would_write": str(target), "rendered_bytes": len(rendered),
                "preview": rendered[:200]}
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(rendered, encoding="utf-8")
    if shutil.which("systemctl"):
        reload = subprocess.run(["systemctl", "--user", "daemon-reload"],
                                capture_output=True, text=True, check=False)
        enable = subprocess.run(["systemctl", "--user", "enable", "--now",
                                 SYSTEMD_UNIT_NAME],
                                capture_output=True, text=True, check=False)
        detail = (f"daemon-reload: {reload.returncode == 0}; "
                  f"enable: {enable.returncode == 0}")
        if enable.returncode != 0:
            detail += f"  stderr: {enable.stderr.strip()}"
    else:
        detail = "written but systemctl not found (cannot enable)"
    return {"platform": "Linux", "installed": True,
            "unit_path": str(target), "detail": detail,
            "interval_seconds": interval_seconds}


def uninstall(*, dry_run: bool = False) -> dict[str, Any]:
    """Remove the OS unit. Idempotent — removing twice is a no-op."""
    sysname = platform.system()
    if sysname == "Darwin":
        target = _launchd_target_path()
        if dry_run:
            return {"platform": "Darwin", "would_remove": str(target),
                    "exists": target.exists()}
        if target.exists() and shutil.which("launchctl"):
            subprocess.run(["launchctl", "unload", str(target)],
                           capture_output=True, check=False)
        existed = target.exists()
        if existed:
            target.unlink()
        return {"platform": "Darwin", "removed": existed,
                "unit_path": str(target)}
    if sysname == "Linux":
        target = _systemd_target_path()
        if dry_run:
            return {"platform": "Linux", "would_remove": str(target),
                    "exists": target.exists()}
        if target.exists() and shutil.which("systemctl"):
            subprocess.run(["systemctl", "--user", "disable", "--now",
                            SYSTEMD_UNIT_NAME], capture_output=True,
                           check=False)
        existed = target.exists()
        if existed:
            target.unlink()
        return {"platform": "Linux", "removed": existed,
                "unit_path": str(target)}
    return {"platform": sysname, "removed": False,
            "detail": f"unsupported platform {sysname!r}"}


def status() -> DaemonStatus:
    """Query the OS to determine whether the daemon is loaded/running."""
    sysname = platform.system()
    if sysname == "Darwin":
        return _status_launchd()
    if sysname == "Linux":
        return _status_systemd()
    return DaemonStatus(
        platform=sysname, installed=False, running=False,
        detail=f"unsupported platform {sysname!r}",
    )


def _status_launchd() -> DaemonStatus:
    target = _launchd_target_path()
    installed = target.exists()
    running = False
    pid: int | None = None
    detail = ""
    if installed and shutil.which("launchctl"):
        result = subprocess.run(["launchctl", "list", LABEL],
                                capture_output=True, text=True, check=False)
        if result.returncode == 0:
            running = True
            # parse PID
            for line in result.stdout.splitlines():
                if line.strip().startswith('"PID"'):
                    try:
                        pid = int(line.split("=", 1)[1].strip().rstrip(";"))
                    except (ValueError, IndexError):
                        pass
            detail = "launchctl reports loaded"
        else:
            detail = "plist written but launchctl reports not loaded"
    elif installed:
        detail = "plist written but launchctl not found"
    return DaemonStatus(
        platform="Darwin", installed=installed, running=running,
        unit_path=str(target), detail=detail, pid=pid,
    )


def _status_systemd() -> DaemonStatus:
    target = _systemd_target_path()
    installed = target.exists()
    running = False
    detail = ""
    if installed and shutil.which("systemctl"):
        result = subprocess.run(["systemctl", "--user", "is-active",
                                 SYSTEMD_UNIT_NAME],
                                capture_output=True, text=True, check=False)
        running = (result.returncode == 0
                   and result.stdout.strip() == "active")
        detail = f"is-active: {result.stdout.strip() or '(empty)'}"
    elif installed:
        detail = "unit written but systemctl not found"
    return DaemonStatus(
        platform="Linux", installed=installed, running=running,
        unit_path=str(target), detail=detail,
    )
