"""Argos colony runner — deploys phalanxs, deposits pheromones.

This is the SINGLE place that writes to the Pheromone table.

Post- ((legacy arc) / E6 — phalanx structure):
  The colony iterates ALL_PHALANGES rather than ALL_EYES. Each Phalanx
  deploys via its own tactic (TESTUDO / TRIPLEX_ACIES / CUNEUS /
  VEXILLATIO / AUXILIA). The colony runner does NOT interpret
  tactics; it dispatches. AoR is preserved: `deposited_by` is still
  the ant name; the phalanx identity travels in evidence JSONB.

Decentralization observation: the runner is NOT a synthesizer.
Each (ant, finding) pair is deposited independently. Synthesis
happens at READ time when `oly-argos-bloom` queries Pheromone and
applies decay across the brain map.

Usage (CLI):
    python3 -m monsters.argos.colony            # scan + deposit (needs DB)
    python3 -m monsters.argos.colony --dry      # scan + print, no DB writes
    python3 -m monsters.argos.colony --list     # show registered phalanxs + ants
    python3 -m monsters.argos.colony --json     # JSON output
"""

from __future__ import annotations

import argparse
import json
import os
import pathlib
import sys

from monsters.argos.base import Eye, EyeFinding
from monsters.argos.phalanges import ALL_PHALANGES, Phalanx
from monsters.argos.demes import ALL_DEMES, Deme, DemeFinding

# Optional psycopg2 import — colony can run --dry without DB libs.
try:
    import psycopg2
    from psycopg2.extras import Json
    _PSYCOPG2_AVAILABLE = True
except ImportError:
    psycopg2 = None
    Json = None
    _PSYCOPG2_AVAILABLE = False


def _project_root() -> pathlib.Path:
    return pathlib.Path(__file__).resolve().parent.parent


def _connect_db():
    """Open a Olympus DB connection from env vars; None if unavailable."""
    if not _PSYCOPG2_AVAILABLE:
        return None
    try:
        return psycopg2.connect(
            host=os.environ.get("OLYMPUS_DB_HOST", "localhost"),
            dbname=os.environ.get("OLYMPUS_DB_NAME", "olympus_test"),
            user=os.environ.get("OLYMPUS_DB_USER", "olympus_app"),
            password=os.environ.get("OLYMPUS_DB_PASSWORD", "olympus_dev_password"),
        )
    except Exception:
        return None


# Type alias for a single deployment result: (Phalanx, list of (EyeClass, findings))
PhalanxResult = tuple[Phalanx, list[tuple[type[Eye], list[EyeFinding]]]]


def run_colony(
    root: pathlib.Path | None = None,
    dry: bool = False,
    recurrence_weighted: bool = True,
) -> list[PhalanxResult]:
    """Deploy every phalanx in ALL_PHALANGES, optionally deposit to DB.

    Returns the per-phalanx scan results. The runner itself does NOT
    aggregate or synthesize. It dispatches to each Phalanx's tactic,
    captures (ant, findings) pairs, and either prints or deposits.

     (BIG MISSION T1#4) — `recurrence_weighted=True` reads recent
    Pheromone deposits + reorders the phalanx deploy sequence to
    investigate recurring + decayed-but-returning surfaces first. The
    stigmergic loop is now closed: a deposit on pass N biases pass N+1.
    Disable with recurrence_weighted=False to fall back to lex order
    (the pre- behavior; preserved for tests + drill).

    Post-: this is Phase 1 of swarm deployment. For the
    full two-phase swarm (phalanxs then citizens), call run_swarm()
    instead. run_colony preserved for backward compatibility.
    """
    if root is None:
        root = _project_root()

    # : read recent Pheromone state + compute priority order
    phalanx_order = ALL_PHALANGES
    if recurrence_weighted and not dry:
        try:
            from monsters.argos.stigmergy import (
                recurrence_weighted_ordering, phalanx_priority_order
            )
            recent = _fetch_recent_pheromones_from_db(hours=24.0)
            priorities = recurrence_weighted_ordering(recent)
            if priorities:
                # Map phalanx names → classes; reorder per priority
                name_to_class = {
                    L.NAME if hasattr(L, "NAME") else L.__name__: L
                    for L in ALL_PHALANGES
                }
                ordered_names = phalanx_priority_order(
                    priorities, list(name_to_class.keys())
                )
                phalanx_order = [name_to_class[n] for n in ordered_names
                                if n in name_to_class]
                # Append any phalanxs not in priority order (shouldn't happen
                # but defensive — preserves G10 "no orphan phalanxs")
                seen = set(phalanx_order)
                for L in ALL_PHALANGES:
                    if L not in seen:
                        phalanx_order.append(L)
        except Exception:
            # G3 (graceful): stigmergy module failure → fall back to lex order
            phalanx_order = ALL_PHALANGES

    results: list[PhalanxResult] = []
    for PhalanxCls in phalanx_order:
        try:
            phalanx = PhalanxCls(root)
            eye_results = phalanx.deploy()
        except Exception as exc:
            # Graceful failure: phalanx-level crash becomes a curious
            # pheromone on the phalanx's own node. The other phalanxs
            # continue.
            phalanx = _make_failed_phalanx(PhalanxCls, root, exc)
            eye_results = [(_PlaceholderFailureEye, [EyeFinding(
                node_id=f"legio:{PhalanxCls.NAME}",
                intensity=4.0,
                kind="curious",
                evidence={
                    "message": "phalanx deploy raised an exception",
                    "exception_type": type(exc).__name__,
                    "exception_text": str(exc)[:240],
                },
            )])]
        results.append((phalanx, eye_results))
    if not dry:
        _deposit_phalanx_results(results)
    return results


# Type alias for civitas results
CitizenResult = tuple[Deme, list[DemeFinding]]


def run_civitas(
    root: pathlib.Path | None = None,
    phalanx_results: list[PhalanxResult] | None = None,
    dry: bool = False,
) -> list[CitizenResult]:
    """Phase 2 of swarm deployment: deploy citizens.

    Demes observe the swarm itself. They read recent pheromones
    (or, in --dry mode, synthesize them from the phalanx deployment's
    in-memory findings) and emit civic observations.

    `phalanx_results` is required when dry=True; the citizens use
    the in-memory phalanx findings rather than querying the DB.
    When dry=False, citizens query the Pheromone table directly.
    """
    if root is None:
        root = _project_root()

    # Build the recent_pheromones list for citizens.
    if dry and phalanx_results is not None:
        recent = _synthesize_recent_pheromones_from_phalanx_results(phalanx_results)
    elif not dry:
        recent = _fetch_recent_pheromones_from_db(hours=72.0)
    else:
        recent = []

    # R1 (): citizens FILTER heartbeats from their input.
    # Heartbeats are operator-facing proof-of-life; citizens
    # interpret real signal, not life-signs. Without this filter
    # the cross-phalanx analyses (Plebs forum imbalance, Eques
    # correlations, Augur convergence) would be diluted by the
    # 18 heartbeats deposited per pass.
    recent = [r for r in recent if not _is_heartbeat(r)]

    results: list[CitizenResult] = []
    for CitizenCls in ALL_DEMES:
        try:
            citizen = CitizenCls(root)
            findings = citizen.observe(recent)
        except Exception as exc:
            citizen = _make_failed_citizen(CitizenCls, exc)
            findings = [DemeFinding(
                node_id=f"citizen:{CitizenCls.NAME}",
                intensity=4.0,
                kind="curious",
                observation_type="citizen_failure",
                evidence={
                    "message": "citizen observe raised an exception",
                    "exception_type": type(exc).__name__,
                    "exception_text": str(exc)[:240],
                },
            )]
        results.append((citizen, findings))
    if not dry:
        _deposit_citizen_results(results)
    return results


def run_swarm(
    root: pathlib.Path | None = None,
    dry: bool = False,
) -> tuple[list[PhalanxResult], list[CitizenResult]]:
    """Two-phase swarm deployment: phalanxs then civitas.

    Phase 1: phalanxs deploy → ants scan → ant findings collected.
    Phase 2: citizens observe the recent pheromones + corpus →
             citizens deposit civic findings.

    Returns (phalanx_results, civitas_results).
    """
    phalanx_results = run_colony(root=root, dry=dry)
    civitas_results = run_civitas(
        root=root, phalanx_results=phalanx_results, dry=dry,
    )
    return phalanx_results, civitas_results


# ── R1 heartbeats () ─────────────────────────────────────────
# Proof-of-life pheromones. Each ant in a phalanx's deploy() output
# generates one heartbeat per pass, regardless of findings count.
# The bloom can distinguish "ant ran, found nothing" from "ant
# didn't run." Demes FILTER heartbeats from their input — they
# observe real swarm signal, not the proof-of-life layer.
HEARTBEAT_INTENSITY = 0.5
HEARTBEAT_HALF_LIFE_HOURS = 24.0
HEARTBEAT_OBSERVATION_TYPE = "heartbeat"


def _build_heartbeat_finding(ant_name: str, phalanx_name: str,
                              findings_count: int) -> EyeFinding:
    """Synthesize a low-intensity heartbeat pheromone for an ant
    that just completed its scan. Authorized by the 
    100-year-architect Delphi R1."""
    return EyeFinding(
        node_id=f"ant:{ant_name}",
        intensity=HEARTBEAT_INTENSITY,
        kind="info",
        evidence={
            "observation_type": HEARTBEAT_OBSERVATION_TYPE,
            "eye": ant_name,
            "phalanx": phalanx_name,
            "findings_count": findings_count,
            "purpose": "proof-of-life; distinguishes silent-and-well from silent-and-broken",
        },
        half_life_hours=HEARTBEAT_HALF_LIFE_HOURS,
    )


def _is_heartbeat(row: dict) -> bool:
    """Demes filter these out — heartbeats are operator-facing
    proof-of-life, not signals to interpret."""
    ev = row.get("evidence") or {}
    return ev.get("observation_type") == HEARTBEAT_OBSERVATION_TYPE


def _synthesize_recent_pheromones_from_phalanx_results(
    phalanx_results: list[PhalanxResult],
) -> list[dict]:
    """For --dry mode: build a list-of-dicts representing the
    just-deposited pheromones from in-memory phalanx output.

    Heartbeats are included here (the operator-facing view) but
    filtered by `run_civitas` before citizens observe (R1 design:
    citizens shouldn't interpret proof-of-life as signal).
    """
    from datetime import datetime, timezone
    now = datetime.now(timezone.utc)
    rows: list[dict] = []
    for phalanx, eye_results in phalanx_results:
        phalanx_name = getattr(phalanx, "NAME", "(unknown)")
        for AntCls, findings in eye_results:
            # The real findings
            for f in findings:
                evidence = dict(f.evidence)
                evidence.setdefault("phalanx", phalanx_name)
                rows.append({
                    "pheromone_id": 0,
                    "deposited_at": now,
                    "deposited_by": AntCls.NAME,
                    "node_id": f.node_id,
                    "intensity": f.intensity,
                    "kind": f.kind,
                    "half_life_hours": f.half_life_hours,
                    "evidence": evidence,
                    "seed": 0,
                })
            # The heartbeat (R1 / ) — one per ant per pass
            hb = _build_heartbeat_finding(
                AntCls.NAME, phalanx_name, len(findings),
            )
            hb_ev = dict(hb.evidence)
            hb_ev.setdefault("phalanx", phalanx_name)
            rows.append({
                "pheromone_id": 0,
                "deposited_at": now,
                "deposited_by": AntCls.NAME,
                "node_id": hb.node_id,
                "intensity": hb.intensity,
                "kind": hb.kind,
                "half_life_hours": hb.half_life_hours,
                "evidence": hb_ev,
                "seed": 0,
            })
    return rows


def _fetch_recent_pheromones_from_db(hours: float) -> list[dict]:
    """Query Pheromone within the recent window. Returns [] if
    DB unavailable."""
    conn = _connect_db()
    if conn is None:
        return []
    try:
        with conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT pheromone_id, deposited_at, deposited_by,
                           node_id, intensity::float, kind,
                           half_life_hours::float, evidence, seed
                      FROM Pheromone
                     WHERE deposited_at >= NOW() - (%s || ' hours')::INTERVAL
                     ORDER BY deposited_at DESC
                    """,
                    (hours,),
                )
                cols = [c.name for c in cur.description]
                return [dict(zip(cols, row)) for row in cur.fetchall()]
    finally:
        conn.close()


def _make_failed_citizen(CitizenCls, exc):
    """Synthesize a stub Citizen record when construction fails."""
    class _FailedCitizen:
        NAME = getattr(CitizenCls, "NAME", "citizen_unknown")
        CIVITAS_CLASS = getattr(CitizenCls, "CIVITAS_CLASS", "unknown")
        DESCRIPTION = getattr(CitizenCls, "DESCRIPTION", "(failed)")
    return _FailedDeme()


def _deposit_citizen_results(results: list[CitizenResult]) -> None:
    """Write each citizen finding as one Pheromone row.

    AoR contract: `deposited_by = citizen.NAME` (not 'civitas' or
    similar). Citizen class travels in evidence JSONB as
    `civitas_class`; observation type in `observation_type`.
    """
    conn = _connect_db()
    if conn is None:
        sys.stderr.write(
            "monsters.argos.colony: no DB connection; citizens "
            "could not deposit\n"
        )
        return
    try:
        with conn:
            with conn.cursor() as cur:
                for citizen, findings in results:
                    if not findings:
                        continue
                    lock_key = abs(hash(citizen.NAME)) % (2 ** 31)
                    cur.execute(
                        "SELECT pg_advisory_xact_lock(%s)", (lock_key,)
                    )
                    seed = getattr(citizen, "seed", 0)
                    for f in findings:
                        evidence = dict(f.evidence)
                        evidence.setdefault("civitas_class", citizen.CIVITAS_CLASS)
                        evidence.setdefault("observation_type", f.observation_type)
                        cur.execute(
                            """
                            INSERT INTO Pheromone
                              (deposited_by, node_id, intensity, kind,
                               half_life_hours, evidence, seed)
                            VALUES (%s, %s, %s, %s, %s, %s, %s)
                            """,
                            (
                                citizen.NAME,
                                f.node_id,
                                f.intensity,
                                f.kind,
                                f.half_life_hours,
                                Json(evidence),
                                seed,
                            ),
                        )
    finally:
        conn.close()


def _make_failed_phalanx(PhalanxCls, root, exc):
    """Synthesize a stub Phalanx record when construction fails."""
    class _FailedPhalanx:
        NAME = PhalanxCls.NAME if hasattr(PhalanxCls, "NAME") else "phalanx_unknown"
        DOMAIN = getattr(PhalanxCls, "DOMAIN", "unknown")
        LEGATUS = getattr(PhalanxCls, "LEGATUS", "(failed)")
    return _FailedPhalanx()


class _PlaceholderFailureEye:
    """Synthetic ant used only to label a phalanx-deploy failure's
    deposit. Not a real Eye subclass; never instantiated by user code."""
    NAME = "phalanx_deploy_failure"
    seed = 0


def _deposit_phalanx_results(results: list[PhalanxResult]) -> None:
    """Write each finding as one Pheromone row.

    AoR contract: `deposited_by = ant.NAME`, NOT the phalanx name.
    Phalanx identity travels in evidence JSONB as `"phalanx"`.

    Per-ant advisory lock keyspace = hash(ant.NAME) % 2^31 — same
    pattern as ; not changed by phalanx introduction.
    """
    conn = _connect_db()
    if conn is None:
        sys.stderr.write(
            "monsters.argos.colony: no DB connection (set OLYMPUS_DB_* "
            "env vars and ensure psycopg2 is installed); use --dry "
            "to scan without writing\n"
        )
        return
    try:
        with conn:
            with conn.cursor() as cur:
                for phalanx, eye_results in results:
                    for AntCls, findings in eye_results:
                        # Per-ant advisory lock
                        lock_key = abs(hash(AntCls.NAME)) % (2 ** 31)
                        cur.execute(
                            "SELECT pg_advisory_xact_lock(%s)", (lock_key,)
                        )
                        ant_instance = (
                            AntCls(phalanx.root)
                            if hasattr(AntCls, "__init__")
                            and AntCls is not _PlaceholderFailureEye
                            else AntCls
                        )
                        seed = getattr(ant_instance, "seed", 0)
                        # Real findings first
                        for f in findings:
                            evidence = dict(f.evidence)
                            evidence.setdefault("phalanx", phalanx.NAME)
                            cur.execute(
                                """
                                INSERT INTO Pheromone
                                  (deposited_by, node_id, intensity, kind,
                                   half_life_hours, evidence, seed)
                                VALUES (%s, %s, %s, %s, %s, %s, %s)
                                """,
                                (
                                    AntCls.NAME,
                                    f.node_id,
                                    f.intensity,
                                    f.kind,
                                    f.half_life_hours,
                                    Json(evidence),
                                    seed,
                                ),
                            )
                        # R1 (): proof-of-life heartbeat per ant
                        # per pass, regardless of findings count.
                        # Heartbeat fades fast (24h half-life) so it
                        # serves the OPERATOR view, not long-term
                        # accumulation.
                        hb = _build_heartbeat_finding(
                            AntCls.NAME, phalanx.NAME, len(findings),
                        )
                        hb_ev = dict(hb.evidence)
                        hb_ev.setdefault("phalanx", phalanx.NAME)
                        cur.execute(
                            """
                            INSERT INTO Pheromone
                              (deposited_by, node_id, intensity, kind,
                               half_life_hours, evidence, seed)
                            VALUES (%s, %s, %s, %s, %s, %s, %s)
                            """,
                            (
                                AntCls.NAME,
                                hb.node_id,
                                hb.intensity,
                                hb.kind,
                                hb.half_life_hours,
                                Json(hb_ev),
                                seed,
                            ),
                        )
    finally:
        conn.close()


def main() -> int:
    p = argparse.ArgumentParser(prog="monsters.argos.colony")
    p.add_argument("--dry", action="store_true",
                   help="scan + print findings; no DB writes")
    p.add_argument("--list", action="store_true",
                   help="list phalanxs + citizens + tactics")
    p.add_argument("--json", action="store_true",
                   help="JSON output (default: human-readable)")
    p.add_argument("--swarm", action="store_true",
                   help="full two-phase commander deployment (phalanxs + civitas)")
    #  hybrid-swarm tier (Delphi 2026-05-14-hybrid-swarm-mirai-pattern)
    p.add_argument("--soldiers", action="store_true",
                   help="run the soldier-tier tight-loop colony (lightweight, "
                        "high-cadence, aggregated deposits)")
    p.add_argument("--hybrid", action="store_true",
                   help="run BOTH tiers: commanders ONCE + soldiers for --duration")
    p.add_argument("--duration", type=float, default=30.0,
                   help="soldier-tier run duration in seconds (default: 30)")
    p.add_argument("--cycle-interval", type=float, default=1.0,
                   help="soldier per-cycle interval in seconds (default: 1.0)")
    args = p.parse_args()

    if args.list:
        print("Registered phalanxs:")
        for PhalanxCls in ALL_PHALANGES:
            tactic = PhalanxCls.TACTIC.tactic.value
            ants = ", ".join(a.NAME for a in PhalanxCls.ANTS)
            print(f"  {PhalanxCls.NAME:22s} {tactic:14s} {PhalanxCls.LEGATUS}")
            print(f"  {'':22s} {'':14s} ants: {ants}")
        print()
        print("Registered citizens (Civitas):")
        for CitizenCls in ALL_DEMES:
            cclass = CitizenCls.CIVITAS_CLASS
            print(f"  {CitizenCls.NAME:24s} {cclass:8s} {CitizenCls.DESCRIPTION}")
        return 0

    # : --soldiers = soldier-tier only (no commanders)
    if args.soldiers and not args.hybrid:
        from monsters.argos.soldier_colony import run_soldier_colony
        summary = run_soldier_colony(
            duration_s=args.duration,
            cycle_interval_s=args.cycle_interval,
            dry=args.dry,
        )
        if args.json:
            import json as _json
            print(_json.dumps(summary, indent=2))
        else:
            print()
            print("─── Argos soldier colony () ───")
            for k, v in summary.items():
                print(f"  {k:24s} {v}")
        return 0

    # If --swarm, run both phases; otherwise just the colony (phalanxs).
    if args.swarm or args.hybrid:
        phalanx_results, civitas_results = run_swarm(dry=args.dry)
        results = phalanx_results
    else:
        results = run_colony(dry=args.dry)
        civitas_results = []

    # : --hybrid also runs the soldier tier after commanders complete
    if args.hybrid:
        from monsters.argos.soldier_colony import run_soldier_colony
        soldier_summary = run_soldier_colony(
            duration_s=args.duration,
            cycle_interval_s=args.cycle_interval,
            dry=args.dry,
        )
        if args.json:
            import json as _json
            print(_json.dumps({"soldier_summary": soldier_summary}, indent=2))
        else:
            print()
            print("─── Argos soldier tier (--hybrid) ───")
            for k, v in soldier_summary.items():
                print(f"  {k:24s} {v}")

    if args.json:
        payload = []
        for phalanx, eye_results in results:
            payload.append({
                "phalanx": phalanx.NAME,
                "domain": phalanx.DOMAIN,
                "legatus": phalanx.LEGATUS,
                "tactic": (
                    phalanx.TACTIC.tactic.value
                    if hasattr(phalanx, "TACTIC")
                    else "(failed)"
                ),
                "ants": [
                    {
                        "eye": AntCls.NAME,
                        "findings": [
                            {
                                "node_id": f.node_id,
                                "intensity": f.intensity,
                                "kind": f.kind,
                                "half_life_hours": f.half_life_hours,
                                "evidence": f.evidence,
                            }
                            for f in findings
                        ],
                    }
                    for AntCls, findings in eye_results
                ],
            })
        print(json.dumps(payload, indent=2))
        return 0

    # Human-readable
    total_findings = sum(
        len(f) for _, eye_results in results for _, f in eye_results
    )
    deposit_word = "DRY" if args.dry else "deposited"
    print(f"Argos colony: {len(results)} phalanx(s) deployed, "
          f"{total_findings} pheromone(s) {deposit_word}")
    for phalanx, eye_results in results:
        tactic_name = (
            phalanx.TACTIC.tactic.value
            if hasattr(phalanx, "TACTIC")
            else "(failed)"
        )
        phalanx_total = sum(len(f) for _, f in eye_results)
        marker = "[silent]" if phalanx_total == 0 else f"[{phalanx_total} findings]"
        print(f"  {marker:18s} {phalanx.NAME} ({tactic_name}) — {phalanx.LEGATUS}")
        for AntCls, findings in eye_results:
            if not findings:
                continue
            for f in findings:
                print(f"      {f.kind:8s} intensity={f.intensity:.2f}  "
                      f"ant={AntCls.NAME}  node={f.node_id}")
                msg = f.evidence.get("message", "")
                if msg:
                    print(f"        → {msg}")

    if args.swarm:
        civitas_findings = sum(len(f) for _, f in civitas_results)
        print()
        print(f"Argos civitas: {len(civitas_results)} citizen(s) observed, "
              f"{civitas_findings} civic finding(s) {deposit_word}")
        for citizen, findings in civitas_results:
            cclass = getattr(citizen, "CIVITAS_CLASS", "?")
            marker = "[silent]" if not findings else f"[{len(findings)} findings]"
            print(f"  {marker:18s} {citizen.NAME} ({cclass}) — "
                  f"{getattr(citizen, 'DESCRIPTION', '')}")
            for f in findings:
                print(f"      {f.kind:8s} intensity={f.intensity:.2f}  "
                      f"obs={f.observation_type}  node={f.node_id}")
                msg = f.evidence.get("message", "")
                if msg:
                    print(f"        → {msg}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
