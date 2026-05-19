"""tests/test_hephaestus_pr.py — the Hephaestus-PR keystone arc.

Per Delphi 2026-05-19-hephaestus-pr-arc.md.

All tests use isolated tmp git repos — NO touches to the real Olympus
repo's git state (the conftest contamination guard would catch state/
mutations, and a `cwd=tmp` discipline keeps git mutations contained).
"""
from __future__ import annotations

import contextlib
import io
import json
import pathlib
import subprocess

import pytest

from olympus.runtime import git_ops
from olympus.runtime.git_ops import (
    CommandResult, PROTECTED_BRANCHES,
    git_clean, current_branch, branch_exists, on_protected_branch,
    is_protected, create_branch, apply_patch, stage_and_commit,
    push_to_remote, checkout, write_file_under_repo, open_pr,
)


# ─────────────────────────────────────────────────────────────────────
# Fixture: fresh git repo in tmp_path
# ─────────────────────────────────────────────────────────────────────


@pytest.fixture
def tmp_repo(tmp_path):
    """Initialize a fresh git repo in tmp_path with one commit on main."""
    subprocess.run(["git", "init", "-q", "-b", "main"],
                    cwd=tmp_path, check=True)
    # Test identity (required for commit)
    subprocess.run(["git", "config", "user.email", "test@olympus"],
                    cwd=tmp_path, check=True)
    subprocess.run(["git", "config", "user.name", "olympus-test"],
                    cwd=tmp_path, check=True)
    # Initial commit
    (tmp_path / "README.md").write_text("# test repo", encoding="utf-8")
    subprocess.run(["git", "add", "README.md"], cwd=tmp_path, check=True)
    subprocess.run(["git", "commit", "-q", "-m", "init"],
                    cwd=tmp_path, check=True)
    return tmp_path


# ─────────────────────────────────────────────────────────────────────
# Read-only queries
# ─────────────────────────────────────────────────────────────────────


class TestReadOnlyQueries:

    def test_git_clean_on_fresh_repo(self, tmp_repo):
        assert git_clean(cwd=tmp_repo) is True

    def test_git_dirty_after_change(self, tmp_repo):
        (tmp_repo / "README.md").write_text("modified", encoding="utf-8")
        assert git_clean(cwd=tmp_repo) is False

    def test_current_branch_is_main(self, tmp_repo):
        assert current_branch(cwd=tmp_repo) == "main"

    def test_branch_exists_main(self, tmp_repo):
        assert branch_exists("main", cwd=tmp_repo)
        assert not branch_exists("does-not-exist", cwd=tmp_repo)

    def test_on_protected(self, tmp_repo):
        assert on_protected_branch(cwd=tmp_repo)

    def test_is_protected_constants(self):
        assert is_protected("main")
        assert is_protected("master")
        assert is_protected("trunk")
        assert not is_protected("prometheus/foo")
        assert not is_protected("feature/anything")


# ─────────────────────────────────────────────────────────────────────
# create_branch safety
# ─────────────────────────────────────────────────────────────────────


class TestCreateBranch:

    def test_creates_new_branch(self, tmp_repo):
        r = create_branch("prometheus/test-1", cwd=tmp_repo)
        assert r.ok, f"create_branch failed: {r.stderr}"
        assert current_branch(cwd=tmp_repo) == "prometheus/test-1"

    def test_refuses_protected(self, tmp_repo):
        r = create_branch("main", cwd=tmp_repo)
        assert not r.ok
        assert "PROTECTED_BRANCHES" in r.error

    def test_refuses_duplicate(self, tmp_repo):
        create_branch("prometheus/dup", cwd=tmp_repo)
        # Switch back
        subprocess.run(["git", "checkout", "main"], cwd=tmp_repo,
                        check=True, capture_output=True)
        r = create_branch("prometheus/dup", cwd=tmp_repo)
        assert not r.ok
        assert "already exists" in r.error

    def test_refuses_dirty_tree(self, tmp_repo):
        (tmp_repo / "README.md").write_text("dirty", encoding="utf-8")
        r = create_branch("prometheus/x", cwd=tmp_repo)
        assert not r.ok
        assert "dirty" in r.error


# ─────────────────────────────────────────────────────────────────────
# apply_patch safety
# ─────────────────────────────────────────────────────────────────────


class TestApplyPatch:

    def test_applies_valid_patch(self, tmp_repo):
        patch = """\
diff --git a/new.txt b/new.txt
new file mode 100644
index 0000000..a907ec3
--- /dev/null
+++ b/new.txt
@@ -0,0 +1,1 @@
+hello from patch
"""
        r = apply_patch(patch, cwd=tmp_repo)
        assert r.ok, f"apply_patch failed: {r.stderr}"
        assert (tmp_repo / "new.txt").exists()

    def test_refuses_empty_patch(self, tmp_repo):
        r = apply_patch("", cwd=tmp_repo)
        assert not r.ok

    def test_refuses_on_dirty_tree(self, tmp_repo):
        (tmp_repo / "README.md").write_text("dirty", encoding="utf-8")
        r = apply_patch("dummy", cwd=tmp_repo)
        assert not r.ok


# ─────────────────────────────────────────────────────────────────────
# stage_and_commit
# ─────────────────────────────────────────────────────────────────────


class TestCommit:

    def test_commit_specific_path(self, tmp_repo):
        (tmp_repo / "f.txt").write_text("content", encoding="utf-8")
        r = stage_and_commit("test commit", "f.txt", cwd=tmp_repo)
        assert r.ok, f"commit failed: {r.stderr}"

    def test_refuses_empty_message(self, tmp_repo):
        r = stage_and_commit("", cwd=tmp_repo)
        assert not r.ok


# ─────────────────────────────────────────────────────────────────────
# Push safety
# ─────────────────────────────────────────────────────────────────────


class TestPushSafety:

    def test_refuses_to_push_main(self):
        # Doesn't need a repo — the safety check is name-only
        r = push_to_remote("main")
        assert not r.ok
        assert "PROTECTED_BRANCH" in r.error

    def test_refuses_to_push_master(self):
        r = push_to_remote("master")
        assert not r.ok

    def test_refuses_to_push_trunk(self):
        r = push_to_remote("trunk")
        assert not r.ok


# ─────────────────────────────────────────────────────────────────────
# write_file_under_repo
# ─────────────────────────────────────────────────────────────────────


class TestWriteFileSafety:

    def test_writes_legal_path(self, tmp_repo):
        r = write_file_under_repo("proposals/x.md", "hello",
                                    cwd=tmp_repo)
        assert r.ok
        assert (tmp_repo / "proposals" / "x.md").read_text() == "hello"

    def test_refuses_dotdot(self, tmp_repo):
        r = write_file_under_repo("../escape.md", "x", cwd=tmp_repo)
        assert not r.ok
        assert "unsafe" in r.error

    def test_refuses_absolute(self, tmp_repo):
        r = write_file_under_repo("/etc/passwd", "x", cwd=tmp_repo)
        assert not r.ok


# ─────────────────────────────────────────────────────────────────────
# open_pr (gh CLI is present on this machine but we don't actually call)
# ─────────────────────────────────────────────────────────────────────


class TestOpenPr:

    def test_refuses_when_gh_missing(self, monkeypatch):
        import olympus.runtime.git_ops as go
        monkeypatch.setattr(go, "gh_available", lambda: False)
        r = open_pr(title="t", body="b")
        assert not r.ok
        assert "gh" in r.error.lower()

    def test_refuses_head_equals_base(self):
        r = open_pr(title="t", body="b", head="main", base="main")
        assert not r.ok
        assert "equals" in r.error.lower()

    def test_refuses_empty_title(self):
        r = open_pr(title="", body="b")
        assert not r.ok


# ─────────────────────────────────────────────────────────────────────
# CLI errand smoke + Throne gating
# ─────────────────────────────────────────────────────────────────────


class TestHephaestusErrand:

    def test_errand_registered(self):
        from olympus.cli import hermes
        assert "hephaestus" in hermes._errands

    def test_pending_smoke(self):
        from olympus.cli import hermes
        errand = hermes._errands["hephaestus"]
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            rc = errand.fn(["pending"])
        assert rc == 0
        assert "hephaestus" in buf.getvalue().lower()

    def test_apply_requires_pid(self):
        from olympus.cli import hermes
        errand = hermes._errands["hephaestus"]
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            rc = errand.fn(["apply"])
        assert rc == 2

    def test_apply_missing_proposal_rejected(self):
        from olympus.cli import hermes
        errand = hermes._errands["hephaestus"]
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            rc = errand.fn(["apply", "definitely-does-not-exist"])
        assert rc == 1
        assert "not found" in buf.getvalue().lower()


class TestThronePosture:

    def test_hephaestus_in_gated_not_safe(self):
        from olympus.throne.router import (
            SAFE_ERRANDS, GATED_ERRANDS,
        )
        assert "hephaestus" in GATED_ERRANDS, \
            "hephaestus apply must be S7-gated"
        assert "hephaestus" not in SAFE_ERRANDS

    def test_gated_suggested_command(self):
        from olympus.throne.router import GATED_ERRANDS
        assert "invoke hephaestus apply" in \
            GATED_ERRANDS["hephaestus"]["suggested"]
