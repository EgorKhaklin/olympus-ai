"""Oceanus — titan of the great river encircling the world.

Oceanus was the personification of the cosmic ocean — the river-belt
that encircled the flat earth. He fathered every river-god and ocean
nymph. In Olympus, Oceanus is the top-level data-flow primitive: he
encircles the whole system, providing the I/O boundary.

Where Poseidon (Olympian) handles internal streams between modules,
Oceanus handles ingress and egress at the system boundary — file
reads, network calls, the outer rim.
"""
from __future__ import annotations

import json
import pathlib
from typing import Any

from olympus.primordials.gaia import root
from olympus.titans.hyperion import hyperion


class Oceanus:
    """I/O boundary helpers. Every read and write goes through here
    when the operator wants to count bytes."""

    def read_text(self, relpath: str) -> str:
        """Read a project-relative text file. Counts a read in Hyperion."""
        path = root.child(relpath)
        text = path.read_text(encoding="utf-8")
        hyperion.incr("oceanus.reads")
        hyperion.incr("oceanus.bytes_read", len(text.encode("utf-8")))
        return text

    def read_json(self, relpath: str) -> Any:
        return json.loads(self.read_text(relpath))

    def write_text(self, relpath: str, content: str) -> pathlib.Path:
        """Write a project-relative text file. Counts a write in Hyperion."""
        path = root.child(relpath)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        hyperion.incr("oceanus.writes")
        hyperion.incr("oceanus.bytes_written", len(content.encode("utf-8")))
        return path

    def write_json(self, relpath: str, data: Any, *, indent: int = 2) -> pathlib.Path:
        return self.write_text(relpath, json.dumps(data, indent=indent, default=str))


oceanus = Oceanus()
