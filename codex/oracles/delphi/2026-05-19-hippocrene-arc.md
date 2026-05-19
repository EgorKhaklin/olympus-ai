# Delphi — the Hippocrene arc 💧 (Decade #2)

**Risk class:** MEDIUM.
**Decided:** Position H — pluggable semantic-recall layer. Default implementation is **TF-IDF in pure Python** (zero new deps, fast on ~1300 records, works great on audit-of-record text). `Embedder` ABC lets future arcs swap in Anthropic embeddings or local sentence-transformers without rewriting Hippocrene. New errand `invoke recall "<query>"` + Throne wiring + grounding integration that unblocks Arc 16 (Hephaestus-PR) and Arc 17 (Demeter-Library).
**Sworn on Styx at this arc's ratification.**

Zeus's directive (planning artifact): *"Arc 13 — Hippocrene: semantic recall over Mnemosyne — vector embeddings ... operator picks embedding source."*

---

## Phase 0 — what we're indexing

Survey of production-tagged Mnemosyne records (after Tartarus filter):

```
agent.invocation               167
llm.call                       448
session.completed              447
throne.turn                    153
decade-plan.approved             1
hades.event                     91
warning.re-raised                4
warning.dismissal-reaffirmed     4
─────────────────────────────────
total                       ~1,315
```

A TF-IDF index over 1,315 short text records (each ≤512 chars of summary + body-head) fits in memory in ~2MB and answers any query in single-digit milliseconds. **Reach for embeddings later if quality demands it; ship value now.**

---

## What ships

### `src/olympus/heroes/hippocrene.py` — the spring of recall (~250 LOC)

In mythology Hippocrene (Ἱπποκρήνη — "horse's spring") was the sacred fountain on Mount Helicon, created when Pegasus struck the ground with his hoof. Those who drank from it received inspiration from the Muses. **In Olympus, Hippocrene is semantic recall**: drink from past wisdom by asking in natural language.

Public API:
```python
from olympus.heroes.hippocrene import hippocrene, Hippocrene, Embedder

results = hippocrene.recall("authentication decisions", k=5)
# [Recall(record_id, kind, summary, score, body_preview, remembered_at), ...]

hippocrene.rebuild()                        # force re-index
hippocrene.stats()                          # {indexed_records, kinds, ...}
hippocrene.index(only_kinds=["throne.turn"]) # narrow indexing
```

Pluggable architecture:
```python
class Embedder(ABC):
    name: str
    @abstractmethod
    def embed_corpus(self, docs: list[str]) -> Any: ...
    @abstractmethod
    def score_query(self, index, query: str) -> list[float]: ...

class TfIdfEmbedder(Embedder):   # default — pure Python, no deps
class AnthropicEmbedder(Embedder):  # FUTURE arc (Hippocrene-2)
class SentenceTransformerEmbedder(Embedder):  # FUTURE arc
```

### Indexing strategy

- **Source**: production records from configured kinds (Tartarus filter applied)
- **Document text**: `actor + " " + summary + " " + body-head(512c)`
- **Stopwords**: small English list + Olympus-specific noise (`record`, `data`, `the`, etc.)
- **Caching**: `state/hippocrene/index.json` with sha256 of source counts + last-record timestamps. Cache invalidates when sources change. Build time on first query ≤ 500ms.
- **Test-seed filter**: ON by default; opt-out via `--include-test-seeds`.

### `invoke recall` errand

```
invoke recall "<query>"             # top 5 across all kinds
invoke recall "<query>" -k 10       # top N
invoke recall "<query>" --kinds throne.turn,agent.invocation
invoke recall "<query>" --rebuild   # force re-index then query
invoke recall --stats               # what's indexed
invoke recall --json                # machine-readable
```

Output format (TTY):
```
score  kind                when                  summary
─────  ─────────────────   ───────────────────   ─────────────────────────────
0.847  agent.invocation    2026-05-19T03:32:00   hephaestus via anthropic: confidence=0.72
0.612  throne.turn         2026-05-19T03:34:51   throne turn: in=42c action=run errands=1 ...
0.534  hades.event         2026-05-19T03:38:14   deposit 'anthropic_api_key' (macOS.Keyring)
```

### Throne integration

Add `recall` to `SAFE_ERRANDS`. Throne can now answer:
- "what did we decide about the daemon?"
- "find recent agent invocations about drift"
- "show me when I deposited the key"

The Throne's two-call flow (route + synthesize) gains real grounding because the LLM now sees actual matching records, not just static prompts.

### Grounding integration

`runtime/grounding.py::build_grounding_for_role` extended: optional `query` parameter. When grounding for an agent call, also include Hippocrene's top-3 semantically-relevant records. This unblocks Arc 16 (Hephaestus-PR) — Hephaestus can find prior similar proposals before raising new ones.

---

## Constitution

| invariant | how Hippocrene honors it |
|---|---|
| S1 | read-only over Mnemosyne; index lives in derived state, not audit |
| S6 | every Recall cites the source kind + remembered_at + body preview |
| S8 | TF-IDF math is deterministic; same query + same corpus → same scores |
| C7-equivalent | `Embedder` pluggable; default has zero deps; swap in via constructor |
| AP1 | one hero ~250 LOC; one errand; one Throne wiring; one grounding patch |
| AP3 | per-kind handling; not per-query hardcoded rules |
| AP7 (ledger-balancing) | recall actually finds things — tested with grounded queries |
| AP8 | the test: the Throne answers a "find X" question better than before |

---

## What does NOT ship this arc

- **No real embeddings**. TF-IDF is the keystone deliverable. Embeddings come as a future Hippocrene-2 mini-arc when (and if) TF-IDF quality is insufficient.
- **No re-ranking**. Top-k by raw cosine — no fancy fusion or RRF.
- **No write-side cache invalidation hook** — re-index runs on `--rebuild` or when sha hash mismatches. Background invalidation would be its own arc.
- **No cross-corpus joins** (e.g. throne.turn + the agent.invocation it spawned). Possible future arc.
- **No long-document chunking** — records are short by design; no chunker needed yet.

---

## Tests

`tests/test_hippocrene.py` — ~20 cases:
- `TfIdfEmbedder.embed_corpus` returns vectors of consistent dim
- `score_query` returns scores in [0, 1] with high-similarity > low
- Tokenizer strips stopwords + lowercases + handles punctuation
- `Hippocrene.recall` returns top-k by score (sorted descending)
- `recall` respects `only_kinds` filter
- `recall` respects test-seed filter by default
- `stats()` reports indexed counts per kind
- `rebuild()` invalidates cache and re-indexes
- `invoke recall` errand smoke tests
- `recall` is in Throne's SAFE_ERRANDS
- Index cache file written and re-used

---

## Authorization

Per the Decade plan approved 2026-05-19 (Arc 13 of 21). **Hippocrene gives the substrate a working memory**: past records become findable by meaning, not just by exact kind. Unblocks the keystone Arc 16 (Hephaestus-PR) and Arc 17 (Demeter-Library).

*The standard is holy shit, that's done. Drink the spring and remember.*
