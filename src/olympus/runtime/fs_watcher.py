"""olympus.runtime.fs_watcher — pure-Python filesystem snapshotter.

Per Delphi 2026-05-19-argos-eyes-arc.md.

Takes shas + mtimes of files under a watched path; diffs two snapshots
to produce a list of (path, change_type) changes. No deps; safe against
huge trees via `max_files` ceiling and an opinionated skip-list.

Used by `monsters/argos/eyes/eye_filesystem.py` to detect changes the
operator declared interest in via `state/config.json::argos.watches[]`.
"""
from __future__ import annotations

import fnmatch
import hashlib
import json
import os
import pathlib
from dataclasses import dataclass, field, asdict
from typing import Any, Literal


# ─────────────────────────────────────────────────────────────────────
# Data classes
# ─────────────────────────────────────────────────────────────────────


ChangeType = Literal["added", "modified", "deleted"]


@dataclass
class FileState:
    """One observation of one file."""
    sha256: str
    mtime: float
    size: int


@dataclass
class FsChange:
    """One change between two snapshots."""
    path: str
    change_type: ChangeType
    sha_before: str = ""
    sha_after: str = ""
    size_before: int = 0
    size_after: int = 0


# ─────────────────────────────────────────────────────────────────────
# Skip list — paths we NEVER descend into
# ─────────────────────────────────────────────────────────────────────


_SKIP_DIRS: frozenset[str] = frozenset({
    ".git", "__pycache__", "node_modules", ".venv", "venv",
    ".pytest_cache", ".mypy_cache", ".ruff_cache", ".tox",
    "dist", "build", ".idea", ".vscode",
    # The substrate's own audit log — watching it would create feedback
    # (writes to Mnemosyne → fs change → pheromone → write to Mnemosyne)
    "mnemosyne",
})


# Conservative max file size to checksum — large binaries waste time
_MAX_FILE_BYTES = 5 * 1024 * 1024   # 5 MB


# ─────────────────────────────────────────────────────────────────────
# Snapshotting
# ─────────────────────────────────────────────────────────────────────


class FsSnapshot:
    """Snapshot of file states under a watched path."""

    @staticmethod
    def take(path: str | pathlib.Path, *,
              glob: str = "*",
              max_files: int = 500) -> dict[str, FileState]:
        """Walk `path`, compute (sha256, mtime, size) per matching file.
        Returns dict keyed by relative-from-path posix string. Safe
        against huge trees via `max_files` ceiling."""
        out: dict[str, FileState] = {}
        root_path = pathlib.Path(path).expanduser()
        try:
            root_path = root_path.resolve()
        except (OSError, RuntimeError):
            return out  # broken symlink, etc.
        if not root_path.exists():
            return out

        # Single-file watch
        if root_path.is_file():
            state = _hash_file(root_path)
            if state is not None:
                out[root_path.name] = state
            return out

        # Directory walk
        if not root_path.is_dir():
            return out
        count = 0
        for dirpath, dirnames, filenames in os.walk(root_path,
                                                      followlinks=False):
            # Prune skip-dirs in-place
            dirnames[:] = [d for d in dirnames if d not in _SKIP_DIRS]
            for fname in filenames:
                if not fnmatch.fnmatch(fname, glob):
                    continue
                full = pathlib.Path(dirpath) / fname
                try:
                    rel = str(full.relative_to(root_path).as_posix())
                except ValueError:
                    continue
                state = _hash_file(full)
                if state is None:
                    continue
                out[rel] = state
                count += 1
                if count >= max_files:
                    return out
        return out


def _hash_file(p: pathlib.Path) -> FileState | None:
    """sha256 + mtime + size; None if unreadable or too large."""
    try:
        st = p.stat()
    except (OSError, FileNotFoundError):
        return None
    if st.st_size > _MAX_FILE_BYTES:
        # Big binary; record size+mtime without hashing the bytes
        # (changes still detected via size/mtime delta)
        return FileState(
            sha256=f"size-only:{st.st_size}",
            mtime=st.st_mtime, size=st.st_size)
    try:
        data = p.read_bytes()
    except (OSError, PermissionError):
        return None
    return FileState(
        sha256=hashlib.sha256(data).hexdigest(),
        mtime=st.st_mtime, size=st.st_size)


# ─────────────────────────────────────────────────────────────────────
# Diffing
# ─────────────────────────────────────────────────────────────────────


def diff(old: dict[str, FileState] | None,
         new: dict[str, FileState]) -> list[FsChange]:
    """Compute the list of changes from old → new. None = first-time
    baseline (returns empty list — baseline establishes, doesn't
    trigger findings)."""
    if old is None:
        return []
    changes: list[FsChange] = []
    old_keys = set(old.keys())
    new_keys = set(new.keys())
    for path in sorted(new_keys - old_keys):
        ns = new[path]
        changes.append(FsChange(
            path=path, change_type="added",
            sha_after=ns.sha256, size_after=ns.size))
    for path in sorted(old_keys - new_keys):
        os_ = old[path]
        changes.append(FsChange(
            path=path, change_type="deleted",
            sha_before=os_.sha256, size_before=os_.size))
    for path in sorted(old_keys & new_keys):
        os_, ns = old[path], new[path]
        if os_.sha256 != ns.sha256 or os_.size != ns.size:
            changes.append(FsChange(
                path=path, change_type="modified",
                sha_before=os_.sha256, size_before=os_.size,
                sha_after=ns.sha256, size_after=ns.size))
    return changes


# ─────────────────────────────────────────────────────────────────────
# Persistence helpers — snapshots live in state/argos/fs_snapshots/
# ─────────────────────────────────────────────────────────────────────


def _snapshot_dir() -> pathlib.Path:
    from olympus.primordials.gaia import root
    d = root.child("state", "argos", "fs_snapshots")
    d.mkdir(parents=True, exist_ok=True)
    return d


def load_snapshot(watch_id: str) -> dict[str, FileState] | None:
    """Load the persisted snapshot for a watch_id, or None if none yet."""
    if not watch_id:
        return None
    p = _snapshot_dir() / f"{watch_id}.json"
    if not p.exists():
        return None
    try:
        raw = json.loads(p.read_text(encoding="utf-8"))
        return {k: FileState(**v) for k, v in raw.items()}
    except Exception:  # noqa: BLE001
        return None


def save_snapshot(watch_id: str,
                   snapshot: dict[str, FileState]) -> None:
    """Persist a snapshot atomically (tmp + rename)."""
    if not watch_id:
        return
    p = _snapshot_dir() / f"{watch_id}.json"
    tmp = p.with_suffix(".json.tmp")
    data = {k: asdict(v) for k, v in snapshot.items()}
    tmp.write_text(json.dumps(data, indent=2), encoding="utf-8")
    tmp.replace(p)


__all__ = [
    "FileState", "FsChange", "ChangeType",
    "FsSnapshot", "diff",
    "load_snapshot", "save_snapshot",
]
