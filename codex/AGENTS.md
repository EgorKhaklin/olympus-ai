<div align="center">

# 🌍 AGENTS 🌍

**how LLMs inhabit Olympus**

</div>

---

Per Delphi 2026-05-18-oikoumene-arc.md.

Five arcs built a beautiful empty city. The oikoumene arc moved agents in. This document is the explicit answer to three questions that ought to be obvious to anyone reading the code, and now are:

1. **How do actual LLM agents inhabit this substrate?**
2. **Is the mythology functioning as prompt grounding/ontology, or as external governance/runtime?**
3. **What's the recursion story? Can agents propose new figures?**

---

## Q1 — How do LLM agents inhabit Olympus?

**By becoming a named figure.**

Every LLM call is made *as* some Greek role. Five canonical roles ship:

| role | based on | reads | writes |
|---|---|---|---|
| `agent.hephaestus` | Hephaestus (drift surfacer) | recent brief + Mnemosyne | a Hephaestus proposal |
| `agent.momus` | Momus (anti-architect) | a proposal | AP-id list + per-AP reasoning |
| `agent.cassandra` | Cassandra (vindication memory) | dismissed-warning history | a vindication assessment |
| `agent.athena` | Athena (synthesis) | findings + history | structured insight set |
| `agent.figure_proposer` | Hephaestus, in figure-proposal mode | constitution + pantheon | a new-figure proposal |

Each role:

1. **Renders the system prompt** — figure docstring + the substrate constitution (S1–S8) + the AP catalog (AP1–AP8) + role-specific output schema
2. **Renders the user prompt** — specific context for this call
3. **Calls the LLM bridge** — pluggable; default `EchoBridge` for safety/tests, `AnthropicBridge` for `claude-opus-4-7` with adaptive thinking
4. **Parses the response** — strict JSON; tolerant of Markdown fences
5. **Feeds the substrate** — the parsed output enters the standard pipeline (proposal, contest, vindication, brief)

The agent **never bypasses** the substrate. Its output is data, not action.

### The provider is pluggable

```bash
# Default — safe, deterministic, never hits network
OLYMPUS_LLM=echo invoke agent hephaestus

# Real LLM (requires `pip install anthropic` + ANTHROPIC_API_KEY)
OLYMPUS_LLM=anthropic invoke agent hephaestus

# A deployment can register its own bridge via entry-points
# (see codex/PLUGINS.md)
```

### Every call is recorded

S8 holds for LLM calls exactly like everything else. `mnemosyne.recall("llm.call")` returns every prompt + response (heads bytes capped to 1024 chars; full prompt hash stored) with model id, token counts, elapsed ms.

```bash
# What did the LLM see and say recently?
invoke mnemosyne llm.call --limit 5    # (via HTTP API)
# Or:
cat state/mnemosyne/llmcall.jsonl | tail -5 | jq
```

---

## Q2 — Mythology as prompt grounding, or external governance?

**Both, by design. The two together are the answer.**

### Prompt grounding (inside the model)

Every agent call's system prompt includes:

- The figure's docstring (their role in Olympus)
- The constitution primer (S1–S8 in compact form)
- The AP catalog (AP1–AP8 — Momus's contestable patterns)
- The role-specific output schema (what shape the response must take)

The model thinks **in** the mythology and the constitution. The figure isn't just a label on the call; it's the lens the model reasons through.

```python
# From src/olympus/runtime/agents.py
CONSTITUTION_PRIMER = """
You operate inside Olympus, a cognitive substrate built in the shape
of Greek mythology. Your role is a single named figure. You think in
the mythology and the constitution; you do not act outside them.

The eight substrate invariants — these always hold:
  S1 Mnemosyne — every load-bearing decision writes to an append-only record.
  ...
The eight anti-patterns Momus contests (AP1-AP8):
  AP1 self-observation without ground-touch
  ...
"""
```

### External governance (outside the model)

Every LLM output is treated as a **proposal**, not an authoritative action:

- **Pan** still gates ratification. If Pan is in panic, agent calls are refused (`PanicError`). The circuit breaker doesn't care whether the proposer is a heuristic or an LLM.
- **Momus** (the heuristic) still contests. An LLM-as-Momus call **augments** the heuristic catalog; it doesn't replace it.
- **Delphi** (S6) still requires a written debate for MEDIUM/HIGH-risk strategic decisions, regardless of who raised them.
- **Zeus** still ratifies. An LLM agent's proposal sits in the action queue until the operator (or, in the future, a federated peer with the right authority) ratifies it.

**The model thinks in the mythology; the substrate enforces the constitution on the model's outputs.** Neither half is sufficient alone.

### The seam, in one ASCII diagram

```
  ┌──── inside the model ─────┐    ┌──── outside the model ─────┐
  │  system prompt:            │    │  Pan circuit breaker        │
  │   figure docstring         │    │  Momus AP catalog (heur)    │
  │   constitution primer      │    │  Delphi (S6 written debate) │
  │   AP catalog               │    │  Zeus ratification          │
  │   output schema            │ →  │  Mnemosyne append (S1 + S8) │
  │                            │    │  Hephaestus pipeline route  │
  │  user prompt: context      │    │  ActionQueue (S7 risk class)│
  └────────────────────────────┘    └─────────────────────────────┘
              "thinks IN"                    "enforces ON"
```

---

## Q3 — Recursion: can agents propose new figures?

**Yes, through the same pipeline. Never auto-executed.**

The recursion path is concrete and gated:

```bash
invoke propose-figure "we need a figure that does X"
```

What happens:

1. `agent.figure_proposer` (LLM-as-Hephaestus in figure-proposal mode) receives:
   - The constitution
   - The current pantheon (first 60 figures, to avoid duplicates)
   - The directive
   - A strict output schema: `figure_name`, `tier`, `mythological_grounding`, `cognitive_role`, `ap_self_check` (the agent must audit its own proposal against AP1–AP8), `skeleton` (suggested Python source — operator's choice whether to use), `confidence`
2. The substrate validates:
   - Refuses if `figure_name` already exists in the pantheon
   - Refuses if Pan is in panic
   - Writes a `HIGH`-risk Hephaestus proposal file to `state/hephaestus/proposals/figure-<id>.json`
   - Records `agent.figure-proposal` in Mnemosyne
3. From here, the **standard pipeline** applies:
   - **Momus** contests (AP catalog runs on the new proposal)
   - **S6 Delphi** required — an operator (or a future LLM-as-Delphi-author with appropriate gating) must write a Delphi document
   - **Zeus** ratifies — manually, with a quoted authorization sworn on Styx
4. **Even after ratification, the substrate does NOT create the Python file.** The proposal's `suggested_skeleton` is *suggestion*. The operator copies it (after review) to `src/olympus/<tier>/<name>.py` and runs `pytest`.

### What's gated, in one table

| action | gated? | why |
|---|:---:|---|
| LLM agent reads substrate state | ❌ no | reads are read-only by definition (S3) |
| LLM agent proposes a fix | ❌ no | proposals are *data*, not actions; the pipeline contests + ratifies them |
| LLM agent proposes a new figure | ❌ no | same — a proposal file is created, contested, ratified |
| LLM agent's response is executed as code | ✅ yes — refused outright | AP6 + AP1 + S7 all fire on LLM-generated code execution |
| LLM agent's proposal bypasses Pan | ✅ yes — refused outright | Pan guards `action.ratify` regardless of proposer |
| LLM agent writes to substrate state directly | ✅ yes — refused outright | the only allowed write is to the proposal queue, via the standard channel |

### The unlock: the operator

The recursion doesn't end with the agent. The **operator** decides whether to copy a proposed skeleton into source. That step is a deliberate human-in-the-loop — exactly as bounded-RSI research recommends (Steunebrink; nfh-self-improvement-loop; ESAA-Security).

The substrate **does not unlock itself**. The operator (or a future, explicitly-ratified delegation) does. The recursion is bounded; the loop continues.

---

## Calibration — was the agent right?

`invoke calibration` reports per-role metrics:

```
role             calls    avg-conf    parse-fail%    error%
hephaestus       12       0.673       8.33%          0.00%
momus            8        0.581       0.00%          0.00%
cassandra        4        0.625       0.00%          0.00%
athena           5        0.720       0.00%          0.00%
figure_proposer  2        0.500       0.00%          50.00%
all              31       0.640       3.23%          3.23%
```

Today the metrics are baseline (invocation counts, average confidence, parse-failure rate, agent-error rate). Future arcs will link agent confidence to realized substrate outcomes — *did the proposed fix actually settle the drift? did the rejected AP fire later?* — but that requires cross-record causal linking, which is Ariadne's domain.

---

## The complete CLI surface for agents

```bash
invoke agent hephaestus "<directive>"      # surface drift via LLM
invoke agent momus <proposal-file>         # contest a proposal via LLM
invoke agent cassandra                     # review dismissed warnings
invoke agent athena                        # LLM synthesis
invoke agent figure_proposer "<seed>"      # underlies propose-figure

invoke propose-figure "<seed>"             # full recursion path
invoke calibration [role]                  # per-role calibration
```

All five roles' parsers tolerate malformed responses; the substrate captures errors as data, not exceptions.

---

## What's NOT in the agent layer

- **No LLM in the daemon's hot path by default.** The daemon runs heuristics; agents are opt-in. (A future arc may add a configurable cadence — every Nth iteration runs an LLM-as-Athena, recorded but not auto-acted-on.)
- **No LLM-generated code execution.** The substrate never `exec()`s an LLM response. The most a proposal can do is suggest source code that an operator chooses to copy.
- **No bypass of any S-invariant by virtue of "the LLM said so."** S1–S8 hold for agents exactly as they hold for the operator and for the heuristic loops.
- **No tier expansion for "agents."** Agents *are* canonical figures. Hephaestus-as-agent is Hephaestus; the agent layer lives in `runtime/` because it's runtime plumbing, not a new pantheon tier.

---

*Per Delphi 2026-05-18-oikoumene-arc.md. The substrate is inhabited. The constitution holds.*
