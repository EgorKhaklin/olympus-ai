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
| **Themis** | `titans/themis.py` | divine law, the Oracle of Delphi before Apollo | the substrate constitution (S1–S8) |
| **Cronus** | `titans/cronus.py` | Time, deposed king of the Titans | structured schedules / cadences |
| **Hyperion** | `titans/hyperion.py` | Light, father of Sun/Moon/Dawn | observability (counters + gauges) |
| **Rhea** | `titans/rhea.py` | Motherhood, mother of Zeus | bootstrap (ensures directory structure) |
| **Oceanus** | `titans/oceanus.py` | the world-encircling river | I/O boundary |
| **Iapetus** | `titans/iapetus.py` | mortality, father of Prometheus | lifecycle state machine |
| **Coeus** | `titans/coeus.py` | the axis of heaven, intellect | investigation / queries |

---

## ☉ Olympians — the twelve (+ Hestia)

| name | module | mythological role | cognitive function |
|------|--------|-------------------|--------------------|
| **Zeus** | `olympians/zeus.py` | king of the gods | operator interface |
| **Hera** | `olympians/hera.py` | queen, goddess of marriage | bindings registry |
| **Poseidon** | `olympians/poseidon.py` | sea, earth-shaker | data flow (pub/sub) |
| **Demeter** | `olympians/demeter.py` | harvest | batch ingestion |
| **Athena** | `olympians/athena.py` | wisdom, strategy | strategic synthesis (briefs) |
| **Apollo** | `olympians/apollo/` | prophecy | falsifiable predicates |
| **Artemis** | `olympians/artemis.py` | huntress, the precise arrow | precision metrics (percentiles) |
| **Ares** | `olympians/ares.py` | war | adversarial assault orchestration |
| **Aphrodite** | `olympians/aphrodite.py` | beauty | terminal aesthetics |
| **Hephaestus** | `olympians/hephaestus.py` | smith, the only laboring god | the Architect — drift surfacing |
| **Hermes** | `olympians/hermes.py` | messenger | CLI dispatch surface |
| **Dionysus** | `olympians/dionysus.py` | wine, transformation | state-transition recording |
| **Hestia** | `olympians/hestia.py` | the hearth, sacred boundary | deployment identity-seal |

---

## ☉ Underworld — Hades's realm

| name | module | mythological role | cognitive function |
|------|--------|-------------------|--------------------|
| **Hades** | `underworld/hades.py` | king of the underworld | archive |
| **Persephone** | `underworld/persephone.py` | queen, half above + half below | cyclical state |
| **Hecate** | `underworld/hecate.py` | crossroads, in-between | error recovery |
| **Styx** | `underworld/styx.py` | river of unbreakable oaths | cryptographic immutable ledger |
| **Lethe** | `underworld/lethe.py` | river of forgetting | ephemeral cache (TTL'd) |

---

## ☉ Fates — the Moirai

| name | module | mythological role | cognitive function |
|------|--------|-------------------|--------------------|
| **Clotho** | `fates/clotho.py` | the Spinner | creation primitive |
| **Lachesis** | `fates/lachesis.py` | the Allotter | quota / resource accounting |
| **Atropos** | `fates/atropos.py` | the Inevitable | termination |

---

## ☉ Furies — the Erinyes

| name | module | mythological role | cognitive function |
|------|--------|-------------------|--------------------|
| **Alecto** | `furies/alecto.py` | unceasing anger | invariant-violation alerter |
| **Megaera** | `furies/megaera.py` | jealousy | concurrency-conflict watcher |
| **Tisiphone** | `furies/tisiphone.py` | avenger of murder | integrity verifier |

---

## ☉ Graces — the Charites

| name | module | mythological role | cognitive function |
|------|--------|-------------------|--------------------|
| **Aglaia** | `graces/aglaia.py` | Splendor | banners, section headers |
| **Euphrosyne** | `graces/euphrosyne.py` | Good Cheer | friendly error message reframing |
| **Thalia** (Grace) | `graces/thalia.py` | Festivity | doc-tone helpers |

---

## ☉ Muses — Mnemosyne's nine daughters

| name | module | mythological role | cognitive function |
|------|--------|-------------------|--------------------|
| **Calliope** | `muses/calliope.py` | epic poetry | codex reader |
| **Clio** | `muses/clio.py` | history | journal writer (`codex/journal/`) |
| **Erato** | `muses/erato.py` | love poetry | warm user-facing prose |
| **Euterpe** | `muses/euterpe.py` | music | rhythm tracker |
| **Melpomene** | `muses/melpomene.py` | tragedy | post-mortem recorder (`codex/postmortems/`) |
| **Polyhymnia** | `muses/polyhymnia.py` | sacred hymns | Styx hymnal |
| **Terpsichore** | `muses/terpsichore.py` | dance | choreography registry |
| **Thalia** (Muse) | `muses/thalia_muse.py` | comedy | closing blessings |
| **Urania** | `muses/urania.py` | astronomy | brain-map (constellation chart) |

---

## ☉ Heroes — mortals who confronted the gods

| name | module | mythological role | cognitive function |
|------|--------|-------------------|--------------------|
| **Heracles** | `heroes/heracles.py` | twelve labors | kill-test harness |
| **Perseus** | `heroes/perseus.py` | mirror, slayer of Medusa | reflection persona |
| **Theseus** | `heroes/theseus.py` | labyrinth navigator | brain-map exploration |
| **Odysseus** | `heroes/odysseus.py` | long return | session-resume helper |
| **Orpheus** | `heroes/orpheus.py` | descent into Hades | archive retrieval |
| **Atalanta** | `heroes/atalanta.py` | the fastest mortal | benchmark runner |
| **Momus** | `heroes/momus.py` | mockery (banished from Olympus) | the Anti-Architect (AP1–AP8) |

---

## ☉ Monsters — the named beasts

| name | module | mythological role | cognitive function |
|------|--------|-------------------|--------------------|
| **HYDRA** | `monsters/hydra/` | multi-headed beast of Lerna | watcher tier |
| **Argos** | `monsters/argos/` | many-eyed giant | decentralized swarm |
| **Cerberus** | `monsters/cerberus.py` | three-headed guardian | perimeter gate |
| **Sphinx** | `monsters/sphinx.py` | the riddler | challenge-response gate |
| **Medusa** | `monsters/medusa.py` | petrifier | snapshot primitive |
| **Chimera** | `monsters/chimera.py` | hybrid beast | composite-test runner |
| **Minotaur** | `monsters/minotaur.py` | labyrinth-dweller | recursive walker (depth-capped) |
| **Typhon** | `monsters/typhon.py` | father of monsters | catastrophic-scenario catalog |

---

## ☉ HYDRA — eight mortal heads + one immortal

The Lernaean Hydra had many heads; one was immortal. Heracles cut the mortal heads (each replaced by a different head covering the same slice), then buried the immortal head under a great stone.

| head | module | watches | immortal? |
|------|--------|---------|:---------:|
| **Cosmogony** | `monsters/hydra/heads/head_cosmogony.py` | constitution naming all S1–S8 | — |
| **Pantheon** | `monsters/hydra/heads/head_pantheon.py` | PANTHEON.md against disk | — |
| **Styx** | `monsters/hydra/heads/head_styx.py` | oath chain integrity | — |
| **Journal** | `monsters/hydra/heads/head_journal.py` | journal for silence | — |
| **Oaths** | `monsters/hydra/heads/head_oaths.py` | cadence of new Styx oaths | — |
| **Lifecycle** | `monsters/hydra/heads/head_lifecycle.py` | Iapetus's lifecycle registry | — |
| **Substrate** | `monsters/hydra/heads/head_substrate.py` | filesystem layout | — |
| **Apollo** | `monsters/hydra/heads/head_apollo.py` | Apollo's predicate coverage | — |
| **Immortal** | `monsters/hydra/heads/head_immortal.py` | the other eight heads themselves | ✓ |

When a mortal head is cut (rewritten), its replacement may take a different form. The immortal head is the structural guarantee that the watcher tier is always operating.

---

## ☉ Argos — the swarm tier

### Eyes — observation specialists (eight)

| eye | module | watches |
|-----|--------|---------|
| **cosmogony_drift** | `monsters/argos/eyes/eye_cosmogony_drift.py` | constitution naming all S1–S8 |
| **pantheon_completeness** | `monsters/argos/eyes/eye_pantheon_completeness.py` | PANTHEON.md ↔ disk |
| **styx_chain_intact** | `monsters/argos/eyes/eye_styx_chain_intact.py` | oath-chain verification |
| **journal_silence** | `monsters/argos/eyes/eye_journal_silence.py` | days since Clio last inscribed |
| **chronicle_gap** | `monsters/argos/eyes/eye_chronicle_gap.py` | days since CHRONICLE.md changed |
| **oath_freshness** | `monsters/argos/eyes/eye_oath_freshness.py` | hours since last Styx oath |
| **apollo_coverage** | `monsters/argos/eyes/eye_apollo_coverage.py` | predicate count + S5 compliance |
| **delphi_pending** | `monsters/argos/eyes/eye_delphi_pending.py` | unresolved Delphi files |

### Satyrs — wild-companion concrete checks (four)

| satyr | module | checks |
|-------|--------|--------|
| **hearth** | `monsters/argos/satyrs/satyr_hearth.py` | Hestia's hearth is lit |
| **substrate** | `monsters/argos/satyrs/satyr_substrate.py` | required dirs all present |
| **styx** | `monsters/argos/satyrs/satyr_styx.py` | quick oath-chain check |
| **pantheon** | `monsters/argos/satyrs/satyr_pantheon.py` | every cosmogonic tier populated |

### Demes — civic-class observers (six)

| deme | module | civic role |
|------|--------|-----------|
| **mantis** | `monsters/argos/demes/mantis.py` | the seer — pattern surfacing |
| **demarchos** | `monsters/argos/demes/demarchos.py` | the deme-leader — registry roll-keeper |
| **hippeus** | `monsters/argos/demes/hippeus.py` | the cavalry — fast correlation |
| **demos** | `monsters/argos/demes/demos.py` | the people — public-facing surfaces |
| **tamias** | `monsters/argos/demes/tamias.py` | the treasurer — quota accounting |
| **ephoros** | `monsters/argos/demes/ephoros.py` | the overseer — Delphi compliance |

### Phalanges — battle formations (four)

| phalanx | module | concern |
|---------|--------|---------|
| **constitutional** | `monsters/argos/phalanges/phalanx_constitutional.py` | the substrate's own laws |
| **substrate** | `monsters/argos/phalanges/phalanx_substrate.py` | filesystem layout |
| **cadence** | `monsters/argos/phalanges/phalanx_cadence.py` | rhythms of operation |
| **oracular** | `monsters/argos/phalanges/phalanx_oracular.py` | Apollo + Delphi surfaces |

---

## Pantheon population

| tier | count |
|------|------:|
| Primordials | 5 |
| Titans | 8 |
| Olympians (incl. Hestia + Apollo subpackage) | 13 |
| Underworld | 5 |
| Fates | 3 |
| Furies | 3 |
| Graces | 3 |
| Muses | 9 |
| Heroes | 7 |
| Monsters (top-level) | 8 |
| HYDRA heads | 9 (8 mortal + 1 immortal) |
| **Total named principal figures** | **73** |

Plus the Argos swarm: **8 Eyes**, **4 Satyrs**, **6 Demes**, **4 Phalanges**.
