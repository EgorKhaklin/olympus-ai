<div align="center">

# ⚡ BUILDING ON OLYMPUS ⚡

**from clone to running deployment in 10 minutes**

</div>

---

This walkthrough takes you from a fresh clone to a working cognitive substrate with a domain-specific Eye, a custom HYDRA Head, an Apollo prediction, and a complete session pass. After this you can build any cognitive agent on top of Olympus.

---

## 0. Prerequisites

- Python 3.9+
- (optional) `pip install anthropic` if you want LLM integration via `olympus.llm`

---

## 1. Clone and install

```bash
git clone https://github.com/EgorKhaklin/olympus ~/Desktop/my-agent
cd ~/Desktop/my-agent
pip install -e .          # exposes `invoke` as a console script
```

## 2. Light the hearth

The hearth-seal binds this deployment to a vocation. Write one sentence on what your agent is FOR.

```bash
invoke kindle research-assistant "draft literature-review sections from a corpus of operator-supplied PDFs without hallucinating citations"
```

The vocation is byte-frozen in `state/hestia_hearth.json`. Changing it requires extinguishing the hearth (a HIGH-risk operation through Delphi).

## 3. Run your first session

```bash
invoke session "first session"
```

You should see the full loop fire — HYDRA observing, Argos scanning, Athena synthesizing, etc. All 9 default Eyes and 9 default Heads report against the substrate itself; on a fresh deployment, everything is INFO (nothing yet to alarm about).

```bash
invoke consult hymn          # Polyhymnia tells you how many oaths Styx holds
invoke meta                  # full self-portrait
```

## 4. Add a domain-specific Eye

Eyes are the highest-leverage extension surface. Each Eye scans one slice of YOUR domain and emits findings.

Create `src/olympus/monsters/argos/eyes/eye_pdf_corpus_freshness.py`:

```python
"""eye_pdf_corpus_freshness — checks the operator's PDF corpus for staleness."""
from __future__ import annotations

import datetime

from olympus.monsters.argos.base import Eye, EyeFinding, KIND_INFO, KIND_DRIFT
from olympus.primordials.gaia import root


STALE_DAYS = 14


class EyePdfCorpusFreshness(Eye):
    NAME = "eye_pdf_corpus_freshness"
    SLICE = "corpus/pdfs/"

    def scan(self) -> list[EyeFinding]:
        corpus = root.child("corpus", "pdfs")
        if not corpus.exists():
            return [self._finding(KIND_INFO,
                "no corpus/pdfs/ directory yet")]
        pdfs = list(corpus.glob("*.pdf"))
        if not pdfs:
            return [self._finding(KIND_INFO,
                "corpus/pdfs/ exists but is empty")]
        newest = max(p.stat().st_mtime for p in pdfs)
        age_days = (datetime.datetime.now().timestamp() - newest) / 86400.0
        if age_days > STALE_DAYS:
            return [self._finding(KIND_DRIFT,
                f"corpus has not been refreshed in {age_days:.0f} days",
                intensity=min(8.0, age_days / 30.0),
                pdf_count=len(pdfs))]
        return [self._finding(KIND_INFO,
            f"corpus current ({len(pdfs)} PDFs, newest {age_days:.0f}d old)")]
```

Register it in `src/olympus/monsters/argos/colony.py` `_register_defaults()`:

```python
from olympus.monsters.argos.eyes.eye_pdf_corpus_freshness import EyePdfCorpusFreshness
# ... add to the for-loop ...
```

Now `invoke session` runs your new eye every pass.

## 5. Add a domain-specific HYDRA Head

Heads observe at a higher level than Eyes. Create `src/olympus/monsters/hydra/heads/head_citation_safety.py`:

```python
"""head_citation_safety — checks recent agent outputs for unsourced claims."""
from __future__ import annotations

from olympus.monsters.hydra.head import Head, HeadFinding, Severity


class HeadCitationSafety(Head):
    NAME = "citation_safety"
    SLICE = "state/agent_outputs/"

    def observe(self) -> list[HeadFinding]:
        # Read recent outputs; check for citation markers
        # Return findings of severity INFO / DRIFT / ALERT
        return [self._finding(
            self.SLICE, Severity.INFO,
            "citation-safety scaffolding registered; implement domain logic",
        )]
```

Attach it in `src/olympus/monsters/hydra/host.py` `_attach_defaults()`.

## 6. Add an Apollo prediction

Apollo predictions are falsifiable claims about your domain's future.

```python
from olympus.olympians.apollo import apollo, Prediction
import datetime

apollo.predict(Prediction(
    name="cite-50pct-bound",
    statement="50% of operator-accepted drafts in the next 30 days will cite ≥3 corpus PDFs",
    horizon=datetime.date.today() + datetime.timedelta(days=30),
    verify=lambda: _compute_cite_rate() >= 0.5,
))
```

The S5 invariant forces every Apollo prediction to carry a `verify()` callable. Predictions without one are refused at register-time.

## 7. Run a session against your domain

```bash
invoke session "draft a literature-review section on diffusion models"
```

Your new Eye fires, your new Head observes, Athena synthesizes them with the existing substrate findings, Hephaestus proposes, Momus contests, the action queue routes.

If a proposal lands at MEDIUM or above, it waits for you:

```bash
invoke action review            # see what's queued
invoke action ratify act-...    # approve
```

## 8. Write your DOMAIN.md

Copy `codex/DOMAIN-TEMPLATE.md` to `DOMAIN.md` at your project root and fill in the domain-specific C1–CN constraints — the invariants your domain must hold beyond the substrate's S1–S8.

## 9. Run tests

```bash
python3 -m unittest discover -s tests
```

The substrate ships with 76 tests covering invariant enforcement (S2 determinism, S3 read-only heads, S4 decentralization, S5 falsifiability, S8 reconstructability), the session loop, the action queue, the runtime layer, the correlation engine, the meta surface, and Heracles's twelve labors. Add a `test_my_domain.py` for your domain's tests.

## 10. The discipline going forward

Per `codex/RITES.md`:

1. **Pick a risk class** for any change (LOW / MEDIUM / HIGH / COMPOSITE).
2. **For HIGH or COMPOSITE**, open a Delphi via:
   `python3 -c "from olympus.underworld.styx import swear; swear(...)"`.
3. **Code change**, then add a test.
4. **`invoke session`** to verify the loop still runs end-to-end.
5. **`invoke meta`** to confirm the self-portrait still matches your expectation.
6. **Commit** with a reference to any Delphi opened.

The substrate's promise is reconstructability (S8). Every load-bearing action you take leaves a trail in Mnemosyne. Every constitutional commitment is on Styx. After a year, after a hundred sessions, after a dozen contributors, the question *"why did this agent do that?"* can be answered from the substrate's own records.

---

## What you DON'T need to build

- An audit log (Mnemosyne)
- An immutable decision record (Styx)
- A read-only observation tier (HYDRA)
- A decentralized scan substrate (Argos)
- A predicate-validation surface (Apollo)
- A strategic-decision protocol (Delphi)
- A drift-detection persona (Hephaestus)
- An adversarial-review catalog (Momus AP1–AP8)
- A retry-or-escalate primitive (Hecate)
- A snapshot primitive (Medusa)
- A quota system (Lachesis)
- A lifecycle state machine (Iapetus)
- A pub/sub bus (Poseidon)
- A precision-metrics tracker (Artemis)
- A pretty terminal formatter (Aphrodite + Graces)
- A self-introspection surface (`olympus.meta`)
- An LLM adapter pattern (`olympus.llm`)

All of this comes free. You build the **domain logic**.

---

*Per the v0.1 cosmogony — Olympus is the substrate. Your deployment is the application.*
