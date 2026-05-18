"""Ariadne — princess of Crete, giver of the thread.

In myth: King Minos's daughter. When Theseus volunteered to enter the
Labyrinth and kill the Minotaur, Ariadne gave him a ball of thread to
unwind on his way in — so he could find his way back out. The thread
was the bridge between *being inside the maze* and *understanding
where you came from*.

In Olympus, Ariadne is the **causal-lineage tracer**. Mnemosyne
records *what* happened; Ariadne lets you ask *what caused what*. Each
load-bearing write can optionally carry:

  - `trace_id`         — a unique id for this work
  - `parent_trace_id`  — the trace_id of the event that caused this

She builds the thread at *query time*. Old records without traces
simply produce shorter chains — backward-compatible by design.

Two surfaces:
  - `ariadne.thread(kind, actor, summary, parent_trace_id=..., **body)`
    is a thin wrapper around mnemosyne.remember that auto-generates a
    trace_id and threads the parent reference through.
  - `ariadne.chain(trace_id)` walks back-pointers to produce the full
    causal chain from the requested event to its root cause.

Per Delphi 2026-05-18-labyrinth-arc.md.
"""
from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from typing import Any, Iterator

from olympus.primordials.nyx import Nyx
from olympus.titans.mnemosyne import mnemosyne


@dataclass
class TracedEvent:
    """One event in a causal chain."""
    trace_id: str
    parent_trace_id: str = ""
    kind: str = ""
    actor: str = ""
    summary: str = ""
    remembered_at: str = ""
    body: dict[str, Any] = field(default_factory=dict)


@dataclass
class CausalChain:
    """The thread from a leaf event back to its root."""
    leaf_trace_id: str
    events: list[TracedEvent] = field(default_factory=list)
    root_reached: bool = False
    depth: int = 0
    truncated_at_depth: int = 0  # > 0 if cycle/cap forced a stop


class Ariadne:
    """The giver of the thread. Causal-lineage tracer."""

    MAX_DEPTH = 64

    def thread(self, *, kind: str, actor: str, summary: str,
                parent_trace_id: str = "",
                trace_id: str | None = None,
                **body: Any) -> str:
        """Wrap mnemosyne.remember with automatic trace_id generation
        and parent-pointer threading. Returns the new event's trace_id."""
        if trace_id is None:
            trace_id = self._generate_trace_id()
        # Embed the trace fields inside the body — Mnemosyne body is
        # the only place we can put structured per-record data.
        body_with_trace = dict(body)
        body_with_trace["trace_id"] = trace_id
        if parent_trace_id:
            body_with_trace["parent_trace_id"] = parent_trace_id
        mnemosyne.remember(kind=kind, actor=actor, summary=summary,
                           **body_with_trace)
        return trace_id

    def chain(self, trace_id: str) -> CausalChain:
        """Walk backward from `trace_id` through parent pointers; return
        the events in order [leaf, ..., root]. Bounded by MAX_DEPTH to
        survive cycles or malformed data."""
        chain = CausalChain(leaf_trace_id=trace_id)
        index = self._build_index()
        current = trace_id
        visited: set[str] = set()
        for depth in range(self.MAX_DEPTH):
            if current in visited:
                chain.truncated_at_depth = depth
                break
            visited.add(current)
            event = index.get(current)
            if event is None:
                break
            chain.events.append(event)
            chain.depth = depth + 1
            parent = event.parent_trace_id
            if not parent:
                chain.root_reached = True
                break
            current = parent
        else:
            chain.truncated_at_depth = self.MAX_DEPTH
        return chain

    def descendants(self, trace_id: str) -> list[TracedEvent]:
        """Find every event whose parent_trace_id is `trace_id`, then
        recursively their descendants. Returns flat list in
        breadth-first order."""
        # Build reverse index: parent → [children]
        children: dict[str, list[TracedEvent]] = {}
        index = self._build_index()
        for ev in index.values():
            if ev.parent_trace_id:
                children.setdefault(ev.parent_trace_id, []).append(ev)
        out: list[TracedEvent] = []
        queue = list(children.get(trace_id, []))
        seen: set[str] = set()
        while queue:
            ev = queue.pop(0)
            if ev.trace_id in seen:
                continue
            seen.add(ev.trace_id)
            out.append(ev)
            queue.extend(children.get(ev.trace_id, []))
        return out

    # ─────────────────────────────────────────────────────────
    # Internal — scan Mnemosyne and build trace_id → event index
    # ─────────────────────────────────────────────────────────

    @staticmethod
    def _build_index() -> dict[str, TracedEvent]:
        """Walk every Mnemosyne kind once; index by trace_id. The
        index is materialized fresh each call — Ariadne does not
        cache, because the audit-of-record is the only source of
        truth (S1)."""
        out: dict[str, TracedEvent] = {}
        for kind in mnemosyne.kinds():
            # mnemosyne.kinds() returns the sanitized filename stems;
            # we have to recover the dotted form by trying both.
            # Easier: read the file directly via mnemosyne.recall(kind)
            # by reconstructing the kind. The file stem is what we
            # have. Skip if it's not parseable.
            for m in mnemosyne.recall(kind):
                body = m.body or {}
                tid = body.get("trace_id")
                if not tid:
                    continue
                out[str(tid)] = TracedEvent(
                    trace_id=str(tid),
                    parent_trace_id=str(body.get("parent_trace_id", "")),
                    kind=m.kind, actor=m.actor, summary=m.summary,
                    remembered_at=m.remembered_at, body=body,
                )
        return out

    @staticmethod
    def _generate_trace_id() -> str:
        return f"t-{uuid.uuid4().hex[:16]}"


ariadne = Ariadne()
