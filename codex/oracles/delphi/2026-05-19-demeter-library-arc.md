# Delphi — the Demeter-Library arc 📚 (Decade #6)

**Risk class:** LOW-MEDIUM.
**Decided:** Position D — extend `olympians/demeter.py` with a `Library` class (alongside the existing `Harvest` primitive). Operator drops .md / .txt / .pdf into `state/demeter/library/`; `invoke demeter ingest` chunks each file and records chunks to Mnemosyne under `demeter.chunk`. Hippocrene (from Arc 13) auto-indexes `demeter.chunk` because we add the kind to its `DEFAULT_KINDS`. The Throne's existing `recall` errand can answer "what does my onboarding doc say about X" — **no new Throne wiring needed**; it just works through the existing semantic-recall layer. PDF support is OPTIONAL via `pypdf` — markdown and plaintext work without any new dep.
**Sworn on Styx at this arc's ratification.**

Zeus's directive (planning artifact): *"Arc 17 — Demeter-Library: KB ingestion; Throne can answer 'what does my onboarding doc say about X' with real citations; depends on Arc 13."*

---

## Phase 0 — what already works

- **Hippocrene** (Arc 13) — TF-IDF semantic search over Mnemosyne records, default kinds include `agent.invocation / llm.call / session.completed / throne.turn / etc.`
- **Throne** — `recall` is in `SAFE_ERRANDS`; the LLM can call it and synthesize an answer with citations
- **No KB layer** — Hippocrene only indexes substrate-emitted records; the operator can't yet drop their own documents in

The arc closes that gap with **the minimum-viable bridge**: ingest user documents → write chunks as Mnemosyne records → Hippocrene's existing index picks them up.

---

## What ships

### `olympians/demeter.py` extension — new `Library` class (~250 LOC)

The existing `Demeter` batching primitive (lines 34-56) stays untouched. The new `Library` is a separate concern; both live in the same module because both belong to the same goddess (Demeter: grain → harvest → cultivated knowledge).

Public API:
```python
from olympus.olympians.demeter import library, Library, Chunk

library.ingest()           # scan state/demeter/library/, ingest new/changed files
library.ingest(reingest=True)   # force re-ingest everything
library.documents()        # list known documents + chunk counts
library.forget(doc_id)     # remove a doc's chunks from Mnemosyne (records the deletion)
```

### File format support

- **`.md` / `.txt` / `.rst`** — read as UTF-8 text; works without any new dep
- **`.pdf`** — uses `pypdf` if installed; otherwise SKIPPED with a clear message (no hard fail)
- **everything else** — skipped with a "unsupported extension" message

### Chunking strategy

Per-document chunking pipeline:
1. Split on double-newlines (`\n\n`) — paragraph boundaries
2. For each paragraph: if > `MAX_CHUNK_CHARS` (default 1500), split on sentence boundaries (`. `, `! `, `? `)
3. If a sentence-split chunk still > MAX_CHUNK_CHARS, hard-split at the boundary
4. Each chunk carries: `{document_id, chunk_index, text, source_path, page_or_section, char_offset, sha_source}`

### Persistence model

- **Library directory**: `state/demeter/library/` — operator-owned input
- **Manifest**: `state/demeter/manifest.json` — per-document `{path, sha256, ingested_at, chunk_count}`; sha mismatch triggers re-ingest
- **Chunks**: each chunk → `mnemosyne.remember(kind="demeter.chunk", ...)` — no separate chunk file; the audit-of-record IS the chunk store
- **Hippocrene picks up `demeter.chunk` automatically** — we add the kind to `hippocrene.DEFAULT_KINDS` so existing `invoke recall` queries match against operator docs

### CLI errand `invoke demeter`

```
invoke demeter ingest [--reingest] [--limit N]
invoke demeter library                              # list ingested docs + counts
invoke demeter forget <doc_id>
```

### Throne integration: ZERO new wiring

The Throne already has `recall` in `SAFE_ERRANDS` (from Arc 13). After Demeter ingests, `recall` queries hit the `demeter.chunk` records automatically. Operator asks "what does my onboarding doc say about authentication" — Throne calls `recall`, gets back chunks with citations to source paths.

### Safety bounds (named explicitly)

- **`MAX_FILE_BYTES = 5MB`** per file — bigger files skipped with a clear message
- **`MAX_CHUNKS_PER_INGEST = 10,000`** — refuses to flood Mnemosyne
- **`MAX_CHUNK_CHARS = 1500`** — chunks above this are split
- **Path safety**: only files under `state/demeter/library/` ingest; symlinks resolved and checked
- **Refused extensions**: anything not in the allowlist gets skipped
- **No PDF errors raise** — failures become "skipped: <reason>" entries in the ingest report

---

## Constitution

| invariant | how Demeter-Library honors it |
|---|---|
| S1 | every chunk → Mnemosyne `demeter.chunk`; every ingest/forget recorded under `demeter.ingest_pass` |
| S3 (no surprise mutation) | reads operator's library/ directory; never writes there |
| S6 | each chunk carries `source_path` + `char_offset` so a recall answer is verifiable |
| S8 | manifest tracks sha256 per file; re-ingestion is reproducible |
| AP1 | one new class in an existing module + one errand + one DEFAULT_KINDS update |
| AP3 | chunking rules are class-level, not per-file |
| AP7 (ledger-balancing) | the test: after ingesting a real doc, `recall` returns chunks from it |
| AP8 | non-decorative: ingest produces real Mnemosyne records, real search results |

---

## What does NOT ship this arc

- **No PDF as hard dep** — install `pypdf` separately if you want PDF ingestion; markdown/txt work without
- **No OCR** — image-only PDFs yield empty text; explicit skip message
- **No embeddings** — relies on Hippocrene's TF-IDF; semantic upgrade is a future Hippocrene-2 mini-arc
- **No auto-ingest on file drop** — operator runs `invoke demeter ingest`; future arc could combine with Argos-Eyes (`watch library/ → errand:demeter-ingest`)
- **No cross-document joins** — each chunk stands alone; recall finds them by text similarity
- **No HTML/DOCX/etc.** — out of scope; future arc

---

## Tests

`tests/test_demeter_library.py` — ~20 cases using `tmp_path` with monkey-patched library dir:
- `Library.chunk_text` splits paragraphs correctly
- Long paragraphs get sentence-split
- Hard-split when sentence > MAX_CHUNK_CHARS
- `.txt` ingestion writes chunks
- `.md` ingestion writes chunks
- `.pdf` ingestion: skipped if `pypdf` absent; ingested if present (conditional skip)
- Unsupported extension skipped
- File > MAX_FILE_BYTES skipped
- Manifest tracks sha256
- Re-ingest skips unchanged files; re-ingests on sha mismatch
- `--reingest` forces re-process
- `forget` removes chunks (writes deletion record; doesn't delete Mnemosyne records since S1)
- `Hippocrene.DEFAULT_KINDS` includes `demeter.chunk`
- After ingest, `recall("known-phrase-from-doc")` finds the chunk

---

## Authorization

Per the Decade plan approved 2026-05-19 (Arc 17 of 21). **Demeter-Library closes the operator-document gap**: drop a PDF or markdown file, ask the Throne about it, get cited answers. Combined with Hippocrene (semantic recall), Hephaestus-PR (real PRs), and the rest of the Decade, Olympus now both knows operator-supplied context AND acts on it.

*The standard is holy shit, that's done. The harvest is in the granary.*
