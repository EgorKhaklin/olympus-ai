# Delphi — the oikoumene arc 🌍

**Risk class:** HIGH-COMPOSITE (sixth heavy-production override).
**Decided:** Position H — pluggable LLM bridge + agent role registry + LLM-as-Hephaestus/Momus/Cassandra + recursion gate for new figures + calibration scoring + answers to Zeus's three explicit questions.
**Sworn on Styx at seq=105.**

Zeus's critique, verbatim (the load-bearing sentence):

> *"Right now it's still mostly high-quality scaffolding and architecture. … we haven't yet seen closed, meaningful agent loops that demonstrate the substrate improving agent behavior in measurable ways. … How do actual LLM agents inhabit this substrate? Is the mythology functioning as grounding/ontology that gets injected into prompts, or is it more of an external governance/runtime that the models interact with through the API? What's the recursion story? Can agents operating inside Olympus propose new figures or extend the pantheon while staying inside the invariants, or is that intentionally gated for now?"*

The critique is the right one. Five arcs built a beautiful empty city. This arc moves agents in.

The name — **oikoumene** (οἰκουμένη) — is the Greek word for *the inhabited world*, as distinct from the wilderness. This arc is when Olympus becomes inhabited.

---

## Phase 0 — system activated, incoherences fixed

Per the directive's standing requirement, the system was started end-to-end before any code was written:
- HTTP API live on `:8765` (`/healthz` ok; `/status` reports hearth lit + 92 Styx oaths intact)
- Daemon ran 2 iterations cleanly
- Hygieia diagnostic flagged 1 incoherence + 2 warnings

Each was fixed in code, not papered over:
- **pan-vs-invariants** (incoherent → well): Hygieia's check now honors Pan's `acknowledged_through` timestamp — operator-acknowledged violations don't count toward incoherence.
- **daedalus-vs-disk** (warning → well): `_known_figures` whitelist extended to recognize tier-names (furies/fates/graces/muses) as concept-nodes; root .py modules (session, wisdom) and subpackage children (pythia) are now found.
- **plato-vs-disk** (warning → well): added `cronus` and `oceanus` to Plato's taxonomy; tightened Hygieia's figure-definition to exclude implementation modules (action, cli, oracle, brief, head, …).

**Result: 6 well, 0 warning, 0 incoherent. 83/83 figures classified by Plato.** Tests still 393/393.

---

## Answering Zeus's three explicit questions

The three questions deserve direct answers before the design. This Delphi codifies them.

### Q1 — *How do actual LLM agents inhabit this substrate?*

By becoming a named figure. An LLM call is always made *as* some Greek role — *as-Hephaestus*, *as-Momus*, *as-Cassandra*. The role determines:
- the **system prompt** (the figure's docstring + the figure's place in the constitution)
- the **context** (what the figure normally reads — Athena reads Mnemosyne; Hephaestus reads briefs and rejection memory; Momus receives a proposal)
- the **output shape** (what the figure normally writes — a proposal, an AP-list, a brief)
- the **destination** (where the output goes — Hephaestus's response becomes a proposal; Momus's response becomes a contest)

The agent does **not** bypass the substrate. It feeds the substrate the same way internal heuristics already do.

### Q2 — *Mythology as prompt-grounding, or external API governance?*

**Both, by design.** The two together are the answer.

- **Prompt grounding (inside the model)**: every agent call receives a system prompt that includes the figure's role, the constitutional invariants (S1–S8), and the AP catalog Momus owns. The mythology is *ontology* the model thinks within.

- **External governance (outside the model)**: every LLM output is treated as a *proposal*, not an authoritative action. Pan still gates ratification. Momus still contests. Delphi still records strategic decisions. Zeus still ratifies. The LLM can speak; only the constitution can act.

The split is intentional: the model thinks in the mythology; the substrate enforces the constitution on the model's outputs. Neither piece alone is sufficient.

### Q3 — *Can agents propose new figures? What's gated?*

**Yes — through the standard pipeline. No — never auto-executed.**

The recursion path is concrete:

1. `invoke propose-figure --by-agent` calls LLM-as-Hephaestus with the directive *"propose a new Greek figure that would close a substrate gap, with name, mythological grounding, tier, role, and suggested module skeleton."*
2. The response becomes a `HIGH`-risk Hephaestus proposal file at `state/hephaestus/proposals/<id>.json`.
3. **Momus contests** with the full AP catalog — particularly AP8 (does it earn its place?) and AP4 (is this constitutional creep?).
4. **Delphi required** (S6 — every HIGH/COMPOSITE proposal needs a written debate).
5. **Zeus ratifies** (manually) — or rejects.
6. **Even after ratification**, the substrate does NOT auto-write the Python file. The proposal contains *suggested* source code; the operator copies it to `src/olympus/<tier>/<name>.py` and runs tests.

What's gated:
- **LLM-generated code is never executed without operator review.** AP6 + AP1 + S7 still hold. The substrate enforces this at the action-queue layer.
- **Pan still gates ratification.** An LLM agent's proposal cannot bypass the circuit breaker.
- **Mnemosyne records every LLM call in full** — system prompt, user prompt, response, model id, token counts. S8 holds.

What's NOT gated:
- LLM agents can read everything (substrate state, JSONL records, the constitution).
- LLM agents can propose anything — including extending the pantheon — provided the proposal passes the standard pipeline.

---

## What ships

### LLM bridge — `src/olympus/runtime/llm_bridge.py`

Pluggable interface for LLM providers. Two built-in bridges:

- **`AnthropicBridge`** — uses the `anthropic` SDK with `claude-opus-4-7` and adaptive thinking (per the `claude-api` skill defaults). Streams long responses via `.get_final_message()`. Records every call to Mnemosyne under `llm.call` with model id, prompt hash, token counts, elapsed ms.
- **`EchoBridge`** — deterministic stub for tests + safe operation when no provider is configured. Returns structured echo data.

The bridge is selected via the `OLYMPUS_LLM` env var:
- `OLYMPUS_LLM=anthropic` → AnthropicBridge (requires `pip install anthropic` + `ANTHROPIC_API_KEY`)
- `OLYMPUS_LLM=echo` (default) → EchoBridge — safe; never hits the network

The bridge is pluggable: a deployment can register its own via the `olympus.llm_bridges` entry-point group.

### Agent registry — `src/olympus/runtime/agents.py`

Five canonical agent roles, each tied to an existing figure:

| role | based on | reads | writes |
|---|---|---|---|
| `agent.hephaestus` | Hephaestus (drift surfacer) | recent brief + Mnemosyne | a Hephaestus proposal |
| `agent.momus` | Momus (anti-architect) | a proposal | AP-id list + per-AP reasoning |
| `agent.cassandra` | Cassandra (vindication memory) | dismissed-warning history | a vindication assessment |
| `agent.athena` | Athena (synthesis) | findings + history | a structured insight set |
| `agent.figure_proposer` | Hephaestus, in figure-proposal mode | constitution + pantheon | a new-figure proposal |

Each role:
1. Renders the system prompt (figure's docstring + constitution + role guidance)
2. Renders the user prompt (the specific context for this call)
3. Calls the LLM bridge
4. Parses the response into a structured object
5. Feeds the result into the standard pipeline (proposal, contest, vindication, brief, …)

### Recursion path — new-figure proposal

`invoke propose-figure --by-agent [--directive "<seed>"]` runs the figure-proposer role. The result is a HIGH-risk Hephaestus proposal file containing:

- proposed figure name + tier
- mythological grounding (so it's not made up)
- one-sentence cognitive role
- AP-self-check (did the agent argue against its own proposal?)
- suggested skeleton (NOT auto-executed; operator's choice)

The proposal goes through the standard pipeline: Momus AP catalog → Delphi (S6) → Zeus.

### Calibration scoring — `runtime/agents.py::calibration()`

Every LLM call records an agent confidence (when the role's output schema includes one). When subsequent substrate state confirms or refutes the agent's claim, calibration updates. Per-role calibration score over time is queryable via `agents.calibration(role)`.

### CLI surface

- `invoke agent hephaestus [--directive "<seed>"]` — LLM-as-Hephaestus surface drift
- `invoke agent momus <proposal-file>` — LLM-as-Momus contest a proposal
- `invoke agent cassandra` — LLM-as-Cassandra review dismissed warnings
- `invoke agent athena` — LLM-as-Athena synthesize from current brief
- `invoke propose-figure [--directive "<seed>"]` — LLM-driven figure proposal
- `invoke calibration [--role <name>]` — per-role calibration over time

### Documentation

- **`codex/AGENTS.md`** — the explicit answers to Zeus's three questions, with operator examples and the gating diagram.
- **README** — gains an "Agents" section.

### Tests

The test suite never hits the network. All agent tests use `EchoBridge` for determinism. We assert:
- Bridge selection via env var works
- Each role renders a non-empty prompt
- Each role parses the bridge's response into the right structured type
- The LLM call is recorded to Mnemosyne (`llm.call`)
- A figure-proposal goes through the standard pipeline (Hephaestus → file → Momus contestable)
- Calibration scoring updates correctly

---

## Q — Languages used

| language | role | why it earns its place |
|---|---|---|
| Python (stdlib first, `anthropic` SDK optional) | every module | discipline holds; `anthropic` is the official SDK for the chosen provider; tested with a stdlib EchoBridge so the suite never requires it |
| Markdown | AGENTS.md + READMEs | already in use |

**No new language this arc.** The `anthropic` dependency is **optional** — the EchoBridge runs without it, and the entire test suite passes without `anthropic` installed.

---

## What does NOT ship

- **No LLM-generated code execution.** Period. The substrate never `exec()`s an LLM response. The most an LLM proposal can do is create a *proposal file* with suggested code that an operator may copy.
- **No LLM in the daemon's hot path by default.** The daemon's iteration runs heuristics; agent calls are opt-in (`invoke agent …`). The daemon can be configured to invoke agents on a slower cadence, but the default is off — to keep the loop deterministic and cost-bounded.
- **No bypass of Pan.** An LLM agent's proposal is subject to Pan's circuit breaker exactly like any internal proposal.
- **No new tier for "agents".** The agent layer lives in `runtime/`; agents *are* canonical figures (Hephaestus-as-agent IS Hephaestus). No tier expansion.

---

## Authorization

Zeus invoked the heavy-production override (sixth invocation, the literal "boil the ocean" clause). Quote captured in the Styx oath payload. All additions ratified. The three explicit questions get explicit answers in `codex/AGENTS.md`.

*The standard is holy shit, that's done. The substrate is inhabited.*
