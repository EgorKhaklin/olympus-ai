"""olympus.runtime.errand_whitelist — single source of truth for the
errands the substrate may run automatically (Argos-Eyes triggers,
Chronos schedules, etc.).

Per Delphi 2026-05-19-chronos-arc.md.

Refactored from Argos-Eyes's local `ERRAND_WHITELIST`: both Argos and
Chronos import from here so adding a new safe-to-automate errand is a
one-line change.

CRITICAL: this list MUST NOT contain any GATED operation (kindle,
ratify, reject, daemon-install/uninstall, panic-clear, purge). Those
require operator-in-person per S7. Throne's GATED_ERRANDS is the
canonical list of what to exclude.
"""
from __future__ import annotations


AUTOMATED_ERRANDS: frozenset[str] = frozenset({
    # Safe read-only / record-only errands the substrate can fire
    # autonomously in response to a trigger (fs change, schedule, etc.)
    "today",      # the single-action oracle (read-only)
    "session",    # one cognitive cycle (mutates derived state only)
    "recall",     # Hippocrene query (read-only)
    "doctor",     # health check (read-only)
    "ferry",      # Charon archive (operates on derived state)
    "spend",      # Plutus report (read-only)
    "heal",       # Asclepius pass (mutates derived state only)
    "blessing",   # Thalia closing blessing (no-op decorative)
    "speak",      # macOS `say` TTS (Throne-Voice arc; read-only output)
})


def is_automated(errand: str) -> bool:
    """True iff `errand` may be triggered automatically by Argos/Chronos."""
    return errand in AUTOMATED_ERRANDS


__all__ = ["AUTOMATED_ERRANDS", "is_automated"]
