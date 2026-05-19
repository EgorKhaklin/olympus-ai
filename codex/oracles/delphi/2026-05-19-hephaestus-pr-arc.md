# Delphi — the Hephaestus-PR arc 🔧 (Decade #5 — KEYSTONE)

**Risk class:** MEDIUM-HIGH (touches the operator's source code).
**Decided:** Position H — ratified Hephaestus proposals can become real git branches + commits + GitHub PRs via `gh` CLI, **gated by operator-explicit `--really` flag** with a `--dry-run` default. Hybrid model: proposals with a `patch` field get the patch applied; proposals without get a tracking-branch + markdown artifact. **Constitution forbids: push to main, apply on dirty tree, autonomous apply, merge.** Throne can READ proposal apply-status but cannot trigger apply (S7-gated).
**Sworn on Styx at this arc's ratification.**

Zeus's directive (planning artifact): *"Arc 16 — Hephaestus-PR: proposals → real git PRs via `gh`. Makes Olympus a coding assistant. Constitution: never push to main; never merge; operator always reviews. Keystone arc."*

---

## Phase 0 — what exists today

- Hephaestus proposals live as JSON in `state/hephaestus/<id>.json`: `{id, drift_observed, proposed_fix, rationale, risk_class, ...}`
- `proposed_fix` is **prose**, not a patch
- Action queue records `action.ratified` when Zeus accepts a proposal
- No machinery exists to turn ratification into source-tree changes
- `gh` CLI is present on this machine (verified: `gh 2.92.0`)

**The gap**: ratification today is symbolic — there's no path from "Zeus said yes" to "the code is changed and the PR is open."

---

## What ships

### `src/olympus/runtime/git_ops.py` (~200 LOC)

Safe git wrappers. Each function refuses to act if the safety check fails; never raises silently.

```python
git_clean()         → bool        # True iff working tree has no uncommitted changes
current_branch()    → str
branch_exists(name) → bool
on_main()           → bool        # True iff current branch is main/master/trunk
create_branch(name) → CommandResult
apply_patch(text)   → CommandResult
commit(message, *paths) → CommandResult
push_to_remote(branch, *, force=False) → CommandResult  # NEVER --force; NEVER main
open_pr(title, body, base="main", head=None) → CommandResult  # via `gh`
gh_available()      → bool
```

Hard rules baked into every mutating call:
- **Never push to main / master / trunk** — caller-supplied branch name is checked against a deny-list
- **Never `--force` push** — the function has no force parameter
- **Never `git merge`** — merging is operator-in-person via GitHub UI
- **Refuse to apply on dirty tree** — `apply_patch` fails if `git status --porcelain` is non-empty
- **All operations time out at 60s** — no hangs

### Hephaestus proposal schema extension

Add two **optional** fields to `state/hephaestus/<id>.json`:
- `patch` — unified diff text (`git apply`-able)
- `target_branch` — base branch for the PR (default `main`)

Existing proposals without these fields still work — they become "tracking proposals" (see below). No migration needed.

### `invoke hephaestus apply <proposal_id>` errand

```
invoke hephaestus apply <pid>             # dry-run (default; explains what would happen)
invoke hephaestus apply <pid> --really    # actually do it (still operator-confirms in TTY)
invoke hephaestus apply <pid> --really --skip-pr   # branch + commit; skip `gh pr create`
```

Flow when `--really` is set:
1. **Pre-flight refuse-list** (any one fails → abort):
   - Proposal exists at `state/hephaestus/<pid>.json`
   - Proposal is `action.ratified` (verified against Mnemosyne)
   - Working tree is clean (`git_ops.git_clean()`)
   - Not currently on a protected branch (or proposal-target-branch is non-protected)
   - Branch `prometheus/<pid>` doesn't already exist
2. **Branch off**: `git checkout -b prometheus/<pid>`
3. **Apply** (one of):
   - If `patch` field present: `git apply` the diff
   - Otherwise: write `proposals/<pid>.md` with the full proposal text → tracking artifact
4. **Commit**: `git commit -m "<title> (#<pid>)"` with body citing Delphi + Styx oath
5. **Push** (unless `--skip-push`): `git push -u origin prometheus/<pid>`
6. **Open PR** (unless `--skip-pr` or `gh` missing): `gh pr create --base <target_branch> --head prometheus/<pid>` with title + body that references the proposal, the Delphi note, and the operator's Styx oath
7. **Record** to Mnemosyne under `prometheus.applied`: `{pid, branch, commit_sha, pr_url, mode}`
8. **Return to original branch** (the apply leaves the working tree on the new branch ONLY if `--checkout-only`; default is to return)

Dry-run mode (default): prints every step that WOULD happen, exits 0 without touching anything. Useful for the operator to audit before committing.

### Throne posture

`hephaestus apply` is **GATED** — added to `GATED_ERRANDS` in `throne/router.py`. The chatbot can show the operator the command to run, but cannot run it. Constitutional reasoning: source-code mutations require operator-in-person (S7).

Throne CAN show proposal status, list ratified-but-unapplied proposals, and explain what `apply` would do — those are read-only.

### `invoke hephaestus pending` errand (bonus, small)

Lists ratified proposals not yet applied. Operator sees what's queued for code change.

---

## Constitution

| invariant | how Hephaestus-PR honors it |
|---|---|
| S1 | every apply (dry-run OR really) → `prometheus.applied` with full evidence |
| S3 (no surprise mutation) | dry-run is default; `--really` is explicit; never on dirty tree |
| S6 | every PR body cites proposal_id + Delphi path + Styx oath sequence number |
| S7 (HIGH-risk gated) | apply stays CLI-only; Throne is read-only on this surface |
| C7-equivalent | `gh` and `git` paths are tested + injectable; no hardcoded paths |
| AP1 | one module ~200 LOC + one errand + small Throne wiring |
| AP3 | refuse-list is class-level (rules), not per-proposal |
| AP7 (ledger-balancing) | `--really` actually changes git state and `gh` creates a real PR |

---

## Safety boundaries (named explicitly)

- **Never push to main/master/trunk** — git_ops constants list these as PROTECTED_BRANCHES; the push function rejects them
- **Never `--force`** — no parameter for it
- **Never merge** — no merge function exists in git_ops
- **Refuse dirty tree** — `git status --porcelain` must be empty before apply
- **Dry-run default** — `--really` required to mutate
- **Branch-name format enforced**: `prometheus/<pid>` — no operator-chosen branch names (prevents path-traversal in branch names)
- **`gh` is optional** — if absent, apply succeeds at the branch+commit level; PR step is skipped with a clear message
- **Timeouts** — every subprocess call times out at 60s
- **Working-tree-restore on failure** — if apply fails mid-way, git_ops returns the tree to the operator's original branch

---

## What does NOT ship this arc

- **No automatic patch generation** — the LLM bridge would need to generate diffs as part of Hephaestus proposal emission. Deferred; the hybrid model (tracking-PR when no `patch` field) works without it.
- **No merge automation** — operator merges via GitHub UI
- **No CI integration** — out of scope
- **No conflict resolution** — if `git apply` fails (e.g. patch doesn't apply to current main), abort with a clear message; operator handles
- **No GitLab/Bitbucket** — `gh` is GitHub-specific. Future arc could add `glab` / `bb`
- **No Throne errand** — apply is CLI-only by constitutional design

---

## Tests

`tests/test_hephaestus_pr.py` — ~25 cases using `tmp_path`-based git repos:
- `git_clean()` correctly reports
- `current_branch()` correctly reports
- Push-to-main refused
- `create_branch` works; refuses duplicate name
- `apply_patch` on clean tree applies; on dirty tree refuses
- `commit` round-trip
- Pre-flight refuse-list rejects: missing proposal, not-ratified, dirty tree, protected branch, existing branch
- Dry-run produces output but doesn't mutate
- `--really` on tmp repo produces real branch + commit
- Tracking PR (no `patch` field) writes the markdown artifact
- `prometheus.applied` recorded to Mnemosyne with all fields
- `gh` mock: `open_pr` records the right `gh pr create` arguments
- Throne posture: `hephaestus apply` is in `GATED_ERRANDS`, not `SAFE_ERRANDS`

All tests use isolated git repos; **NO touches to the real Olympus repo's git state.**

---

## Authorization

Per the Decade plan approved 2026-05-19 (Arc 16 of 21 — the keystone). **Hephaestus-PR makes Olympus a real coding assistant.** A ratified proposal becomes a real branch, a real commit, and a real PR — with the audit trail back through the proposal, the Delphi note, the Styx oath, and the agent.invocation that surfaced the drift. The substrate is no longer just measuring; it's *doing*.

*The standard is holy shit, that's done. The forge has fire and a hammer.*
