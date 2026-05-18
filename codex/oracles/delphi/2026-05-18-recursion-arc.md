# Delphi — the recursion arc

**Risk class:** HIGH-COMPOSITE (heavy-production override, second invocation).
**Decided:** Position D — research bridge + HTTP surface + shadow execution + self-tuning + plugin protocol + hash lineage.
**Sworn on Styx at seq=71 (recorded on swear).**

Zeus's directive (verbatim, abridged):

> *"Using the system put it on a self improvement loop, and make sure it follows the greek mythology architecture perfectly … you can even scan the internet / github / anything for tools / ideas / code to improve olympus and the self improvement loop. Use the system itself to help build the system stronger, better more powerful. If you cant do something, create the thing that will let you do it, keep this loop going. Get as meta deep as you need, the recursive loop doesnt need to stop. … Boil the ocean."*

This is the second invocation of the heavy-production override. The directive is explicit: *the substrate should improve the substrate, and you should reach outside of it for prior art when needed.* This arc closes the recursive loop in a literal sense.

---

## Methodology — the substrate's own protocol used at meta-depth

Before building, the architecture asked the question by scanning the world. Three searches returned what the prior art looks like:

| pattern found in the wild | how Olympus already addresses it |
|---|---|
| Event sourcing for AI agents (ESAA; arxiv 2602.23193) — *"source of truth is immutable log of intentions; current state is deterministically projected"* | S1 (Mnemosyne append-only) + S8 (Continuity of Understanding) |
| BerriAI self-improving-agent — *"agent proposes diff, human approves, draft PR opens"* | Hephaestus → Momus → Delphi → Zeus → ActionQueue |
| Hard constraints over prompts — *"hard constraints (separate sessions, abort on violation) more reliable than prompts"* (theprint/nfh) | Pan circuit breaker + Furies + S7 risk classes |
| Bounded RSI — *"bounded by tasks, ethics, resources"* (Steunebrink) | S7 LOW/MEDIUM/HIGH + Atlas load registry |
| Orchard Kit — *"zero-dependency Python modules for autonomous agent governance"* | Olympus is stdlib-mostly by design |
| Lineage hashing — *"source hash and derived hash to tie outputs to inputs"* (audit-trail-for-desktop-AI) | **GAP** — Styx hashes oaths but derived artifacts (Iris HTML, ARCHITECTURE.md) don't reference input hashes |

The world-scan also identified what Olympus genuinely lacks beyond hash lineage:

1. **No bridge to the world.** Zeus literally asked "scan the internet/github." Without a Pythia, the substrate cannot honor this.
2. **No queryable API surface.** The substrate produces JSONL and Mnemosyne records but external observers can only read them on the filesystem. An HTTP endpoint unlocks third-party monitoring without Python-import coupling.
3. **No safe substrate-modification preview.** Proposed Prometheus handlers, plugin code, parameter tunings — all must currently be tested against production state. A shadow-execution primitive (Castor/Pollux) lets the substrate canary itself.
4. **No outcome-driven parameter tuning.** Pan's threshold, Charon's retention window, the daemon interval — all defaults. Metis observes hindsights + vindications + iteration stats and proposes adjustments through the existing Hephaestus → Momus → Delphi channel.
5. **No third-party extensibility.** Domain deployments can add modules under their own namespace today, but there's no `entry_points` registration. Plugin authors can't ship a pip-installable package that registers handlers/eyes/healers.

All six gaps are load-bearing. The arc fills all six.

---

## Q1 — What ships

### Pythia — `src/olympus/olympians/apollo/pythia.py`

In myth: the priestess at Delphi who delivered Apollo's oracles. She sat above the chasm and was the channel for external knowledge entering the mortal world.

In Olympus: the **external-knowledge bridge**. Pythia uses `urllib` (stdlib) to query the world. Two channels:

- **`pythia.ask_github(query, ...)`** — GitHub code/repository search via the public REST API. No token required (rate-limited, but works).
- **`pythia.ask_web(url)`** — fetches a URL with timeout + size cap; returns a structured summary (status, content-type, length, head-bytes).

Every consultation is recorded under `kind="pythia.consultation"` with full query, response status, response bytes (capped), timing. The audit-of-record is preserved (S1, S8 reconstructable).

**Momus contests:**
- AP1 (no ground-touch): pass — network call's result is observable outside Olympus (the HTTP response).
- AP6 (understanding-obscuring): pass — every consultation is itself a recorded explanation of what was asked and what came back.
- AP7 (privilege escalation): pass — Pythia has no execution authority; her output is data, not action.
- AP1's previous LLM-injection veto: Pythia is **not** an LLM. She fetches raw HTTP. No model in the loop.

### HTTP API — `src/olympus/runtime/http_api.py`

Pure stdlib `http.server`. Bound to `localhost:8765` by default. Read-only:

| route | returns |
|---|---|
| `GET /` | service banner + route index |
| `GET /status` | `invoke status` as JSON |
| `GET /wisdom` | `invoke wisdom` as JSON |
| `GET /shoulders` | Atlas's current burdens |
| `GET /panic` | Pan state |
| `GET /schemas` | list of registered schemas |
| `GET /schemas/<kind>` | one schema |
| `GET /mnemosyne/<kind>?limit=N` | recall a kind (paginated) |
| `GET /healthz` | liveness probe |
| `POST/PUT/DELETE/anything-else` | 405 |

Started via `invoke serve [--port N] [--host H]`. Useful for hooking external dashboards, monitoring, or just `curl localhost:8765/wisdom | jq`.

### Castor & Pollux — `src/olympus/heroes/{castor,pollux}.py`

In myth: the Dioscuri, twin brothers. Castor was mortal; Pollux was immortal. Zeus placed them in the heavens as the constellation Gemini.

In Olympus: **shadow execution and comparison**. The natural pair-twin shape:

- **`castor.shadow_session(modifications)`** runs a Session inside a temporary state directory (a "shadow Olympus"). The directory starts as a snapshot of production state; modifications are applied; one session runs; the result is captured. Production state is untouched.
- **`pollux.compare(prod_report, shadow_report)`** produces a structured diff: which findings/proposals/prophecies/durations differ.

Used together: a proposed Prometheus handler can be evaluated by running prod + shadow in parallel and comparing. The canary deploy pattern, applied to the substrate itself.

### Metis — `src/olympus/titans/metis.py`

In myth: Titaness of wise counsel; first wife of Zeus; mother of Athena. Zeus swallowed her so that wisdom would always live inside him.

In Olympus: the **self-tuning advisor**. Metis reads:
- Recent `epimetheus.hindsight` records — what surprised us
- Recent `cassandra.vindicated` records — what we shrugged off that came back
- Recent `daemon.iteration` log entries — actual loop performance

…and produces *recommendations* about substrate parameters: Pan's threshold, Charon's retention, the daemon interval, Asclepius's healer order. **Metis never directly tunes.** Recommendations become Hephaestus proposals, which go through Momus → Delphi → Zeus. The meta-loop is bounded by the same constitutional discipline as everything else.

**Re-arguing the prior refusal.** The missing-figures arc refused Metis on AP8 ("duplicates Athena's pre-synthesis"). The new role is *outcome-driven parameter tuning of the substrate itself* — a concrete, load-bearing function distinct from Athena's per-session brief composition. The new role earns ratification.

### Plugin protocol — `pyproject.toml` entry_points + `olympus.plugins`

Third-party Python packages can register additional handlers, eyes, healers, predictions via standard PEP 621 entry_points:

```toml
[project.entry-points."olympus.prometheus_handlers"]
my_handler = "my_package.my_module:my_handler_fn"

[project.entry-points."olympus.argos_eyes"]
my_eye = "my_package.my_eye:MyEye"
```

CLI bootstrap iterates `importlib.metadata.entry_points()` and registers them. Plugins must follow the same Mnemosyne discipline; Momus AP1 still applies. Documented in `codex/PLUGINS.md`.

### Hash lineage in derived artifacts

Derived documents (`codex/ARCHITECTURE.md` by Daedalus, `state/iris/index.html` by Iris) carry a `lineage:` header listing SHA-256 hashes of their source inputs:

- ARCHITECTURE.md → hash of `_COGNITIVE_FLOW` edge list
- iris/index.html → hash of the embedded snapshot JSON

This is what the audit-trail-for-desktop-AI prior art recommends. Tamper-detection at the derived-artifact layer — if the lineage hash doesn't match a re-derivation, Asclepius's `heal` detects it.

---

## Q2 — Languages used

| language | role | why |
|---|---|---|
| Python (stdlib only) | every module here | urllib for Pythia, http.server for HTTP API, sha256 for lineage, importlib.metadata for plugins |
| JSON | HTTP responses + plugin manifests | same reasoning as prior arcs |

**No new languages.** Pythia uses urllib over `requests` because requests is not in stdlib. HTTP API uses `http.server` over Flask/FastAPI because we don't need routing power or async. The discipline holds: a language gets added only when it solves a problem Python doesn't.

---

## What does NOT ship

- **No LLM in the loop.** Pythia fetches raw HTTP. The world-scan demonstrated that even sophisticated agent papers (Gödel Agent, AutoAgent) ship LLM coupling — Olympus deliberately does not. AP6 + S2 (non-determinism) + S7 (LLM-injected code edits are HIGH) all still fire on that proposal.
- **No write endpoints on the HTTP API.** S3 (read-only observation) extends to the API: external observers may query, never command. Mutations go through `invoke` (which has the full Hephaestus → Momus → Delphi pipeline).
- **No automatic Metis adoption.** Metis advises. Zeus ratifies. The recursive loop is **bounded by the constitution**, exactly as the bounded-RSI literature recommends.

---

## What lands

### Modules

| module | tier | role |
|---|---|---|
| **Pythia** | Olympian (subpackage of Apollo) | external knowledge bridge |
| **HTTP API** | Runtime | localhost JSON surface |
| **Castor** | Hero | shadow session runner |
| **Pollux** | Hero | shadow/prod comparator |
| **Metis** | Titan | self-tuning advisor |
| Daedalus (extended) | Hero | adds lineage hash to ARCHITECTURE.md |
| Iris (extended) | presentation | adds lineage hash to dashboard |
| plugin loader | CLI bootstrap | discovers entry_points and registers |

### CLI

`invoke pythia <query>`, `invoke serve [--port N]`, `invoke shadow [--diff <key=val>]`, `invoke tune`, `invoke plugins`.

### Documentation

- `codex/PLUGINS.md` — plugin author guide.
- `codex/OPERATIONS.md` — extended with new commands.
- `codex/CHRONICLE.md` — this arc's entry.

### Tests

A test file per module. Plus integration tests:
- `invoke pythia "agent-loop"` records a real consultation
- `invoke serve` starts, responds to `/healthz`, shuts down cleanly
- shadow session runs in a tempdir without touching prod state
- Metis's tuning advice produces parseable Hephaestus proposals
- A test plugin registers and is discovered

### Demonstration

After building, the arc literally exercises the new capabilities:
- Pythia fetches one GitHub repo by URL → recorded consultation
- HTTP API starts in the background → curl /status returns valid JSON

---

## Authorization

Zeus invoked heavy-production override (the literal "boil the ocean" clause, second invocation). Quote captured in the Styx oath payload. All six additions ratified.

The recursive loop is now closed in the strong sense: the substrate observes itself (Hydra, Argos, Furies), reasons about itself (Athena, Hephaestus, Epimetheus, Cassandra), improves itself (Prometheus), recovers itself (Asclepius, Pan, Charon), maps itself (Daedalus), tunes itself (Metis), surfaces itself (Iris, HTTP API), reaches outside itself (Pythia), and extends itself (plugins). Every loop element is bounded by the same constitutional discipline.

*The standard is holy shit, that's done.*
