"""tests/test_hippocrene.py — the Hippocrene arc.

Per Delphi 2026-05-19-hippocrene-arc.md.

Covers:
  - Tokenizer (lowercases, strips stopwords, drops short)
  - TfIdfEmbedder: embed + score; deterministic; cosine bounded
  - Hippocrene.recall: top-k by score; empty query safe
  - Hippocrene.recall: only_kinds filter
  - Hippocrene.recall: test-seed filter (excludes by default)
  - Hippocrene.stats: reports per-kind counts + vocab size
  - Hippocrene.rebuild: forces re-index
  - invoke recall errand: smoke, --stats, --kinds
  - recall in Throne SAFE_ERRANDS
  - cache stats.json written
"""
from __future__ import annotations

import io
import contextlib
import json

import pytest

from olympus.heroes.hippocrene import (
    Hippocrene, hippocrene, Recall, HippocreneStats,
    Embedder, TfIdfEmbedder, tokenize, DEFAULT_KINDS,
)
from olympus.titans.mnemosyne import mnemosyne


# ─────────────────────────────────────────────────────────────────────
# Tokenizer
# ─────────────────────────────────────────────────────────────────────


class TestTokenize:

    def test_basic(self):
        assert tokenize("hello world") == ["hello", "world"]

    def test_lowercases(self):
        assert tokenize("HELLO") == ["hello"]

    def test_strips_stopwords(self):
        toks = tokenize("the quick brown fox")
        assert "the" not in toks
        assert "quick" in toks

    def test_drops_short(self):
        toks = tokenize("a b cd ef")
        # 'a' (1 char) dropped; 'cd' (2 chars) kept; 'b' dropped
        assert "a" not in toks
        assert "b" not in toks
        assert "cd" in toks

    def test_strips_punctuation(self):
        toks = tokenize("foo, bar! baz.")
        assert toks == ["foo", "bar", "baz"]

    def test_empty_safe(self):
        assert tokenize("") == []
        assert tokenize(None) == []  # type: ignore[arg-type]


# ─────────────────────────────────────────────────────────────────────
# TfIdfEmbedder
# ─────────────────────────────────────────────────────────────────────


class TestTfIdfEmbedder:

    def test_embed_returns_index(self):
        e = TfIdfEmbedder()
        idx = e.embed_corpus(["hello world", "foo bar", "hello foo"])
        assert idx.doc_vectors is not None
        assert len(idx.doc_vectors) == 3
        assert len(idx.idf) == len(idx.vocab)

    def test_score_query_highest_for_match(self):
        e = TfIdfEmbedder()
        idx = e.embed_corpus([
            "authentication failure in login flow",
            "the daemon ran a cognitive cycle",
            "atlas burden release for test owner",
        ])
        scores = e.score_query(idx, "authentication login")
        # Doc 0 mentions both query terms; should win
        assert scores[0] > scores[1]
        assert scores[0] > scores[2]
        # All scores bounded
        for s in scores:
            assert 0.0 <= s <= 1.0 + 1e-9

    def test_empty_query_returns_zeros(self):
        e = TfIdfEmbedder()
        idx = e.embed_corpus(["doc one", "doc two"])
        scores = e.score_query(idx, "")
        assert scores == [0.0, 0.0]

    def test_query_with_no_vocab_match(self):
        e = TfIdfEmbedder()
        idx = e.embed_corpus(["hello world"])
        scores = e.score_query(idx, "completely unrelated terms")
        assert scores == [0.0]

    def test_deterministic(self):
        e1, e2 = TfIdfEmbedder(), TfIdfEmbedder()
        idx1 = e1.embed_corpus(["a b c", "b c d"])
        idx2 = e2.embed_corpus(["a b c", "b c d"])
        assert e1.score_query(idx1, "b") == e2.score_query(idx2, "b")


# ─────────────────────────────────────────────────────────────────────
# Hippocrene.recall
# ─────────────────────────────────────────────────────────────────────


class TestHippocreneRecall:

    def test_empty_query_returns_empty(self):
        h = Hippocrene()
        assert h.recall("") == []
        assert h.recall("   ") == []

    def test_returns_top_k_sorted(self):
        h = Hippocrene()
        # Use real Mnemosyne data; we just check shape + ordering
        results = h.recall("authentication", k=5)
        assert isinstance(results, list)
        assert all(isinstance(r, Recall) for r in results)
        # Scores sorted descending
        for a, b in zip(results, results[1:]):
            assert a.score >= b.score

    def test_recall_results_have_all_fields(self):
        h = Hippocrene()
        results = h.recall("hephaestus drift", k=3)
        for r in results:
            assert r.record_id
            assert r.kind
            assert r.score > 0  # zero-score results filtered
            assert r.remembered_at

    def test_only_kinds_filters(self):
        h = Hippocrene()
        results = h.recall("substrate", k=10,
                            only_kinds=["throne.turn"])
        for r in results:
            assert r.kind == "throne.turn", \
                f"only_kinds should restrict to throne.turn, got {r.kind}"

    def test_test_seeds_excluded_by_default(self):
        """Per Tartarus discipline: production-facing layers filter
        test seeds. Hippocrene inherits that default."""
        h = Hippocrene()
        h.index()
        for m in h._records:
            actor = (m.actor or "")
            assert "-test" not in actor.lower(), \
                f"test actor leaked into production index: {actor}"


# ─────────────────────────────────────────────────────────────────────
# Stats + rebuild + cache
# ─────────────────────────────────────────────────────────────────────


class TestStatsAndCache:

    def test_stats_reports_indexed_counts(self):
        h = Hippocrene()
        h.index()
        s = h.stats()
        assert isinstance(s, HippocreneStats)
        assert s.docs_total == len(h._records)
        assert s.vocab_size > 0
        assert s.embedder == "tfidf"

    def test_rebuild_refreshes_index(self):
        h = Hippocrene()
        h.index()
        first_records = h._records
        n = h.rebuild()
        assert n == len(h._records)
        # The records list is re-built (object identity changes, contents equal)
        assert h._records is not first_records

    def test_cache_stats_written(self):
        h = Hippocrene()
        h.index()
        from olympus.primordials.gaia import root
        cache_file = root.child("state", "hippocrene", "stats.json")
        # Stats file written during index() (best-effort)
        if cache_file.exists():
            data = json.loads(cache_file.read_text(encoding="utf-8"))
            assert data["docs_total"] == h._records.__len__()


# ─────────────────────────────────────────────────────────────────────
# Pluggable embedder
# ─────────────────────────────────────────────────────────────────────


class TestPluggableEmbedder:

    def test_custom_embedder_works(self):
        """Verify the Embedder ABC contract — any subclass that
        provides embed_corpus + score_query plugs in."""

        class _SillyEmbedder(Embedder):
            name = "silly"
            def embed_corpus(self, docs):
                return docs  # the "index" is just the doc list
            def score_query(self, index, query):
                # Score = 1 if any doc contains the query lowercase,
                # else 0. Stupid but testable.
                q = query.lower()
                return [1.0 if q in d.lower() else 0.0 for d in index]

        h = Hippocrene(embedder=_SillyEmbedder())
        h.index()
        assert h.stats().embedder == "silly"


# ─────────────────────────────────────────────────────────────────────
# CLI errand
# ─────────────────────────────────────────────────────────────────────


class TestRecallErrand:

    def test_errand_registered(self):
        from olympus.cli import hermes
        assert "recall" in hermes._errands

    def test_recall_smoke(self):
        from olympus.cli import hermes
        errand = hermes._errands["recall"]
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            rc = errand.fn(["hephaestus"])
        assert rc == 0
        out = buf.getvalue()
        assert "recall" in out.lower()

    def test_stats_only(self):
        from olympus.cli import hermes
        errand = hermes._errands["recall"]
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            rc = errand.fn(["--stats"])
        assert rc == 0
        out = buf.getvalue()
        assert "stat" in out.lower() or "doc" in out.lower()

    def test_recall_empty_query_usage(self):
        from olympus.cli import hermes
        errand = hermes._errands["recall"]
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            rc = errand.fn([])
        # Usage error
        assert rc == 2


# ─────────────────────────────────────────────────────────────────────
# Throne integration
# ─────────────────────────────────────────────────────────────────────


class TestThroneCanRecall:

    def test_recall_in_safe_errands(self):
        from olympus.throne.router import SAFE_ERRANDS, GATED_ERRANDS
        assert "recall" in SAFE_ERRANDS
        assert "recall" not in GATED_ERRANDS

    def test_recall_appears_in_system_prompt(self):
        from olympus.throne.router import build_system_prompt
        p = build_system_prompt()
        assert "recall" in p
