"""Notes capture + recall + topic inference.

Notes are stored as Mnemosyne entries under kind="note.captured". Each
note has an id (Eros-derived), text, inferred topics, and a captured-at
timestamp. C1 (append-only) is satisfied because Mnemosyne is the only
write path.
"""
from __future__ import annotations

import datetime
import re
from dataclasses import dataclass, field
from typing import Iterable

from olympus.primordials.eros import Eros
from olympus.primordials.nyx import Nyx
from olympus.titans.cronus import Cronus
from olympus.titans.mnemosyne import mnemosyne


_KIND = "note.captured"

# Minimal stopword list — topics come from the words that aren't these
_STOPWORDS = frozenset("""
the a an of and or but if then so to from on in by at for with as is are
was were be been being it its this that these those have has had not no
yes do does did i me my we us our you your they them their he she him her
his hers what which who when where why how all any some most more less
about into onto over under between through during after before
""".split())


@dataclass
class Note:
    id: str
    text: str
    topics: list[str]
    captured_at: str


# ─────────────────────────────────────────────────────────────────
# Capture
# ─────────────────────────────────────────────────────────────────


def infer_topics(text: str, *, max_topics: int = 5) -> list[str]:
    """Pure-function topic inference from text alone (C2 enforced by
    the domain — topics come ONLY from the captured text).

    Strategy: lowercase, tokenize, drop stopwords + short tokens,
    rank by frequency, return the top N stems.
    """
    if not text or not text.strip():
        return []
    tokens = re.findall(r"[A-Za-z][A-Za-z0-9]{2,}", text.lower())
    counts: dict[str, int] = {}
    for tok in tokens:
        if tok in _STOPWORDS:
            continue
        counts[tok] = counts.get(tok, 0) + 1
    ranked = sorted(counts.items(), key=lambda kv: (-kv[1], kv[0]))
    return [tok for tok, _ in ranked[:max_topics]]


def capture(text: str, *, operator: str = "operator") -> Note:
    """Capture a note. Refuses empty text (AP-NK1). Records via
    Mnemosyne (C1 append-only)."""
    text = (text or "").strip()
    if not text:
        raise ValueError("notekeeper: capture-without-text refused (AP-NK1)")
    topics = infer_topics(text)
    note_id = Eros.begotten_id(
        prefix="note",
        seed=f"{operator}::{Nyx.now().isoformat()}::{text[:50]}",
    )
    note = Note(
        id=note_id,
        text=text,
        topics=topics,
        captured_at=Nyx.now().isoformat(),
    )
    mnemosyne.remember(
        kind=_KIND,
        actor=operator,
        summary=f"captured: {text[:80]}",
        note_id=note_id,
        text=text,
        topics=topics,
    )
    return note


# ─────────────────────────────────────────────────────────────────
# Recall
# ─────────────────────────────────────────────────────────────────


def _rehydrate(memory) -> Note:
    return Note(
        id=memory.body.get("note_id", ""),
        text=memory.body.get("text", ""),
        topics=list(memory.body.get("topics", [])),
        captured_at=memory.remembered_at,
    )


def all_notes() -> list[Note]:
    return [_rehydrate(m) for m in mnemosyne.recall(_KIND)]


def by_id(note_id: str) -> Note | None:
    for m in mnemosyne.recall(_KIND):
        if m.body.get("note_id") == note_id:
            return _rehydrate(m)
    return None


def by_topic(topic: str) -> list[Note]:
    topic = topic.lower()
    out: list[Note] = []
    for m in mnemosyne.recall(_KIND):
        if topic in (t.lower() for t in m.body.get("topics", [])):
            out.append(_rehydrate(m))
    return out


def notes_in_window(*, max_age_hours: float) -> list[Note]:
    """All notes captured in the last `max_age_hours` hours."""
    out: list[Note] = []
    for n in all_notes():
        if Cronus.age_seconds(n.captured_at) / 3600.0 <= max_age_hours:
            out.append(n)
    return out
