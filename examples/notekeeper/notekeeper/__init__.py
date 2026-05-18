"""notekeeper — a notes-capture deployment built on Olympus.

This package is intentionally tiny. The substrate (Olympus) handles
audit-of-record, decision discipline, observation, synthesis, etc.
Notekeeper provides only the domain logic: capture, topic inference,
recall.
"""

from notekeeper.notes import (
    Note, capture, all_notes, by_topic, by_id,
    notes_in_window, infer_topics,
)

__all__ = [
    "Note", "capture", "all_notes", "by_topic", "by_id",
    "notes_in_window", "infer_topics",
]
