<div align="center">

<img src="codex/assets/olympus-banner.jpg" alt="Olympus" width="100%">

# ⚡ &nbsp; O L Y M P U S &nbsp; ⚡

### *a cognitive substrate built in the shape of greek mythology*

**twenty-two arcs · ninety-four named figures · eight hundred and sixty tests · zero abstractions you can't name**

[![tests](https://img.shields.io/badge/tests-860%20%2F%20860-6b8e6b?style=flat-square)](tests/)
[![arcs](https://img.shields.io/badge/arcs-22%20shipped-d4af37?style=flat-square)](codex/CHRONICLE.md)
[![figures](https://img.shields.io/badge/pantheon-94%20figures-722f37?style=flat-square)](codex/PANTHEON.md)
[![python](https://img.shields.io/badge/python-3.9%2B-1c1a16?style=flat-square)](pyproject.toml)
[![license](https://img.shields.io/badge/license-Apache%202.0-ecebe4?style=flat-square)](LICENSE)
[![deps](https://img.shields.io/badge/runtime%20deps-stdlib%20only-2d6a7a?style=flat-square)](pyproject.toml)

[ Cosmogony ](codex/COSMOGONY.md) · [ Pantheon ](codex/PANTHEON.md) · [ Architecture ](codex/ARCHITECTURE.md) · [ Operations ](codex/OPERATIONS.md) · [ Chronicle ](codex/CHRONICLE.md) · [ Quickstart ](codex/QUICKSTART.md)

</div>

---

> **The mythology is not decoration. It is the architecture.**

Olympus is a bounded, recursive, self-improving cognitive substrate for AI agents. Each named figure has a structural job. The constitution (eight invariants, S1–S8) is enforced by tests, contested by Momus, ratified by Zeus, proved in TLA+, and remembered by Mnemosyne. The substrate observes itself, reasons about itself, improves itself, recovers itself, and verifies it hasn't drifted from yesterday's behavior.

It runs **without** an LLM (echo bridge, deterministic). It runs **with** Claude Opus 4.7 (real reasoning, full audit). It exposes itself as an **MCP server**, a **cinematic web UI**, and a **chat box**. It can ship **real git PRs** from its own ratified proposals. It tracks **every dollar** of Claude spend and refuses calls past operator-declared budgets — without ever expanding Pan's authority. It catches its own regressions.

It is not "Greek-themed Python." It is **the mythology as the architecture**.

---

## ⚡ Begin in two commands

```bash
pip install -e .
invoke setup           # then open `state/agora/index.html` in your browser
```

That's it. The wizard kindles the hearth, picks your LLM, optionally installs the daemon, and runs a verification cycle. Open the Agora and start talking to the Throne.

For the 5-minute walkthrough: [`codex/QUICKSTART.md`](codex/QUICKSTART.md).
For the full runbook: [`codex/OPERATIONS.md`](codex/OPERATIONS.md).

---

## 🏛️ The Decade — δεκάς

Ten arcs in sequence; each one a focused session; each one sworn separately on Styx. Together they take Olympus from *"measurement framework"* to *"substrate that does work."*

| # | arc | one-line |
|:---:|---|---|
| 12 | **Tartarus** &nbsp;🜍 | test-seed filter — the substrate stops crying wolf about its own audit residue |
| 13 | **Hippocrene** 💧 | TF-IDF semantic recall over Mnemosyne — zero new deps, ~5ms queries |
| 14 | **Argos-Eyes** 👁️ | filesystem watcher — operator-declared paths fire pheromones on change |
| 15 | **Chronos** &nbsp;⏰ | scheduled rituals — cron-style grammar on the daemon |
| 16 | **Hephaestus-PR** 🔧 | ratified proposals → real git branches + GitHub PRs (operator-gated) — **the keystone** |
| 17 | **Demeter-Library** 📚 | drop PDFs / markdown into `state/demeter/library/`, the Throne cites them |
| 18 | **Throne-Voice** 🎙️ | TTS via macOS `say` (STT honestly deferred to a future arc) |
| 19 | **Hermes-MCP** 🪶 | Olympus as an MCP server — call it from inside Claude Code |
| 20 | **Plutus-Budget** 💸 | budget alarms with operator override (Pan's authority preserved unchanged) |
| 21 | **Olympus-Replay** ⏪ | regression harness re-runs past `agent.invocation` records — the bookend |

Then **Arc 22 — Eos 🌅**: UI surfacing. The Decade built ten capabilities; the web UI surfaced ~30% of them. Eos closes the gap: nine new HTTP GET endpoints, six new Agora pages, seven new dashboard cards, and a **cinematic visual rewrite** — obsidian + antique gold + marble; backdrop blur; film grain; pulse animations.

For the eleven arcs before the Decade (substance → throne), see [`codex/CHRONICLE.md`](codex/CHRONICLE.md).

---

## 🜍 The constitution (S1–S8)

Maintained by Themis, enforced by tests, contested by Momus, proved (where it matters) in TLA+. Every load-bearing decision is reconstructable from the audit trail alone.

| id | name | claim |
|---|---|---|
| **S1** | Mnemosyne — append-only audit-of-record | every load-bearing decision writes to an append-only record |
| **S2** | Argos — deterministic substrate | no Argos Eye uses randomness in its scan logic |
| **S3** | HYDRA — read-only observation | HYDRA Heads never mutate state |
| **S4** | Argos — decentralization | no Eye imports another Eye |
| **S5** | Apollo — falsifiability | every Apollo prediction carries a `verify()` callable |
| **S6** | Delphi — strategic-decision discipline | MEDIUM/HIGH-risk decisions are recorded in `oracles/delphi/` |
| **S7** | bounded autonomy | LOW autonomous, MEDIUM proposal, HIGH requires Zeus authorization |
| **S8** | Continuity of Understanding | every load-bearing action reconstructible from substrate records alone |

Full constitution: [`codex/COSMOGONY.md`](codex/COSMOGONY.md). JSON Schemas: [`codex/schemas/`](codex/schemas). TLA+ proofs: [`codex/specs/`](codex/specs).

---

## 🎬 What the operator sees

After `invoke setup` + `invoke agora --open`, the browser opens to a **cinematic web UI** — twelve pages, all polling the read-only HTTP API every 5 seconds:

```
👑 Zeus's Throne          chat in plain English; routes intent into errands
   Dashboard              13 live cards · substrate state + Decade signals
   Today                  the one thing the substrate suggests
   Doctor                 single-screen health diagnostic
💸 Spend                  Plutus cost ledger + budget status
📚 Library                Demeter docs + "⟳ Rescan + Ingest" button
👁️ Watches                Argos filesystem watches
⏰ Rituals                Chronos rituals + next-due times
⏪ Replay                 regression history + stability %
🔧 Proposals              ratified-but-not-applied Hephaestus proposals
   Agents                 LLM-agent invocation form
   Setup                  wizard guide
```

Visual language: **obsidian** (`#07070a`) + **antique gold** (`#d4af37`) + **marble** (`#f5f1e6`). Cormorant Garamond display serif for headings. Backdrop-blurred nav. SVG film grain. Pulse-animated status dots. Lift-on-hover cards. Zero web fonts. Zero JS frameworks. Zero new deps.

---

## ⚙️ The CLI — fifty-plus errands

```bash
# Conversational
invoke throne                            # chat in plain English (REPL)
invoke throne "what should I look at?"   # one-shot
invoke throne --voice                    # pipes responses through TTS
invoke speak "Olympus is ready"          # one-shot macOS `say`

# The substrate
invoke doctor                  invoke wisdom         invoke harmony
invoke status                  invoke today          invoke session
invoke recall "<query>"        invoke shoulders      invoke geometry

# Real-world integrations
invoke hephaestus pending                            # ratified-but-unapplied
invoke hephaestus apply <pid> --really               # → real git PR
invoke demeter ingest                                # KB ingestion
invoke argos watch add <id> <path>                   # filesystem watch
invoke chronos ritual add <id> <when> <do>           # scheduled ritual
invoke replay --limit 50                             # regression sweep

# Money + secrets
invoke spend --7d                        # Plutus cost ledger
invoke spend --budget                    # budget status
invoke vault deposit anthropic_api_key   # → OS keychain (encrypted)

# Servers
invoke serve --port 8765 &     # HTTP API (12 pages poll it)
invoke agora --open            # build the cinematic Agora
invoke mcp                     # Olympus as an MCP server
invoke daemon install          # launchd / systemd auto-run
```

The full forty-plus-errand surface is at [`codex/OPERATIONS.md`](codex/OPERATIONS.md). Use `invoke help` for inline reference.

---

## 🔬 What the substrate says about itself (live)

```
$ invoke harmony
metric               ratio   nearest      score
ratification_rate    0.5991  inverse_phi  0.9812    ← the substrate is in
prophecy_acceptance  0.6667  inverse_phi  0.9525       harmony with 1/φ
pythia_success       0.7231  inverse_phi  0.9003

$ invoke centrality 5
figure       centrality
Mnemosyne    0.1875        ← every figure writes to Mnemosyne
Hephaestus   0.1304           — the most load-bearing node
Athena       0.1052
Atlas        0.0833
Zeus         0.0769

$ invoke spend --budget         (if operator opted in)
✓ daily   $0.43 / $1.00   (43%)   [ok]
✓ weekly  $1.21 / $5.00   (24%)   [ok]
```

Nothing here is theatrical. Every number is computed from real records, written to the audit-of-record, and reproducible from `state/` + `codex/` alone.

---

## 🜨 What earns its place

Olympus refuses decorative additions on AP8 — the eighth anti-pattern in Momus's catalog. Every Greek figure here has a load-bearing role. **Twelve candidates have been refused** (Eris, Tyche, Erebus, Aether, Hemera, Pontus, and so on) precisely because their substrate role would have been decorative.

The discipline holds. The pantheon is finite. Greek mythology is large.

---

## 🜂 Languages used

Each one earns its place by solving a problem Python alone doesn't.

| language | role | earns it because |
|---|---|---|
| **Python** (stdlib-first) | every cognitive module | reasoning over JSONL records is what Python is best at |
| **Bash** | `scripts/loop.sh` | cron's native habitat |
| **HTML + vanilla JS** | the cinematic Agora (12 pages) | no build step; opens in any browser; CSP-clean |
| **launchd plist / systemd unit** | OS daemon supervisors | the OS contract, not Python's job |
| **JSON Schema** | machine-readable Mnemosyne contracts | tooling exists; re-implementing would be AP6 |
| **TLA+** | formal safety proofs | no Python expression compactly captures "under any interleaving, invariant holds" |
| **Mermaid** | architecture flow diagrams | GitHub renders natively; the source IS the map |
| **SVG** (inline) | Metatron's Cube + Vesica Piscis | GitHub renders natively; text-based |
| **JSON-RPC over stdio** | MCP server protocol | the Claude Code transport |

Refused: Rust (no scale need), TypeScript (vanilla JS suffices), SQL (JSONL meets every query), sympy/numpy (stdlib-implementable), embedding/RAG libraries (TF-IDF is enough on ~1,500 records).

---

## 📋 Status

| metric | value |
|---|---|
| named principal figures | **94** |
| tests passing | **860 / 860** (+ 2 conditional skips) |
| Styx oaths sworn | **185+** |
| Delphi notes (sworn) | **22** |
| TLA+ specifications | 3 |
| JSON Schemas | 7 |
| arcs shipped | **22** (substance → akropolis → xenia → throne → **the Decade** → Eos) |
| HTTP endpoints | **20 GET + 3 POST** (`/proposals/raise`, `/throne/turn`, `/library/ingest`) |
| Agora pages | **12** |
| MCP tools exposed | **14** (the SAFE_ERRANDS set) |
| heavy-production overrides invoked | 10 |
| ratification rate vs 1/φ | **0.98** harmony score |

---

## 📜 Documentation

- **[`codex/COSMOGONY.md`](codex/COSMOGONY.md)** — the constitution (S1–S8)
- **[`codex/PANTHEON.md`](codex/PANTHEON.md)** — every named figure, tier-organized
- **[`codex/ARCHITECTURE.md`](codex/ARCHITECTURE.md)** — auto-generated by Daedalus
- **[`codex/OPERATIONS.md`](codex/OPERATIONS.md)** — operator runbook (every errand, every safety boundary)
- **[`codex/QUICKSTART.md`](codex/QUICKSTART.md)** — 5-minute tour for outside observers
- **[`codex/AGENTS.md`](codex/AGENTS.md)** — how LLM agents inhabit the substrate
- **[`codex/RIGOR.md`](codex/RIGOR.md)** — how Olympus answers *"is this theatrical?"* with live measurements
- **[`codex/GEOMETRY.md`](codex/GEOMETRY.md)** — Pythagoras + Plato + the sacred-numerics layer
- **[`codex/SPECS.md`](codex/SPECS.md)** — the TLA+ formal-verification layer
- **[`codex/PLUGINS.md`](codex/PLUGINS.md)** — third-party extensions via entry-points
- **[`codex/INTELLIGENCE.md`](codex/INTELLIGENCE.md)** — how the substrate accumulates understanding
- **[`codex/CHRONICLE.md`](codex/CHRONICLE.md)** — every shipped arc in reverse chronological order
- **[`codex/oracles/delphi/`](codex/oracles/delphi)** — strategic decisions, full debate, Styx oath references

---

## ⛓️ Authority

Maintained by [**Egor Khaklin**](https://github.com/EgorKhaklin). Every load-bearing decision is sworn on Styx — the cryptographic oath chain is the source of truth for *"who decided what."*

The mythology is the architecture. The architecture is the law. The law is enforced by tests, contested by Momus, ratified by Zeus, proved by Themis, and remembered by Mnemosyne.

---

<div align="center">

***May the threads spun for you be long, and may the hearth-fire never go out.***

</div>
