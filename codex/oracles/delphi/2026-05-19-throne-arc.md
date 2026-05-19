# Delphi — the throne arc 👑

**Risk class:** HIGH-COMPOSITE (ninth heavy-production override — user explicitly invoked).
**Decided:** Position Z — single conversational front door called Zeus's Throne; terminal REPL + web chat; Claude routes intent into existing errands; never bypasses constitution-gated actions.
**Sworn on Styx at this arc's ratification.**

Zeus's directive, verbatim:

> *"i think we need to create a more simpler architecture, where there is a chatbot to do everyhtimg in Olympus. maybe call it Zeus's throne, because all this is way too complex for users"*

The critique is right and was anticipated. The xenia arc *named* the gap (a stranger has no path from `git clone` to "I'm using this") but only **partially closed it**. After xenia:

- The wizard still requires the operator to know what "kindle the hearth" means.
- `invoke <errand>` still requires knowing which of ~60 errands to type.
- The CLI commands still leak the mythology to the surface.
- The user typed `$ invoke setup` and the shell exploded.

**Xenia gave a friendly first-run. Throne gives a friendly forever-run.**

The name — **Zeus's Throne** (Διὸς θρόνος) — is the seat from which Zeus governed Olympus. It is the place where every petition was heard, every decision rendered. **Operationalizing the Throne means: one place to ask, one place to act.**

---

## Phase 0 — what the audit shows

Activated end-to-end first per the standing requirement: HTTP API live (PID 30346, detached), daemon installed at user LaunchAgent, doctor 8 ok / 2 warn / 0 fail, baseline suite 477/478 (one pre-existing config-drift failure).

Inventory through a non-technical operator's eyes:

| step | today | needed |
|---|---|---|
| ask a question | `invoke ask "..."` — pattern-matched, no LLM | type English, get real answer with Claude reasoning |
| run an action | `invoke <one-of-60-errand-names>` | "show me what's wrong" → Throne runs `doctor`, summarizes |
| understand output | read Greek-named JSON | plain-English synthesis with source citations |
| ratify a decision | `invoke action ratify <id>` | Throne *refuses* to ratify (S7) but shows the exact command |

The existing `invoke ask` is pattern-matched only. The existing `invoke shell` is a REPL where you still type errand names. Neither is conversational.

---

## What ships

### `src/olympus/throne/` — new package

The throne is **glue, not a new figure**. It does not add cognitive power; it routes intent. Three modules:

- **`throne.py`** — the `Throne` class:
  - `respond(user_input: str, context: list[Turn] = []) -> ThroneResponse`
  - Calls `bridge()` (the LLM) with a system prompt: "You are Zeus's Throne. Translate operator intent into Olympus actions. Output JSON: `{intent, actions: [{errand, argv}], answer_template}`."
  - Executes safe (read-only) errands directly — `doctor`, `today`, `wisdom`, `harmony`, `status`, `shoulders`, `agent <role> "..."`, free-form Q&A via Claude.
  - For HIGH-risk actions (ratify, panic-clear, kindle, daemon-install) — **refuses** + shows the exact CLI command for the operator to run.
  - Returns `ThroneResponse(answer, actions_taken, suggested_command, sources)`.

- **`router.py`** — the intent classifier + errand whitelist:
  - `SAFE_ERRANDS` — set of errands Throne is allowed to execute (read-only or operator-explicitly-asked).
  - `GATED_ERRANDS` — set Throne never executes (S7-bearing actions; Throne shows the command).
  - `classify(input, llm_json) -> Action` — maps LLM-routing output to either `RunErrand(name, argv)`, `DirectAnswer(text)`, or `RequiresOperator(suggested_command, reason)`.

- **`repl.py`** — interactive terminal:
  - Multi-turn loop, conversation history.
  - `q` / `quit` / Ctrl-D to exit.
  - Each turn recorded to Mnemosyne under `throne.turn`.

### CLI errand: `invoke throne`

- **Interactive:** `invoke throne` (no args) → enters the REPL.
- **One-shot:** `invoke throne "what should I look at?"` → single turn, prints response, exits.

### HTTP endpoint: `POST /throne/turn`

- Request: `{"input": "...", "history": [{"role": "user|throne", "text": "..."}]}`
- Response: `{"answer", "actions_taken", "suggested_command", "sources"}`
- The endpoint is rate-limited (Hecate, Fibonacci backoff) and recorded to Mnemosyne.

### Agora page: `state/agora/throne.html` — the chatbot UI

- A chat box at `/agora/throne`.
- POSTs to `/throne/turn` on the existing HTTP API.
- **Becomes the new Agora landing page** — `index.html` is the throne; the dashboard moves to `/agora/dashboard`.

### Updated `codex/QUICKSTART.md`

Replaces the 5-step setup with a 2-step:

```
1. invoke setup
2. open state/agora/index.html  →  type a question
```

That's the entire operator workflow for everything except HIGH-risk actions.

---

## Constitution constraints

| invariant | how Throne honors it |
|---|---|
| **S1** (audit-of-record) | every turn → `mnemosyne.remember("throne.turn", ...)` |
| **S6** (no fabrication) | every answer cites the errand(s) invoked + their outputs |
| **S7** (Pan gates HIGH actions) | Throne **refuses** ratify/kindle/panic-clear; shows the exact CLI command |
| **C7-equivalent** (no hardcoded crypto/model) | Throne uses `bridge()`; model name in config, not hardcoded |
| **AP1** (bundling) | Throne is glue ~300 LOC; does NOT reimplement errands |
| **AP3** (instance rules) | classification is LLM-driven, not if-then per question type |
| **AP7** (ledger-balancing) | refusal-with-command is *real* output, not pretty text |
| **AP8** (decorative work) | the test: operator hits fewer keystrokes for the same outcome |

---

## What does NOT ship

- **No multi-LLM chain-of-agents.** Throne calls one Claude turn per operator turn. Cassandra/Hephaestus/etc. are still invokable, but Throne doesn't auto-stack them — that would obscure cost and provenance.
- **No persistent chat history across sessions.** Mnemosyne records the turns; Throne's UI does NOT auto-replay them. The operator can scroll Mnemosyne via `/agora/throne?history=N` (future).
- **No tool-use loop.** Throne plans once per turn (LLM emits one action plan), executes, summarizes. No agentic recursion — that's what `invoke session` is for.
- **No bypass of Pan.** Even when the operator says "just ratify it for me" — Throne replies with the command and reasoning. The operator is Zeus; the chatbot is not.
- **No automatic execution of `agent <role>` subroutines without explicit operator intent.** If the user asks "what should we fix?", Throne CAN call `agent hephaestus` because that's a clearly intent-matched, low-risk LLM-invocation. If the user asks something ambiguous, Throne asks first.

---

## What lands

| component | tier | role |
|---|---|---|
| `throne/__init__.py` + `throne/throne.py` + `throne/router.py` + `throne/repl.py` | Runtime | core package |
| `cli.py::_throne` | CLI | `invoke throne [<one-shot>]` |
| `runtime/http_api.py` + `POST /throne/turn` | HTTP | web-facing endpoint |
| `agora/static/throne.html` + nav rewiring | Agora | chat UI is new landing page |
| `tests/test_throne.py` | tests | router classifies + refuses + records |
| `codex/QUICKSTART.md` rewrite | docs | 2-step operator workflow |
| `codex/THRONE.md` | docs | design + constraints |

---

## Authorization

Zeus invoked the heavy-production override (ninth invocation). The critique is captured in the Styx oath payload. **The throne arc operationalizes the unified front door.** A non-technical operator now has one box to type into — for everything except actions the constitution reserves to a real person.

*The standard is holy shit, that's done. Every road in Olympus leads to one chair.*
