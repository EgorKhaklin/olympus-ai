"""tests/test_argos_eyes.py — the Argos-Eyes arc.

Per Delphi 2026-05-19-argos-eyes-arc.md.

Covers (all using tmp_path — NO touches to the real state/config.json,
per the conftest contamination guard from the pause-arc):
  - FsSnapshot.take: single file, directory glob, missing path
  - diff(): added/modified/deleted/baseline-None
  - Skip-list excludes .git etc.
  - max_files ceiling
  - WatchSpec validation: id pattern, errand whitelist, alert allowed
  - FilesystemEye: baseline pass emits info only, change pass emits finding
  - FilesystemEye: invalid spec emits ALERT
  - load/save snapshot persistence
  - colony.register accepts both class and instance
  - config schema includes argos.watches[] with round-trip
"""
from __future__ import annotations

import json
import pathlib
import time

import pytest

from olympus.runtime.fs_watcher import (
    FileState, FsChange, FsSnapshot, diff,
    load_snapshot, save_snapshot,
)
from olympus.monsters.argos.eyes.eye_filesystem import (
    WatchSpec, FilesystemEye, ERRAND_WHITELIST,
)
from olympus.monsters.argos.base import KIND_INFO, KIND_DRIFT, KIND_ALERT


# ─────────────────────────────────────────────────────────────────────
# FsSnapshot
# ─────────────────────────────────────────────────────────────────────


class TestFsSnapshot:

    def test_single_file(self, tmp_path):
        f = tmp_path / "hello.txt"
        f.write_text("hello world", encoding="utf-8")
        snap = FsSnapshot.take(f)
        assert "hello.txt" in snap
        assert snap["hello.txt"].size == len(b"hello world")

    def test_directory_glob(self, tmp_path):
        (tmp_path / "a.md").write_text("aaa")
        (tmp_path / "b.md").write_text("bbb")
        (tmp_path / "c.txt").write_text("ccc")
        snap = FsSnapshot.take(tmp_path, glob="*.md")
        assert set(snap.keys()) == {"a.md", "b.md"}

    def test_missing_path_returns_empty(self, tmp_path):
        snap = FsSnapshot.take(tmp_path / "does-not-exist")
        assert snap == {}

    def test_skip_list_excludes_git(self, tmp_path):
        (tmp_path / ".git").mkdir()
        (tmp_path / ".git" / "config").write_text("[core]")
        (tmp_path / "real.md").write_text("real")
        snap = FsSnapshot.take(tmp_path)
        # .git contents must NOT appear
        assert all(".git" not in k for k in snap.keys()), \
            f"snapshot leaked .git contents: {list(snap.keys())}"

    def test_max_files_ceiling(self, tmp_path):
        for i in range(50):
            (tmp_path / f"file_{i}.txt").write_text(str(i))
        snap = FsSnapshot.take(tmp_path, max_files=10)
        assert len(snap) == 10


# ─────────────────────────────────────────────────────────────────────
# diff()
# ─────────────────────────────────────────────────────────────────────


class TestDiff:

    def test_baseline_none_returns_empty(self):
        # First-ever snapshot establishes baseline; no changes reported
        assert diff(None, {"a": FileState("sha", 1.0, 1)}) == []

    def test_added(self):
        old = {}
        new = {"a": FileState("sha-a", 1.0, 5)}
        changes = diff(old, new)
        assert len(changes) == 1
        assert changes[0].change_type == "added"
        assert changes[0].path == "a"

    def test_deleted(self):
        old = {"a": FileState("sha-a", 1.0, 5)}
        new = {}
        changes = diff(old, new)
        assert len(changes) == 1
        assert changes[0].change_type == "deleted"

    def test_modified(self):
        old = {"a": FileState("sha-old", 1.0, 5)}
        new = {"a": FileState("sha-new", 2.0, 7)}
        changes = diff(old, new)
        assert len(changes) == 1
        assert changes[0].change_type == "modified"
        assert changes[0].sha_before == "sha-old"
        assert changes[0].sha_after == "sha-new"

    def test_no_change_returns_empty(self):
        s = {"a": FileState("sha", 1.0, 5)}
        assert diff(s, s) == []


# ─────────────────────────────────────────────────────────────────────
# WatchSpec validation
# ─────────────────────────────────────────────────────────────────────


class TestWatchSpec:

    def test_alert_is_valid(self):
        ok, _ = WatchSpec(id="x", path="/tmp", action="alert").validate()
        assert ok

    def test_whitelisted_errand_valid(self):
        ok, _ = WatchSpec(id="x", path="/tmp",
                          action="errand:today").validate()
        assert ok

    def test_unwhitelisted_errand_rejected(self):
        ok, err = WatchSpec(id="x", path="/tmp",
                            action="errand:rm-rf").validate()
        assert not ok
        assert "whitelist" in err.lower()

    def test_bad_action_format_rejected(self):
        ok, err = WatchSpec(id="x", path="/tmp",
                            action="floob").validate()
        assert not ok

    def test_id_must_match_pattern(self):
        ok, _ = WatchSpec(id="bad/id", path="/tmp").validate()
        assert not ok
        ok, _ = WatchSpec(id="valid_id-123", path="/tmp").validate()
        assert ok

    def test_empty_path_rejected(self):
        ok, _ = WatchSpec(id="x", path="").validate()
        assert not ok


# ─────────────────────────────────────────────────────────────────────
# FilesystemEye
# ─────────────────────────────────────────────────────────────────────


class TestFilesystemEye:

    def test_baseline_pass_emits_info_only(self, tmp_path, monkeypatch):
        """First scan establishes baseline; no DRIFT/ALERT findings."""
        # Redirect snapshot dir to tmp so we don't pollute state/
        import olympus.runtime.fs_watcher as fsw_mod
        snap_dir = tmp_path / "snapshots"
        monkeypatch.setattr(fsw_mod, "_snapshot_dir",
                             lambda: snap_dir.resolve())
        snap_dir.mkdir(parents=True, exist_ok=True)

        (tmp_path / "a.txt").write_text("aaa")
        spec = WatchSpec(id="baseline-test",
                          path=str(tmp_path), glob="*.txt")
        eye = FilesystemEye(spec)
        findings = eye.scan()
        kinds = [f.kind for f in findings]
        assert all(k == KIND_INFO for k in kinds), \
            f"baseline pass should emit only INFO; got {kinds}"

    def test_second_pass_after_change_emits_drift(self, tmp_path,
                                                   monkeypatch):
        import olympus.runtime.fs_watcher as fsw_mod
        snap_dir = tmp_path / "snapshots"
        monkeypatch.setattr(fsw_mod, "_snapshot_dir",
                             lambda: snap_dir.resolve())
        snap_dir.mkdir(parents=True, exist_ok=True)

        (tmp_path / "a.txt").write_text("aaa")
        spec = WatchSpec(id="change-test",
                          path=str(tmp_path), glob="*.txt")
        eye = FilesystemEye(spec)
        eye.scan()  # baseline
        # Modify
        time.sleep(0.01)
        (tmp_path / "a.txt").write_text("AAA")
        # Add
        (tmp_path / "b.txt").write_text("bbb")
        findings = eye.scan()
        # Expect: 1 modified, 1 added → 2 findings minimum
        change_findings = [f for f in findings
                           if f.kind in (KIND_DRIFT, KIND_ALERT)]
        assert len(change_findings) >= 2

    def test_invalid_spec_emits_alert(self, tmp_path):
        spec = WatchSpec(id="bad/id", path=str(tmp_path),
                          action="alert")
        findings = FilesystemEye(spec).scan()
        assert any(f.kind == KIND_ALERT for f in findings)

    def test_disabled_spec_emits_nothing(self, tmp_path):
        spec = WatchSpec(id="off-test", path=str(tmp_path),
                          enabled=False)
        assert FilesystemEye(spec).scan() == []


# ─────────────────────────────────────────────────────────────────────
# Snapshot persistence
# ─────────────────────────────────────────────────────────────────────


class TestSnapshotPersistence:

    def test_round_trip(self, tmp_path, monkeypatch):
        import olympus.runtime.fs_watcher as fsw_mod
        monkeypatch.setattr(fsw_mod, "_snapshot_dir",
                             lambda: tmp_path.resolve())
        snap = {"a.txt": FileState("sha-a", 1.0, 5),
                "b.txt": FileState("sha-b", 2.0, 7)}
        save_snapshot("test-id", snap)
        loaded = load_snapshot("test-id")
        assert loaded is not None
        assert set(loaded.keys()) == {"a.txt", "b.txt"}
        assert loaded["a.txt"].sha256 == "sha-a"

    def test_load_missing_returns_none(self, tmp_path, monkeypatch):
        import olympus.runtime.fs_watcher as fsw_mod
        monkeypatch.setattr(fsw_mod, "_snapshot_dir",
                             lambda: tmp_path.resolve())
        assert load_snapshot("never-saved") is None


# ─────────────────────────────────────────────────────────────────────
# Colony.register accepts both class and instance
# ─────────────────────────────────────────────────────────────────────


class TestColonyAcceptsInstance:

    def test_instance_registration(self, tmp_path):
        from olympus.monsters.argos.colony import Colony
        c = Colony(log_path=tmp_path / "log.jsonl")
        spec = WatchSpec(id="inst-test", path=str(tmp_path))
        c.register(FilesystemEye(spec))
        assert any(e.NAME == "eye_fs_inst-test" for e in c.eyes())


# ─────────────────────────────────────────────────────────────────────
# Config schema round-trip — uses _path monkey-patch (no real config touch)
# ─────────────────────────────────────────────────────────────────────


class TestConfigArgosWatches:

    def test_watches_round_trip(self, tmp_path, monkeypatch):
        from olympus.runtime import config as cfg_mod
        fake_path = tmp_path / "config.json"
        monkeypatch.setattr(cfg_mod, "_path", lambda: fake_path)
        # Build a config with one watch
        c = cfg_mod.Config()
        c.argos.watches = [
            {"id": "test-watch", "path": "/tmp/x",
              "glob": "*", "action": "alert", "enabled": True},
        ]
        cfg_mod.save(c)
        # Load fresh
        loaded = cfg_mod.load()
        assert len(loaded.argos.watches) == 1
        assert loaded.argos.watches[0]["id"] == "test-watch"

    def test_missing_argos_section_defaults_to_empty(
            self, tmp_path, monkeypatch):
        from olympus.runtime import config as cfg_mod
        fake_path = tmp_path / "config.json"
        # Write a config WITHOUT argos section
        fake_path.write_text(json.dumps({"kindled": "x"}),
                              encoding="utf-8")
        monkeypatch.setattr(cfg_mod, "_path", lambda: fake_path)
        loaded = cfg_mod.load()
        assert loaded.argos.watches == []


# ─────────────────────────────────────────────────────────────────────
# CLI smoke
# ─────────────────────────────────────────────────────────────────────


class TestArgosErrand:

    def test_registered(self):
        from olympus.cli import hermes
        assert "argos" in hermes._errands

    def test_watches_subcommand_smoke(self):
        import io, contextlib
        from olympus.cli import hermes
        errand = hermes._errands["argos"]
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            rc = errand.fn(["watches"])
        assert rc == 0
        assert "argos watches" in buf.getvalue()

    def test_watch_add_invalid_errand_rejected(self, tmp_path,
                                                 monkeypatch):
        """`watch add` with an unwhitelisted errand must refuse."""
        from olympus.runtime import config as cfg_mod
        fake_path = tmp_path / "config.json"
        monkeypatch.setattr(cfg_mod, "_path", lambda: fake_path)
        import io, contextlib
        from olympus.cli import hermes
        errand = hermes._errands["argos"]
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            rc = errand.fn(["watch", "add", "test-id", "/tmp",
                              "--action", "errand:rm-rf"])
        assert rc == 1
        assert "whitelist" in buf.getvalue().lower()
