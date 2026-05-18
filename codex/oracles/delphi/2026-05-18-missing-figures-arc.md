# Delphi — the missing-figures arc

**Risk class:** COMPOSITE
**Decided:** Position B — three additions (Epimetheus, Cassandra, Atlas); the rest refused.
**Sworn on Styx at seq=55 (recorded on swear).**

Zeus's question (verbatim):

> *"scan the whole system, are we missing anything from greek mythology? and if we are we can add new features that represent who we are missing. You can use any langauge you want , and use the system to do this"*

---

## Methodology

The substrate's own decision protocol decided this. The temptation is to add every recognizable Greek name as a "complete the set" gesture — that is precisely the AP8 (decorative additions) failure mode the catalog was written to refuse. So Hephaestus surfaced every plausible candidate, Momus dinged the decorative ones, and only figures that **close a load-bearing substrate gap** survived.

Three did. Eleven did not.

---

## Q1 — Who is missing, and which gaps do they close?

### Pre-debate inventory

**Already present (73 named figures):**
- Primordials (5): Chaos, Gaia, Nyx, Eros, Tartarus
- Titans (8): Mnemosyne, Themis, Cronus, Hyperion, Rhea, Oceanus, Iapetus, Coeus
- Olympians (13): the canonical twelve + Hestia, all present
- Underworld (5): Hades, Persephone, Hecate, Styx, Lethe
- Fates (3): Clotho, Lachesis, Atropos
- Furies (3): Alecto, Megaera, Tisiphone
- Graces (3): Aglaia, Euphrosyne, Thalia
- Muses (9): all nine
- Heroes (8): Atalanta, Heracles, Momus, Odysseus, Orpheus, Perseus, Prometheus, Theseus
- Monsters (8 top-level + Hydra heads + Argos swarm)
- Iris (just shipped in the self-improvement arc as the dashboard module)

### Candidates surfaced

| candidate | proposed role | dings | passes |
|---|---|---|---|
| **Epimetheus** | Hindsight Titan — postmortem of every action | **(none)** | AP1, AP3, AP6, AP7, AP8 |
| **Cassandra** | Cursed prophetess — track warnings that were ignored, then later vindicated | **(none)** | AP1, AP3, AP6, AP7, AP8 |
| **Atlas** | Load-bearer — live registry of what the substrate is carrying right now | **(none)** | AP1, AP3, AP6, AP7, AP8 |
| Helios | All-seeing sun — aggregate read-only view across all of Mnemosyne | AP8 | — |
| Ananke | Necessity — hard constraints stronger than Themis | AP8, AP3 | — |
| Eris | Productive discord — deliberate hypothesis-discrimination via opposing predictions | AP8 | — |
| Tyche | Luck — non-deterministic noise injection | AP8 | — |
| Metis | Pre-Athena planning — wisdom before strategy | AP8 | — |
| Erebus, Aether, Hemera, Pontus | Primordial complements to Nyx/Oceanus | AP8 | — |
| Crius, Phoebe, Tethys, Theia | Lesser Titans with no distinct substrate role | AP8 | — |
| Helios, Selene, Eos | Sun/Moon/Dawn — overlap with Hyperion/Artemis | AP8 | — |
| Bellerophon, Achilles, Tiresias, Daedalus, Sisyphus, Pandora | Heroes whose role overlaps existing modules or is purely decorative | AP8 | — |
| Pegasus, Charybdis, Scylla, Echidna, Stymphalian birds | Monsters with no distinct cognitive function | AP8 | — |

---

## Position B — what ships, and why

### Epimetheus — hindsight (Titan)

**Module:** `src/olympus/titans/epimetheus.py`

In myth: Brother of Prometheus. Their names are paired and opposite — *pro-* + *metheus* ("forethought") versus *epi-* + *metheus* ("afterthought"). Where Prometheus tries to anticipate, Epimetheus recognizes after the fact. In one version of the story he accepts Pandora despite his brother's warning; in another he is simply slower to see.

In Olympus: closes the loop that Prometheus opened. Prometheus *acts*; Epimetheus *reviews*. For every ratified action, every prophecy verification, every Prometheus handler run, and every session error, Epimetheus produces a structured hindsight record: **expected** vs **actual**, with a concise English **lesson** naming what would be done differently. Records to Mnemosyne under `kind="epimetheus.hindsight"`.

**Why it has bite:** Today the substrate accumulates events but does not formally compare them to their own pre-statements. Hephaestus surfaces drift forward; Epimetheus measures whether what was supposed to happen actually did. Without hindsight as a first-class module, "learning from experience" is only the operator's mental work — the substrate cannot itself answer *"what surprised us last week?"*.

**Momus's contests, in detail:**
- **AP1** (no ground-touch): pass — read-only over Mnemosyne; no writes to source.
- **AP2** (scope creep): pass — single concern: post-hoc analysis.
- **AP3** (instance vs class): pass — every event of the relevant kinds gets a hindsight, not one specific event.
- **AP4** (premature constitutional elevation): pass — no MISSION or COSMOGONY change.
- **AP5** (declining a directive): pass — directly responds to Zeus's scan-and-fill request.
- **AP6** (understanding-obscuring): pass — every hindsight is itself a recorded explanation.
- **AP7** (privilege escalation): pass — no execution authority.
- **AP8** (decorative): pass — closes a structural gap (forethought → hindsight loop).

### Cassandra — vindication memory (Hero)

**Module:** `src/olympus/heroes/cassandra.py`

In myth: Apollo gave her the gift of prophecy and, when she refused him, cursed her so that no one would believe her. She predicted the fall of Troy; she was dismissed; Troy fell.

In Olympus: tracks warnings that were dismissed or rejected, then surfaces them when later evidence supports them. Rejection-memory (already shipped under Hephaestus) is the *forward* version: don't re-propose what Zeus killed. Cassandra is the *backward* version: when a warning that was dismissed later proves correct, the substrate records it.

Definition of "dismissed":
- ALERT-severity Argos pheromone or HYDRA finding on slice X
- followed by `action.rejected` on the proposal raised for slice X, OR no proposal ever raised

Definition of "vindicated":
- slice X subsequently alerts again in ≥2 distinct sessions, OR
- a Furies invariant later triggers covering slice X

Records to Mnemosyne under `kind="cassandra.vindicated"`.

**Why it has bite:** without this loop, dismissed warnings are silently forgotten. With it, the substrate can answer *"what did we shrug off that came back?"* — exactly the question a careful operator asks before signing off on a release.

**Momus's contests:** identical pattern to Epimetheus — read-only, class-level, ground-touching only via memory writes, not decorative.

### Atlas — load-bearer / active operations (Titan)

**Module:** `src/olympus/titans/atlas.py`

In myth: Titan who fought against the Olympians and was sentenced by Zeus to hold up the celestial sphere forever. Sometimes depicted as bearing the earth; always the embodiment of *carrying load*.

In Olympus: live-state registry. Sessions register themselves as "borne" by Atlas at start; release at end. Same for Prometheus loops, action executions, and any long-lived operation. Reports what is being carried *right now* — a thing the JSONL audit-of-record cannot answer because it is, by design, history.

Storage: `state/atlas/burdens.jsonl` — append-only writes (S1) with a `released_at` field for completed burdens. The live view is computed by reading the file and filtering to where `released_at` is empty.

**Why it has bite:** the substrate has rich history (Mnemosyne) and rich invariants (Furies/HYDRA) but no answer to "what is currently in flight." An operator looking at the system has to infer it by reading the freshest Mnemosyne entries. Atlas makes it cheap.

**Momus's contests:** pass on all eight; this is operational state, not constitutional, and JSONL preserves the audit trail (S1, S8).

---

## What does NOT ship — and the discipline of refusing

### Helios — refused (AP8)

The "all-seeing sun" is decoratively gorgeous but functionally already covered: `invoke wisdom` aggregates session/prophecy/proposal stats; `invoke iris` visualizes them; `invoke status` shows live health. Adding a third aggregate view dilutes rather than improves.

### Ananke — refused (AP8 + AP3)

"Necessity, the cannot-be-otherwise" sounds load-bearing but in practice maps to constraints already enforced by Furies + S1–S8 tests + database-level invariants. Adding an Ananke module would either duplicate Furies (AP8) or add instance-level constraint checks (AP3).

### Eris, Tyche — refused (AP8)

Discord-as-hypothesis and luck-as-noise both overlap with Ares (adversarial assault) and Apollo (prediction). The substrate already has rich adversarial mechanics; another wrapper around them would be decorative.

### Metis — refused (AP8)

"Pre-Athena planning" is exactly what Athena's `compose_from()` already does internally. Adding a pre-step adds a hop without adding a thought.

### The minor Primordials, Titans, Heroes, and Monsters — refused (AP8)

Erebus, Aether, Hemera, Pontus, Crius, Phoebe, Tethys, Theia, Selene, Eos, Bellerophon, Achilles, Tiresias, Daedalus, Sisyphus, Pandora, Pegasus, Charybdis, Scylla, Echidna — every one was considered. Every one was refused on AP8 because their substrate role would either duplicate an existing module or be purely decorative. **Greek mythology is large; the substrate is finite. The discipline of refusing applies to mythology too.**

---

## Q2 — Other languages?

The same question as the self-improvement arc. The same answer: nothing here justifies another language. Epimetheus reads Mnemosyne (Python); Cassandra reads Mnemosyne + correlation (Python); Atlas writes append-only JSONL (Python).

The substrate is Python because reasoning over JSONL records is what Python is best at. Languages get added when they solve a real problem Python does not. At the volumes Atlas writes (one heartbeat per session, one per Prometheus pass), JSONL is correct.

---

## What lands

### `src/olympus/titans/epimetheus.py`

- `Epimetheus.reflect(lookback_hours: float = 24.0) -> ReflectionReport`
- `Epimetheus.reflect_on_action(action_id: str) -> HindsightRecord | None`
- `Epimetheus.hindsights() -> list[HindsightRecord]`
- Records to Mnemosyne under `kind="epimetheus.hindsight"`

### `src/olympus/heroes/cassandra.py`

- `Cassandra.ignored_warnings() -> list[IgnoredWarning]`
- `Cassandra.vindicated() -> list[Vindication]`
- `Cassandra.review() -> CassandraReport`
- Records to Mnemosyne under `kind="cassandra.vindicated"`

### `src/olympus/titans/atlas.py`

- `Atlas.bear(operation, owner, payload) -> Burden`
- `Atlas.release(burden_id, outcome="ok") -> None`
- `Atlas.shoulders() -> ShoulderReport`
- Writes to `state/atlas/burdens.jsonl`

### Wiring

- `session.Session.run()` — calls `atlas.bear("session", session_id, ...)` at start; `atlas.release(...)` at end.
- `Prometheus.improve()` — calls `atlas.bear("improvement-pass", ...)` at start; `atlas.release(...)` at end.

### CLI

- `invoke reflect [--hours N]` — Epimetheus's hindsight pass.
- `invoke cassandra` — review ignored + vindicated warnings.
- `invoke shoulders` — what Atlas is currently bearing.

### Tests

- `tests/test_epimetheus.py` — hindsight extraction from action.ratified, prophecy.verified, session.errored, prometheus.handler failures.
- `tests/test_cassandra.py` — dismissed-warning detection, vindication recognition.
- `tests/test_atlas.py` — bear/release lifecycle, append-only invariant, current-shoulders filter.

### Documentation

- `codex/PANTHEON.md` — new entries; population total 73 → 76 principal figures + Iris already counted in the previous arc.
- `codex/CHRONICLE.md` — the missing-figures arc entry.

---

## Authorization

Zeus's quote captured in the Styx oath payload. Sworn at seq=55. The decision is recorded; the implementation follows. Future arcs may revisit the refused list if a real substrate gap surfaces that one of those figures naturally fills — but the bar is the same: AP8 must pass, and a measurable consequence outside the cognitive layer must be nameable.
