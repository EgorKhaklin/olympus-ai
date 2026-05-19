"""Tiresias — the blind prophet of Thebes who saw what others could not.

In myth: Tiresias was struck blind by Hera (or, in other versions,
Athena) but granted the gift of true sight. Where Apollo predicted
*forward*, Tiresias *revealed* — he saw what was already happening
that the sighted could not perceive.

In Olympus, Tiresias is the **ground-truth tracker for agent claims**.
Where Apollo forms falsifiable predictions before their horizons,
Tiresias persists *claims made now* and *verifies them when ground
truth arrives*. The result is **real calibration**: per-claimant
Brier score, hit rate by confidence bucket — not just average
confidence.

Re-arguing the prior refusal. The missing-figures arc refused Tiresias
on AP8 ("overlaps with Apollo"). The new role is *post-hoc verification
of agent claims against realized outcomes* — distinct from Apollo's
pre-horizon prediction formulation. Apollo PREDICTS; Tiresias REVEALS.

Per Delphi 2026-05-18-akropolis-arc.md.
"""
from __future__ import annotations

import datetime
import uuid
from dataclasses import dataclass, field, asdict
from typing import Any

from olympus.primordials.nyx import Nyx
from olympus.titans.mnemosyne import mnemosyne


@dataclass
class Claim:
    """One claim awaiting verification."""
    claim_id: str
    claimant: str          # e.g., "agent:hephaestus" or "heuristic:momus"
    claim: str             # human-readable claim text
    expected: str          # what the claimant expects to be observed
    confidence: float      # 0..1
    claimed_at: str = ""
    verified_at: str = ""
    observed: str = ""
    outcome: str = "pending"  # 'pending' | 'hit' | 'miss' | 'inconclusive'

    def __post_init__(self) -> None:
        if not self.claimed_at:
            self.claimed_at = Nyx.now().isoformat()


@dataclass
class Verification:
    """One verification event."""
    claim_id: str
    outcome: str           # 'hit' | 'miss' | 'inconclusive'
    observed: str
    verified_at: str = ""

    def __post_init__(self) -> None:
        if not self.verified_at:
            self.verified_at = Nyx.now().isoformat()


@dataclass
class CalibrationReport:
    """Per-claimant calibration. Brier-style scoring + bucket hit rates."""
    claimant: str
    total_claims: int
    verified_claims: int
    hits: int
    misses: int
    inconclusive: int
    brier_score: float       # mean squared error of confidence vs outcome
    avg_confidence: float
    hit_rate: float
    bucket_hit_rate: dict[str, float] = field(default_factory=dict)


class Tiresias:
    """The blind prophet. Records claims; verifies them when truth
    arrives; produces real calibration."""

    def claim(self, *,
              claimant: str,
              claim: str,
              expected: str,
              confidence: float) -> str:
        """Persist a claim. Returns a claim_id the caller MUST keep
        in order to verify later."""
        if not (0.0 <= confidence <= 1.0):
            raise ValueError(f"confidence must be in [0,1], got {confidence}")
        cid = f"t-{uuid.uuid4().hex[:16]}"
        record = Claim(
            claim_id=cid, claimant=claimant, claim=claim,
            expected=expected, confidence=confidence,
        )
        mnemosyne.remember(
            kind="tiresias.claim",
            actor=f"tiresias:{claimant}",
            summary=(f"claim {cid[:12]}: {claim[:80]} "
                     f"(conf={confidence:.2f})"),
            **asdict(record),
        )
        return cid

    def verify(self, claim_id: str, *,
               observed: str,
               hit: bool | None = None) -> Verification:
        """Record what was actually observed. `hit` can be:
          True  → observed matches expected (claim correct)
          False → observed contradicts expected (claim wrong)
          None  → ambiguous (substring match against expected — used
                  as fallback)
        """
        record = self._find_claim(claim_id)
        if record is None:
            raise KeyError(f"no claim with id {claim_id!r}")

        if hit is None:
            # Fallback: substring match. Caller is encouraged to pass
            # an explicit hit=True/False.
            expected_low = (record.expected or "").lower()
            observed_low = (observed or "").lower()
            if expected_low and expected_low in observed_low:
                outcome = "hit"
            elif expected_low and observed_low and \
                 (observed_low not in expected_low):
                outcome = "miss"
            else:
                outcome = "inconclusive"
        else:
            outcome = "hit" if hit else "miss"

        v = Verification(claim_id=claim_id, outcome=outcome,
                          observed=observed)
        mnemosyne.remember(
            kind="tiresias.verification",
            actor=f"tiresias:{record.claimant}",
            summary=(f"verify {claim_id[:12]}: {outcome} — "
                     f"observed: {observed[:80]}"),
            **asdict(v),
            claimant=record.claimant,
            confidence_at_claim=record.confidence,
        )
        return v

    def calibration(self, claimant: str | None = None
                     ) -> CalibrationReport | dict[str, CalibrationReport]:
        """Per-claimant calibration. With no claimant, returns a dict
        of all claimants."""
        if claimant is None:
            # Discover all claimants from claim records
            claimants: set[str] = set()
            for m in mnemosyne.recall("tiresias.claim"):
                c = (m.body or {}).get("claimant", "")
                if c:
                    claimants.add(c)
            return {c: self.calibration(c) for c in sorted(claimants)}

        # Build the claimant's claim map keyed by id
        claims: dict[str, Claim] = {}
        for m in mnemosyne.recall("tiresias.claim"):
            body = m.body or {}
            if body.get("claimant") != claimant:
                continue
            cid = body.get("claim_id", "")
            if cid:
                try:
                    claims[cid] = Claim(
                        claim_id=cid, claimant=claimant,
                        claim=body.get("claim", ""),
                        expected=body.get("expected", ""),
                        confidence=float(body.get("confidence", 0.0)),
                        claimed_at=body.get("claimed_at", m.remembered_at),
                    )
                except (TypeError, ValueError):
                    continue

        # Overlay verifications
        for m in mnemosyne.recall("tiresias.verification"):
            body = m.body or {}
            if body.get("claimant") != claimant:
                continue
            cid = body.get("claim_id", "")
            c = claims.get(cid)
            if c is None:
                continue
            c.outcome = body.get("outcome", "pending")
            c.observed = body.get("observed", "")
            c.verified_at = body.get("verified_at", m.remembered_at)

        total = len(claims)
        verified = [c for c in claims.values() if c.outcome != "pending"]
        hits = [c for c in verified if c.outcome == "hit"]
        misses = [c for c in verified if c.outcome == "miss"]
        inconclusive = [c for c in verified
                         if c.outcome == "inconclusive"]
        # Brier: MSE of confidence vs (1 if hit else 0); skip inconclusive
        decisive = hits + misses
        if decisive:
            brier = sum((c.confidence -
                          (1.0 if c.outcome == "hit" else 0.0)) ** 2
                         for c in decisive) / len(decisive)
            avg_conf = sum(c.confidence for c in decisive) / len(decisive)
            hit_rate = len(hits) / len(decisive)
        else:
            brier = 0.0
            avg_conf = 0.0
            hit_rate = 0.0

        # Bucket hit rates: 0.0–0.2, 0.2–0.4, …, 0.8–1.0
        buckets: dict[str, list[int]] = {
            "0.0-0.2": [0, 0], "0.2-0.4": [0, 0], "0.4-0.6": [0, 0],
            "0.6-0.8": [0, 0], "0.8-1.0": [0, 0],
        }
        for c in decisive:
            if c.confidence < 0.2:
                key = "0.0-0.2"
            elif c.confidence < 0.4:
                key = "0.2-0.4"
            elif c.confidence < 0.6:
                key = "0.4-0.6"
            elif c.confidence < 0.8:
                key = "0.6-0.8"
            else:
                key = "0.8-1.0"
            buckets[key][0] += (1 if c.outcome == "hit" else 0)
            buckets[key][1] += 1
        bucket_hit_rate = {
            k: (v[0] / v[1]) if v[1] > 0 else 0.0
            for k, v in buckets.items()
        }

        return CalibrationReport(
            claimant=claimant,
            total_claims=total,
            verified_claims=len(verified),
            hits=len(hits),
            misses=len(misses),
            inconclusive=len(inconclusive),
            brier_score=brier,
            avg_confidence=avg_conf,
            hit_rate=hit_rate,
            bucket_hit_rate=bucket_hit_rate,
        )

    def open_claims(self, claimant: str | None = None) -> list[Claim]:
        """All claims that have not yet been verified."""
        out: list[Claim] = []
        verified_ids = {
            (m.body or {}).get("claim_id")
            for m in mnemosyne.recall("tiresias.verification")
        }
        for m in mnemosyne.recall("tiresias.claim"):
            body = m.body or {}
            cid = body.get("claim_id", "")
            if cid in verified_ids:
                continue
            if claimant is not None and body.get("claimant") != claimant:
                continue
            try:
                out.append(Claim(
                    claim_id=cid,
                    claimant=body.get("claimant", ""),
                    claim=body.get("claim", ""),
                    expected=body.get("expected", ""),
                    confidence=float(body.get("confidence", 0.0)),
                    claimed_at=body.get("claimed_at", m.remembered_at),
                ))
            except (TypeError, ValueError):
                continue
        return out

    @staticmethod
    def _find_claim(claim_id: str) -> Claim | None:
        for m in mnemosyne.recall("tiresias.claim"):
            body = m.body or {}
            if body.get("claim_id") == claim_id:
                try:
                    return Claim(
                        claim_id=claim_id,
                        claimant=body.get("claimant", ""),
                        claim=body.get("claim", ""),
                        expected=body.get("expected", ""),
                        confidence=float(body.get("confidence", 0.0)),
                        claimed_at=body.get("claimed_at", m.remembered_at),
                    )
                except (TypeError, ValueError):
                    return None
        return None


tiresias = Tiresias()
