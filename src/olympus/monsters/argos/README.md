# Argos

Argos Panoptes had a hundred eyes. Sleep never closed all of them at once.

In Olympus, Argos is the decentralized swarm — four sub-tiers of observers, each scanning one slice. No Eye imports another Eye (substrate invariant S4). Synthesis is emergent at read time.

| sub-tier | role | count |
|----------|------|------:|
| `eyes/` | observation specialists | 8 |
| `satyrs/` | concrete checks (lower cadence) | 4 |
| `demes/` | civic-class observers | 6 |
| `phalanges/` | battle formations grouping Eyes | 4 |

```python
from monsters.argos import colony

census = colony.deploy()
print(f"{census.count} pheromones emitted by {len(colony.eyes())} eyes")
```

Pheromones are written to `monsters/argos/pheromones.jsonl`. Mantis (the seer in `demes/`) reads the log to surface the dominant pattern.
