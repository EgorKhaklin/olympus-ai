"""olympus.runtime — hardening utilities.

These are the operational primitives that keep Olympus running under
real load:

  boundaries.py    error-boundary decorator (Hecate at the crossroads)
  concurrency.py   thread-safe wrappers + Megaera integration
  persistence.py   JSONL compaction + rotation
  recovery.py      Hades + Iapetus integration on component end
"""

from olympus.runtime.boundaries import bounded, BoundaryResult
from olympus.runtime.concurrency import with_lock, atomic_append
from olympus.runtime.persistence import compact_jsonl, rotate_jsonl
from olympus.runtime.recovery import retire_component

__all__ = [
    "bounded", "BoundaryResult",
    "with_lock", "atomic_append",
    "compact_jsonl", "rotate_jsonl",
    "retire_component",
]
