# meta/ant-predicates.md — falsifiable predicate per commander ant

**Origin:** BIG MISSION Delphi (`delphi/2026-05-16-cognitive-substrate-must-bite.md`), Tier 1 #2.
**Status:** Enumeration complete for .  grace cycle resolved
2026-05-17 (joint Architect/Momus review): of 5 DEPRECATION_
CANDIDATE entries, 4 strengthened in-place (ant_release_velocity,
ant_recent_churn, ant_build_freshness, ant_rust_toolchain) and 1
marked for cut (ant_pattern_warmth — overlap with head_cognitive).
The DEPRECATION_CANDIDATE marker is retained in the prose below for
provenance; the in-body label has been removed from the 4 strengthened
entries and replaced with  DECISION: CUT on the 1 cut.
**Cadence:** Re-audit on every ant added or modified.

---

## Rule (Tier 1 #2 from the  Delphi)

> Rewrite each ant's rule from "differs from the  snapshot" to
> "X is true and must be false." First step: go ant by ant, write the
> one-sentence predicate. No predicate, no ant.

A predicate is **falsifiable** if there exists an observable system
state that would refute it. "X drifts" is not falsifiable; "the count
of X equals N" is. Predicates that can only be tested against an
internal HYDRA snapshot are AP1 hits (self-observation without
ground-touch) — they get DEPRECATION_CANDIDATE until the operator
either grounds the predicate or accepts the ant's deletion in .

---

## The 33 commander ants — per-ant predicates

### Republican phalanxs

#### phalanx_schema

**ant_aor_immutability** — `Audit-class tables (TokenLifecycleEvent,
VerificationEvent, EnrollmentStatusEvent, AnchorBatch, AuditAccessLog,
LifecycleArchiveCheckpoint, LifecyclePheromoneCheckpoint, schema_version)
have zero rows where the actor attempted an UPDATE or DELETE without
going through uc_archive_purge() or uc_pheromone_archive_purge().`
Falsifiable by `psql` query against pg_stat_user_tables + trigger event log.

**ant_fk_cascade_guard** — `Every FOREIGN KEY in olympus_sql/01_schema.sql
explicitly declares ON DELETE CASCADE, ON DELETE SET NULL, or ON DELETE
RESTRICT (no default behaviors).` Falsifiable by grep + AST parse of
01_schema.sql.

**ant_substrate_catalog** — `The count of distinct SystemDependency
rows in olympus_sql/13_substrate.sql matches the count of bullet items
in DEVNOTES/substrate.md.` Falsifiable by line-count comparison.

#### phalanx_security

**ant_csp_health** — `olympus_web/security.py's secure_headers() does
not emit a Content-Security-Policy header containing 'unsafe-inline',
'unsafe-eval', or 'data:' in script-src or style-src.` Falsifiable by
grep against the generated header string.

**ant_atlas_endpoint_health** — `Every /api/atlas/* route responds 200
to a request with valid bbox parameters within 2 seconds, and 400 to
a request without bbox.` Falsifiable by live HTTP probe (the oracle
runner exercises this).

#### phalanx_mission

**ant_mission_drift** — `Every C1-C10 constraint line in MISSION.md
present at  (cog-commit hash recorded in meta/structural-constants.json)
is present byte-identical in the current MISSION.md.` Falsifiable by
sha256 of the constraint block.

**ant_principle_invariant** — `Every numbered PRINCIPLE in
docs/PRINCIPLES.md is referenced by name in at least one TestCase class
docstring or test method name within test_structural_invariants.py.`
Falsifiable by grep across both files.

**ant_done_list_arithmetic** — `The count of ✅ markers in MISSION.md
done-list equals the count of done items declared in the line "Status:
N/M done".` Falsifiable by regex count.

#### phalanx_adversary

**ant_adversary_walk_complete** — `meta/oracle-state.json's
adversary.per_constraint_exit dict has all ten keys C1..C10 AND the
last_run_utc is within 7 days.` Falsifiable by JSON read.

**ant_unbumped_version** — `olympus_web/__version__.py's OLYMPUS_VERSION
literal equals the version portion of the most-recent "## vX.Y" header
in CHANGELOG.md.` Falsifiable by string compare.

#### phalanx_performance

**ant_release_velocity** — `Consecutive "## v9.\d+" headers in
CHANGELOG.md never skip a minor version (v9.N → v9.N+1, never
v9.N → v9.N+2). The trailing 10 ships' inter-ship-interval has
no gap > 7 days (matches v9.x cadence floor).` Falsifiable by
grep-and-parse over CHANGELOG.md headers + date arithmetic.
Strengthened  (was: "skipped versions ≤ 1" — weak heuristic;
the no-skip-minor-version claim is load-bearing because version
numbers ARE the audit-of-record per C1).

**ant_ship_burst** — `Per-day count of CHANGELOG ship headers is ≤ 5
(empirically chosen ceiling for the v9.x trajectory; exceeding it is
the → burst pattern that historically preceded scope drift).`
Falsifiable by grep + date parse.

#### phalanx_trajectory

**ant_proposal_stagnation** — `Every proposals/R-XX-*.md file has
either DECIDED status in its frontmatter OR a git-log entry within the
last 30 days.` Falsifiable by file scan + git log.

**ant_changelog_gap** — `The most-recent CHANGELOG.md "## v" entry
date is within 7 days of the olympus_web/__version__.py mtime.`
Falsifiable by date parse.

**ant_recent_churn** — `For each directory in {olympus_web/,
olympus_sql/, monsters.hydra/, monsters.argos/}: count of git-touched
files in the last 24h does NOT exceed 75% of total source files in
that directory (concentrated-churn anomaly threshold; 75% mirrors
the head_trajectory's file-churn-cluster ceiling).` Falsifiable
by git log --since='24 hours ago' --name-only | uniq -c per
directory. Strengthened  (was: "steady-state mode active"
operator-dependent clause — replaced with a directory-level
concentration metric the head_trajectory already validates).

#### phalanx_cognitive

**ant_self_model_accuracy** — `For every watcher in ALL_WATCHERS, the
count of expected-emission node_ids declared in the watcher class
matches the count of distinct node_ids emitted in the last 24h of
Pheromone rows.` Falsifiable by SQL aggregation + class inspection.

**ant_brain_map_freshness** — `meta/brain-map/brain-map.html mtime is
newer than any source file under monsters.argos/, monsters.hydra/,
olympians.apollo/.` Falsifiable by mtime compare.

**ant_pattern_warmth** — `Every patterns/*.md file has been git-touched
(any commit modifying it) within the last 180 days.` Falsifiable by
git log per file.
** DECISION: CUT** — joint Architect/Momus review
2026-05-17: predicate is heuristic-not-falsifiable ("a load-bearing
pattern can be untouched for years and still load-bearing"); overlap
with `head_cognitive` which already enforces pattern catalog
correspondence via ai-meta. The cognitive layer does not need two
weak claims when one strong claim exists.
**Cut-execution plan** (deferred to dedicated  ship under
structural-invariant discipline; not session-level work):
1. Remove `monsters.argos/eyes/ant_pattern_warmth.py`
2. Remove import + registration in `monsters.argos/eyes/__init__.py`
3. Remove from `monsters.argos/phalanxs/phalanx_cognitive.py` TACTIC
4. Remove from `monsters.argos/civitas/treasury.py` STEADY_STATE_ANTS
5. Remove from `scripts/oly-argos-health.sh` phalanx-counts allowlist
6. Update `olympus_web/test_structural_invariants.py` references
7. Update this file's Summary count (33 → 32 commander ants)
8. Add a new structural invariant: `ant_pattern_warmth` is NOT in the
   eyes/ inventory (regression guard).

#### phalanx_docs

**ant_api_doc_coverage** — `Every Flask route declared in
olympus_web/app.py (@app.route('...')) appears in
docs/reference/API.md, and every docs/reference/API.md entry has a corresponding
route.` Falsifiable by grep + diff.

**ant_devnotes_ships_coverage** — `Every CHANGELOG ## v entry for v8.x
or v9.x has either a DEVNOTES/ships/<name>.md file OR a comment in
DEVNOTES/README.md explicitly listing it as excluded.` Falsifiable by
ls + grep.

**ant_docs_structure** — `Every immediate subdirectory under docs/ has
a README.md.` Falsifiable by ls.

**ant_readme_counts** — `The "Status · vX.Y · N ships · M structural
invariants" line in README.md matches OLYMPUS_VERSION + the ship count
from CHANGELOG headers + the structural-invariant test count from
oly-test-counts.sh.` Falsifiable by parse + compare.

#### phalanx_substrate

**ant_dependency_in_use** — `Every package in olympus_web/requirements.txt
has at least one matching `import` or `from` line in olympus_web/.`
Falsifiable by grep.

**ant_journal_silence** — `If git log --since='today 00:00 UTC' shows
≥1 commit, journal/YYYY-MM-DD.md exists and has at least one '- **decision**'
or '- **learning**' line.` Falsifiable by file scan + git log.

**ant_delphi_outcome** — `Every delphi/*.md file has a '**Status:**'
line in the first 30 lines AND the status value is in the set {OPEN,
DECIDING, DECIDED, SHIPPED, CLOSED, DECIDED + SHIPPED, DECIDED + CLOSED}.`
Falsifiable by grep.

### Imperial phalanxs

#### phalanx_praetorian

**ant_phalanx_doctrine_health** — `Every monsters.argos/phalanxs/phalanx_*.py
file: (a) imports `Phalanx` from `monsters.argos.phalanges.base`; (b)
declares a class inheriting `Phalanx`; (c) declares ≥1 ant in its
TACTIC.` Falsifiable by AST parse.

**ant_swarm_inventory_drift** — `The count of monsters.argos/eyes/ant_*.py
files matches the sum of ant counts declared across phalanx_*.py
__init_subclass__ banner.` Falsifiable by ls + grep.

#### phalanx_engineer

**ant_build_freshness** — `IF olympus_zk/target/release/olympus-zk
exists THEN it must be newer than every .rs file under olympus_zk/src/.
Conditional invariant: claim makes no assertion in fresh clones where
cargo build has not yet run; only fires when a stale binary exists.`
Falsifiable by mtime + file existence. Strengthened  (was:
unconditional existence-AND-freshness — failed in fresh clones; now
conditional, only fires on the real failure mode of "binary exists
but is stale").

**ant_stale_script** — `Every scripts/ai-*.sh and scripts/olympus-*.sh
has been invoked (per shell history OR git-touch) within the last 90
days OR has a `# DEPRECATED` marker in the first 10 lines.` Falsifiable
by grep + git log.

**ant_test_gap** — `Every constraint C1..C10 has ≥1 test function in
test_structural_invariants.py OR test_app.py whose name or docstring
contains "C1"..."C10" respectively.` Falsifiable by grep.

**ant_treasury_health** — `Sum of all Treasury ledger entries (per
treasury-roll.json) equals zero (conservation invariant: every credit
has a corresponding debit).` Falsifiable by JSON sum.

**ant_todo_debt** — `Count of `# TODO` / `# FIXME` / `# XXX` / `# HACK`
markers in core code paths (olympus_web/, olympus_sql/, monsters.hydra/,
monsters.argos/, olympians.apollo/, olympus_zk/) is zero. DEVNOTES/ is
exempt (it's allowed to document known debt).` Falsifiable by grep.

**ant_rust_toolchain** — `olympus_zk/rust-toolchain.toml exists AND
its `channel` value is one of {"stable", "nightly", "beta"} OR is a
semver-formatted toolchain string ("1.NN.N"). The check is offline:
the value is read from the file; no network call is made.` Falsifiable
by file read + string match against the allowed set / semver regex.
Strengthened  (was: "rustup manifest within last 30 days" —
network-dependent and CI-flaky; the offline form is sufficient because
unknown channel values fail cargo invocation locally, surfacing the
real failure mode without needing network state).

---

## Summary

- **Predicates written:** 33 of 33 (100%)
- **DEPRECATION_CANDIDATE flagged in :** 5
  (ant_release_velocity, ant_recent_churn, ant_pattern_warmth,
  ant_build_freshness, ant_rust_toolchain)
- ** grace-cycle resolution (joint Architect/Momus
  2026-05-17):**
  - **Strengthened (4)**: ant_release_velocity, ant_recent_churn,
    ant_build_freshness, ant_rust_toolchain — predicates rewritten
    above as falsifiable claims that no longer carry the
    DEPRECATION_CANDIDATE marker.
  - **Marked for cut (1)**: ant_pattern_warmth — overlap with
    head_cognitive's pattern-catalog enforcement. Cut-execution
    plan recorded above; file/code surgery deferred to a dedicated
     ship (touches 9 files including test_structural_invariants;
    not session-level work).
- **Structural invariant:**
  `test_every_commander_ant_has_predicate_in_index` verifies that the
  count of `ant_*.py` files matches the count of named ants in this
  document. (See `olympus_web/test_structural_invariants.py`
  TestWave24V924.)

---

*Per BIG MISSION Delphi 2026-05-16, Tier 1 #2.*
