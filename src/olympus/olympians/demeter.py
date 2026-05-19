"""Demeter — goddess of grain, harvest, and the cycle of seasons.

Demeter taught humans to farm. Her grief for Persephone brings winter.
In Olympus, Demeter is the ingestion primitive — collecting raw
observations from many sources, batching them into harvests for
downstream processing.

Two distinct surfaces under one goddess:

  - Harvest / Demeter (original): generic batching primitive used by
    other figures to accumulate items until a `reap()` call.

  - Library (Delphi 2026-05-19-demeter-library-arc.md): operator-facing
    knowledge-base ingestion. Drop .md/.txt/.pdf into
    `state/demeter/library/`; `library.ingest()` chunks each file and
    records chunks to Mnemosyne under `demeter.chunk`. Hippocrene's
    DEFAULT_KINDS includes `demeter.chunk`, so the existing `recall`
    errand answers operator-document questions automatically.
"""
from __future__ import annotations

import hashlib
import json
import pathlib
import re
import time
from dataclasses import dataclass, field, asdict
from typing import Any, Callable


@dataclass
class Harvest:
    """A batch of observations gathered together."""
    label: str
    started_at: float
    items: list[Any] = field(default_factory=list)

    def add(self, item: Any) -> None:
        self.items.append(item)

    @property
    def size(self) -> int:
        return len(self.items)

    @property
    def elapsed(self) -> float:
        return time.monotonic() - self.started_at


class Demeter:
    """Batch-collecting ingestion. Each call to `gather()` accumulates
    items until the batch is yielded via `reap()`."""

    def __init__(self) -> None:
        self._current: dict[str, Harvest] = {}

    def gather(self, label: str, item: Any) -> Harvest:
        """Add an item to the current harvest under `label`."""
        h = self._current.get(label)
        if h is None:
            h = Harvest(label=label, started_at=time.monotonic())
            self._current[label] = h
        h.add(item)
        return h

    def reap(self, label: str) -> Harvest:
        """Take the current harvest under `label`; start a fresh one."""
        h = self._current.pop(label, Harvest(label=label, started_at=time.monotonic()))
        return h

    def harvests(self) -> dict[str, Harvest]:
        return dict(self._current)


demeter = Demeter()


# ─────────────────────────────────────────────────────────────────────
# Library — knowledge-base ingestion
# Per Delphi 2026-05-19-demeter-library-arc.md
# ─────────────────────────────────────────────────────────────────────


MAX_FILE_BYTES = 5 * 1024 * 1024        # 5 MB per file
MAX_CHUNK_CHARS = 1500
MAX_CHUNKS_PER_INGEST = 10_000

SUPPORTED_EXTS = frozenset({".md", ".txt", ".rst", ".pdf"})


@dataclass
class Chunk:
    """One chunk of an ingested document. JSON-safe."""
    document_id: str        # stable id derived from source path
    chunk_index: int
    text: str
    source_path: str        # relative to library root
    char_offset: int = 0    # offset in source document (best-effort)
    page: int = 0           # for PDFs; 0 = N/A
    sha_source: str = ""    # sha256 of the source file at ingest time


@dataclass
class IngestReport:
    """Outcome of one ingestion pass. JSON-safe."""
    started_at: str
    finished_at: str = ""
    documents_ingested: int = 0
    documents_skipped: int = 0
    documents_unchanged: int = 0
    chunks_recorded: int = 0
    by_extension: dict[str, int] = field(default_factory=dict)
    skipped: list[dict[str, str]] = field(default_factory=list)


# ─────────────────────────────────────────────────────────────────────
# Internal helpers
# ─────────────────────────────────────────────────────────────────────


def _library_dir() -> pathlib.Path:
    """Where operator drops files. Injectable for tests."""
    from olympus.primordials.gaia import root
    p = root.child("state", "demeter", "library")
    p.mkdir(parents=True, exist_ok=True)
    return p


def _manifest_path() -> pathlib.Path:
    """Where the per-file sha manifest lives. Injectable for tests."""
    from olympus.primordials.gaia import root
    p = root.child("state", "demeter", "manifest.json")
    p.parent.mkdir(parents=True, exist_ok=True)
    return p


def _load_manifest() -> dict[str, dict[str, Any]]:
    p = _manifest_path()
    if not p.exists():
        return {}
    try:
        return json.loads(p.read_text(encoding="utf-8")) or {}
    except Exception:  # noqa: BLE001
        return {}


def _save_manifest(manifest: dict[str, dict[str, Any]]) -> None:
    p = _manifest_path()
    tmp = p.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(manifest, indent=2, sort_keys=True),
                   encoding="utf-8")
    tmp.replace(p)


def _doc_id_for(relpath: str) -> str:
    """Stable id derived from the relative path."""
    h = hashlib.sha256(relpath.encode("utf-8")).hexdigest()[:12]
    safe = re.sub(r"[^a-zA-Z0-9_-]+", "-", relpath)[:60].strip("-")
    return f"{safe}-{h}" if safe else f"doc-{h}"


def _read_text(path: pathlib.Path) -> tuple[str, str]:
    """Return (text, error). text is empty on error."""
    ext = path.suffix.lower()
    if ext in {".md", ".txt", ".rst"}:
        try:
            return path.read_text(encoding="utf-8", errors="replace"), ""
        except Exception as exc:  # noqa: BLE001
            return "", f"read failed: {exc}"
    if ext == ".pdf":
        try:
            import pypdf  # type: ignore
        except ImportError:
            return "", "pypdf not installed; pip install pypdf to enable"
        try:
            reader = pypdf.PdfReader(str(path))
            parts: list[str] = []
            for pg in reader.pages:
                try:
                    parts.append(pg.extract_text() or "")
                except Exception:  # noqa: BLE001
                    continue
            return "\n\n".join(parts), ""
        except Exception as exc:  # noqa: BLE001
            return "", f"pdf parse failed: {exc}"
    return "", f"unsupported extension: {ext}"


_SENT_BOUNDARY_RX = re.compile(r"(?<=[.!?])\s+")


def chunk_text(text: str, *,
               max_chars: int = MAX_CHUNK_CHARS) -> list[str]:
    """Paragraph → sentence → hard split. Conservative."""
    if not text or not text.strip():
        return []
    paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
    out: list[str] = []
    for para in paragraphs:
        if len(para) <= max_chars:
            out.append(para); continue
        # Sentence split
        sentences = _SENT_BOUNDARY_RX.split(para)
        buf: list[str] = []
        cur_len = 0
        for sent in sentences:
            if cur_len + len(sent) + 1 > max_chars and buf:
                out.append(" ".join(buf))
                buf, cur_len = [], 0
            if len(sent) > max_chars:
                # Hard-split a too-long sentence
                if buf:
                    out.append(" ".join(buf))
                    buf, cur_len = [], 0
                for i in range(0, len(sent), max_chars):
                    out.append(sent[i:i + max_chars])
                continue
            buf.append(sent); cur_len += len(sent) + 1
        if buf:
            out.append(" ".join(buf))
    return out


# ─────────────────────────────────────────────────────────────────────
# The Library class
# ─────────────────────────────────────────────────────────────────────


class Library:
    """Operator-facing KB ingestion. Drop files into the library
    directory; `ingest()` chunks + records to Mnemosyne under
    `demeter.chunk`. Hippocrene's `DEFAULT_KINDS` includes this kind
    so the existing `recall` errand finds matches."""

    SUPPORTED_EXTS = SUPPORTED_EXTS
    MAX_FILE_BYTES = MAX_FILE_BYTES
    MAX_CHUNK_CHARS = MAX_CHUNK_CHARS
    MAX_CHUNKS_PER_INGEST = MAX_CHUNKS_PER_INGEST

    def ingest(self, *, reingest: bool = False,
                limit: int | None = None) -> IngestReport:
        """Scan library directory; ingest new/changed files. Returns
        IngestReport with per-file outcomes."""
        from olympus.primordials.nyx import Nyx
        from olympus.titans.mnemosyne import mnemosyne
        report = IngestReport(started_at=Nyx.now().isoformat())
        lib = _library_dir()
        manifest = _load_manifest()
        total_chunks = 0
        files_seen: list[pathlib.Path] = []
        for p in sorted(lib.rglob("*")):
            if not p.is_file():
                continue
            files_seen.append(p)
            if limit is not None and report.documents_ingested >= limit:
                break
            relpath = str(p.relative_to(lib).as_posix())
            ext = p.suffix.lower()
            # Skip non-supported
            if ext not in self.SUPPORTED_EXTS:
                report.documents_skipped += 1
                report.skipped.append(
                    {"path": relpath,
                     "reason": f"unsupported extension {ext!r}"})
                continue
            # Skip too-large
            try:
                size = p.stat().st_size
            except OSError as exc:
                report.documents_skipped += 1
                report.skipped.append(
                    {"path": relpath, "reason": f"stat failed: {exc}"})
                continue
            if size > self.MAX_FILE_BYTES:
                report.documents_skipped += 1
                report.skipped.append(
                    {"path": relpath,
                     "reason": f"size {size}b > {self.MAX_FILE_BYTES}b"})
                continue
            # sha check
            try:
                data = p.read_bytes()
            except Exception as exc:  # noqa: BLE001
                report.documents_skipped += 1
                report.skipped.append(
                    {"path": relpath, "reason": f"read: {exc}"})
                continue
            sha = hashlib.sha256(data).hexdigest()
            old = manifest.get(relpath)
            if (old and old.get("sha256") == sha and not reingest):
                report.documents_unchanged += 1
                continue
            # Read + chunk
            text, err = _read_text(p)
            if err:
                report.documents_skipped += 1
                report.skipped.append(
                    {"path": relpath, "reason": err})
                continue
            chunks = chunk_text(text, max_chars=self.MAX_CHUNK_CHARS)
            if not chunks:
                report.documents_skipped += 1
                report.skipped.append(
                    {"path": relpath, "reason": "empty after chunking"})
                continue
            if total_chunks + len(chunks) > self.MAX_CHUNKS_PER_INGEST:
                report.documents_skipped += 1
                report.skipped.append(
                    {"path": relpath,
                     "reason": f"would exceed MAX_CHUNKS_PER_INGEST "
                               f"({self.MAX_CHUNKS_PER_INGEST})"})
                break
            doc_id = _doc_id_for(relpath)
            # If reingesting an existing doc, record a forget marker
            # first so the audit shows the supersession (S1 — we don't
            # delete the old chunk records; we mark them superseded).
            if old:
                mnemosyne.remember(
                    kind="demeter.superseded",
                    actor="demeter:library",
                    summary=f"superseded {doc_id} "
                            f"(prev sha={old.get('sha256','')[:12]})",
                    document_id=doc_id, source_path=relpath,
                    old_sha=old.get("sha256", ""),
                    new_sha=sha,
                )
            for i, chunk in enumerate(chunks):
                mnemosyne.remember(
                    kind="demeter.chunk",
                    actor="demeter:library",
                    summary=(f"{doc_id} chunk {i}/{len(chunks)-1}: "
                             f"{chunk[:80].replace(chr(10), ' ')}"),
                    document_id=doc_id,
                    chunk_index=i,
                    text=chunk,
                    source_path=relpath,
                    sha_source=sha,
                )
                total_chunks += 1
            manifest[relpath] = {
                "document_id": doc_id,
                "sha256": sha,
                "ingested_at": Nyx.now().isoformat(),
                "chunk_count": len(chunks),
                "size_bytes": size,
            }
            report.documents_ingested += 1
            report.by_extension[ext] = report.by_extension.get(ext, 0) + 1
            report.chunks_recorded += len(chunks)
        _save_manifest(manifest)
        report.finished_at = Nyx.now().isoformat()
        # Record the whole pass
        mnemosyne.remember(
            kind="demeter.ingest_pass",
            actor="demeter:library",
            summary=(f"ingested {report.documents_ingested}, "
                     f"unchanged {report.documents_unchanged}, "
                     f"skipped {report.documents_skipped}, "
                     f"chunks {report.chunks_recorded}"),
            documents_ingested=report.documents_ingested,
            documents_unchanged=report.documents_unchanged,
            documents_skipped=report.documents_skipped,
            chunks_recorded=report.chunks_recorded,
            by_extension=report.by_extension,
            skipped=report.skipped[:30],
        )
        return report

    def documents(self) -> list[dict[str, Any]]:
        """List ingested documents from the manifest."""
        manifest = _load_manifest()
        out: list[dict[str, Any]] = []
        for relpath, entry in sorted(manifest.items()):
            out.append({"source_path": relpath, **entry})
        return out

    def forget(self, document_id: str) -> bool:
        """Mark a document as forgotten (records a `demeter.forgotten`
        marker; S1 — we don't delete the chunk records). Returns True
        if the doc was in the manifest."""
        from olympus.primordials.nyx import Nyx
        from olympus.titans.mnemosyne import mnemosyne
        manifest = _load_manifest()
        target_relpath: str | None = None
        for relpath, entry in manifest.items():
            if entry.get("document_id") == document_id:
                target_relpath = relpath
                break
        if target_relpath is None:
            return False
        manifest.pop(target_relpath, None)
        _save_manifest(manifest)
        mnemosyne.remember(
            kind="demeter.forgotten",
            actor="demeter:library",
            summary=f"forgot {document_id} ({target_relpath})",
            document_id=document_id,
            source_path=target_relpath,
            forgotten_at=Nyx.now().isoformat(),
        )
        return True


library = Library()
