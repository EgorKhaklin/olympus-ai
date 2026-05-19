"""olympus.heroes.hippocrene — semantic recall over Mnemosyne.

Per Delphi 2026-05-19-hippocrene-arc.md.

Hippocrene (Ἱπποκρήνη — "horse's spring") was the sacred fountain on
Mount Helicon, created when Pegasus struck the ground. Those who drank
received inspiration from the Muses.

In Olympus, Hippocrene is **semantic recall**: drink from past wisdom
by asking in natural language. Default implementation is TF-IDF in pure
Python — no extra deps, fast on the substrate's ~1300 production records,
deterministic. The `Embedder` ABC makes it trivial to swap in real
embeddings (Anthropic, sentence-transformers, etc.) in a future arc.

Constitutional posture:
  - S1: read-only over Mnemosyne; index lives in derived state
  - S6: every Recall cites the source kind + remembered_at + preview
  - S8: TF-IDF math is deterministic; reproducible
  - AP1: ~250 LOC; one hero; pluggable but not over-engineered
"""
from __future__ import annotations

import hashlib
import json
import math
import re
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field, asdict
from typing import Any, Iterable

from olympus.primordials.gaia import root
from olympus.primordials.nyx import Nyx
from olympus.titans.mnemosyne import mnemosyne
from olympus.runtime.test_seeds import is_test_record


# ─────────────────────────────────────────────────────────────────────
# Data classes
# ─────────────────────────────────────────────────────────────────────


@dataclass
class Recall:
    """One semantic-recall hit. JSON-safe."""
    record_id: str            # mnemosyne kind + sequence-in-corpus index
    kind: str                 # which Mnemosyne kind
    summary: str
    score: float              # 0..1, higher = more similar
    body_preview: str         # first ~200 chars of body, JSON-encoded
    remembered_at: str
    actor: str


@dataclass
class HippocreneStats:
    """What's indexed right now."""
    indexed_at: str
    embedder: str
    docs_total: int
    docs_by_kind: dict[str, int] = field(default_factory=dict)
    vocab_size: int = 0
    cache_path: str = ""
    cache_valid: bool = False


# ─────────────────────────────────────────────────────────────────────
# Default kinds to index — operator can override per call
# ─────────────────────────────────────────────────────────────────────


DEFAULT_KINDS: tuple[str, ...] = (
    "agent.invocation",
    "llm.call",
    "session.completed",
    "throne.turn",
    "decade-plan.approved",
    "hades.event",
    "warning.re-raised",
    "warning.dismissal-reaffirmed",
    "asclepius.test_burden_release",
    "doctor.diagnosis",
    # Per Delphi 2026-05-19-demeter-library-arc.md: operator-supplied
    # knowledge-base chunks ingested by Demeter's Library
    "demeter.chunk",
)


# ─────────────────────────────────────────────────────────────────────
# Tokenization
# ─────────────────────────────────────────────────────────────────────


_WORD_RX = re.compile(r"[a-zA-Z][a-zA-Z0-9_]{1,}")

_STOPWORDS = frozenset({
    # Common English
    "the", "a", "an", "and", "or", "but", "if", "of", "to", "in", "on",
    "at", "for", "with", "by", "from", "as", "is", "was", "are", "were",
    "be", "been", "being", "have", "has", "had", "do", "does", "did",
    "will", "would", "could", "should", "may", "might", "can", "must",
    "this", "that", "these", "those", "it", "its", "they", "them",
    "we", "us", "our", "you", "your", "i", "me", "my",
    # Olympus-specific noise (very common across all records)
    "record", "data", "summary", "kind", "actor", "body", "memory",
    "olympus", "substrate", "mnemosyne",
})


def tokenize(text: str) -> list[str]:
    """Lowercase + word-split + stopword-strip. Conservative."""
    if not text:
        return []
    out: list[str] = []
    for m in _WORD_RX.finditer(text.lower()):
        w = m.group(0)
        if w in _STOPWORDS or len(w) < 2:
            continue
        out.append(w)
    return out


# ─────────────────────────────────────────────────────────────────────
# Embedder interface
# ─────────────────────────────────────────────────────────────────────


class Embedder(ABC):
    """Pluggable similarity backend. Implementations: TfIdfEmbedder
    (default, no deps), AnthropicEmbedder (future), etc."""

    name: str = "abstract"

    @abstractmethod
    def embed_corpus(self, docs: list[str]) -> Any:
        """Build whatever index this embedder needs over the corpus.
        Return value is opaque (passed back into score_query)."""

    @abstractmethod
    def score_query(self, index: Any, query: str) -> list[float]:
        """Return one similarity score per corpus document."""


# ─────────────────────────────────────────────────────────────────────
# TF-IDF embedder (default — zero deps)
# ─────────────────────────────────────────────────────────────────────


@dataclass
class _TfIdfIndex:
    """The materialized TF-IDF index."""
    vocab: dict[str, int]       # term → column id
    idf: list[float]            # one entry per vocab term
    doc_vectors: list[dict[int, float]]   # sparse rows
    doc_norms: list[float]                # for cosine math


class TfIdfEmbedder(Embedder):
    """Pure-Python TF-IDF + cosine. Deterministic, no deps, fast on
    the substrate's ~1300 records."""

    name = "tfidf"

    def embed_corpus(self, docs: list[str]) -> _TfIdfIndex:
        # 1. Tokenize and count per doc
        tokenized = [tokenize(d) for d in docs]
        # 2. Document-frequency per term
        df: dict[str, int] = {}
        for toks in tokenized:
            for t in set(toks):
                df[t] = df.get(t, 0) + 1
        vocab = {t: i for i, t in enumerate(sorted(df.keys()))}
        n_docs = max(len(docs), 1)
        # 3. IDF = log((N + 1) / (df + 1)) + 1 (smoothed)
        idf = [0.0] * len(vocab)
        for t, col in vocab.items():
            idf[col] = math.log((n_docs + 1) / (df[t] + 1)) + 1.0
        # 4. Per-doc TF-IDF sparse vectors
        doc_vectors: list[dict[int, float]] = []
        doc_norms: list[float] = []
        for toks in tokenized:
            if not toks:
                doc_vectors.append({})
                doc_norms.append(0.0)
                continue
            tf: dict[int, float] = {}
            for t in toks:
                col = vocab.get(t)
                if col is None:
                    continue
                tf[col] = tf.get(col, 0.0) + 1.0
            # Normalize TF by max term frequency in this doc
            max_tf = max(tf.values()) if tf else 1.0
            vec = {col: (0.5 + 0.5 * (count / max_tf)) * idf[col]
                   for col, count in tf.items()}
            norm = math.sqrt(sum(v * v for v in vec.values()))
            doc_vectors.append(vec)
            doc_norms.append(norm)
        return _TfIdfIndex(vocab=vocab, idf=idf,
                           doc_vectors=doc_vectors,
                           doc_norms=doc_norms)

    def score_query(self, index: _TfIdfIndex, query: str) -> list[float]:
        toks = tokenize(query)
        if not toks or not index.vocab:
            return [0.0] * len(index.doc_vectors)
        # Build query TF-IDF the same way
        qtf: dict[int, float] = {}
        for t in toks:
            col = index.vocab.get(t)
            if col is None:
                continue
            qtf[col] = qtf.get(col, 0.0) + 1.0
        if not qtf:
            return [0.0] * len(index.doc_vectors)
        max_qtf = max(qtf.values())
        qvec = {col: (0.5 + 0.5 * (count / max_qtf)) * index.idf[col]
                for col, count in qtf.items()}
        qnorm = math.sqrt(sum(v * v for v in qvec.values()))
        if qnorm == 0.0:
            return [0.0] * len(index.doc_vectors)
        # Cosine = sum(q[c] * d[c]) / (qnorm * dnorm) for shared cols
        scores: list[float] = []
        for vec, dnorm in zip(index.doc_vectors, index.doc_norms):
            if dnorm == 0.0:
                scores.append(0.0); continue
            # Iterate over the SHORTER of qvec / vec for speed
            if len(qvec) < len(vec):
                dot = sum(qv * vec.get(col, 0.0)
                          for col, qv in qvec.items())
            else:
                dot = sum(dv * qvec.get(col, 0.0)
                          for col, dv in vec.items())
            scores.append(dot / (qnorm * dnorm))
        return scores


# ─────────────────────────────────────────────────────────────────────
# Hippocrene — the singleton
# ─────────────────────────────────────────────────────────────────────


_CACHE_DIR = "state/hippocrene"


def _doc_for_record(m: Any) -> str:
    """Turn a Memory into one search-friendly text blob. Used by
    indexing. Truncated to keep TF-IDF tractable."""
    parts: list[str] = []
    actor = getattr(m, "actor", "") or ""
    summary = getattr(m, "summary", "") or ""
    body = getattr(m, "body", {}) or {}
    parts.append(actor)
    parts.append(summary)
    # Body: include scalar values (skip nested dicts/lists to avoid bloat)
    for k, v in body.items():
        if isinstance(v, (str, int, float, bool)):
            parts.append(f"{k}:{v}")
    blob = " ".join(parts)
    return blob[:1024]


class Hippocrene:
    """The semantic-recall hero. Default backend: TF-IDF."""

    def __init__(self, *, embedder: Embedder | None = None) -> None:
        self.embedder = embedder if embedder is not None else TfIdfEmbedder()
        self._index: Any = None
        self._records: list[Any] = []   # parallel array to index docs
        self._kinds_indexed: tuple[str, ...] = ()
        self._cache_hash: str = ""

    # ─────────────────────────────────────────────────────────────
    # Public API
    # ─────────────────────────────────────────────────────────────

    def recall(self, query: str, *, k: int = 5,
                only_kinds: Iterable[str] | None = None,
                include_test_seeds: bool = False) -> list[Recall]:
        """Top-k semantic matches for `query`. Builds the index lazily
        if not yet built."""
        if not query or not query.strip():
            return []
        # Ensure index covers the kinds we're querying
        wanted_kinds = (tuple(sorted(only_kinds))
                         if only_kinds else DEFAULT_KINDS)
        if (self._index is None
                or self._kinds_indexed != wanted_kinds):
            self.index(only_kinds=wanted_kinds,
                        include_test_seeds=include_test_seeds)
        if not self._records:
            return []
        scores = self.embedder.score_query(self._index, query)
        # Pair scores with records, sort, slice
        ranked = sorted(
            zip(scores, self._records, range(len(scores))),
            key=lambda x: -x[0])[:max(k, 1)]
        out: list[Recall] = []
        for score, m, ri in ranked:
            if score <= 0.0:
                continue
            body = getattr(m, "body", {}) or {}
            preview = json.dumps(
                {k: v for k, v in body.items()
                 if isinstance(v, (str, int, float, bool))},
                default=str)[:200]
            out.append(Recall(
                record_id=f"{m.kind}#{ri}",
                kind=m.kind,
                summary=m.summary or "",
                score=round(score, 4),
                body_preview=preview,
                remembered_at=m.remembered_at,
                actor=m.actor or "",
            ))
        return out

    def index(self, *, only_kinds: Iterable[str] | None = None,
              include_test_seeds: bool = False) -> int:
        """Build or rebuild the index over the configured kinds.
        Returns count of indexed records."""
        kinds = (tuple(sorted(only_kinds))
                 if only_kinds else DEFAULT_KINDS)
        records: list[Any] = []
        for kind in kinds:
            try:
                raw = mnemosyne.recall(kind)
            except Exception:  # noqa: BLE001
                continue
            for m in raw:
                if (not include_test_seeds) and is_test_record(m):
                    continue
                records.append(m)
        docs = [_doc_for_record(m) for m in records]
        self._index = self.embedder.embed_corpus(docs)
        self._records = records
        self._kinds_indexed = kinds
        self._cache_hash = self._compute_hash(records)
        self._write_cache_stats()
        return len(records)

    def rebuild(self, *, only_kinds: Iterable[str] | None = None,
                 include_test_seeds: bool = False) -> int:
        """Force a fresh index build (clears any cached state)."""
        self._index = None
        return self.index(only_kinds=only_kinds,
                           include_test_seeds=include_test_seeds)

    def stats(self) -> HippocreneStats:
        from collections import Counter
        by_kind = Counter(getattr(m, "kind", "?") for m in self._records)
        vocab_size = (len(getattr(self._index, "vocab", {}))
                      if self._index else 0)
        return HippocreneStats(
            indexed_at=Nyx.now().isoformat(),
            embedder=self.embedder.name,
            docs_total=len(self._records),
            docs_by_kind=dict(by_kind),
            vocab_size=vocab_size,
            cache_path=str(root.child(_CACHE_DIR, "stats.json")),
            cache_valid=bool(self._records),
        )

    # ─────────────────────────────────────────────────────────────
    # Internals
    # ─────────────────────────────────────────────────────────────

    def _compute_hash(self, records: list[Any]) -> str:
        """Fingerprint the input corpus so we can detect drift."""
        h = hashlib.sha256()
        for m in records:
            h.update(((m.kind or "") + "|"
                       + (m.remembered_at or "")).encode("utf-8"))
        return h.hexdigest()

    def _write_cache_stats(self) -> None:
        """Persist a small stats file under state/hippocrene/ so the
        operator can inspect what's indexed without re-running."""
        try:
            cache_dir = root.child(_CACHE_DIR)
            cache_dir.mkdir(parents=True, exist_ok=True)
            (cache_dir / "stats.json").write_text(
                json.dumps(asdict(self.stats()), default=str, indent=2),
                encoding="utf-8")
        except Exception:  # noqa: BLE001
            pass


# Module-level singleton
hippocrene = Hippocrene()


__all__ = [
    "Hippocrene", "hippocrene",
    "Recall", "HippocreneStats",
    "Embedder", "TfIdfEmbedder",
    "tokenize", "DEFAULT_KINDS",
]
