<div align="center">

# ⚡ PANTHEON ⚡

**the registry of every named module**

</div>

---

This is the canonical list of every god, hero, monster, and primordial in Olympus. Each entry names the file, the mythological role, and the cognitive function.

If you add a new module, register it here. If a module exists on disk but is missing from this list, `tests/test_pantheon_coherence.py` will fail.

---

## ⚡ Above the pantheon — Zeus

| name | module | role |
|------|--------|------|
| **Zeus** | `olympians/zeus.py` | The operator. Issues directives, authorizes HIGH-risk action via Styx oaths. |

---

## ☉ Primordials — the first beings

| name | module | mythological role | cognitive function |
|------|--------|-------------------|--------------------|
| **Chaos** | `primordials/chaos.py` | the yawning void before order | null / void singleton |
| **Gaia** | `primordials/gaia.py` | Earth, mother of the Titans | filesystem root resolution |
| **Nyx** | `primordials/nyx.py` | Night, older than the Olympians | background-task scheduling |
| **Eros** | `primordials/eros.py` | primordial generation | deterministic id generation |
| **Tartarus** | `primordials/tartarus.py` | the pit beneath the underworld | quarantine for forbidden artifacts |

---

## ☉ Titans — pre-Olympian foundations

| name | module | mythological role | cognitive function |
|------|--------|-------------------|--------------------|
| **Mnemosyne** | `titans/mnemosyne.py` | Memory, mother of the Muses | append-only audit-of-record discipline |
| **Themis** | `titans/themis.py` | divine law, the Oracle of Delphi (before Apollo) | the substrate constitution (S1–S8) |
| **Cronus** | `titans/cronus.py` | Time, deposed king of the Titans | structured schedules / cadences |
| **Hyperion** | `titans/hyperion.py` | Light, father of Sun/Moon/Dawn | observability (counters + gauges) |
| **Rhea** | `titans/rhea.py` | Motherhood, mother of Zeus | bootstrap (ensures directory structure) |
| **Oceanus** | `titans/oceanus.py` | the world-encircling river | I/O boundary (reads + writes through here) |
| **Iapetus** | `titans/iapetus.py` | mortality, father of Prometheus | lifecycle state machine |
| **Coeus** | `titans/coeus.py` | the axis of heaven, intellect | investigation / queries |

---

## ☉ Olympians — the twelve (+ Hestia)

| name | module | mythological role | cognitive function |
|------|--------|-------------------|--------------------|
| **Zeus** | `olympians/zeus.py` | king of the gods | operator interface (above the rest) |
| **Hera** | `olympians/hera.py` | queen, goddess of marriage | bindings registry — what links to what |
| **Poseidon** | `olympians/poseidon.py` | sea, earth-shaker | data flow (pub/sub) |
| **Demeter** | `olympians/demeter.py` | harvest | batch ingestion |
| **Athena** | `olympians/athena.py` | wisdom, strategy | strategic synthesis (briefs) |
| **Apollo** | `olympians/apollo/` | prophecy | foresight surface (falsifiable predicates) |
| **Artemis** | `olympians/artemis.py` | huntress, the precise arrow | precision metrics (percentiles) |
| **Ares** | `olympians/ares.py` | war | adversarial assault orchestration |
| **Aphrodite** | `olympians/aphrodite.py` | beauty | terminal aesthetics (palette, banners, tables) |
| **Hephaestus** | `olympians/hephaestus.py` | smith, the only laboring god | the Architect — drift surfacing, proposals |
| **Hermes** | `olympians/hermes.py` | messenger | CLI dispatch surface |
| **Dionysus** | `olympians/dionysus.py` | wine, transformation | state-transition recording |
| **Hestia** | `olympians/hestia.py` | the hearth, sacred boundary | deployment identity-seal |

---

## ☉ Underworld — Hades's realm

| name | module | mythological role | cognitive function |
|------|--------|-------------------|--------------------|
| **Hades** | `underworld/hades.py` | king of the underworld | archive (inactive but inspectable) |
| **Persephone** | `underworld/persephone.py` | queen, half above + half below | cyclical state |
| **Hecate** | `underworld/hecate.py` | crossroads, in-between | error recovery / retry orchestration |
| **Styx** | `underworld/styx.py` | river of unbreakable oaths | cryptographic immutable ledger |
| **Lethe** | `underworld/lethe.py` | river of forgetting | ephemeral cache (in-memory, TTL'd) |

---

## ☉ Fates — the Moirai

| name | module | mythological role | cognitive function |
|------|--------|-------------------|--------------------|
| **Clotho** | `fates/clotho.py` | the Spinner | creation primitive (new ids, new threads) |
| **Lachesis** | `fates/lachesis.py` | the Allotter | quota / resource accounting |
| **Atropos** | `fates/atropos.py` | the Inevitable | termination / clean shutdown |

---

## ☉ Furies — the Erinyes

| name | module | mythological role | cognitive function |
|------|--------|-------------------|--------------------|
| **Alecto** | `furies/alecto.py` | unceasing anger | invariant-violation alerter |
| **Megaera** | `furies/megaera.py` | jealousy | concurrency-conflict watcher |
| **Tisiphone** | `furies/tisiphone.py` | avenger of murder | integrity verifier (Styx chain) |

---

## ☉ Graces — the Charites

| name | module | mythological role | cognitive function |
|------|--------|-------------------|--------------------|
| **Aglaia** | `graces/aglaia.py` | Splendor | banners, section headers, accent formatting |
| **Euphrosyne** | `graces/euphrosyne.py` | Good Cheer | friendly error message reframing |
| **Thalia** (Grace) | `graces/thalia.py` | Festivity | doc-tone helpers (biography extraction) |

---

## ☉ Muses — Mnemosyne's nine daughters

| name | module | mythological role | cognitive function |
|------|--------|-------------------|--------------------|
| **Calliope** | `muses/calliope.py` | epic poetry | codex reader (long-form docs) |
| **Clio** | `muses/clio.py` | history | journal writer (`chronicle/journal/`) |
| **Erato** | `muses/erato.py` | love poetry | welcoming / warm user-facing prose |
| **Euterpe** | `muses/euterpe.py` | music | rhythm tracker (pheromone cadence) |
| **Melpomene** | `muses/melpomene.py` | tragedy | post-mortem recorder |
| **Polyhymnia** | `muses/polyhymnia.py` | sacred hymns | Styx hymnal (constitutional readings) |
| **Terpsichore** | `muses/terpsichore.py` | dance | choreography (cron-step registry) |
| **Thalia** (Muse) | `muses/thalia_muse.py` | comedy | closing blessings / casual register |
| **Urania** | `muses/urania.py` | astronomy | brain-map (constellation chart) |

---

## ☉ Heroes — mortals who confronted the gods

| name | module | mythological role | cognitive function |
|------|--------|-------------------|--------------------|
| **Heracles** | `heroes/heracles.py` | twelve labors | kill-test (12-labor harness) |
| **Perseus** | `heroes/perseus.py` | mirror, slayer of Medusa | reflection / journal-writing persona |
| **Theseus** | `heroes/theseus.py` | labyrinth navigator | brain-map exploration |
| **Odysseus** | `heroes/odysseus.py` | long return | session-resume helper |
| **Orpheus** | `heroes/orpheus.py` | descent into Hades | archive retrieval |
| **Atalanta** | `heroes/atalanta.py` | the fastest mortal | benchmark runner |
| **Momus** | `heroes/momus.py` | mockery (banished from Olympus) | the Anti-Architect (AP1–AP8 catalog) |

---

## ☉ Monsters — the named beasts

| name | module | mythological role | cognitive function |
|------|--------|-------------------|--------------------|
| **HYDRA** | `monsters/hydra/` | multi-headed beast of Lerna | watcher tier (read-only Heads) |
| **Argos** | `monsters/argos/` | many-eyed giant | decentralized swarm (Eyes + Satyrs + Demes + Phalanges) |
| **Cerberus** | `monsters/cerberus.py` | three-headed guardian | perimeter gate (auth + authz + integrity) |
| **Sphinx** | `monsters/sphinx.py` | the riddler | challenge-response gate |
| **Medusa** | `monsters/medusa.py` | petrifier | snapshot primitive |
| **Chimera** | `monsters/chimera.py` | hybrid beast | composite-test runner |
| **Minotaur** | `monsters/minotaur.py` | labyrinth-dweller | recursive-structure walker (with depth cap) |
| **Typhon** | `monsters/typhon.py` | father of monsters | catastrophic-scenario catalog |

---

## ☉ HYDRA — the heads (nine + immortal CM)

The heads of HYDRA each watch one slice of the substrate. Like the original Hydra's heads, when one is cut, another grows in its place — the replacement may take a different form, but the slice is covered.

| head | module | watches |
|------|--------|---------|
| **Cognitive** | `monsters/hydra/heads/head_cognitive.py` | the cognitive layer's self-state |
| **Security** | `monsters/hydra/heads/head_security.py` | perimeter / Cerberus traffic |
| **Performance** | `monsters/hydra/heads/head_performance.py` | latency, throughput |
| **Mission** | `monsters/hydra/heads/head_mission.py` | DOMAIN.md drift |
| **Adversary** | `monsters/hydra/heads/head_adversary.py` | Ares scenarios |
| **Swarm** | `monsters/hydra/heads/head_swarm.py` | Argos colony state |
| **Demes** | `monsters/hydra/heads/head_demes.py` | Argos civic tier |
| **Substrate** | `monsters/hydra/heads/head_substrate.py` | filesystem / Gaia state |
| **Trajectory** | `monsters/hydra/heads/head_trajectory.py` | rate-of-change drift |

---

## ☉ Argos — the swarm (eyes, satyrs, demes, phalanges)

Argos Panoptes had a hundred eyes that never all slept. The swarm tier carries that pattern: many specialized Eyes scan in parallel, never coordinating, depositing pheromones the colony integrates at read time.

**Eyes** (`monsters/argos/eyes/`) — observation specialists. Each Eye scans one slice; ~33 are registered. Each is one of Argos's hundred eyes.

**Satyrs** (`monsters/argos/satyrs/`) — wild-companion observers. Lower-cadence than Eyes; cover specific concrete checks (process alive, disk usage, log tail).

**Demes** (`monsters/argos/demes/`) — civic observers. The Greek polis-class:
- Mantis (seer) — `mantis_bloom_reader.py`
- Demarchos (deme leader) — `demarchos_roll_keeper.py`
- Hippeus (knight) — `hippeus_correlator.py`
- Demos (the people) — `demos_forum_watcher.py`
- Tamias (treasurer) — `tamias_treasurer.py`
- Ephoros (overseer) — `ephoros_watcher.py`

**Phalanges** (`monsters/argos/phalanges/`) — battle formations grouping Eyes by concern (adversary / cognitive / docs / engineer / mission / performance / guard / schema / security / substrate / trajectory).

---

## Pantheon population

| tier | count |
|------|------:|
| Primordials | 5 |
| Titans | 8 |
| Olympians (incl. Hestia, Apollo as subpackage) | 13 |
| Underworld | 5 |
| Fates | 3 |
| Furies | 3 |
| Graces | 3 |
| Muses | 9 |
| Heroes | 7 |
| Monsters (top-level) | 8 |
| HYDRA heads | 9 |
| **Total named gods** | **73** |

Plus the swarm's ~33 Eyes, 9 Satyrs, 6 Demes, 11 Phalanges — a full polis of observers.
