"""Pytest configuration.

Two responsibilities:

1. Add `src/` to sys.path so `import olympus` works when tests are run
   from the repo root.

2. **Real-state contamination guard** — per Delphi 2026-05-19-pause-arc.md.
   At session start, snapshot sha256 of each watched file under `state/`.
   At session end, re-snapshot and fail the entire suite if anything
   changed.

   Motivation: the Hades arc demonstrated that a test using
   `monkeypatch.setenv("OLYMPUS_STATE_DIR", ...)` does NOT actually
   redirect `runtime.config._path()` (which is anchored to project root).
   The test wrote to the real `state/config.json` and clobbered the
   operator's API key while passing green. This guard makes that class
   of bug LOUD: contamination → suite-level failure with the offending
   file + sha-before + sha-after, recorded to Mnemosyne under
   `test.session-guard`.

   Opt-out for legitimate state writes (rare):
       OLYMPUS_TEST_ALLOW_STATE_WRITE=1 pytest ...
"""
from __future__ import annotations

import hashlib
import os
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))


# ─────────────────────────────────────────────────────────────────────
# Real-state contamination guard
# ─────────────────────────────────────────────────────────────────────


_STATE_DIR = ROOT / "state"

# Files we watch for changes during the suite. We focus on
# operator-bearing config + rebuilt artifacts; we deliberately do NOT
# watch the entire state/ tree because many tests legitimately add to
# .jsonl audit logs (append is fine; replace is the failure mode).
_WATCHED_RELS: tuple[str, ...] = (
    "config.json",
)


def _sha256_of(p: pathlib.Path) -> str | None:
    """Return hex sha256 of a file's contents, or None if absent."""
    try:
        return hashlib.sha256(p.read_bytes()).hexdigest()
    except (OSError, FileNotFoundError):
        return None


def _snapshot_watched() -> dict[str, str | None]:
    """Map relative-name → sha (or None if absent)."""
    return {rel: _sha256_of(_STATE_DIR / rel) for rel in _WATCHED_RELS}


# Module-level cache populated at session start
_BEFORE: dict[str, str | None] = {}


def pytest_configure(config):  # noqa: ARG001 (pytest hook)
    """Session start: snapshot the watched files."""
    global _BEFORE
    _BEFORE = _snapshot_watched()


def pytest_sessionfinish(session, exitstatus):  # noqa: ARG001
    """Session end: compare. Fail the suite if any watched file's sha
    changed AND the opt-out env var isn't set."""
    if os.environ.get("OLYMPUS_TEST_ALLOW_STATE_WRITE") == "1":
        return
    after = _snapshot_watched()
    changed = [(rel, _BEFORE.get(rel), after.get(rel))
               for rel in _WATCHED_RELS
               if _BEFORE.get(rel) != after.get(rel)]
    if not changed:
        return

    # Record the violation to Mnemosyne (if importable)
    try:
        from olympus.titans.mnemosyne import mnemosyne
        mnemosyne.remember(
            kind="test.session-guard",
            actor="conftest.guard",
            summary=(f"REAL-STATE CONTAMINATION: "
                     f"{len(changed)} watched file(s) changed"),
            changed=[{"file": rel, "before": b, "after": a}
                     for rel, b, a in changed],
        )
    except Exception:  # noqa: BLE001
        pass

    msg_lines = [
        "",
        "═" * 70,
        "  OLYMPUS REAL-STATE CONTAMINATION GUARD FIRED",
        "═" * 70,
        "",
        "  A test modified file(s) under state/ that should have",
        "  remained untouched. This is the AP7 failure mode the Hades",
        "  arc exposed: a green suite while real state was being",
        "  corrupted. Find the offending test (most likely one that",
        "  uses `monkeypatch.setenv(\"OLYMPUS_STATE_DIR\", ...)` and",
        "  then calls `save()` — see Delphi 2026-05-19-pause-arc.md).",
        "",
        "  Files changed:",
    ]
    for rel, before, after in changed:
        msg_lines.append(f"    state/{rel}")
        msg_lines.append(f"      before: {before or '(absent)'}")
        msg_lines.append(f"      after:  {after or '(absent)'}")
    msg_lines.extend([
        "",
        "  If this write was intentional, re-run with:",
        "      OLYMPUS_TEST_ALLOW_STATE_WRITE=1 pytest",
        "═" * 70,
        "",
    ])
    sys.stderr.write("\n".join(msg_lines))
    # Override exit status to fail
    session.exitstatus = max(session.exitstatus or 0, 4)
