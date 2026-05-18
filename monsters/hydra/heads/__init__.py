"""monsters.hydra.heads — the Hydra's nine canonical heads (+).

Each watcher monitors one Olympus dimension. Watchers do not call
LLMs; they are deterministic. The HYDRA host (`monsters.hydra.host`)
aggregates watcher reports and is the only LLM caller.

**The Hydra-9 mythology lives here** (since ). The Lernaean
Hydra had nine mortal heads (Apollodorus). HYDRA's nine watchers
match the canonical count. CM is the immortal 10th head —
narrative only, lives in `MISSION.md` as a constitutional
principle, not in this registry.

Phase 1 (): SchemaWatcher.
Phase 2 (–): CognitiveWatcher (), SecurityWatcher
(), MissionWatcher, AdversaryWatcher, PerformanceWatcher — one
per ship.
Post-Arc-D (): TrajectoryWatcher — observes shipping
trajectory rather than current health. Authorized by
`delphi/2026-05-13-trajectory-watcher-7th-channel.md`.

**Mythology relocation ():** AntColonyWatcher + CivitasWatcher
— close the runtime-observation gap (the swarm and the citizen
layer became primary in (legacy arc)+F+G but had no dedicated watchers).
Adding them brings HYDRA to nine, completing the canonical Hydra-9
count for the first time at its etymological home. Authorized by
`delphi/2026-05-13-hydra-mythology-relocation-to-watchers.md`.

Prior to , the Hydra-9 anchor was on Argos phalanxs
() — see that ship's Delphi and CHANGELOG for the
historical reading.  relocates the mythology to where
its etymology already pointed.
"""

from .adversary_watcher import AdversaryWatcher
from .ant_colony_watcher import AntColonyWatcher
from .base import Finding, Watcher, WatcherReport
from .civitas_watcher import CivitasWatcher
from .cognitive_watcher import CognitiveWatcher
from .mission_watcher import MissionWatcher
from .performance_watcher import PerformanceWatcher
from .schema_watcher import SchemaWatcher
from .security_watcher import SecurityWatcher
from .trajectory_watcher import TrajectoryWatcher

__all__ = [
    "Finding",
    "Watcher",
    "WatcherReport",
    # The nine Hydra heads (+):
    "SchemaWatcher",
    "CognitiveWatcher",
    "SecurityWatcher",
    "MissionWatcher",
    "AdversaryWatcher",
    "PerformanceWatcher",
    "TrajectoryWatcher",
    "AntColonyWatcher",   # 8th head ()
    "CivitasWatcher",     # 9th head ()
]
