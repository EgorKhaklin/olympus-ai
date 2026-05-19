<div align="center">

# 🏺 QUICKSTART 🏺

**from `git clone` to a running Olympus in 5 minutes**

</div>

---

This document is for someone who has never seen Olympus before.

---

## What Olympus is (30 seconds)

Olympus is a **cognitive substrate for AI agents, organized as Greek mythology**. Each named figure has a structural job:

- **Mnemosyne** keeps the audit-of-record (append-only memory).
- **Athena** synthesizes a brief from observations + history.
- **Hephaestus** surfaces drift; **Momus** contests via 8 anti-patterns.
- **Zeus** ratifies decisions, sworn on **Styx**.
- **Prometheus** improves the substrate within bounds.
- **Pan** is a panic circuit breaker; **Asclepius** heals derived state.

There are 93 named figures total. The mythology is **the architecture** — every claim Olympus makes about itself is a Greek figure you can read about.

LLM agents can inhabit any figure. The substrate enforces a constitution (S1–S8) on every output, whether from a heuristic or an LLM.

**Olympus runs without an LLM.** The default `echo` provider is a deterministic stub. Switch to `anthropic` later for real agent reasoning.

---

## Five minutes, five steps

```bash
# 1. Install
pip install -e .

# 2. Run the welcome wizard (it does the rest)
invoke setup

# 3. Start the HTTP API in the background
invoke serve --port 8765 &

# 4. Build + open the Agora (web UI)
invoke agora --open

# 5. See what one concrete action the substrate suggests
invoke today
```

That's the whole tour. Steps 2 and 4 are interactive; everything else takes seconds.

---

## What `invoke setup` does

Six steps, idempotent (re-running is safe):

1. **Welcomes you** — explains the mythology in 5 sentences
2. **Kindles the hearth** — names your deployment (Hestia is lit)
3. **Asks your LLM choice** — `echo` (safe default), `anthropic` (real LLM), or `skip`
   - If anthropic: **tests the API call before saving** — no silent failures
4. **Asks about the daemon** — auto-run the loop in background? (optional)
5. **Asks the Agora port** — defaults to 8765
6. **Runs one cognitive session** — confirms everything works

Config is saved to `state/config.json` (gitignored, plaintext, operator-owned).

---

## What you'll see day-to-day

| command | what it shows |
|---|---|
| `invoke today` | the **one** thing the substrate suggests you look at |
| `invoke doctor` | single-screen health (warnings + fails honestly) |
| `invoke status` | quick check (hearth, oaths, hydra, argos, sessions) |
| `invoke wisdom` | what the substrate has *learned* over time |
| `invoke harmony` | substrate ratios scored against φ (golden ratio) |
| `invoke agora --open` | the operator's web UI in your browser |

---

## Switching to real LLM later

```bash
# Edit your config (or just re-run setup — idempotent)
invoke setup        # pick anthropic this time

# Or via env var (which always wins)
export OLYMPUS_LLM=anthropic
export ANTHROPIC_API_KEY=sk-ant-...
invoke agent hephaestus "what is drifting in the substrate?"
```

Every LLM call is recorded to Mnemosyne under `llm.call` — full audit trail. See [`codex/AGENTS.md`](AGENTS.md) for how agents inhabit Greek roles.

---

## When you want to go deeper

Read in roughly this order:

1. **[README.md](../README.md)** — the project overview
2. **[`codex/AGENTS.md`](AGENTS.md)** — how LLM agents inhabit the substrate (prompt grounding + external governance + recursion)
3. **[`codex/RIGOR.md`](RIGOR.md)** — how Olympus answers "is this theatrical or real?" with live measurements
4. **[`codex/OPERATIONS.md`](OPERATIONS.md)** — full operator runbook
5. **[`codex/GEOMETRY.md`](GEOMETRY.md)** — Pythagoras + Plato + the sacred-numerics layer
6. **[`codex/SPECS.md`](SPECS.md)** — TLA+ formal-verification layer
7. **[`codex/PANTHEON.md`](PANTHEON.md)** — every named figure
8. **[`codex/CHRONICLE.md`](CHRONICLE.md)** — every arc in reverse chronological order

---

## When things go wrong

```bash
# Diagnostic that honestly tells you what's off
invoke doctor

# Substrate panicked (Pan tripped)
invoke panic            # see why
invoke panic --clear    # acknowledge and resume

# Substrate's derived state looks weird
invoke heal             # Asclepius rebuilds Iris, Pan state, dirs

# State is growing large
invoke ferry            # Charon archives old burdens to Hades
```

All recovery is bounded by the constitution. None of these commands modifies the audit-of-record; they only restore derived state.

---

## What `invoke setup` does NOT do

- It does **not** install the OS daemon by default (you opt in)
- It does **not** save your API key encrypted (it's plaintext in `state/config.json`; we tell you this so you're not surprised)
- It does **not** write to anything outside the repo
- It does **not** make any network calls unless you explicitly pick the `anthropic` provider and approve the test call

---

## What if I have no terminal experience?

The Agora web UI shows the same information without requiring CLI literacy. After `invoke setup` and `invoke serve`, open `state/agora/index.html` in your browser. The constitution-bearing actions (ratify, panic-clear, kindle) stay on the CLI by design — they shouldn't be one-click.

---

*The door is open. Welcome to Olympus.*
