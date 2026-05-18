<div align="center">

# ⚡ PANTHEON ⚡

**the registry of every named module**

</div>

---

The canonical list of every god, hero, monster, and primordial in Olympus. Each entry names the file, the mythological role, and the cognitive function.

If you add a new module, register it here. If a module exists on disk but is missing from this list, `tests/test_pantheon_coherence.py` will fail.

---

## ⚡ Above the pantheon — Zeus

| name | module | role |
|------|--------|------|
| **Zeus** | `src/olympus/olympians/zeus.py` | The operator. Issues directives, authorizes HIGH-risk action via Styx oaths. |

---

## ☉ Primordials — the first beings

| name | module | mythological role | cognitive function |
|------|--------|-------------------|--------------------|
| **Chaos** | `src/olympus/primordials/chaos.py` | the yawning void before order | null / void singleton |
| **Gaia** | `src/olympus/primordials/gaia.py` | Earth, mother of the Titans | filesystem root resolution |
| **Nyx** | `src/olympus/primordials/nyx.py` | Night, older than the Olympians | background-task scheduling |
| **Eros** | `src/olympus/primordials/eros.py` | primordial generation | deterministic id generation |
| **Tartarus** | `src/olympus/primordials/tartarus.py` | the pit beneath the underworld | quarantine for forbidden artifacts |

---

## ☉ Titans — pre-Olympian foundations

| name | module | mythological role | cognitive function |
|------|--------|-------------------|--------------------|
| **Mnemosyne** | `src/olympus/titans/mnemosyne.py` | Memory, mother of the Muses | append-only audit-of-record discipline |
| **Themis** | `src/olympus/titans/themis.py` | divine law, the Oracle of Delphi before Apollo | the substrate constitution (S1–S8) |
| **Cronus** | `src/olympus/titans/cronus.py` | Time, deposed king of the Titans | structured schedules / cadences |
| **Hyperion** | `src/olympus/titans/hyperion.py` | Light, father of Sun/Moon/Dawn | observability (counters + gauges) |
| **Rhea** | `src/olympus/titans/rhea.py` | Motherhood, mother of Zeus | bootstrap (ensures directory structure) |
| **Oceanus** | `src/olympus/titans/oceanus.py` | the world-encircling river | I/O boundary |
| **Iapetus** | `src/olympus/titans/iapetus.py` | mortality, father of Prometheus | lifecycle state machine |
| **Coeus** | `src/olympus/titans/coeus.py` | the axis of heaven, intellect | investigation / queries |
| **Atlas** | `src/olympus/titans/atlas.py` | bearer of the heavens, condemned to hold the celestial sphere | live-state registry of in-flight operations |
| **Epimetheus** | `src/olympus/titans/epimetheus.py` | afterthought, brother of Prometheus | post-hoc hindsight (expected-vs-actual over events) |
| **Metis** | `src/olympus/titans/metis.py` | wise counsel, first wife of Zeus, mother of Athena | self-tuning advisor — recommends parameter changes via Hephaestus channel |

---

## ☉ Olympians — the twelve (+ Hestia, +Apollo's Pythia)

**Apollo's Pythia** (`src/olympus/olympians/apollo/pythia.py`) — the priestess at Delphi, channel for external knowledge entering the substrate via `urllib`. Pure stdlib network bridge; every consultation recorded under `pythia.consultation`. Per Delphi 2026-05-18-recursion-arc.md.



| name | module | mythological role | cognitive function |
|------|--------|-------------------|--------------------|
| **Zeus** | `src/olympus/olympians/zeus.py` | king of the gods | operator interface |
| **Hera** | `src/olympus/olympians/hera.py` | queen, goddess of marriage | bindings registry |
| **Poseidon** | `src/olympus/olympians/poseidon.py` | sea, earth-shaker | data flow (pub/sub) |
| **Demeter** | `src/olympus/olympians/demeter.py` | harvest | batch ingestion |
| **Athena** | `src/olympus/olympians/athena.py` | wisdom, strategy | strategic synthesis (briefs) |
| **Apollo** | `src/olympus/olympians/apollo/` | prophecy | falsifiable predicates |
| **Artemis** | `src/olympus/olympians/artemis.py` | huntress, the precise arrow | precision metrics (percentiles) |
| **Ares** | `src/olympus/olympians/ares.py` | war | adversarial assault orchestration |
| **Aphrodite** | `src/olympus/olympians/aphrodite.py` | beauty | terminal aesthetics |
| **Hephaestus** | `src/olympus/olympians/hephaestus.py` | smith, the only laboring god | the Architect — drift surfacing |
| **Hermes** | `src/olympus/olympians/hermes.py` | messenger | CLI dispatch surface |
| **Dionysus** | `src/olympus/olympians/dionysus.py` | wine, transformation | state-transition recording |
| **Hestia** | `src/olympus/olympians/hestia.py` | the hearth, sacred boundary | deployment identity-seal |
| **Pan** | `src/olympus/olympians/pan.py` | god of the wild and panic (the etymology) | circuit breaker — refuses ratifications when Furies fire above threshold |
| **Asclepius** | `src/olympus/olympians/asclepius.py` | god of medicine, healer of mortals | healer — rebuild derived state from canonical sources (Iris, Pan, Atlas, dirs) |
| **Hygieia** | `src/olympus/olympians/hygieia.py` | daughter of Asclepius, goddess of health | whole-substrate cohesion checks (Pan↔invariants, Atlas↔sessions, Daedalus↔modules, Themis↔records, Plato↔figures, Charon backlog) |

---

## ☉ Underworld — Hades's realm

| name | module | mythological role | cognitive function |
|------|--------|-------------------|--------------------|
| **Hades** | `src/olympus/underworld/hades.py` | king of the underworld | archive |
| **Persephone** | `src/olympus/underworld/persephone.py` | queen, half above + half below | cyclical state |
| **Hecate** | `src/olympus/underworld/hecate.py` | crossroads, in-between | error recovery |
| **Styx** | `src/olympus/underworld/styx.py` | river of unbreakable oaths | cryptographic immutable ledger |
| **Lethe** | `src/olympus/underworld/lethe.py` | river of forgetting | ephemeral cache (TTL'd) |
| **Charon** | `src/olympus/underworld/charon.py` | ferryman of the dead across Styx and Acheron | safe migration of released burdens from Atlas → Hades archive |

---

## ☉ Fates — the Moirai

| name | module | mythological role | cognitive function |
|------|--------|-------------------|--------------------|
| **Clotho** | `src/olympus/fates/clotho.py` | the Spinner | creation primitive |
| **Lachesis** | `src/olympus/fates/lachesis.py` | the Allotter | quota / resource accounting |
| **Atropos** | `src/olympus/fates/atropos.py` | the Inevitable | termination |

---

## ☉ Furies — the Erinyes

| name | module | mythological role | cognitive function |
|------|--------|-------------------|--------------------|
| **Alecto** | `src/olympus/furies/alecto.py` | unceasing anger | invariant-violation alerter |
| **Megaera** | `src/olympus/furies/megaera.py` | jealousy | concurrency-conflict watcher |
| **Tisiphone** | `src/olympus/furies/tisiphone.py` | avenger of murder | integrity verifier |

---

## ☉ Graces — the Charites

| name | module | mythological role | cognitive function |
|------|--------|-------------------|--------------------|
| **Aglaia** | `src/olympus/graces/aglaia.py` | Splendor | banners, section headers |
| **Euphrosyne** | `src/olympus/graces/euphrosyne.py` | Good Cheer | friendly error message reframing |
| **Thalia** (Grace) | `src/olympus/graces/thalia.py` | Festivity | doc-tone helpers |

---

## ☉ Muses — Mnemosyne's nine daughters

| name | module | mythological role | cognitive function |
|------|--------|-------------------|--------------------|
| **Calliope** | `src/olympus/muses/calliope.py` | epic poetry | codex reader |
| **Clio** | `src/olympus/muses/clio.py` | history | journal writer (`codex/journal/`) |
| **Erato** | `src/olympus/muses/erato.py` | love poetry | warm user-facing prose |
| **Euterpe** | `src/olympus/muses/euterpe.py` | music | rhythm tracker |
| **Melpomene** | `src/olympus/muses/melpomene.py` | tragedy | post-mortem recorder (`codex/postmortems/`) |
| **Polyhymnia** | `src/olympus/muses/polyhymnia.py` | sacred hymns | Styx hymnal |
| **Terpsichore** | `src/olympus/muses/terpsichore.py` | dance | choreography registry |
| **Thalia** (Muse) | `src/olympus/muses/thalia_muse.py` | comedy | closing blessings |
| **Urania** | `src/olympus/muses/urania.py` | astronomy | brain-map (constellation chart) |

---

## ☉ Heroes — mortals who confronted the gods

| name | module | mythological role | cognitive function |
|------|--------|-------------------|--------------------|
| **Heracles** | `src/olympus/heroes/heracles.py` | twelve labors | kill-test harness |
| **Perseus** | `src/olympus/heroes/perseus.py` | mirror, slayer of Medusa | reflection persona |
| **Theseus** | `src/olympus/heroes/theseus.py` | labyrinth navigator | brain-map exploration |
| **Odysseus** | `src/olympus/heroes/odysseus.py` | long return | session-resume helper |
| **Orpheus** | `src/olympus/heroes/orpheus.py` | descent into Hades | archive retrieval |
| **Atalanta** | `src/olympus/heroes/atalanta.py` | the fastest mortal | benchmark runner |
| **Momus** | `src/olympus/heroes/momus.py` | mockery (banished from Olympus) | the Anti-Architect (AP1–AP8) |
| **Prometheus** | `src/olympus/heroes/prometheus.py` | titan of forethought, fire-bringer | bounded auto-improver (handler registry on ratified-LOW actions) |
| **Cassandra** | `src/olympus/heroes/cassandra.py` | prophetess of Troy, cursed never to be believed | vindication memory — dismissed warnings that later recurred |
| **Daedalus** | `src/olympus/heroes/daedalus.py` | master craftsman, builder of the Labyrinth | cartographer — generates the Mermaid architecture map (`codex/ARCHITECTURE.md`) |
| **Castor** | `src/olympus/heroes/castor.py` | mortal twin of the Dioscuri | shadow session runner — spawns sessions in a tempdir substrate |
| **Pollux** | `src/olympus/heroes/pollux.py` | immortal twin of the Dioscuri | comparator — diffs prod-vs-shadow session reports |
| **Ariadne** | `src/olympus/heroes/ariadne.py` | princess of Crete, giver of the thread | causal-lineage tracer — threads trace_id/parent_trace_id through Mnemosyne |
| **Nemesis** | `src/olympus/heroes/nemesis.py` | goddess of retribution and divine balance | counterfactual reasoner — measures gap between what was done and what could have been |
| **Pythagoras** | `src/olympus/heroes/pythagoras.py` | mathematician of Samos, father of sacred numerics | constants (φ, π, √2, e), Fibonacci, golden-section search, harmony scoring, Pythagorean triples |
| **Plato** | `src/olympus/heroes/plato.py` | philosopher of the five regular solids | five-solid taxonomy of substrate work (tetrahedron/cube/octahedron/dodecahedron/icosahedron → fire/earth/air/cosmos/water → observation/state/reasoning/authority/execution) |
| **Phoenix** | `src/olympus/heroes/phoenix.py` | firebird of cyclical death and rebirth | regeneration primitive — surfaces state due for rebirth (retired prophecies, hung burdens, stale graduations) |

---

## ☉ Monsters — the named beasts

| name | module | mythological role | cognitive function |
|------|--------|-------------------|--------------------|
| **HYDRA** | `src/olympus/monsters/hydra/` | multi-headed beast of Lerna | watcher tier |
| **Argos** | `src/olympus/monsters/argos/` | many-eyed giant | decentralized swarm |
| **Cerberus** | `src/olympus/monsters/cerberus.py` | three-headed guardian | perimeter gate |
| **Sphinx** | `src/olympus/monsters/sphinx.py` | the riddler | challenge-response gate |
| **Medusa** | `src/olympus/monsters/medusa.py` | petrifier | snapshot primitive |
| **Chimera** | `src/olympus/monsters/chimera.py` | hybrid beast | composite-test runner |
| **Minotaur** | `src/olympus/monsters/minotaur.py` | labyrinth-dweller | recursive walker (depth-capped) |
| **Typhon** | `src/olympus/monsters/typhon.py` | father of monsters | catastrophic-scenario catalog |

---

## ☉ HYDRA — eight mortal heads + one immortal

The Lernaean Hydra had many heads; one was immortal. Heracles cut the mortal heads (each replaced by a different head covering the same slice), then buried the immortal head under a great stone.

| head | module | watches | immortal? |
|------|--------|---------|:---------:|
| **Cosmogony** | `src/olympus/monsters/hydra/heads/head_cosmogony.py` | constitution naming all S1–S8 | — |
| **Pantheon** | `src/olympus/monsters/hydra/heads/head_pantheon.py` | PANTHEON.md against disk | — |
| **Styx** | `src/olympus/monsters/hydra/heads/head_styx.py` | oath chain integrity | — |
| **Journal** | `src/olympus/monsters/hydra/heads/head_journal.py` | journal for silence | — |
| **Oaths** | `src/olympus/monsters/hydra/heads/head_oaths.py` | cadence of new Styx oaths | — |
| **Lifecycle** | `src/olympus/monsters/hydra/heads/head_lifecycle.py` | Iapetus's lifecycle registry | — |
| **Substrate** | `src/olympus/monsters/hydra/heads/head_substrate.py` | filesystem layout | — |
| **Apollo** | `src/olympus/monsters/hydra/heads/head_apollo.py` | Apollo's predicate coverage | — |
| **Immortal** | `src/olympus/monsters/hydra/heads/head_immortal.py` | the other eight heads themselves | ✓ |

When a mortal head is cut (rewritten), its replacement may take a different form. The immortal head is the structural guarantee that the watcher tier is always operating.

---

## ☉ Argos — the swarm tier

### Eyes — observation specialists (nine)

| eye | module | watches |
|-----|--------|---------|
| **cosmogony_drift** | `src/olympus/monsters/argos/eyes/eye_cosmogony_drift.py` | constitution naming all S1–S8 |
| **pantheon_completeness** | `src/olympus/monsters/argos/eyes/eye_pantheon_completeness.py` | PANTHEON.md ↔ disk |
| **styx_chain_intact** | `src/olympus/monsters/argos/eyes/eye_styx_chain_intact.py` | oath-chain verification |
| **journal_silence** | `src/olympus/monsters/argos/eyes/eye_journal_silence.py` | days since Clio last inscribed |
| **chronicle_gap** | `src/olympus/monsters/argos/eyes/eye_chronicle_gap.py` | days since CHRONICLE.md changed |
| **oath_freshness** | `src/olympus/monsters/argos/eyes/eye_oath_freshness.py` | hours since last Styx oath |
| **apollo_coverage** | `src/olympus/monsters/argos/eyes/eye_apollo_coverage.py` | predicate count + S5 compliance |
| **delphi_pending** | `src/olympus/monsters/argos/eyes/eye_delphi_pending.py` | unresolved Delphi files |
| **understanding_gap** | `src/olympus/monsters/argos/eyes/eye_understanding_gap.py` | load-bearing memories missing rationale (S8 structural enforcement) |

### Satyrs — wild-companion concrete checks (four)

| satyr | module | checks |
|-------|--------|--------|
| **hearth** | `src/olympus/monsters/argos/satyrs/satyr_hearth.py` | Hestia's hearth is lit |
| **substrate** | `src/olympus/monsters/argos/satyrs/satyr_substrate.py` | required dirs all present |
| **styx** | `src/olympus/monsters/argos/satyrs/satyr_styx.py` | quick oath-chain check |
| **pantheon** | `src/olympus/monsters/argos/satyrs/satyr_pantheon.py` | every cosmogonic tier populated |

### Demes — civic-class observers (six)

| deme | module | civic role |
|------|--------|-----------|
| **mantis** | `src/olympus/monsters/argos/demes/mantis.py` | the seer — pattern surfacing |
| **demarchos** | `src/olympus/monsters/argos/demes/demarchos.py` | the deme-leader — registry roll-keeper |
| **hippeus** | `src/olympus/monsters/argos/demes/hippeus.py` | the cavalry — fast correlation |
| **demos** | `src/olympus/monsters/argos/demes/demos.py` | the people — public-facing surfaces |
| **tamias** | `src/olympus/monsters/argos/demes/tamias.py` | the treasurer — quota accounting |
| **ephoros** | `src/olympus/monsters/argos/demes/ephoros.py` | the overseer — Delphi compliance |

### Phalanges — battle formations (four)

| phalanx | module | concern |
|---------|--------|---------|
| **constitutional** | `src/olympus/monsters/argos/phalanges/phalanx_constitutional.py` | the substrate's own laws |
| **substrate** | `src/olympus/monsters/argos/phalanges/phalanx_substrate.py` | filesystem layout |
| **cadence** | `src/olympus/monsters/argos/phalanges/phalanx_cadence.py` | rhythms of operation |
| **oracular** | `src/olympus/monsters/argos/phalanges/phalanx_oracular.py` | Apollo + Delphi surfaces |

---

## Pantheon population

| tier | count |
|------|------:|
| Primordials | 5 |
| Titans | 11 |
| Olympians (incl. Hestia + Apollo subpackage with Pythia) | 16 |
| Underworld | 6 |
| Fates | 3 |
| Furies | 3 |
| Graces | 3 |
| Muses | 9 |
| Heroes | 17 |
| Monsters (top-level) | 8 |
| HYDRA heads | 9 (8 mortal + 1 immortal) |
| **Total named principal figures** | **91** |

Plus the presentation-layer module **Iris** (`src/olympus/iris/`) — the rainbow-messenger between Olympus and mortals; static dashboard. Iris is an Olympian by myth but lives outside the `olympians/` directory because she is structurally a renderer, not a god participating in the cognitive loop.

Plus the operational modules:
- **Daemon** (`src/olympus/runtime/daemon.py`) + templates at `scripts/daemon/` — generates launchd / systemd units so the self-improvement loop runs continuously.
- **HTTP API** (`src/olympus/runtime/http_api.py`) — read-only JSON surface bound to localhost; lets external observers query substrate state without Python coupling.
- **Plugin loader** (`src/olympus/runtime/plugins.py`) — discovers third-party packages via `importlib.metadata` entry_points and registers their handlers/eyes/healers.

Not gods; pure operational scaffolding.

Plus the Argos swarm: **9 Eyes**, **4 Satyrs**, **6 Demes**, **4 Phalanges**.
