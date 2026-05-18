"""Pythia — priestess of Delphi, channel for Apollo's oracle.

In myth: Pythia sat above the chasm at Delphi and delivered Apollo's
prophecies. She was the bridge through which external knowledge — the
god's voice — entered the mortal world.

In Olympus, Pythia is the **external knowledge bridge**. She uses
`urllib` (stdlib only) to query the world and brings findings back
under the Mnemosyne audit-of-record discipline. Two channels:

  - `ask_github(query, ...)` — GitHub code/repo search via REST API
  - `ask_web(url)`            — generic URL fetch with size/time caps

She is **not an LLM**. She does not interpret, summarize, or generate;
she fetches and records. Interpretation is Hephaestus's job; ratification
is Zeus's. Pythia provides raw external evidence into the same channel
that internal evidence (Hydra findings, Argos pheromones) already uses.

Every consultation produces a `pythia.consultation` record in Mnemosyne
with full query, response status, size, head bytes, timing — so that
*"what did the system learn from outside, and when"* is reconstructable
without joining elsewhere (S8).

Network discipline:
  - 10s timeout per request (configurable)
  - 256 KB response cap (configurable; truncates and flags)
  - User-Agent identifies as Olympus
  - No credentials; rate-limited but works against public APIs

Per Delphi 2026-05-18-recursion-arc.md.
"""
from __future__ import annotations

import json
import time
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass, field, asdict
from typing import Any

from olympus.primordials.nyx import Nyx
from olympus.titans.mnemosyne import mnemosyne


@dataclass
class Consultation:
    """One Pythia consultation — request and response, captured."""
    channel: str                          # 'github' | 'web'
    query: str                            # the request (URL or search string)
    url: str                              # the actual URL fetched
    status: int                           # HTTP status
    content_type: str = ""
    bytes_received: int = 0
    truncated: bool = False
    head: str = ""                        # first chunk of body (capped)
    error: str = ""
    elapsed_ms: float = 0.0
    consulted_at: str = ""

    def __post_init__(self) -> None:
        if not self.consulted_at:
            self.consulted_at = Nyx.now().isoformat()


@dataclass
class GitHubFinding:
    """One result from a GitHub search — name, url, description."""
    repo: str
    url: str
    description: str = ""
    score: float = 0.0


@dataclass
class GitHubReport:
    query: str
    total_count: int
    findings: list[GitHubFinding] = field(default_factory=list)
    consulted_at: str = ""
    consultation: Consultation | None = None


# ─────────────────────────────────────────────────────────
# Network primitives — stdlib only
# ─────────────────────────────────────────────────────────


_USER_AGENT = "Olympus-Pythia/1.0 (+https://github.com/EgorKhaklin/olympus-ai)"
_DEFAULT_TIMEOUT_SECONDS = 10.0
_DEFAULT_MAX_BYTES = 256 * 1024  # 256 KB cap; head bytes only


def _fetch(url: str, *,
           timeout_seconds: float = _DEFAULT_TIMEOUT_SECONDS,
           max_bytes: int = _DEFAULT_MAX_BYTES,
           accept: str | None = None) -> Consultation:
    """One HTTP GET. Always returns a Consultation; never raises."""
    headers = {"User-Agent": _USER_AGENT}
    if accept:
        headers["Accept"] = accept
    started = time.perf_counter()
    consultation = Consultation(channel="web", query=url, url=url, status=0)
    try:
        req = urllib.request.Request(url, headers=headers, method="GET")
        with urllib.request.urlopen(req, timeout=timeout_seconds) as resp:
            consultation.status = resp.status
            consultation.content_type = resp.headers.get("Content-Type", "")
            body = resp.read(max_bytes + 1)
            consultation.truncated = len(body) > max_bytes
            if consultation.truncated:
                body = body[:max_bytes]
            consultation.bytes_received = len(body)
            try:
                consultation.head = body.decode("utf-8", errors="replace")
            except Exception:  # noqa: BLE001
                consultation.head = repr(body[:200])
    except urllib.error.HTTPError as exc:
        consultation.status = exc.code
        consultation.error = f"HTTPError {exc.code}: {exc.reason}"
    except urllib.error.URLError as exc:
        consultation.error = f"URLError: {exc.reason}"
    except Exception as exc:  # noqa: BLE001
        consultation.error = f"{type(exc).__name__}: {exc}"
    consultation.elapsed_ms = (time.perf_counter() - started) * 1000.0
    return consultation


# ─────────────────────────────────────────────────────────
# Pythia
# ─────────────────────────────────────────────────────────


class Pythia:
    """The priestess. Channels external knowledge into the substrate."""

    GITHUB_SEARCH_BASE = "https://api.github.com/search/repositories"

    def ask_github(self, query: str, *,
                   per_page: int = 5,
                   sort: str = "stars",
                   timeout_seconds: float = _DEFAULT_TIMEOUT_SECONDS,
                   ) -> GitHubReport:
        """Search GitHub repositories. Returns top N by stars by default."""
        params = {
            "q": query,
            "per_page": str(max(1, min(per_page, 30))),
            "sort": sort,
            "order": "desc",
        }
        url = f"{self.GITHUB_SEARCH_BASE}?{urllib.parse.urlencode(params)}"
        consultation = _fetch(url, timeout_seconds=timeout_seconds,
                              accept="application/vnd.github+json")
        consultation.channel = "github"
        consultation.query = query

        report = GitHubReport(
            query=query, total_count=0,
            consulted_at=consultation.consulted_at,
            consultation=consultation,
        )

        if consultation.status == 200 and consultation.head:
            try:
                payload = json.loads(consultation.head)
                report.total_count = int(payload.get("total_count", 0))
                for item in payload.get("items", [])[:per_page]:
                    report.findings.append(GitHubFinding(
                        repo=item.get("full_name", ""),
                        url=item.get("html_url", ""),
                        description=(item.get("description") or "")[:200],
                        score=float(item.get("stargazers_count", 0)),
                    ))
            except (json.JSONDecodeError, TypeError, ValueError) as exc:
                consultation.error = (consultation.error
                                      + f" parse: {exc}").strip()

        self._record(consultation, extra={
            "channel": "github",
            "github_query": query,
            "total_count": report.total_count,
            "findings_returned": len(report.findings),
            "top_repos": [f.repo for f in report.findings[:3]],
        })
        return report

    def ask_web(self, url: str, *,
                timeout_seconds: float = _DEFAULT_TIMEOUT_SECONDS,
                ) -> Consultation:
        """Fetch any URL. Returns a Consultation."""
        consultation = _fetch(url, timeout_seconds=timeout_seconds)
        consultation.channel = "web"
        self._record(consultation, extra={
            "channel": "web",
            "url": url,
        })
        return consultation

    def consultations(self, limit: int = 50) -> list[Consultation]:
        """Recent consultations, newest first."""
        out: list[Consultation] = []
        for m in mnemosyne.recall("pythia.consultation"):
            body = m.body or {}
            try:
                out.append(Consultation(
                    channel=body.get("channel", ""),
                    query=body.get("query", ""),
                    url=body.get("url", ""),
                    status=int(body.get("status", 0)),
                    content_type=body.get("content_type", ""),
                    bytes_received=int(body.get("bytes_received", 0)),
                    truncated=bool(body.get("truncated", False)),
                    head=body.get("head", "")[:200],
                    error=body.get("error", ""),
                    elapsed_ms=float(body.get("elapsed_ms", 0.0)),
                    consulted_at=body.get("consulted_at",
                                          m.remembered_at),
                ))
            except (TypeError, ValueError):
                continue
        return list(reversed(out))[:limit]

    # ─────────────────────────────────────────────────────────
    # Internal — record to Mnemosyne; head bytes capped further to
    # avoid bloating the JSONL.
    # ─────────────────────────────────────────────────────────

    @staticmethod
    def _record(consultation: Consultation,
                extra: dict[str, Any] | None = None) -> None:
        body = asdict(consultation)
        body["head"] = body.get("head", "")[:2048]
        if extra:
            body.update(extra)
        summary = (f"{consultation.channel}: {consultation.query[:60]} "
                   f"→ {consultation.status} "
                   f"({consultation.bytes_received}B "
                   f"in {consultation.elapsed_ms:.0f}ms)")
        if consultation.error:
            summary += f" — {consultation.error[:80]}"
        mnemosyne.remember(
            kind="pythia.consultation",
            actor="pythia",
            summary=summary,
            **body,
        )


pythia = Pythia()
