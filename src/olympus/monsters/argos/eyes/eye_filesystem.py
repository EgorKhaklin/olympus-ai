"""eye_filesystem — operator-declared filesystem watchers.

Per Delphi 2026-05-19-argos-eyes-arc.md.

One FilesystemEye per `WatchSpec` declared in
`state/config.json::argos.watches[]`. Each scan compares the current
fs snapshot against the persisted baseline and emits findings for
each added / modified / deleted file. Baseline is established on
first scan (no findings); subsequent scans report deltas.

Action types (per-watch):
  - "alert"          → just emit pheromone (default; cheap)
  - "errand:<name>"  → emit pheromone + record an intent to run the
                        named errand (the operator/daemon picks it up)

Action execution is NOT done by the Eye itself (Eyes are read-only by
S3); the Eye emits findings, and a downstream consumer can act on the
intent. This preserves S4 (decentralized eyes).
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any

from olympus.monsters.argos.base import (
    Eye, EyeFinding, KIND_INFO, KIND_DRIFT, KIND_ALERT,
)
from olympus.runtime.fs_watcher import (
    FsSnapshot, diff, load_snapshot, save_snapshot,
)


# ─────────────────────────────────────────────────────────────────────
# WatchSpec — operator-declared
# ─────────────────────────────────────────────────────────────────────


# Whitelist of errand names allowed in `action: "errand:<name>"`.
# Per Delphi 2026-05-19-chronos-arc.md: refactored to a shared module
# so Argos and Chronos use one source of truth. Backward-compat alias
# preserved for existing imports and tests.
from olympus.runtime.errand_whitelist import AUTOMATED_ERRANDS
ERRAND_WHITELIST: frozenset[str] = AUTOMATED_ERRANDS


# Valid id pattern (filesystem-safe)
_ID_RX = re.compile(r"^[a-zA-Z0-9_\-]{1,64}$")


@dataclass
class WatchSpec:
    """One operator-declared filesystem watch."""
    id: str                         # short stable identifier
    path: str                       # absolute or ~-prefixed
    glob: str = "*"
    action: str = "alert"           # "alert" | "errand:<whitelisted>"
    enabled: bool = True
    max_files: int = 500

    def validate(self) -> tuple[bool, str]:
        """Return (ok, error_message). Strict: bad specs are loud."""
        if not _ID_RX.match(self.id or ""):
            return (False,
                    f"watch id {self.id!r} must match {_ID_RX.pattern}")
        if not self.path:
            return (False, "watch path must be non-empty")
        if self.action == "alert":
            return (True, "")
        if self.action.startswith("errand:"):
            errand_name = self.action.split(":", 1)[1]
            if errand_name not in ERRAND_WHITELIST:
                return (False,
                        f"errand {errand_name!r} not in whitelist "
                        f"({sorted(ERRAND_WHITELIST)})")
            return (True, "")
        return (False,
                f"action {self.action!r} must be 'alert' or "
                f"'errand:<name>'")


# ─────────────────────────────────────────────────────────────────────
# The Eye class — one instance per WatchSpec
# ─────────────────────────────────────────────────────────────────────


class FilesystemEye(Eye):
    """One Eye instance per operator-declared filesystem watch."""

    SLICE_PREFIX = "filesystem/"

    def __init__(self, spec: WatchSpec) -> None:
        self.spec = spec
        # Make NAME unique per spec so the colony can register multiple
        self.NAME = f"eye_fs_{spec.id}"
        self.SLICE = f"{self.SLICE_PREFIX}{spec.id}"

    def scan(self) -> list[EyeFinding]:
        if not self.spec.enabled:
            return []
        # Validate first — bad specs emit an alert and do nothing else
        ok, err = self.spec.validate()
        if not ok:
            return [self._finding(KIND_ALERT,
                f"watch spec invalid: {err}",
                intensity=8.0, spec_id=self.spec.id)]

        # Snapshot now
        current = FsSnapshot.take(self.spec.path,
                                    glob=self.spec.glob,
                                    max_files=self.spec.max_files)
        if not current and not load_snapshot(self.spec.id):
            # Path doesn't exist AND we have no baseline → just info
            return [self._finding(KIND_INFO,
                f"watch '{self.spec.id}': path does not exist yet",
                path=self.spec.path)]

        previous = load_snapshot(self.spec.id)
        changes = diff(previous, current)
        # Always persist current snapshot for next pass
        save_snapshot(self.spec.id, current)

        # First-ever scan establishes baseline; no findings
        if previous is None:
            return [self._finding(KIND_INFO,
                f"watch '{self.spec.id}': baseline established "
                f"({len(current)} file(s))",
                file_count=len(current))]

        if not changes:
            return [self._finding(KIND_INFO,
                f"watch '{self.spec.id}': no changes "
                f"({len(current)} file(s))",
                file_count=len(current))]

        # Emit one finding per change. Use DRIFT for modifications,
        # ALERT for added/deleted (more attention-worthy by default).
        # Higher intensity if action='errand:' (operator wants action).
        intensity_base = 5.0 if self.spec.action.startswith("errand:") \
                         else 3.0
        out: list[EyeFinding] = []
        for ch in changes:
            kind = (KIND_DRIFT if ch.change_type == "modified"
                    else KIND_ALERT)
            detail = (f"watch '{self.spec.id}': {ch.change_type} "
                      f"{ch.path}")
            out.append(self._finding(
                kind, detail,
                intensity=intensity_base,
                spec_id=self.spec.id,
                action=self.spec.action,
                change_type=ch.change_type,
                path=ch.path,
                sha_before=ch.sha_before,
                sha_after=ch.sha_after,
                size_before=ch.size_before,
                size_after=ch.size_after,
            ))
        return out


# ─────────────────────────────────────────────────────────────────────
# Spec loading from config
# ─────────────────────────────────────────────────────────────────────


def watch_specs_from_config() -> list[WatchSpec]:
    """Read state/config.json::argos.watches[] and return a list of
    WatchSpec. Invalid specs are dropped with a warning to stderr
    (we don't want one bad watch to break the colony)."""
    import sys as _sys
    try:
        from olympus.runtime.config import load as load_config
        cfg = load_config()
    except Exception:  # noqa: BLE001
        return []
    raw = getattr(cfg.argos, "watches", None) or []
    specs: list[WatchSpec] = []
    for entry in raw:
        if not isinstance(entry, dict):
            continue
        try:
            spec = WatchSpec(
                id=str(entry.get("id", "")),
                path=str(entry.get("path", "")),
                glob=str(entry.get("glob", "*")),
                action=str(entry.get("action", "alert")),
                enabled=bool(entry.get("enabled", True)),
                max_files=int(entry.get("max_files", 500)),
            )
        except Exception as exc:  # noqa: BLE001
            _sys.stderr.write(
                f"[argos-eyes] skipping malformed watch: {exc}\n")
            continue
        ok, err = spec.validate()
        if not ok:
            _sys.stderr.write(
                f"[argos-eyes] skipping invalid watch "
                f"{spec.id!r}: {err}\n")
            continue
        specs.append(spec)
    return specs


def register_filesystem_eyes(colony: Any) -> int:
    """Register one FilesystemEye per configured WatchSpec on `colony`.
    Returns count registered. Idempotent — calling twice is safe."""
    specs = watch_specs_from_config()
    n = 0
    for spec in specs:
        try:
            colony.register(FilesystemEye(spec))
            n += 1
        except Exception:  # noqa: BLE001
            continue
    return n


__all__ = [
    "WatchSpec", "FilesystemEye",
    "ERRAND_WHITELIST",
    "watch_specs_from_config", "register_filesystem_eyes",
]
