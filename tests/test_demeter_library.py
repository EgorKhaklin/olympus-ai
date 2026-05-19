"""tests/test_demeter_library.py — the Demeter-Library arc.

Per Delphi 2026-05-19-demeter-library-arc.md.

All tests use tmp_path with monkey-patched `_library_dir` and
`_manifest_path`. NO touches to the real state/demeter/.
"""
from __future__ import annotations

import contextlib
import hashlib
import io
import json
import pathlib

import pytest

from olympus.olympians.demeter import (
    Library, library, Chunk, IngestReport,
    chunk_text,
    MAX_CHUNK_CHARS, MAX_FILE_BYTES, MAX_CHUNKS_PER_INGEST,
    SUPPORTED_EXTS,
)
from olympus.titans.mnemosyne import mnemosyne


# ─────────────────────────────────────────────────────────────────────
# Fixture: isolated library dir
# ─────────────────────────────────────────────────────────────────────


@pytest.fixture
def isolated_library(tmp_path, monkeypatch):
    """Redirect _library_dir + _manifest_path to tmp."""
    from olympus.olympians import demeter as demeter_mod
    lib_dir = tmp_path / "library"
    lib_dir.mkdir(parents=True, exist_ok=True)
    manifest = tmp_path / "manifest.json"
    monkeypatch.setattr(demeter_mod, "_library_dir",
                         lambda: lib_dir.resolve())
    monkeypatch.setattr(demeter_mod, "_manifest_path",
                         lambda: manifest.resolve())
    return lib_dir


# ─────────────────────────────────────────────────────────────────────
# chunk_text
# ─────────────────────────────────────────────────────────────────────


class TestChunkText:

    def test_empty(self):
        assert chunk_text("") == []
        assert chunk_text("   \n   ") == []

    def test_paragraphs_become_chunks(self):
        text = "First paragraph.\n\nSecond paragraph.\n\nThird."
        chunks = chunk_text(text)
        assert len(chunks) == 3
        assert chunks[0] == "First paragraph."

    def test_long_paragraph_sentence_split(self):
        # Build a paragraph longer than MAX_CHUNK_CHARS via many sentences
        sentence = "Sentence with substantive content. "
        big = sentence * 100   # ~3500 chars
        chunks = chunk_text(big, max_chars=1500)
        assert len(chunks) > 1
        for c in chunks:
            # Allow small overrun for the last sentence (≤ max + sentence len)
            assert len(c) <= 1500 + len(sentence) + 5

    def test_hard_split_very_long_sentence(self):
        long_sentence = "A" * 5000   # no sentence boundaries
        chunks = chunk_text(long_sentence, max_chars=1000)
        # Each chunk capped at max_chars
        for c in chunks:
            assert len(c) <= 1000
        assert sum(len(c) for c in chunks) == 5000


# ─────────────────────────────────────────────────────────────────────
# Ingest: .md / .txt
# ─────────────────────────────────────────────────────────────────────


class TestIngestText:

    def test_ingests_md_file(self, isolated_library):
        (isolated_library / "onboarding.md").write_text(
            "# Onboarding\n\nWelcome to the company. Step one.\n\n"
            "Step two: meet your team.",
            encoding="utf-8")
        before = len(mnemosyne.recall("demeter.chunk"))
        report = Library().ingest()
        after = len(mnemosyne.recall("demeter.chunk"))
        assert report.documents_ingested == 1
        assert report.chunks_recorded >= 1
        assert after > before
        assert ".md" in report.by_extension

    def test_ingests_txt_file(self, isolated_library):
        (isolated_library / "notes.txt").write_text(
            "Simple notes file.", encoding="utf-8")
        report = Library().ingest()
        assert report.documents_ingested == 1
        assert ".txt" in report.by_extension

    def test_unsupported_extension_skipped(self, isolated_library):
        (isolated_library / "weird.xyz").write_text("xxx", encoding="utf-8")
        report = Library().ingest()
        assert report.documents_skipped == 1
        assert any("unsupported" in s["reason"]
                   for s in report.skipped)

    def test_oversize_file_skipped(self, isolated_library, monkeypatch):
        # Lower MAX_FILE_BYTES temporarily
        from olympus.olympians import demeter as dem
        monkeypatch.setattr(dem, "MAX_FILE_BYTES", 100)
        monkeypatch.setattr(Library, "MAX_FILE_BYTES", 100)
        (isolated_library / "big.md").write_text("x" * 500,
                                                   encoding="utf-8")
        report = Library().ingest()
        assert report.documents_skipped == 1
        assert any("size" in s["reason"] for s in report.skipped)


# ─────────────────────────────────────────────────────────────────────
# Re-ingestion semantics
# ─────────────────────────────────────────────────────────────────────


class TestReingest:

    def test_unchanged_file_skipped_on_second_run(self, isolated_library):
        (isolated_library / "stable.md").write_text(
            "Stable content.", encoding="utf-8")
        lib = Library()
        r1 = lib.ingest()
        assert r1.documents_ingested == 1
        # Second run: unchanged
        r2 = lib.ingest()
        assert r2.documents_ingested == 0
        assert r2.documents_unchanged == 1

    def test_changed_file_reingested(self, isolated_library):
        f = isolated_library / "evolving.md"
        f.write_text("Version one.", encoding="utf-8")
        lib = Library()
        r1 = lib.ingest()
        assert r1.documents_ingested == 1
        # Change content (sha changes)
        f.write_text("Version two now.", encoding="utf-8")
        r2 = lib.ingest()
        assert r2.documents_ingested == 1
        assert r2.documents_unchanged == 0

    def test_force_reingest(self, isolated_library):
        (isolated_library / "x.md").write_text("hello", encoding="utf-8")
        lib = Library()
        lib.ingest()
        r = lib.ingest(reingest=True)
        assert r.documents_ingested == 1


# ─────────────────────────────────────────────────────────────────────
# Manifest + forget
# ─────────────────────────────────────────────────────────────────────


class TestManifestAndForget:

    def test_manifest_tracks_sha(self, isolated_library):
        (isolated_library / "tracked.md").write_text("body",
                                                       encoding="utf-8")
        Library().ingest()
        docs = Library().documents()
        assert len(docs) == 1
        d = docs[0]
        assert d["source_path"] == "tracked.md"
        assert d["sha256"]
        assert d["chunk_count"] >= 1

    def test_forget_removes_from_manifest(self, isolated_library):
        (isolated_library / "doomed.md").write_text("x", encoding="utf-8")
        lib = Library()
        lib.ingest()
        docs = lib.documents()
        doc_id = docs[0]["document_id"]
        ok = lib.forget(doc_id)
        assert ok
        assert lib.documents() == []
        # And records a forgotten marker
        markers = mnemosyne.recall("demeter.forgotten")
        assert any(m.body.get("document_id") == doc_id for m in markers)

    def test_forget_unknown_returns_false(self, isolated_library):
        assert Library().forget("never-existed") is False


# ─────────────────────────────────────────────────────────────────────
# PDF handling (conditional)
# ─────────────────────────────────────────────────────────────────────


class TestPdfHandling:

    def test_pdf_skipped_when_pypdf_absent(self, isolated_library):
        # We don't have pypdf installed in this env; ingestion should
        # skip the PDF cleanly (no exception).
        try:
            import pypdf  # noqa: F401
            pytest.skip("pypdf is installed; the absent-skip path "
                         "cannot be exercised here")
        except ImportError:
            pass
        (isolated_library / "fake.pdf").write_bytes(b"%PDF-1.4 fake")
        report = Library().ingest()
        assert any("pypdf" in s["reason"]
                   for s in report.skipped)


# ─────────────────────────────────────────────────────────────────────
# Hippocrene integration — recall picks up chunks
# ─────────────────────────────────────────────────────────────────────


class TestHippocreneIntegration:

    def test_demeter_chunk_in_default_kinds(self):
        from olympus.heroes.hippocrene import DEFAULT_KINDS
        assert "demeter.chunk" in DEFAULT_KINDS

    def test_recall_finds_ingested_content(self, isolated_library):
        from olympus.heroes.hippocrene import Hippocrene
        # Use a distinctive phrase that won't appear elsewhere in the
        # substrate's audit log
        unique = "ostensible vespertine quantum xenolith"
        (isolated_library / "uniq.md").write_text(
            f"This document mentions {unique} as the keystone concept.",
            encoding="utf-8")
        Library().ingest()
        # Rebuild Hippocrene's index so it picks up the new chunks
        h = Hippocrene()
        h.rebuild()
        hits = h.recall(unique, k=3)
        assert hits, f"recall should find the chunk containing {unique!r}"
        # The top hit should be from demeter.chunk
        top = hits[0]
        assert top.kind == "demeter.chunk"
        assert unique.split()[0] in top.body_preview.lower() \
            or unique.split()[0] in top.summary.lower()


# ─────────────────────────────────────────────────────────────────────
# CLI smoke
# ─────────────────────────────────────────────────────────────────────


class TestDemeterErrand:

    def test_registered(self):
        from olympus.cli import hermes
        assert "demeter" in hermes._errands

    def test_library_subcommand_smoke(self, isolated_library):
        from olympus.cli import hermes
        errand = hermes._errands["demeter"]
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            rc = errand.fn(["library"])
        assert rc == 0
        assert "demeter library" in buf.getvalue()

    def test_ingest_subcommand(self, isolated_library):
        (isolated_library / "cli-test.md").write_text(
            "Content for CLI test.", encoding="utf-8")
        from olympus.cli import hermes
        errand = hermes._errands["demeter"]
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            rc = errand.fn(["ingest"])
        assert rc == 0
        out = buf.getvalue()
        assert "ingested" in out.lower()

    def test_forget_missing_id(self, isolated_library):
        from olympus.cli import hermes
        errand = hermes._errands["demeter"]
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            rc = errand.fn(["forget", "never-existed-id"])
        assert rc == 1
