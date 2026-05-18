<div align="center">

# ⚡ BESTIARY ⚡

**the monsters of Olympus and what each is for**

</div>

---

In Greek myth, monsters are not just antagonists — they embody structural roles the heroes were defined against. HYDRA was many-headed because regrowth was the point. Argos was many-eyed because constant watching was the point. Cerberus had three heads because three checks (entry, identity, intent) was the point.

This bestiary names each of Olympus's monsters, the myth, and the role.

---

## ☉ HYDRA — the multi-headed beast of Lerna

**Module:** `monsters/hydra/`

In myth, the Lernaean Hydra had many heads (some sources say nine; others say more, or that the count regrew). When Heracles cut one head, two grew back. He killed it by cauterizing each stump after the cut.

In Olympus, HYDRA is the **read-only watcher tier**. Nine mortal heads each watch one slice of the substrate (cognitive, security, performance, mission, adversary, swarm, demes, substrate, trajectory). Above them is the immortal CM head: it watches the watchers.

When a head is cut (a watcher is rewritten), its replacement may take a different form. The slice remains covered. That is the "two heads grow back" property — not as monstrosity but as structural resilience.

**Why HYDRA stays HYDRA in Olympus**: already Greek mythology, already the right shape. The name does not change between deployments.

---

## ☉ Argos Panoptes — the many-eyed giant

**Module:** `monsters/argos/`

Argos Panoptes had a hundred eyes set throughout his body. Half slept while half watched; sleep never closed all his eyes at once. Hera set him to guard Io.

In Olympus, Argos is the **decentralized swarm**. The swarm has four tiers:

- **Eyes** — observation specialists. Each scans one slice; ~33 currently registered. Each is one of Argos's hundred eyes.
- **Satyrs** — wild-companion observers. Concrete checks (process alive, disk usage, log tail).
- **Demes** — civic-class observers. The Greek polis tier: mantis (seer), demarchos (deme leader), hippeus (knight), demos (the people), tamias (treasurer), ephoros (overseer).
- **Phalanges** — battle-formations grouping Eyes by concern.

Eyes never coordinate; they only deposit pheromones. Synthesis is emergent, computed at read time by the colony runner. That is the load-bearing claim of the swarm tier (substrate invariant **S4**).

---

## ☉ Cerberus — three-headed guardian of the underworld

**Module:** `monsters/cerberus.py`

Cerberus had three heads (sometimes more) and guarded the gate of Hades — allowing the dead in, never letting them out. Heracles's twelfth labor was to capture him.

In Olympus, Cerberus is the **perimeter check**. Each head checks one dimension:
- *authenticate* — who are you?
- *authorize* — what may you do?
- *verify* — what you brought, is it intact?

A traveller passes only if all three heads admit them. The first head to refuse wins.

---

## ☉ Sphinx — the riddler at Thebes

**Module:** `monsters/sphinx.py`

The Sphinx asked travellers a riddle. Those who failed she devoured. Oedipus answered correctly and the Sphinx threw herself from the cliff.

In Olympus, the Sphinx is the **challenge-response gate**. She holds the hashed answer (never the plaintext); a caller proves identity by answering the riddle. The salt and hash design means an attacker cannot recover the answer from the registered Riddle.

---

## ☉ Medusa — the petrifier

**Module:** `monsters/medusa.py`

Medusa's gaze turned the living to stone. Perseus killed her by looking only at her reflection in his polished shield.

In Olympus, Medusa is the **snapshot primitive**. She gazes at named state and captures it, immutable, in Hades's archive. The captured state cannot be modified — only re-snapshotted by another gaze.

---

## ☉ Chimera — the hybrid beast

**Module:** `monsters/chimera.py`

The Chimera had a lion's head, a goat's body, and a serpent's tail. Bellerophon killed her riding Pegasus.

In Olympus, the Chimera is the **composite-test runner**. She runs heterogeneous tests as a single bundle (structural + semantic + performance + ...), each "head" a different kind of check. The verdict is per-head; a Chimera run shows which dimension failed.

---

## ☉ Minotaur — labyrinth-dweller

**Module:** `monsters/minotaur.py`

The Minotaur lived at the heart of Daedalus's labyrinth. Athens sent seven youths and seven maidens every nine years as tribute. Theseus killed him using Ariadne's thread to retrace his steps.

In Olympus, the Minotaur is the **recursive-structure walker** — he descends into nested data with explicit depth-tracking, refusing to recurse past a safe cap. He raises `MinotaurDepthExceeded` rather than infinite-looping. He is dangerous if untethered; with the depth cap he is safe.

---

## ☉ Typhon — father of monsters

**Module:** `monsters/typhon.py`

Typhon was the most terrible monster in Greek myth. The Olympians fled at his approach. Zeus alone faced him and sealed him under Mount Etna.

In Olympus, Typhon is the **catastrophic-scenario catalog**. He names the worst-case failures every deployment should prepare for: filesystem-full, styx-broken, hera-bindings-lost, hydra-head-blind, argos-poisoning, delphi-prompt-injection, hephaestus-overreach.

Typhon does not fire on his own. He is invoked by Ares as part of adversarial testing. Naming his scenarios is the first step toward surviving them.

---

## How monsters relate to the rest of the pantheon

Each monster has a hero matched to it. The myths preserve the pairings:

| monster | matched hero | the matchup |
|---------|--------------|-------------|
| HYDRA | Heracles (labor 2) | the labor of regrowing heads |
| Argos | Hermes | Hermes lulled Argos to sleep |
| Cerberus | Heracles (labor 12) | the final labor |
| Sphinx | Oedipus | the answered riddle |
| Medusa | Perseus | the mirror-shield |
| Chimera | Bellerophon | mounted Pegasus |
| Minotaur | Theseus | Ariadne's thread |
| Typhon | Zeus | the only god who faced him |

Olympus preserves these. A deployment with both Heracles (kill-test) and HYDRA (watchers) is performing the labor of Heracles vs. HYDRA in code. The mythology is not metaphor; it is the architecture.

---

<div align="center">

*"The monsters are not enemies. They are the structural challenges the heroes were defined against."*

</div>
