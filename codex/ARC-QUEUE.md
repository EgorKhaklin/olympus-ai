# 📋 ARC-QUEUE

Deferred work surfaced by recent arcs. **Not a wish list** — every entry
is a real opportunity named by a previous Delphi note, with a known cost
or risk that justified deferral at the time.

The Architect's job is to leave this list **shorter than they found it**.
Adding here is cheap; removing requires either shipping the work or
documenting why it's no longer needed.

---

## High-impact, low-risk (next pickable)

### Throne routing-prompt cache
- **Surfaced by**: Plutus arc (2026-05-19). Plutus measured that ~65 %
  of all Claude spend was the throne's routing call's system prompt.
- **Fix**: apply `cache_control: {type: "ephemeral"}` to the routing
  system prompt in `runtime/llm_bridge.py::AnthropicBridge.call` when
  the role is `throne-routing`. Anthropic caches ≥ 1024-token prefixes
  for 5 min.
- **Estimated impact**: ~90 % reduction in throne-routing spend; today
  that's $0.27/week → ~$0.03/week. Compounding savings as use grows.
- **Risk**: LOW. Cache misses still work. Test: confirm `usage.cache_
  read_input_tokens > 0` on second call.

### Test-isolation lint
- **Surfaced by**: pause-and-harden arc (2026-05-19). The conftest guard
  catches contamination at end-of-suite; a pre-commit lint would catch
  the *pattern* (`monkeypatch.setenv("OLYMPUS_STATE_DIR", ...)` followed
  by `cfg_mod.save(...)`) before it ever runs.
- **Fix**: small flake8 plugin or pre-commit hook that greps test files.
- **Risk**: LOW. Lint can be bypassed; the guard is the backstop.

### `today` actionable warning closure
- **Surfaced by**: doctor (Hygieia tier) running consistently across
  the last 4 arcs. Cassandra has vindication evidence for a dismissed
  warning on slice `cassandra-test-review-record-1b6d6050`; recurred
  2× after dismissal.
- **Fix**: operator decides — either re-raise the original proposal
  (`invoke action raise ...`) OR explicitly document why the dismissal
  remains correct (records to `warning.dismissal-reaffirmed`).
- **Risk**: requires operator judgment, not autonomous fix.

---

## Medium-impact, needs design

### Hades multi-secret rotation
- **Surfaced by**: Hades arc (2026-05-19). Today the only API is
  overwrite-by-name; there's no concept of "previous key still valid
  for 1h while clients pick up new key."
- **Fix**: extend `hades.deposit` to accept `rotation_overlap_seconds`;
  add `hades.previous(name)` for the grace window.
- **Risk**: MEDIUM. Touches the secrets vault directly.

### Grounding RAG (semantic retrieval)
- **Surfaced by**: grounding arc (2026-05-19). Today each agent role
  gets a hand-curated slice of Mnemosyne (recent records by kind).
  A vector index would let agents retrieve relevant records by
  semantic similarity to the operator's question.
- **Fix**: ingest Mnemosyne records into a local vector store
  (chromadb / faiss); add a `recall_semantic(query, k)` to grounding.
- **Risk**: MEDIUM. New dep; embedding costs (small but real); cache
  invalidation on new records.

### Refresh PRICING table from Models API
- **Surfaced by**: Plutus arc (2026-05-19). `PRICING` is hand-cached
  as of 2026-04-29; an `invoke spend --refresh-pricing` errand
  querying the Anthropic Models API would keep it current.
- **Fix**: add the errand; cache the response with 30-day TTL.
- **Risk**: LOW. Read-only API call.

---

## Needs constitutional debate (operator-led Delphi tier)

### Budget alarms via Pan
- **Surfaced by**: Plutus arc (2026-05-19) explicitly deferred. Should
  the substrate be able to *stop* the operator from running expensive
  calls? E.g. trip Pan when today's spend exceeds $X.
- **Constitutional question**: Pan tripping on cost is a new authority.
  S7 says HIGH-risk actions require operator-in-person; cost-driven
  refusal is the substrate refusing to act on the operator's behalf
  WITHOUT explicit request. Different shape.
- **Tier**: Delphi-debate (operator-led debate).

### Multi-operator ACLs
- **Surfaced by**: 20-item brainstorm (2026-05-19). Today S2 reads as
  "one identity per substrate"; ACLs would allow trusted humans
  beyond Zeus to ratify scoped actions.
- **Constitutional question**: this changes the substrate's identity
  model. The Architect's preference: keep it single-operator until
  proven necessary.
- **Tier**: Delphi-debate (operator-led debate).

### Email / Slack / inbound triggers
- **Surfaced by**: 20-item brainstorm (2026-05-19). Would turn the
  substrate from operator-driven to autonomous-trigger.
- **Constitutional question**: violates the spirit of S3 (no surprise
  mutation) — the substrate would act on inputs the operator didn't
  explicitly authorize.
- **Tier**: Delphi-debate. Recommend NOT pursuing without first deciding
  whether autonomous-trigger is a direction Olympus should take.

---

## Closed (here for the audit trail)

- *(none yet — first iteration of this doc was the pause-and-harden arc)*

<!-- argos-eyes change-detection test -->
