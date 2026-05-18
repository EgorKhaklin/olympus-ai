"""ant_build_freshness — Engineer-class observation of build hygiene.

(legacy arc) / G1 — Legio Engineer (CUNEUS lead). Where the  / E10
acceleration ants surfaced source-level debt (TODOs, test gaps,
recent churn), this ant surfaces *build-artifact-level* drift:
stale Docker images, orphaned `.pyc` files, missing rust binary
for ZK ops, vendored asset version drift.

Slice: filesystem state at the project root and selected
artifact locations:

  - `olympus_zk/target/` — Rust ZK build dir; if missing OR
    older than `olympus_zk/src/` by >7 days, the prover binary
    is stale.
  - `olympus_web/__pycache__/` — should not exist in the
    working tree (cleaned in  publication pass).
  - `olympus_web/static/vendor/d3.v7.min.js` — vendored asset;
    its mtime should be older than `static/atlas-globe.js`
    (which uses it). A vendored asset newer than its consumer
    suggests an unaudited upgrade.

Local rule: each finding is `drift` at intensity 4.0-6.0. The
Engineer's role is to surface what's slowing down ship velocity;
fixes are operator decisions.

CUNEUS doctrine: this is the LEAD ant. If it fires, the
follower (`ant_release_velocity`) deploys to characterize the
velocity impact.

G17 (acceleration ant, read-only): observes but never modifies
build state.

Determinism: pure filesystem scan + mtime comparisons.

Authorized by `delphi/2026-05-13-arc-g-roman-empire-opening.md`.
"""

from __future__ import annotations

from datetime import datetime, timezone

from monsters.argos.base import Eye, EyeFinding, KIND_DRIFT


STALE_BUILD_DAYS = 7.0


class AntBuildFreshness(Eye):
    NAME = "ant_build_freshness"
    DESCRIPTION = "Engineer (lead): surfaces stale build artifacts and vendored-asset drift."

    def __init__(self, root, seed=None, at: datetime | None = None):
        super().__init__(root, seed=seed)
        self.at = at if at is not None else datetime.now(timezone.utc)

    def scan(self) -> list[EyeFinding]:
        findings: list[EyeFinding] = []

        # Check 1: orphaned __pycache__ in working tree
        pycache = self.root / "olympus_web" / "__pycache__"
        if pycache.is_dir():
            findings.append(EyeFinding(
                node_id="build:pycache_orphan",
                intensity=4.0,
                kind=KIND_DRIFT,
                evidence={
                    "message": (
                        "olympus_web/__pycache__/ present in working "
                        "tree; cleaned in  publication pass"
                    ),
                    "fix_hint": (
                        "rm -rf olympus_web/__pycache__/ — "
                        ".gitignore covers it"
                    ),
                },
                half_life_hours=72.0,
            ))

        # Check 2: rust ZK target staleness
        zk_src = self.root / "olympus_zk" / "src"
        zk_target = self.root / "olympus_zk" / "target"
        if zk_src.is_dir():
            if not zk_target.is_dir():
                findings.append(EyeFinding(
                    node_id="build:zk_binary_missing",
                    intensity=5.0,
                    kind=KIND_DRIFT,
                    evidence={
                        "message": (
                            "olympus_zk/target/ missing; ZK prover "
                            "needs rebuild via cargo +nightly build"
                        ),
                        "fix_hint": (
                            "see docs/operator/INSTALL.md "
                            "'Building the ZK prover (optional)'"
                        ),
                    },
                    half_life_hours=168.0,
                ))
            else:
                # Compare mtimes: latest src vs latest target
                src_mtime = self._latest_mtime(zk_src)
                target_mtime = self._latest_mtime(zk_target)
                if src_mtime is not None and target_mtime is not None:
                    if src_mtime > target_mtime:
                        gap = (src_mtime - target_mtime).total_seconds() / 86400.0
                        if gap > STALE_BUILD_DAYS:
                            findings.append(EyeFinding(
                                node_id="build:zk_target_stale",
                                intensity=round(min(6.0, 3.0 + gap / 7.0), 3),
                                kind=KIND_DRIFT,
                                evidence={
                                    "message": (
                                        f"olympus_zk/src/ is "
                                        f"{gap:.1f}d newer than "
                                        f"olympus_zk/target/"
                                    ),
                                    "gap_days": round(gap, 3),
                                    "fix_hint": (
                                        "rebuild: cd olympus_zk && "
                                        "cargo +nightly build --release"
                                    ),
                                },
                                half_life_hours=168.0,
                            ))

        # Check 3: vendored asset version drift
        vendor_d3 = self.root / "olympus_web" / "static" / "vendor" / "d3.v7.min.js"
        atlas_globe = self.root / "olympus_web" / "static" / "atlas-globe.js"
        if vendor_d3.is_file() and atlas_globe.is_file():
            try:
                d3_mtime = datetime.fromtimestamp(
                    vendor_d3.stat().st_mtime, tz=timezone.utc,
                )
                ag_mtime = datetime.fromtimestamp(
                    atlas_globe.stat().st_mtime, tz=timezone.utc,
                )
                # Suspicious only if vendored is NEWER than its
                # consumer by >1 day (unaudited upgrade pattern).
                if d3_mtime > ag_mtime:
                    gap = (d3_mtime - ag_mtime).total_seconds() / 86400.0
                    if gap > 1.0:
                        findings.append(EyeFinding(
                            node_id="build:vendor_d3_unaudited",
                            intensity=4.5,
                            kind=KIND_DRIFT,
                            evidence={
                                "message": (
                                    f"vendor/d3.v7.min.js is "
                                    f"{gap:.1f}d newer than "
                                    f"atlas-globe.js (consumer)"
                                ),
                                "fix_hint": (
                                    "audit the vendored upgrade; "
                                    "verify atlas-globe.js still works "
                                    "with the new d3 surface"
                                ),
                            },
                            half_life_hours=168.0,
                        ))
            except OSError:
                pass

        return findings

    def _latest_mtime(self, base):
        """Return latest mtime under base (recursive), or None.

         / B1: filters venv/, site-packages/, etc. via
        scan_filters.is_olympus_source — pre- the latest-mtime
        was often a pip-touched site-packages file, not Olympus source.
        """
        from monsters.argos.scan_filters import is_olympus_source
        latest = None
        try:
            for p in base.rglob("*"):
                if not p.is_file():
                    continue
                if not is_olympus_source(p):
                    continue
                try:
                    ts = p.stat().st_mtime
                except OSError:
                    continue
                if latest is None or ts > latest:
                    latest = ts
        except OSError:
            return None
        if latest is None:
            return None
        return datetime.fromtimestamp(latest, tz=timezone.utc)
