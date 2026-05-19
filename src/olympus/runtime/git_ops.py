"""olympus.runtime.git_ops — safe git wrappers.

Per Delphi 2026-05-19-hephaestus-pr-arc.md.

Every mutating function refuses to act if a safety check fails. The
hard rules baked in here:
  - Never push to main / master / trunk (PROTECTED_BRANCHES)
  - Never --force push (no parameter for it)
  - Never `git merge` (no merge function exists)
  - Refuse to apply on dirty tree (`git status --porcelain` non-empty)
  - All operations time out at 60s

Throne is constitutionally prohibited from triggering apply (it's a
GATED errand). This module is CLI-only.
"""
from __future__ import annotations

import pathlib
import shutil
import subprocess
from dataclasses import dataclass, field
from typing import Any


# ─────────────────────────────────────────────────────────────────────
# Constitutional constants
# ─────────────────────────────────────────────────────────────────────


PROTECTED_BRANCHES: frozenset[str] = frozenset({
    "main", "master", "trunk", "production", "release",
})


_DEFAULT_TIMEOUT_S = 60


# ─────────────────────────────────────────────────────────────────────
# Data classes
# ─────────────────────────────────────────────────────────────────────


@dataclass
class CommandResult:
    """One git/gh invocation's outcome."""
    ok: bool
    cmd: list[str] = field(default_factory=list)
    stdout: str = ""
    stderr: str = ""
    exit_code: int = -1
    error: str = ""


# ─────────────────────────────────────────────────────────────────────
# Internal helper — bounded subprocess
# ─────────────────────────────────────────────────────────────────────


def _run(cmd: list[str], *,
         cwd: pathlib.Path | str | None = None,
         timeout: float = _DEFAULT_TIMEOUT_S,
         stdin: str | None = None) -> CommandResult:
    """Run a subprocess with a hard timeout. Returns CommandResult;
    never raises."""
    try:
        proc = subprocess.run(
            cmd, cwd=cwd, timeout=timeout,
            capture_output=True, text=True,
            input=stdin,
        )
        return CommandResult(
            ok=(proc.returncode == 0),
            cmd=list(cmd),
            stdout=proc.stdout or "",
            stderr=proc.stderr or "",
            exit_code=proc.returncode,
        )
    except subprocess.TimeoutExpired:
        return CommandResult(
            ok=False, cmd=list(cmd),
            error=f"timeout after {timeout}s")
    except FileNotFoundError as exc:
        return CommandResult(
            ok=False, cmd=list(cmd),
            error=f"executable not found: {exc}")
    except Exception as exc:  # noqa: BLE001
        return CommandResult(
            ok=False, cmd=list(cmd),
            error=f"{type(exc).__name__}: {exc}")


# ─────────────────────────────────────────────────────────────────────
# Read-only queries
# ─────────────────────────────────────────────────────────────────────


def git_clean(cwd: pathlib.Path | str | None = None) -> bool:
    """True iff the working tree has no uncommitted changes."""
    r = _run(["git", "status", "--porcelain"], cwd=cwd)
    if not r.ok:
        return False
    return r.stdout.strip() == ""


def current_branch(cwd: pathlib.Path | str | None = None) -> str:
    r = _run(["git", "branch", "--show-current"], cwd=cwd)
    return r.stdout.strip() if r.ok else ""


def branch_exists(name: str,
                    cwd: pathlib.Path | str | None = None) -> bool:
    r = _run(["git", "rev-parse", "--verify",
              f"refs/heads/{name}"], cwd=cwd)
    return r.ok


def on_protected_branch(cwd: pathlib.Path | str | None = None) -> bool:
    return current_branch(cwd=cwd) in PROTECTED_BRANCHES


def gh_available() -> bool:
    return shutil.which("gh") is not None


def is_protected(branch: str) -> bool:
    return branch in PROTECTED_BRANCHES


# ─────────────────────────────────────────────────────────────────────
# Mutating operations (with safety checks)
# ─────────────────────────────────────────────────────────────────────


def create_branch(name: str, *,
                   cwd: pathlib.Path | str | None = None,
                   from_ref: str | None = None) -> CommandResult:
    """Create + check out a new branch. Refuses if:
      - name is a protected branch
      - branch already exists
      - working tree is dirty (would lose changes on checkout)
    """
    if is_protected(name):
        return CommandResult(
            ok=False, cmd=["git", "checkout", "-b", name],
            error=f"branch name {name!r} is in PROTECTED_BRANCHES; "
                  f"refusing")
    if branch_exists(name, cwd=cwd):
        return CommandResult(
            ok=False, cmd=["git", "checkout", "-b", name],
            error=f"branch {name!r} already exists")
    if not git_clean(cwd=cwd):
        return CommandResult(
            ok=False, cmd=["git", "checkout", "-b", name],
            error="working tree is dirty; refusing to switch branches")
    args = ["git", "checkout", "-b", name]
    if from_ref:
        args.append(from_ref)
    return _run(args, cwd=cwd)


def apply_patch(patch_text: str, *,
                 cwd: pathlib.Path | str | None = None) -> CommandResult:
    """Apply a unified diff via `git apply`. Refuses on dirty tree
    (would conflate operator changes with patch changes)."""
    if not git_clean(cwd=cwd):
        return CommandResult(
            ok=False, cmd=["git", "apply"],
            error="working tree is dirty; refusing to apply patch")
    if not patch_text or not patch_text.strip():
        return CommandResult(
            ok=False, cmd=["git", "apply"],
            error="patch text is empty")
    return _run(["git", "apply", "--whitespace=nowarn"],
                cwd=cwd, stdin=patch_text)


def stage_and_commit(message: str, *paths: str,
                      cwd: pathlib.Path | str | None = None,
                      author: str | None = None) -> CommandResult:
    """Stage the given paths and commit. If no paths, stages all
    tracked changes (`-a`)."""
    if not message:
        return CommandResult(
            ok=False, cmd=["git", "commit"],
            error="commit message is empty")
    # Stage
    if paths:
        add = _run(["git", "add", "--"] + list(paths), cwd=cwd)
        if not add.ok:
            return add
        commit_args = ["git", "commit", "-m", message]
    else:
        commit_args = ["git", "commit", "-a", "-m", message]
    if author:
        commit_args = commit_args[:2] + [f"--author={author}"] + \
                       commit_args[2:]
    return _run(commit_args, cwd=cwd)


def push_to_remote(branch: str, *,
                    remote: str = "origin",
                    cwd: pathlib.Path | str | None = None,
                    upstream: bool = True) -> CommandResult:
    """Push `branch` to `remote`. Refuses if branch is protected.
    No `--force` parameter exists by design."""
    if is_protected(branch):
        return CommandResult(
            ok=False, cmd=["git", "push", remote, branch],
            error=f"refusing to push to PROTECTED_BRANCH "
                  f"{branch!r}")
    args = ["git", "push", remote, branch]
    if upstream:
        args = ["git", "push", "-u", remote, branch]
    return _run(args, cwd=cwd)


def checkout(ref: str, *,
              cwd: pathlib.Path | str | None = None) -> CommandResult:
    """Plain checkout (e.g., return to original branch). Refuses on
    dirty tree (per S3 — no surprise mutation)."""
    if not git_clean(cwd=cwd):
        return CommandResult(
            ok=False, cmd=["git", "checkout", ref],
            error="working tree is dirty; refusing to switch branches")
    return _run(["git", "checkout", ref], cwd=cwd)


def write_file_under_repo(rel_path: str, content: str, *,
                            cwd: pathlib.Path | str | None = None
                            ) -> CommandResult:
    """Write a file at `rel_path` (relative to repo root) with
    `content`. Used for the tracking-PR markdown artifact when no
    patch is provided. Refuses if rel_path tries to escape the repo
    via `..`."""
    if ".." in rel_path.split("/") or rel_path.startswith("/"):
        return CommandResult(
            ok=False, cmd=["write"],
            error=f"unsafe path {rel_path!r}")
    base = pathlib.Path(cwd) if cwd else pathlib.Path.cwd()
    target = (base / rel_path).resolve()
    # Confirm the target resolves under base
    try:
        target.relative_to(base.resolve())
    except ValueError:
        return CommandResult(
            ok=False, cmd=["write"],
            error=f"resolved path escapes repo: {target}")
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content, encoding="utf-8")
    return CommandResult(ok=True, cmd=["write", rel_path],
                         stdout=str(target))


# ─────────────────────────────────────────────────────────────────────
# `gh` PR creation
# ─────────────────────────────────────────────────────────────────────


def open_pr(*, title: str, body: str,
             base: str = "main", head: str | None = None,
             cwd: pathlib.Path | str | None = None,
             draft: bool = False) -> CommandResult:
    """Open a PR via the `gh` CLI. Returns CommandResult with the PR
    URL in stdout. Refuses if `gh` is missing or if `base` would push
    against itself (head == base)."""
    if not gh_available():
        return CommandResult(
            ok=False, cmd=["gh", "pr", "create"],
            error="`gh` CLI not installed (operator can run manually)")
    if not title:
        return CommandResult(
            ok=False, cmd=["gh", "pr", "create"],
            error="title is empty")
    if head and head == base:
        return CommandResult(
            ok=False, cmd=["gh", "pr", "create"],
            error=f"head ({head}) equals base ({base})")
    args = ["gh", "pr", "create",
            "--title", title,
            "--body", body,
            "--base", base]
    if head:
        args += ["--head", head]
    if draft:
        args.append("--draft")
    return _run(args, cwd=cwd, timeout=30.0)


__all__ = [
    "CommandResult", "PROTECTED_BRANCHES",
    "git_clean", "current_branch", "branch_exists",
    "on_protected_branch", "gh_available", "is_protected",
    "create_branch", "apply_patch", "stage_and_commit",
    "push_to_remote", "checkout", "write_file_under_repo",
    "open_pr",
]
