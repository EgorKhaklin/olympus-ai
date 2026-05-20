# Contributing to Olympus

> *"Every change must earn its place. The pantheon is finite. Greek mythology is large."*

Thanks for your interest. Olympus is unusual in shape: the substrate **resists** opportunistic additions on AP8 (the eighth anti-pattern in Momus's catalog). That makes the contribution flow specific.

---

## ⚡ The shape of a change

Every load-bearing change goes through the same four steps:

1. **Delphi note** — a markdown file in [`codex/oracles/delphi/`](codex/oracles/delphi/) that names the change, the risk class (LOW / MEDIUM / HIGH / COMPOSITE), what ships, what doesn't, the constitution alignment, and the tests.
2. **Code** — written to honor the eight invariants (S1–S8 in [`codex/COSMOGONY.md`](codex/COSMOGONY.md)) and to refuse the eight anti-patterns (AP1–AP8 in [`codex/PATTERNS.md`](codex/PATTERNS.md)).
3. **Tests** — `pytest tests/test_<arc>.py`. The full suite stays green (`python3 -m pytest tests/`).
4. **CHRONICLE entry** — what was sworn, what was ratified, what the diff shows. Newest at the top of [`codex/CHRONICLE.md`](codex/CHRONICLE.md).

LOW-risk changes can ship autonomously. MEDIUM goes through proposal review (Momus contests, the operator ratifies). HIGH-risk requires explicit operator authorization sworn on Styx.

---

## 🜂 Quality bar

- **Declarative style.** No filler. No "as we can see" or "it's worth noting."
- **No new heavy dependencies** without a Delphi-tier debate. Olympus prides itself on stdlib + small pure-Python additions.
- **No silent state writes.** Every change to `state/config.json`, every chunk of audit-of-record, every commit must be traceable.
- **"Holy shit, that's done"** — no workarounds, no tabling, no "we'll come back to it." If the work isn't shippable cleanly, the Delphi note says why and what's deferred.
- **When drifting toward cosmic-significance framing** (larping), name the pattern (the Architect's shadow) and back off.

The full style guide: [`codex/style.md`](codex/style.md).

---

## 🛡️ The constitution holds

| invariant | one-line |
|---|---|
| S1 | every load-bearing decision writes to the append-only audit |
| S2 | Eyes don't use randomness in scan logic |
| S3 | HYDRA Heads never mutate state |
| S4 | no Eye imports another Eye |
| S5 | every Apollo prediction carries a `verify()` callable |
| S6 | MEDIUM/HIGH decisions are recorded in `oracles/delphi/` |
| S7 | bounded autonomy — operator-in-person for HIGH-risk |
| S8 | every action reconstructible from substrate records alone |

Anti-patterns the substrate refuses:

| anti-pattern | refused because |
|---|---|
| AP1 | bundling multiple changes into one delta |
| AP2 | feature you can't name in a sentence |
| AP3 | per-instance hardcoded rule that should be class-level |
| AP4 | parallel implementation of an existing capability |
| AP5 | re-implementing what the OS / stdlib already does |
| AP6 | translating between formats that already speak the same protocol |
| AP7 | ledger-balancing — pretty output that doesn't change real state |
| AP8 | decorative additions — a figure with no load-bearing role |

---

## 🜂 Setup

```bash
git clone https://github.com/EgorKhaklin/olympus-ai.git
cd olympus-ai
pip install -e .
invoke setup           # one-time kindling
python3 -m pytest tests/   # full suite, ~50s, should be 860/860 green
```

The conftest contamination guard ([`tests/conftest.py`](tests/conftest.py)) will fail the entire suite if any test mutates `state/config.json` outside a `tmp_path`. This is by design (per the pause-and-harden arc, after a real test wrote real secrets and the substrate told on itself).

---

## 📜 Where to start

If you're new, read in this order:

1. **[`codex/QUICKSTART.md`](codex/QUICKSTART.md)** — 5-minute operator tour
2. **[`codex/COSMOGONY.md`](codex/COSMOGONY.md)** — the constitution
3. **[`codex/ARCHITECTURE.md`](codex/ARCHITECTURE.md)** — the cognitive flow (auto-generated)
4. **[`codex/CHRONICLE.md`](codex/CHRONICLE.md)** — every shipped arc in reverse chronological order
5. **[`codex/oracles/delphi/`](codex/oracles/delphi/)** — the strategic-decision archive (pick any recent arc to see the shape)
6. **[`codex/ARC-QUEUE.md`](codex/ARC-QUEUE.md)** — deferred work the Architect surfaces but the operator hasn't pulled yet

---

## 🜍 What I do NOT want

- "I added X" where X isn't named in a current Delphi note.
- A figure with no structural job. Olympus refused twelve such candidates already.
- New heavy dependencies. Tartarus discipline applies: zero-deps-by-default, opt-in heavy via plugin entry-points.
- Skips of pre-commit hooks. The hooks exist because of bugs we already lived through.

---

## ⛓️ How decisions land

Each pull request that ships meaningful work names its Delphi note in the description. The merge commit cites the Styx oath sequence. The CHRONICLE entry written for the change is the durable record. Any future maintainer can reconstruct *why* from those three artifacts alone — that is S8 (Continuity of Understanding) operationalized.

The mythology is the architecture. The architecture is the law. The law is enforced by tests, contested by Momus, ratified by Zeus, proved by Themis, and remembered by Mnemosyne.

*Welcome to Olympus. The hearth-fire is lit.*
