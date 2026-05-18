"""olympus.runtime.persistence — JSONL compaction + rotation.

Olympus's append-only files (Mnemosyne records, Styx oaths, Argos
pheromones, the action queue) grow without bound. This module provides:

  - `rotate_jsonl(path, max_lines=N)` — when a JSONL exceeds N lines,
    move the older portion to an archive file with a date suffix.
  - `compact_jsonl(path, keep_predicate)` — drop rows that no longer
    satisfy `keep_predicate`. Used carefully — this CAN'T be applied
    to Styx (S1 audit-of-record immutability) but is appropriate for
    pheromones and cache-like state.
  - `integrity_check(path)` — every line must parse as JSON; reports
    the first broken line for triage.

All operations create a `.tmp` file first, fsync, then rename, so
crashes during operation don't leave a half-written file.
"""
from __future__ import annotations

import json
import os
import pathlib
from typing import Callable, Any

from olympus.primordials.nyx import Nyx
from olympus.underworld.hades import descend
from olympus.titans.mnemosyne import mnemosyne


def integrity_check(path: pathlib.Path) -> tuple[bool, int | None, str | None]:
    """Walk the file line-by-line, JSON-parse each. Returns
    (intact, first_bad_line, error_message)."""
    if not path.exists():
        return True, None, None
    with path.open("r", encoding="utf-8") as f:
        for i, line in enumerate(f, start=1):
            line = line.rstrip("\n")
            if not line:
                continue
            try:
                json.loads(line)
            except json.JSONDecodeError as exc:
                return False, i, str(exc)
    return True, None, None


def rotate_jsonl(path: pathlib.Path, *, max_lines: int = 10_000) -> pathlib.Path | None:
    """If path exceeds max_lines, move the first half to an archive."""
    if not path.exists():
        return None
    with path.open("r", encoding="utf-8") as f:
        lines = f.readlines()
    if len(lines) <= max_lines:
        return None

    cut = len(lines) // 2
    archive_lines, live_lines = lines[:cut], lines[cut:]

    ts = Nyx.now().strftime("%Y%m%dT%H%M%S")
    archive_path = path.with_name(f"{path.stem}--{ts}-archive{path.suffix}")
    tmp = path.with_suffix(path.suffix + ".tmp")

    archive_path.write_text("".join(archive_lines), encoding="utf-8")
    tmp.write_text("".join(live_lines), encoding="utf-8")
    fd = os.open(str(tmp), os.O_RDONLY)
    try:
        os.fsync(fd)
    finally:
        os.close(fd)
    tmp.replace(path)

    # Hades archives the moved chunk for inspection
    descend(f"jsonl-rotated--{path.name}", {
        "archived_path": str(archive_path),
        "archived_lines": len(archive_lines),
        "remaining_lines": len(live_lines),
    })
    mnemosyne.remember(
        kind="persistence.rotated",
        actor="persistence",
        summary=f"rotated {path.name}: {len(archive_lines)} → archive, "
                f"{len(live_lines)} remain",
        path=str(path), archive=str(archive_path),
    )
    return archive_path


def compact_jsonl(path: pathlib.Path, *,
                  keep_predicate: Callable[[dict[str, Any]], bool]) -> int:
    """Read every row; keep only those satisfying keep_predicate; rewrite.
    Returns the number of rows dropped.

    USE WITH CARE: do not apply to Styx (S1 immutability). Safe for
    pheromone logs, action queues, transition ledgers."""
    if not path.exists():
        return 0
    with path.open("r", encoding="utf-8") as f:
        all_rows = [json.loads(line) for line in f if line.strip()]
    kept = [r for r in all_rows if keep_predicate(r)]
    dropped = len(all_rows) - len(kept)
    if dropped == 0:
        return 0
    tmp = path.with_suffix(path.suffix + ".tmp")
    with tmp.open("w", encoding="utf-8") as f:
        for r in kept:
            f.write(json.dumps(r, default=str) + "\n")
    fd = os.open(str(tmp), os.O_RDONLY)
    try:
        os.fsync(fd)
    finally:
        os.close(fd)
    tmp.replace(path)
    mnemosyne.remember(
        kind="persistence.compacted",
        actor="persistence",
        summary=f"compacted {path.name}: dropped {dropped} of {len(all_rows)}",
        path=str(path),
    )
    return dropped
