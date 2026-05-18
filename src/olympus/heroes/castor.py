"""Castor — the mortal twin of the Dioscuri.

In myth: Castor and his immortal brother Pollux were the Dioscuri,
twin sons of Leda. Castor was a horseman and warrior; Pollux a boxer.
When Castor was killed in battle, Pollux begged Zeus to share his
immortality. Zeus placed them in the heavens as the constellation
Gemini, taking turns above the horizon.

In Olympus, Castor is the **shadow session runner**. He spawns a
session in a temporary substrate rooted at a tempdir — *a shadow
Olympus that shares the codex (source of truth) but writes to its own
state*. Production state is never touched. The shadow can apply a
proposed modification (a parameter change, a new handler) and report
what would happen.

Pollux is the comparator. Together they form the canary deploy for
substrate self-modification: run prod, run shadow, compare outcomes,
decide.

Per Delphi 2026-05-18-recursion-arc.md.
"""
from __future__ import annotations

import json
import os
import pathlib
import shutil
import subprocess
import tempfile
import time
from dataclasses import dataclass, field
from typing import Any

from olympus.primordials.gaia import root
from olympus.primordials.nyx import Nyx
from olympus.titans.mnemosyne import mnemosyne


@dataclass
class ShadowReport:
    """Result of one shadow session run."""
    started_at: str
    ended_at: str = ""
    succeeded: bool = False
    return_code: int = -1
    duration_ms: float = 0.0
    shadow_root: str = ""
    session_report: dict[str, Any] = field(default_factory=dict)
    stderr_tail: str = ""
    error: str = ""
    modifications: dict[str, Any] = field(default_factory=dict)


class Castor:
    """The shadow-runner twin. Spawns sessions in tempdir substrates."""

    INVOKE_RELATIVE = "scripts/invoke"

    def shadow_session(self,
                       *,
                       modifications: dict[str, str] | None = None,
                       directive: str | None = None,
                       timeout_seconds: float = 60.0,
                       ) -> ShadowReport:
        """Run one session in a shadow substrate. Returns a ShadowReport.

        `modifications` is a dict of env-var overrides applied to the
        shadow subprocess (e.g., {'OLYMPUS_INTERVAL': '60'}). These
        let us test the effect of a parameter change without touching
        prod settings.

        Production state is **never** touched. The shadow substrate
        has its own state/ tempdir; codex/ and src/ are symlinked
        from prod so behavior matches production source code."""
        report = ShadowReport(
            started_at=Nyx.now().isoformat(),
            modifications=dict(modifications or {}),
        )
        started = time.perf_counter()

        try:
            shadow_root = self._materialize_shadow_root()
            report.shadow_root = str(shadow_root)
        except Exception as exc:  # noqa: BLE001
            report.error = f"materialize-failed: {type(exc).__name__}: {exc}"
            report.ended_at = Nyx.now().isoformat()
            return report

        try:
            cmd_argv = [
                str(shadow_root / self.INVOKE_RELATIVE),
                "--json", "--quiet",
                "session",
            ]
            if directive:
                cmd_argv.append(directive)
            env = os.environ.copy()
            env["OLYMPUS_ROOT"] = str(shadow_root)
            for k, v in (modifications or {}).items():
                env[k] = str(v)

            result = subprocess.run(
                cmd_argv, env=env, cwd=str(shadow_root),
                capture_output=True, text=True,
                timeout=timeout_seconds, check=False,
            )
            report.return_code = result.returncode
            report.stderr_tail = (result.stderr or "")[-2048:]
            stdout = result.stdout or ""
            # The session emits the report as JSON on stdout
            if stdout.strip():
                try:
                    report.session_report = json.loads(stdout)
                    report.succeeded = (result.returncode == 0
                                        and not report.session_report.get(
                                            "error"))
                except json.JSONDecodeError as exc:
                    report.error = (f"json-parse: {exc}; "
                                    f"stdout head: {stdout[:200]!r}")
            else:
                report.error = "shadow subprocess produced no stdout"
        except subprocess.TimeoutExpired:
            report.error = f"shadow timed out after {timeout_seconds}s"
        except Exception as exc:  # noqa: BLE001
            report.error = f"shadow-run failed: {type(exc).__name__}: {exc}"
        finally:
            report.duration_ms = (time.perf_counter() - started) * 1000.0
            report.ended_at = Nyx.now().isoformat()
            # Don't auto-clean — the operator may want to inspect.
            # Asclepius's healer or Charon could clean up later.

        mnemosyne.remember(
            kind="castor.shadow",
            actor="castor",
            summary=(f"shadow session at {report.shadow_root} → "
                     f"rc={report.return_code} "
                     f"succeeded={report.succeeded} "
                     f"({report.duration_ms:.0f}ms)"),
            shadow_root=report.shadow_root,
            succeeded=report.succeeded,
            return_code=report.return_code,
            duration_ms=report.duration_ms,
            modifications=report.modifications,
            error=report.error,
        )
        return report

    # ─────────────────────────────────────────────────────────
    # Internal — materialize a shadow substrate at a tempdir
    # ─────────────────────────────────────────────────────────

    def _materialize_shadow_root(self) -> pathlib.Path:
        """Create a tempdir, symlink codex/ + src/ + scripts/ from prod
        (read-only-ish), copy state/ shallow (so writes don't touch
        prod). Returns the shadow root."""
        prefix = "olympus-shadow-"
        shadow = pathlib.Path(tempfile.mkdtemp(prefix=prefix))

        # Symlink the parts that are read-only-by-design from the
        # shadow's perspective.
        for name in ("codex", "src", "scripts", "pyproject.toml",
                     "LICENSE", "NOTICE", "README.md"):
            src = root.child(name)
            if not src.exists():
                continue
            dst = shadow / name
            try:
                dst.symlink_to(src)
            except OSError:
                # Symlinks not permitted (e.g., Windows) — fall back to copy
                if src.is_dir():
                    shutil.copytree(src, dst, symlinks=True)
                else:
                    shutil.copy2(src, dst)

        # Copy minimal state — Hestia hearth seal + an empty state dir
        # so the substrate believes itself kindled. We do NOT copy
        # mnemosyne/ or styx.jsonl (those are the audit-of-record and
        # the shadow gets a fresh ledger by design).
        state_dir = shadow / "state"
        state_dir.mkdir(exist_ok=True)
        hearth_src = root.child("state", "hestia_hearth.json")
        if hearth_src.exists():
            shutil.copy2(hearth_src, state_dir / "hestia_hearth.json")
        return shadow


castor = Castor()
