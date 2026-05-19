"""olympus.runtime.doctor — single-screen health diagnostic.

Per Delphi 2026-05-18-akropolis-arc.md. Inspired by OpenClaw's
`openclaw doctor` command: one screen, the operator sees everything
they need to triage in 30 seconds.

What it aggregates (all read-only — diagnostic, not corrective):
  - Hygieia wellness (6 cross-module cohesion checks)
  - Pan state (calm / panicked)
  - Atlas burdens currently in flight
  - Styx chain integrity (via Tisiphone)
  - Themis schema + spec counts
  - LLM bridge connectivity (echo always; anthropic if configured)
  - Python version + key deps (psutil optional)
  - state/ disk usage
  - Recent error rate from session.errored
  - Today's oracle headline (the substrate's single-action oracle)
"""
from __future__ import annotations

import os
import platform
import sys
from dataclasses import dataclass, field, asdict
from typing import Any

from olympus.primordials.gaia import root
from olympus.primordials.nyx import Nyx
from olympus.titans.mnemosyne import mnemosyne


@dataclass
class DoctorFinding:
    """One diagnostic finding."""
    name: str
    status: str          # 'ok' | 'warn' | 'fail'
    detail: str


@dataclass
class DoctorReport:
    diagnosed_at: str
    olympus_version: str
    python_version: str
    platform: str
    findings: list[DoctorFinding] = field(default_factory=list)

    @property
    def ok_count(self) -> int:
        return sum(1 for f in self.findings if f.status == "ok")

    @property
    def warn_count(self) -> int:
        return sum(1 for f in self.findings if f.status == "warn")

    @property
    def fail_count(self) -> int:
        return sum(1 for f in self.findings if f.status == "fail")


# ─────────────────────────────────────────────────────────
# Diagnostic helpers
# ─────────────────────────────────────────────────────────


def _check_hygieia() -> DoctorFinding:
    try:
        from olympus.olympians.hygieia import hygieia
        report = hygieia.check()
        if report.incoherent_count > 0:
            return DoctorFinding(
                "hygieia", "fail",
                f"{report.incoherent_count} incoherence(s); see invoke hygieia",
            )
        if report.warning_count > 0:
            return DoctorFinding(
                "hygieia", "warn",
                f"{report.warning_count} warning(s); see invoke hygieia",
            )
        return DoctorFinding(
            "hygieia", "ok",
            f"{report.well_count} well · 0 warning · 0 incoherent",
        )
    except Exception as exc:  # noqa: BLE001
        return DoctorFinding(
            "hygieia", "fail",
            f"check failed: {type(exc).__name__}: {exc}",
        )


def _check_pan() -> DoctorFinding:
    try:
        from olympus.olympians.pan import pan
        state = pan.state()
        if state.panicked:
            return DoctorFinding(
                "pan", "fail",
                f"PANICKED — {state.detail[:80]}",
            )
        return DoctorFinding("pan", "ok", "calm")
    except Exception as exc:  # noqa: BLE001
        return DoctorFinding(
            "pan", "fail",
            f"pan unreachable: {type(exc).__name__}: {exc}",
        )


def _check_atlas() -> DoctorFinding:
    try:
        from olympus.titans.atlas import atlas
        report = atlas.shoulders()
        n = report.current_count
        if n == 0:
            return DoctorFinding("atlas", "ok", "no burdens in flight")
        if n > 50:
            return DoctorFinding(
                "atlas", "warn",
                f"{n} burdens in flight (high) — investigate hung burdens",
            )
        return DoctorFinding(
            "atlas", "ok",
            f"{n} burden(s) in flight",
        )
    except Exception as exc:  # noqa: BLE001
        return DoctorFinding(
            "atlas", "fail",
            f"atlas unreachable: {type(exc).__name__}: {exc}",
        )


def _check_styx() -> DoctorFinding:
    try:
        from olympus.furies.tisiphone import tisiphone
        v = tisiphone.verify_styx()
        if v.intact:
            return DoctorFinding(
                "styx", "ok",
                f"chain intact — {v.detail[:80]}",
            )
        return DoctorFinding(
            "styx", "fail",
            f"chain BROKEN — {v.detail[:100]}",
        )
    except Exception as exc:  # noqa: BLE001
        return DoctorFinding(
            "styx", "fail",
            f"verify failed: {type(exc).__name__}: {exc}",
        )


def _check_themis() -> DoctorFinding:
    try:
        from olympus.titans.themis import themis
        schemas = themis.schemas()
        specs = themis.specs()
        return DoctorFinding(
            "themis", "ok",
            f"{len(schemas)} schemas · {len(specs)} TLA+ specs",
        )
    except Exception as exc:  # noqa: BLE001
        return DoctorFinding(
            "themis", "fail",
            f"themis unreachable: {type(exc).__name__}: {exc}",
        )


def _check_llm_bridge() -> DoctorFinding:
    try:
        from olympus.runtime.llm_bridge import bridge, EchoBridge
        b = bridge()
        if isinstance(b, EchoBridge):
            return DoctorFinding(
                "llm-bridge", "ok",
                "echo (safe default) — set OLYMPUS_LLM=anthropic for real LLM",
            )
        # Try a tiny call as a connectivity check
        resp = b.call(system="doctor connectivity check",
                       user="ping",
                       max_tokens=8, role="doctor")
        if resp.error:
            return DoctorFinding(
                "llm-bridge", "warn",
                f"{b.name} configured but errored: {resp.error[:80]}",
            )
        return DoctorFinding(
            "llm-bridge", "ok",
            f"{b.name} connected (model={resp.model})",
        )
    except Exception as exc:  # noqa: BLE001
        return DoctorFinding(
            "llm-bridge", "warn",
            f"bridge check failed: {type(exc).__name__}: {exc}",
        )


def _check_python_deps() -> DoctorFinding:
    py = sys.version_info
    optional = []
    try:
        import psutil  # noqa: F401
        optional.append("psutil✓")
    except ImportError:
        optional.append("psutil✗")
    try:
        import anthropic  # noqa: F401
        optional.append("anthropic✓")
    except ImportError:
        optional.append("anthropic✗")
    return DoctorFinding(
        "python+deps", "ok",
        f"py{py.major}.{py.minor}.{py.micro} · {' '.join(optional)}",
    )


def _check_state_disk() -> DoctorFinding:
    try:
        state = root.child("state")
        total = 0
        files = 0
        for p in state.rglob("*"):
            if p.is_file():
                total += p.stat().st_size
                files += 1
        mb = total / (1024 * 1024)
        if mb > 500:
            return DoctorFinding(
                "state-disk", "warn",
                f"{mb:.1f} MB across {files} files — consider invoke ferry",
            )
        return DoctorFinding(
            "state-disk", "ok",
            f"{mb:.1f} MB across {files} files",
        )
    except Exception as exc:  # noqa: BLE001
        return DoctorFinding(
            "state-disk", "warn",
            f"could not stat state/: {exc}",
        )


def _check_session_errors() -> DoctorFinding:
    """Recent error rate from session.errored vs session.completed."""
    try:
        errors = mnemosyne.recall("session.errored")
        completed = mnemosyne.recall("session.completed")
        if not completed:
            return DoctorFinding(
                "session-errors", "ok",
                "no sessions yet",
            )
        # Last 50 of each
        recent_e = len(errors[-50:])
        recent_c = len(completed[-50:])
        denom = max(recent_c, 1)
        rate = recent_e / denom
        if rate > 0.2:
            return DoctorFinding(
                "session-errors", "warn",
                f"{recent_e}/{recent_c} recent error rate "
                f"({rate*100:.1f}%) — investigate",
            )
        return DoctorFinding(
            "session-errors", "ok",
            f"{recent_e}/{recent_c} recent ({rate*100:.1f}%)",
        )
    except Exception as exc:  # noqa: BLE001
        return DoctorFinding(
            "session-errors", "warn",
            f"could not check: {exc}",
        )


def _check_today() -> DoctorFinding:
    """Surface the single-action oracle's current priority."""
    try:
        from olympus.runtime.today import today
        action = today()
        status_map = {"urgent": "fail", "noteworthy": "warn",
                      "gentle": "ok", "calm": "ok"}
        return DoctorFinding(
            "today", status_map.get(action.priority, "ok"),
            f"[{action.priority}] {action.headline[:80]}",
        )
    except Exception as exc:  # noqa: BLE001
        return DoctorFinding(
            "today", "warn",
            f"oracle unreachable: {exc}",
        )


# ─────────────────────────────────────────────────────────
# Public — run the full diagnostic
# ─────────────────────────────────────────────────────────


def diagnose() -> DoctorReport:
    """Run every check; return a DoctorReport. Pure read; no mutations."""
    try:
        from olympus import __version__ as _v
    except ImportError:
        _v = "unknown"
    report = DoctorReport(
        diagnosed_at=Nyx.now().isoformat(),
        olympus_version=_v,
        python_version=platform.python_version(),
        platform=f"{platform.system()} {platform.machine()}",
    )
    for check in (
        _check_python_deps,
        _check_hygieia,
        _check_pan,
        _check_styx,
        _check_atlas,
        _check_themis,
        _check_llm_bridge,
        _check_state_disk,
        _check_session_errors,
        _check_today,
    ):
        try:
            report.findings.append(check())
        except Exception as exc:  # noqa: BLE001
            report.findings.append(DoctorFinding(
                name=check.__name__.lstrip("_").replace("_", "-"),
                status="fail",
                detail=f"raised: {type(exc).__name__}: {exc}",
            ))

    mnemosyne.remember(
        kind="doctor.diagnosis",
        actor="doctor",
        summary=(f"diagnosis: {report.ok_count} ok · "
                 f"{report.warn_count} warn · "
                 f"{report.fail_count} fail"),
        ok=report.ok_count,
        warn=report.warn_count,
        fail=report.fail_count,
    )
    return report
