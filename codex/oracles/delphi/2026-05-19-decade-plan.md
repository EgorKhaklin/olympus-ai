# Delphi — the Decade plan 📜 (δεκάς)

**Risk class:** PLANNING (no code this turn — this is the survey + the sequence).
**Decided:** Position D — ten arcs sequenced by dependency + impact. Each arc gets its own future session per the operator's "1 arc per session" directive. **No bundling.** Operator confirms or revises before arc #12 ships.
**Sworn on Styx as a planning oath — the *plan* is the artifact; each arc's own Delphi follows when it ships.**

Zeus's directive (verbatim):

> *"okay fix errors now, bugs, drifts, warnings, and make it more useful than openclaw, and add more feauture. start a massive arch of 10 archs. where each arc you create something super useful and new, each session is 1 arch. create the list first using the system identify the gaps in the system"*

---

## Phase 0 — what the substrate told me (the honest audit)

Activated end-to-end first per the standing requirement. Tools used: `doctor`, `harmony`, `wisdom`, `status`, `shoulders`, plus reads of `codex/ARC-QUEUE.md` and `codex/CHRONICLE.md`. **Six concrete gaps surfaced by the substrate itself:**

| # | gap | source | severity |
|---|---|---|---|
| G1 | `hydra::fatigue-slice` proposed **150×** and rejected each time | `invoke wisdom` | MEDIUM (waste + signals broken Hephaestus loop) |
| G2 | **10.5%** session-error rate lifetime (substrate's own threshold: 5%) | `invoke wisdom` | MEDIUM (above self-set bar) |
| G3 | Hephaestus ratification rate **28%** (72% of proposals = noise) | `invoke wisdom` | MEDIUM (operator review burden) |
| G4 | **22 burdens in flight** currently — needs investigation | `invoke shoulders` | LOW-MEDIUM (Atlas integrity) |
| G5 | `today` warning (Cassandra finding) **unaddressed for 4+ arcs** | `invoke doctor` | LOW (operator decision overdue) |
| G6 | `llm-bridge` warning — key not re-deposited yet | `invoke doctor` | INFO (operator action) |

**Nine more gaps named in `codex/ARC-QUEUE.md`** (from prior arcs):
- Throne routing-prompt cache (~90% Plutus cost reduction)
- Test-isolation lint (pre-commit hook)
- `today` warning closure
- Hades multi-secret rotation
- Grounding RAG (semantic retrieval)
- PRICING refresh from Models API
- Budget alarms via Pan (constitutional debate needed)
- Multi-operator ACLs (constitutional debate needed)
- Email/Slack/inbound triggers (constitutional debate — recommend NOT pursuing)

**vs OpenClaw**: Olympus already matches the diagnostic/benchmark surface (`doctor`, Heracles, Atalanta, Typhon, Tiresias, Ananke). To be **more useful**, Olympus needs to deliver real daily-operator value — the kind that survives the question "why would I open this instead of just using Claude directly?"

---

## The 10-arc plan (sequenced)

Each arc gets its own session. Each is independent enough to ship alone. Each addresses a real surfaced gap OR delivers a clearly-named new useful capability. **No bundling within an arc beyond what's atomic.**

### Arc 12 — **Tartarus** 🜍 (data-driven gap closure)
**Risk:** MEDIUM. **What:** close G1–G4 with surgical fixes.
- **G1 fix**: investigate why `hydra::fatigue-slice` keeps being proposed; either Hephaestus learns to never re-raise it (after-N-rejections rule) OR the underlying signal stops firing.
- **G2 fix**: classify all session-errored records; most are likely from test seeds; add a `session.errored.reason` field so the 10.5% gets a denominator we can act on.
- **G3 fix**: tighten Hephaestus's confidence threshold for proposal emission (require ≥ 0.6 instead of any-positive).
- **G4 fix**: extend Asclepius healer to auto-release burdens older than 24h (with operator-confirm prompt).
- **G5 fix**: explicit `invoke today --resolve <slice> [--re-raise|--dismiss]` errand.

### Arc 13 — **Hippocrene** 💧 (semantic recall over the audit-of-record)
**Risk:** MEDIUM. **What:** vector embeddings of `llm.call` + `agent.invocation` + `proposal.raised` + Mnemosyne records broadly. New errand `invoke recall "<query>"` returns top-k semantically similar records with citations. Uses either Anthropic embeddings or a local model (operator choice). This unblocks Arcs 16 + 17.
**Closes:** ARC-QUEUE "Grounding RAG (semantic retrieval)".

### Arc 14 — **Argos-Eyes** 👁️ (filesystem watcher)
**Risk:** LOW-MEDIUM. **What:** extend the Argos tier with fsevents/inotify. Operator declares watch paths in `state/config.json::argos.watches[]`. Changes fire sessions OR raise pheromones. Useful examples: "watch `~/Documents/journal/`; on new file, summarize"; "watch `state/config.json`; alert on any change" (would have caught my Hades bug at runtime).

### Arc 15 — **Chronos** ⏰ (scheduled rituals)
**Risk:** LOW. **What:** cron-style scheduling on top of the existing daemon. Operator declares rituals in `state/config.json::chronos.rituals[]` — `{when: "weekday 09:00", do: "invoke today"}` / `{when: "sunday 20:00", do: "invoke ferry"}` / `{when: "monthly 1st", do: "invoke spend --30d"}`. The daemon checks ritual triggers each iteration.

### Arc 16 — **Hephaestus-PR** 🔧 (proposals become real git commits)
**Risk:** MEDIUM-HIGH. **What:** when a Hephaestus proposal is ratified AND the operator opts in (`--apply-as-pr`), Prometheus generates a real patch, commits to a *branch* (never main), opens a PR via `gh` CLI, links the proposal ID + the Delphi note + the Styx oath. This is the arc that makes Olympus a **coding assistant**. Constitution: never push to main; never merge; operator always reviews. Depends on Arc 1 (grounding) so Hephaestus's proposals cite real files.

### Arc 17 — **Demeter-Library** 📚 (knowledge-base ingestion)
**Risk:** LOW-MEDIUM. **What:** operator drops PDFs/markdown/text into `state/demeter/library/`; Demeter chunks + embeds them via Hippocrene's index. Throne can now answer "what does my onboarding doc say about X" or "find the section in `paper.pdf` about adversarial loss." Depends on Arc 13.

### Arc 18 — **Throne-Voice** 🎙️ (voice in/out)
**Risk:** LOW. **What:** macOS `say` for TTS (built-in, free) + Whisper API for STT (~$0.006/min — Plutus tracks it). New errand `invoke throne --voice` enters voice REPL: hotkey to record, throne responds in voice + text. Useful for "while walking" sessions. No background mic (explicit opt-in only).

### Arc 19 — **Hermes-MCP** 🪶 (Olympus as MCP server)
**Risk:** MEDIUM. **What:** expose the substrate as a Model Context Protocol server. Claude Code (or any MCP-capable client) can call `mcp__olympus__*` tools: `doctor`, `today`, `wisdom`, `agent`, `spend`, `throne`. This makes Olympus **directly usable from inside Claude Code** without leaving the editor. Reuses the same SAFE_ERRANDS whitelist that gates the Throne; GATED stays CLI-only.

### Arc 20 — **Plutus-Budget** 💸 (budget alarms via Pan — constitutional debate first)
**Risk:** MEDIUM-HIGH (constitutional). **What:** operator declares thresholds (`{daily_usd: 1.00, weekly_usd: 5.00}`). Pan trips on breach (the only autonomous "stop" the substrate ever takes against operator action). Closes the deferred-from-Plutus question. The arc opens with a Delphi debate: should Pan tripping on cost be allowed at all? If yes → ship the alarm. If no → document the refusal honestly.

### Arc 21 — **Olympus-Replay** ⏪ (regression harness via Heracles extension)
**Risk:** LOW. **What:** select N recent `agent.invocation` records; re-run them through current code; diff parsed-output and confidence; flag behavior drift. Catches the kind of regression unit tests miss — constitutional drift, prompt-shape changes, model upgrade effects. Each replay records to `replay.regression` so over time we see what behaviors are stable vs flaky.

---

## Sequencing rationale (why this order)

- **Arc 12 first** because the substrate is *currently lying about its own health* and the operator should see the fixes before adding new surface area.
- **Arc 13 second** because Hippocrene (semantic recall) unblocks **Arc 16** (Hephaestus needs semantic codebase search to write real patches) and **Arc 17** (Demeter needs the same index).
- **Arcs 14-15** (Argos-Eyes + Chronos) are independent low-risk operator-quality-of-life wins.
- **Arc 16** (Hephaestus-PR) is the keystone: it's the arc that makes Olympus actually do useful coding work.
- **Arc 17** (Demeter) extends Arc 13 with a real KB use case.
- **Arcs 18-19** (voice, MCP) make the Throne reachable from new contexts.
- **Arc 20** (budgets) needs a real constitutional debate — placed late so we have months of Plutus data to ground the debate.
- **Arc 21** (replay) is the bookend: regression harness that protects the work of all 9 prior arcs.

---

## What does NOT make the list

| candidate | why excluded |
|---|---|
| Email/Slack inbound triggers | violates S3 spirit (operator-driven, not autonomous-trigger) — see ARC-QUEUE.md |
| Multi-operator ACLs | constitutional change too big without operator-led debate first |
| Throne routing prompt-cache | LOW-effort optimization, do as a hotfix when convenient — doesn't deserve a whole arc |
| Hades multi-secret rotation | needed but small; fold into a future Hades-2 mini-arc |
| Refresh PRICING from Models API | a one-evening errand, not an arc |
| HomeAssistant / smart home | wrong shape — Olympus is cognitive, not home automation |

---

## Honest accounting

- **Total estimated work**: 10 arcs at roughly the size of the Plutus or Hades arc (~200-400 LOC each + tests + docs). Total ~3500 LOC + ~250 new tests.
- **Total cost** (if operator runs each via Claude Opus 4.7 development): roughly $0.50-$2.00 per arc in routing + synthesis, so ~$5-20 for the full Decade.
- **Operator time per arc**: each arc designed to be one session = one ~hour-long working block + review.
- **What this does NOT promise**: it does not solve "make Olympus do everything." It solves the specific 10 things above.

---

## Authorization (placeholder)

Each arc is a separate HIGH-COMPOSITE override at ship time. **This planning document is itself sworn** so the operator has a stable contract: ten arcs, in this order, one session each. The operator may revise the plan before each arc starts; doing so records as `decade-plan.revision` in Mnemosyne.

*The standard, when shipped: holy shit, that's done — ten times in a row. The Decade is real.*
