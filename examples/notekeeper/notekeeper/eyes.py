"""notekeeper-specific Argos eyes.

Three eyes that watch the notekeeper domain:
  eye_untopiced_notes    notes captured but with no topics (C2 violation)
  eye_stale_notes        notes older than STALE_DAYS surface as INFO (C3)
  eye_capture_velocity   sudden burst of captures within 1h (C4)

Each Eye is registered in colony.py at the deployment's startup.
"""
from __future__ import annotations

from olympus.monsters.argos.base import Eye, EyeFinding, KIND_INFO, KIND_DRIFT
from olympus.titans.cronus import Cronus


STALE_DAYS = 30
BURST_THRESHOLD = 50


class EyeUntopicedNotes(Eye):
    """C2 enforcement — notes without inferred topics."""
    NAME = "eye_untopiced_notes"
    SLICE = "notekeeper/topics"

    def scan(self) -> list[EyeFinding]:
        from notekeeper.notes import all_notes
        bare = [n for n in all_notes() if not n.topics]
        if bare:
            return [self._finding(KIND_DRIFT,
                f"{len(bare)} note(s) captured with no inferred topics — C2 drift",
                intensity=min(8.0, len(bare) / 5.0),
                bare_ids=[n.id for n in bare[:10]])]
        return [self._finding(KIND_INFO,
            f"all captured notes carry topics ({len(all_notes())} total)")]


class EyeStaleNotes(Eye):
    """C3 surfacing — notes older than STALE_DAYS."""
    NAME = "eye_stale_notes"
    SLICE = "notekeeper/staleness"

    def scan(self) -> list[EyeFinding]:
        from notekeeper.notes import all_notes
        notes = all_notes()
        if not notes:
            return [self._finding(KIND_INFO, "no notes captured yet")]
        stale = [
            n for n in notes
            if Cronus.age_seconds(n.captured_at) / 86400.0 > STALE_DAYS
        ]
        if stale:
            return [self._finding(KIND_INFO,
                f"{len(stale)} note(s) older than {STALE_DAYS} days — "
                f"surface for operator revisit",
                stale_count=len(stale),
                sample_ids=[n.id for n in stale[:5]])]
        return [self._finding(KIND_INFO,
            f"no stale notes ({len(notes)} fresh)")]


class EyeCaptureVelocity(Eye):
    """C4 enforcement — capture-burst detection."""
    NAME = "eye_capture_velocity"
    SLICE = "notekeeper/velocity"

    def scan(self) -> list[EyeFinding]:
        from notekeeper.notes import notes_in_window
        recent = notes_in_window(max_age_hours=1.0)
        if len(recent) > BURST_THRESHOLD:
            return [self._finding(KIND_DRIFT,
                f"{len(recent)} captures in last hour — exceeds threshold "
                f"of {BURST_THRESHOLD}; possible paste-from-elsewhere event",
                intensity=min(8.0, len(recent) / BURST_THRESHOLD * 2.0),
                count_last_hour=len(recent))]
        return [self._finding(KIND_INFO,
            f"capture velocity normal ({len(recent)}/hour)")]


def register_with_colony() -> None:
    """Call this once at deployment startup to register the notekeeper eyes."""
    from olympus.monsters.argos.colony import colony
    for cls in (EyeUntopicedNotes, EyeStaleNotes, EyeCaptureVelocity):
        # Avoid double-registration
        if not any(type(e) is cls for e in colony.eyes()):
            colony.register(cls)
