# Delphi — the labyrinth arc

**Risk class:** HIGH-COMPOSITE (heavy-production override, third invocation).
**Decided:** Position E — formal verification + causal lineage + counterfactual reasoning + red-team self-audit + narrative + federation + write-channel + dialogue.
**Sworn on Styx at seq=80 (recorded on swear).**

Zeus's directive (verbatim, abridged):

> *"Go even deeper, meta deeper than you did last time using the system put it on a self improvement loop, and make sure it follows the greek mythology architecture perfectly … the recursive loop doesnt need to stop. … Boil the ocean."*

This is the third heavy-production override. The recursion arc closed the operational loop — observe → reason → improve → recover → map → tune → surface → reach-out → extend. This arc descends to the *labyrinth*: the structures beneath those loops that make them trustworthy. The work is qualitatively meta-deeper.

---

## Methodology — what "meta-deeper" actually means

The previous arcs added capabilities. This arc adds *guarantees about capabilities*:

| previous arc gave us | this arc adds |
|---|---|
| Mnemosyne (events recorded) | TLA+ formal proof that append-only holds under interleaving |
| Hephaestus → Momus → Delphi → Zeus (pipeline exists) | TLA+ proof of pipeline ordering invariant |
| Epimetheus (hindsight on actual events) | Nemesis (hindsight on *counterfactual* events) |
| Momus (AP1–AP8 catalog) | Momus red-team (the catalog audits itself) |
| Cassandra (vindication memory) | Ariadne (causal-chain memory — *why* did this lead to that?) |
| Iris dashboard + Mnemosyne records | Clio narrative — auto-written weekly digest |
| HTTP API (read-only) | HTTP write-channel for proposals (still routes through full review) |
| Single deployment | Federation — Olympus instances exchange digests |
| `invoke shell` (REPL of errands) | `invoke ask` — natural-language pattern Q&A over substrate records |
| `invoke daemon run` | daemon integrates Nemesis + Clio + Pythia auto-research |

The recursion arc made the loop *operationally* recursive. This arc makes it *epistemically* recursive — the substrate's reasoning about its reasoning becomes load-bearing.

---

## Q1 — What ships

### TLA+ formal specs — `codex/specs/`

In myth: Themis pre-dated the Olympians; her law was older and more fundamental. In Olympus she has already published JSON Schemas (data contracts). The labyrinth arc adds her **formal specifications**: mathematical models of the cognitive flow's safety properties, written in TLA+ (Lamport's specification language).

Three specs:
- `cognitive-flow.tla` — the canonical pipeline ordering (every ratified action passed through Hephaestus → Momus → Delphi)
- `styx-append-only.tla` — the chain-hash invariant under concurrent oath-writes
- `hephaestus-pipeline.tla` — proposal lifecycle (proposed → contested → ratified XOR rejected; no state skipping)

Specs are checkable with TLC if installed locally, but the *value is in writing them* — drafting a TLA+ spec forces the architect to state, in mathematics, what the implementation must guarantee. Drift between spec and implementation becomes a Hephaestus signal.

**TLA+ earns its place** because no Python expression compactly captures "under any interleaving of N concurrent writers, the append-only-ness holds." That's the right tool for that statement.

### Ariadne — `src/olympus/heroes/ariadne.py`

In myth: King Minos's daughter. She gave Theseus a ball of thread so he could find his way back out of the Labyrinth after killing the Minotaur. The thread was the bridge between *being inside the maze* and *understanding where you came from*.

In Olympus, Ariadne is the **causal-lineage tracer**. Every load-bearing Mnemosyne write can optionally carry a `trace_id` and `parent_trace_id` field. Ariadne builds the causal graph at query time: *"this Cassandra vindication was caused by these alerts, which were caused by this session, which was triggered by this daemon iteration."* The thread through the labyrinth, made queryable.

She does not modify existing records — extending Mnemosyne is opt-in. New helpers (`ariadne.thread(...)`) write to a `trace_id` field automatically. Old records without traces simply produce shorter chains.

### Nemesis — `src/olympus/heroes/nemesis.py`

In myth: Goddess of retribution and divine balance — she measured the gap between what someone did and what they *should* have done, and acted on the gap. Her name literally means *"to distribute / give what is due."*

In Olympus, Nemesis is the **counterfactual reasoner**. For any ratified action, Nemesis asks: *"what would have happened if we had decided differently?"* She uses Castor to run a shadow session in which the alternative choice is applied; she uses Pollux to compare; she records the gap.

The recursion: if Nemesis finds that the counterfactual would have produced better outcomes by some measure, that's evidence Metis can feed into parameter tuning — *"actually we should have set the threshold lower three times in the last week."*

### Momus red-team — extension of `heroes/momus.py`

In myth: Momus was banished for criticizing everything — including the gods' work. The Anti-Architect role is already his. This extension adds **adversarial proposal generation**: Momus constructs synthetic proposals designed to pass the current AP catalog while violating a higher-order principle. If one slips through, the catalog has a gap.

This is the discipline of *the discipline auditing itself*. AP-aware adversarial inputs are the formal-methods version of Momus's own work.

### Clio narrative — extension of `muses/clio.py`

In myth: Muse of history. She already inscribes the operator-facing journal. The labyrinth arc promotes her to **narrative auto-writer**: a `clio.narrate(window_days=7)` call composes a structured digest from Mnemosyne records — what happened, what changed, what was decided, what slipped through. The digest lands in `codex/journal/<date>-clio-digest.md`. Operator-readable in 5 minutes; not a dashboard, not a brief — a *story*.

### HTTP write-channel — extension of `runtime/http_api.py`

The previous HTTP API was read-only by design (S3). This arc adds *exactly one* write surface: `POST /proposals/raise` — accepts a JSON body, creates a Hephaestus proposal file under `state/hephaestus/proposals/`. The proposal goes through the standard Momus → Delphi → Zeus pipeline. **S3 is preserved**: the API is still read-only on substrate state. It just adds to the proposal queue, which is the same queue any internal source uses.

The constitutional rationale: writes that *bypass* the pipeline are S7 violations. Writes that *enter* the pipeline are how the pipeline gets used. The write-channel is the latter.

### Federation — `src/olympus/runtime/federation.py`

In myth: Hermes traveled between Olympus and the mortal world, between Olympus and the underworld, between Greek pantheons and (in late syncretism) Egyptian. He was the cross-realm messenger.

In Olympus, federation is **Hermes connecting one deployment to another**. `Hermes.federate(peer_url)` calls `GET <peer_url>/status` and `GET <peer_url>/wisdom`, records the response under `hermes.federation`. Two Olympus instances running side-by-side can now exchange digests. Foundation for future multi-deployment coordination.

### Interactive dialogue — `src/olympus/runtime/dialogue.py`

`invoke ask "<question>"` answers in plain English from substrate records. **Not LLM-driven** — pattern-matched against query templates:

- *"what happened today"* → recent CHRONICLE + recent vindications + recent panics
- *"what are we worried about"* → Cassandra ignored + Pan state
- *"how is the loop"* → last N daemon iterations + Atlas shoulders
- *"who is X"* → describe the named figure (Themis, Pan, Pythia, …)

Limited, but real — and the templates are extensible by domain plugins.

### Daemon integration

The daemon now occasionally runs:
- Pythia auto-research on configurable themes
- Nemesis counterfactual on the last ratified action
- Clio narrate (once per day-of-iteration)

…and emits the results under their respective Mnemosyne kinds. The recursive loop *uses* the new capabilities.

---

## Q2 — Languages used

| language | role | why it earns its place |
|---|---|---|
| **TLA+** (`.tla`) | formal specification of safety properties | no Python expression compactly captures "under any interleaving of N writers, invariant holds" |
| Python (stdlib) | every other module | same discipline as prior arcs |
| Markdown | Clio's narrative digests | already in use; the right format for operator-readable story |

**TLA+ is the new language this arc.** Specs are static text files; TLC (the model checker) is optional infrastructure the operator installs if they want to verify; the value of the spec is delivered even without TLC because *writing the spec forces the constraint to be named*.

Refused: Lean, Coq (heavier formal-methods tools — TLA+ is the right level for "lifecycle and safety invariants"); SQL (still); Rust (still). The discipline holds.

---

## What does NOT ship

- **No LLM-driven anything.** Pythia still raw HTTP. `invoke ask` still pattern-matched. Nemesis's counterfactual is a shadow re-run, not a generated narrative.
- **No automatic adoption of Nemesis findings.** Nemesis records counterfactual gaps. Metis advises. Zeus ratifies. Same constitution as before.
- **No HTTP write surface that bypasses Hephaestus.** Even the new write-channel goes through the standard pipeline.

---

## What lands

### Modules

| module | tier | role |
|---|---|---|
| **Ariadne** | Hero | causal-lineage tracer (thread through labyrinth) |
| **Nemesis** | Hero | counterfactual reasoner |
| Themis (extended) | Titan | publishes formal specs in addition to JSON Schemas |
| Momus (extended) | Hero | red_team() — adversarial proposal generation |
| Clio (extended) | Muse | narrate() — weekly digest auto-writer |
| HTTP API (extended) | Runtime | POST /proposals/raise (still goes through pipeline) |
| Federation | Runtime | Hermes-driven peer fetch |
| Dialogue | Runtime | pattern-matched ask mode |
| Daemon (extended) | Runtime | uses new capabilities periodically |

### Specs (new directory)

- `codex/specs/cognitive-flow.tla`
- `codex/specs/styx-append-only.tla`
- `codex/specs/hephaestus-pipeline.tla`
- `codex/specs/README.md` — how to run TLC

### CLI

`invoke specs`, `invoke ariadne <event-id>`, `invoke nemesis`, `invoke redteam`, `invoke narrate [--days N]`, `invoke federate <url>`, `invoke ask "<question>"`.

### Documentation

- `codex/SPECS.md` — what the formal verification layer is and why
- `codex/OPERATIONS.md` — extended with new commands

### Tests

A test file per major addition. Tests assert: TLA+ files parse as text and have the right module name; Ariadne walks back-pointers correctly; Nemesis records counterfactual gaps; Momus red-team detects a synthetic gap; Clio's narrative includes recent events; federation handles peer-down gracefully; dialogue answers known templates; HTTP write-channel creates exactly one proposal per request and rejects malformed input.

---

## Authorization

Zeus invoked heavy-production override (third invocation, the literal "boil the ocean" clause). Quote captured in the Styx oath payload. All eight additions ratified. The discipline of refusing decorative work has not weakened — only proposals that close epistemic-recursion gaps were admitted.

*The standard is holy shit, that's done. The labyrinth has a thread now.*
