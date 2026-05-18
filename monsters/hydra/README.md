# HYDRA

The Lernaean Hydra had many heads. Heracles cut the mortal heads (each replaced by a different head covering the same slice); the immortal head he buried under a stone.

In Olympus, HYDRA is the read-only watcher tier — eight mortal heads plus one immortal.

| head | watches |
|------|---------|
| `head_cosmogony.py` | the constitution still names S1–S8 |
| `head_pantheon.py` | PANTHEON.md against disk |
| `head_styx.py` | oath chain integrity |
| `head_journal.py` | days since Clio last inscribed |
| `head_oaths.py` | hours since the last Styx oath |
| `head_lifecycle.py` | Iapetus's lifecycle registry |
| `head_substrate.py` | Rhea's required directories |
| `head_apollo.py` | Apollo's predicate coverage (S5) |
| `head_immortal.py` | **the other eight heads themselves** |

Substrate invariant S3: every Head is read-only. A Head that mutates is a bug.

```python
from monsters.hydra import hydra

report = hydra.behead()
print(f"{report.total} findings across {len(hydra.heads())} heads")
for f in report.alerts:
    print(f"ALERT: {f.head} — {f.detail}")
```
