# Delphi — the grounding arc 🌾

**Risk class:** HIGH-COMPOSITE (tenth heavy-production override).
**Decided:** Position D — every agent call gets a tailored grounding context (real file reads + Mnemosyne recall + pantheon registry) injected into the user prompt; cited paths are post-verified; confidence is downgraded when grounding fails.
**Sworn on Styx at this arc's ratification — oath payload includes the directive quote.**

Zeus's directive came as part of a 4-arc queue (override #10 batch); grounding goes first because the throne demo proved the gap is real and visible. Hephaestus cited `strategic/delphi/debates/*.md` — a path that **does not exist**. Cassandra refused to fabricate (S8 + AP8) but the others happily made things up. **The LLM agents reason brilliantly *in* the mythology but have zero grounding in the actual filesystem or audit-of-record.** Until this lands, the Throne is impressive but unreliable.

---

## Phase 0 — what the audit shows

Activated end-to-end first per the standing requirement: HTTP API live (PID 34428), daemon installed, doctor 8 ok / 2 warn / 0 fail, baseline suite 503/504 (one pre-existing config-drift).

Inventory of where grounding is missing today:

| agent | grounded? | symptom |
|---|---|---|
| Hephaestus | ❌ | fabricates `strategic/delphi/debates/*.md` |
| Momus | ❌ | accepts/contests *claims* without verifying the path/data exists |
| Cassandra | ✅ (partially) | refuses on empty input — but doesn't verify what it does receive |
| Athena | ❌ | synthesizes themes without citing the actual session records |
| figure_proposer | ❌ | proposes figures whose niche may already be filled |

**The constitution already says (S6) every claim must be falsifiable.** Today we trust the LLM to honor S6 voluntarily. After this arc, the substrate **enforces** S6 by verifying cited paths and downgrading confidence on fabrication.

---

## What ships

### `src/olympus/runtime/grounding.py` — the core module

Four functions:

- **`read_file_grounded(relpath: str) → GroundedRead`** — reads a file from the project root, whitelisted (no `..`, no symlink-escape, must resolve under `root`). Returns `(exists, content_head, sha256_head, error)`. Never raises.

- **`recall_grounded(kind: str, *, limit: int) → list[dict]`** — wraps `mnemosyne.recall(kind)`, returns the last `limit` records as JSON-safe dicts. Used to give agents real history.

- **`cited_paths_in_text(text: str) → list[str]`** — extracts all path-shaped substrings from agent output (regex matches `[a-z_/.-]+\.[a-z]{1,4}` minus false positives).

- **`verify_cited_paths(paths: list[str]) → list[GroundedCheck]`** — for each cited path, `(exists, normalized, reason)`. Used to post-validate every agent response.

- **`build_grounding_for_role(role: str) → str`** — assembles a role-specific grounding block:
  - **Hephaestus**: pantheon roster (90+ figures) + recent `session.completed` + `session.errored` + `proposal.raised`
  - **Momus**: AP catalog + recent `proposal.raised` (the targets it might contest)
  - **Cassandra**: recent `warning.dismissed` + recent re-occurrences of the same slice
  - **Athena**: last 10 `session.completed` summaries
  - **figure_proposer**: full pantheon roster (so it doesn't propose duplicates)
  - Each block is hard-capped at ~3000 chars (token-budget friendly)

### Patch `src/olympus/runtime/agents.py::run()`

- After `r.render_system()`, build grounding for the role
- Prepend grounding to the user_prompt with a clear header: `"GROUNDING (verified at call time — cite these where relevant):\n…\n\n---\n\nQUESTION:\n{user_prompt}"`
- After `r.parse()`, extract cited paths from `raw_text` via `cited_paths_in_text`
- Verify each via `verify_cited_paths`; record the result to `agent.grounding_check`
- If ≥ 1 cited path is fabricated, **subtract 0.2 from confidence** and add `fabricated_paths` to `parsed` (the operator sees both the answer AND the honesty)

### Constitution

| invariant | how grounding honors it |
|---|---|
| S1 | every grounding-build + every verify result → Mnemosyne (`agent.grounding_check`) |
| S6 | cited claims are checked against ground truth; confidence drops on fabrication |
| S8 | grounding context is JSON-serializable so the reproduction is exact |
| AP1 | the module is small (~150 LOC); grounding is *additive*, not a parallel agent system |
| AP3 | no per-question hardcoded rules — grounding is *per-role* (5 roles) and *data-driven* (Mnemosyne queries) |
| AP7 (ledger-balancing) | downgrade-on-fabrication is a **real** consequence, not a logged-but-ignored signal |

### What does NOT ship this arc

- **No full RAG over the entire codebase.** Grounding is targeted: each role gets the data it needs, not a vector index. Future arc may add semantic retrieval.
- **No tool-use loop.** Agents read grounding once at call time. They do not iteratively fetch more.
- **No refusal-on-no-grounding.** Confidence-downgrade is the consequence; refusal would be a behavior change too big for one arc.
- **No retroactive grounding-check.** Only new calls get grounded; the existing 580+ historical `agent.invocation` records are not re-validated.

### Tests

`tests/test_grounding.py` — 12+ cases:
- `read_file_grounded`: whitelisted root, rejects `..`, rejects symlink escape, returns exists/sha256
- `recall_grounded`: respects limit, returns dicts not dataclasses
- `cited_paths_in_text`: extracts real paths, ignores Greek figures, ignores fragments
- `verify_cited_paths`: marks real paths as exists=True, fake as exists=False
- `build_grounding_for_role`: each of the 5 roles returns a non-empty block; budget cap respected
- Integration: `agents.run("hephaestus", "...")` injects grounding; confidence drops if model fabricates (tested via ScriptedBridge)

---

## What lands

| component | role |
|---|---|
| `runtime/grounding.py` | the four functions |
| `runtime/agents.py` patch | injection + post-verify + Mnemosyne recording |
| Each parser extended with `cited_paths` | inline extraction |
| `tests/test_grounding.py` | 12+ cases |
| CHRONICLE entry | the arc rationale + delta |

---

## Authorization

Zeus invoked the heavy-production override (tenth invocation, batch position #1 of 4). **The grounding arc closes the most-visible reliability gap.** After this lands, when Hephaestus cites a path, that path *exists*; if it doesn't, the confidence score tells you. Cassandra's discipline becomes universal.

*The standard is holy shit, that's done. Every cited stone is a real stone.*
