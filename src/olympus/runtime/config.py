"""olympus.runtime.config — operator configuration at state/config.json.

Per Delphi 2026-05-18-xenia-arc.md.

This is the *single* file that holds operator setup choices. Env vars
override file values everywhere — operators who use env vars are
unaffected. The file is additive convenience for the setup wizard
and the web UI.

The config file lives at `state/config.json` (state/ is gitignored).
**API keys stored here are plaintext;** the operator is responsible
for filesystem-level security. Future arcs may add OS-keychain
integration. This is documented so the operator isn't surprised.
"""
from __future__ import annotations

import json
import os
from dataclasses import dataclass, field, asdict
from typing import Any

from olympus.primordials.gaia import root


CONFIG_PATH = "state/config.json"


@dataclass
class LLMConfig:
    provider: str = ""                # 'echo' | 'anthropic' | ''
    anthropic_api_key: str = ""       # only present if operator chose anthropic


@dataclass
class DaemonConfig:
    installed: bool = False
    interval_seconds: int = 600


@dataclass
class AgoraConfig:
    port: int = 8765
    host: str = "127.0.0.1"


@dataclass
class ArgosConfig:
    """Per Delphi 2026-05-19-argos-eyes-arc.md.

    `watches` is a list of dicts (kept as raw dicts here for
    forward-compatibility; FilesystemEye does the strict parsing).
    Each entry:
      {id, path, glob?, action?, enabled?, max_files?}
    """
    watches: list[dict[str, Any]] = field(default_factory=list)


@dataclass
class ChronosConfig:
    """Per Delphi 2026-05-19-chronos-arc.md.

    `rituals` is a list of dicts (kept as raw dicts here for
    forward-compatibility; Chronos does the strict parsing via
    RitualSpec.validate). Each entry:
      {id, when, do, enabled?, min_interval_seconds?}
    """
    rituals: list[dict[str, Any]] = field(default_factory=list)


@dataclass
class BudgetConfig:
    """Per Delphi 2026-05-19-plutus-budget-arc.md.

    Operator-declared LLM spend ceilings. All thresholds optional;
    `enabled=False` (default) means no enforcement. Breach refuses
    new LLM calls until operator acknowledges; Pan is NOT involved."""
    enabled: bool = False
    daily_usd: float = 0.0
    weekly_usd: float = 0.0
    monthly_usd: float = 0.0
    warn_at_pct: float = 80.0


@dataclass
class PlutusConfig:
    budget: BudgetConfig = field(default_factory=BudgetConfig)


@dataclass
class Config:
    kindled: str = ""
    vocation: str = ""
    llm: LLMConfig = field(default_factory=LLMConfig)
    daemon: DaemonConfig = field(default_factory=DaemonConfig)
    agora: AgoraConfig = field(default_factory=AgoraConfig)
    argos: ArgosConfig = field(default_factory=ArgosConfig)
    chronos: ChronosConfig = field(default_factory=ChronosConfig)
    plutus: PlutusConfig = field(default_factory=PlutusConfig)
    setup_completed_at: str = ""
    version: str = ""


# ─────────────────────────────────────────────────────────
# Load / save
# ─────────────────────────────────────────────────────────


def _path():
    return root.child(*CONFIG_PATH.split("/"))


def load() -> Config:
    """Read state/config.json. Returns a default Config if missing or
    malformed (never raises)."""
    path = _path()
    if not path.exists():
        return Config()
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return Config()
    cfg = Config()
    cfg.kindled = str(raw.get("kindled", ""))
    cfg.vocation = str(raw.get("vocation", ""))
    cfg.setup_completed_at = str(raw.get("setup_completed_at", ""))
    cfg.version = str(raw.get("version", ""))
    llm = raw.get("llm") or {}
    cfg.llm.provider = str(llm.get("provider", ""))
    cfg.llm.anthropic_api_key = str(llm.get("anthropic_api_key", ""))
    daemon = raw.get("daemon") or {}
    cfg.daemon.installed = bool(daemon.get("installed", False))
    cfg.daemon.interval_seconds = int(daemon.get("interval_seconds", 600))
    agora = raw.get("agora") or {}
    cfg.agora.port = int(agora.get("port", 8765))
    cfg.agora.host = str(agora.get("host", "127.0.0.1"))
    argos = raw.get("argos") or {}
    watches_raw = argos.get("watches") or []
    if isinstance(watches_raw, list):
        cfg.argos.watches = [w for w in watches_raw if isinstance(w, dict)]
    chronos = raw.get("chronos") or {}
    rituals_raw = chronos.get("rituals") or []
    if isinstance(rituals_raw, list):
        cfg.chronos.rituals = [r for r in rituals_raw if isinstance(r, dict)]
    plutus = raw.get("plutus") or {}
    budget = plutus.get("budget") or {}
    if isinstance(budget, dict):
        cfg.plutus.budget.enabled = bool(budget.get("enabled", False))
        try:
            cfg.plutus.budget.daily_usd = float(budget.get("daily_usd", 0.0))
            cfg.plutus.budget.weekly_usd = float(budget.get("weekly_usd", 0.0))
            cfg.plutus.budget.monthly_usd = float(budget.get("monthly_usd", 0.0))
            cfg.plutus.budget.warn_at_pct = float(
                budget.get("warn_at_pct", 80.0))
        except (TypeError, ValueError):
            pass
    return cfg


def save(cfg: Config) -> None:
    """Persist Config to state/config.json. Pretty-printed JSON for
    operator readability."""
    path = _path()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(asdict(cfg), indent=2, default=str) + "\n",
        encoding="utf-8",
    )


def exists() -> bool:
    """True iff state/config.json exists (operator has run setup)."""
    return _path().exists()


# ─────────────────────────────────────────────────────────
# Effective values (env-var OVERRIDES config; safe defaults)
# ─────────────────────────────────────────────────────────


def effective_llm_provider() -> str:
    """Returns the active LLM provider name. Order:
      1. OLYMPUS_LLM env var (operator's explicit choice)
      2. state/config.json::llm.provider
      3. 'echo' (safe default — no network)
    """
    env = os.environ.get("OLYMPUS_LLM", "").strip().lower()
    if env:
        return env
    cfg = load()
    if cfg.llm.provider:
        return cfg.llm.provider.lower()
    return "echo"


def effective_anthropic_api_key() -> str | None:
    """Resolve the Anthropic API key in priority order. Per Delphi
    2026-05-19-hades-arc.md:

      1. ANTHROPIC_API_KEY env var (always wins)
      2. Hades keychain (`hades.retrieve("anthropic_api_key")`)
      3. state/config.json::llm.anthropic_api_key (legacy plaintext;
         emits a one-line deprecation warning to stderr)
      4. None
    """
    env_val = os.environ.get("ANTHROPIC_API_KEY")
    if env_val:
        return env_val
    # Try Hades (OS keychain)
    try:
        from olympus.olympians.hades import hades, PLAINTEXT_SENTINEL
        kc_val = hades.retrieve("anthropic_api_key")
        if kc_val:
            return kc_val
    except Exception:  # noqa: BLE001
        PLAINTEXT_SENTINEL = "(in-hades)"  # type: ignore[assignment]
    # Fall back to plaintext config (legacy)
    cfg = load()
    legacy = cfg.llm.anthropic_api_key
    if legacy and legacy != PLAINTEXT_SENTINEL:
        import sys as _sys
        _sys.stderr.write(
            "[olympus.config] anthropic_api_key is in plaintext "
            "state/config.json; run `invoke vault migrate` to move "
            "it to the OS keychain.\n"
        )
        return legacy
    return None


def migrate_plaintext_to_hades() -> dict[str, Any]:
    """One-shot: if state/config.json holds a plaintext anthropic key
    that looks real (≥ 20 chars, starts with 'sk-'), deposit to Hades
    and replace the config field with the sentinel.

    Idempotent: re-running is safe. Returns {migrated, where, reason}."""
    cfg = load()
    legacy = cfg.llm.anthropic_api_key or ""
    try:
        from olympus.olympians.hades import (
            hades, PLAINTEXT_SENTINEL,
        )
    except Exception as exc:  # noqa: BLE001
        return {"migrated": False, "where": "plaintext",
                "reason": f"hades unavailable: {exc}"}
    if not legacy or legacy == PLAINTEXT_SENTINEL:
        return {"migrated": False, "where": "already-migrated-or-empty",
                "reason": "nothing to migrate"}
    if not (legacy.startswith("sk-") and len(legacy) >= 20):
        return {"migrated": False, "where": "plaintext",
                "reason": "value doesn't look like a real key; "
                          "refusing to migrate"}
    if not hades.available():
        return {"migrated": False, "where": "plaintext",
                "reason": "no keyring backend available on this platform"}
    hades.deposit("anthropic_api_key", legacy)
    cfg.llm.anthropic_api_key = PLAINTEXT_SENTINEL
    save(cfg)
    return {"migrated": True, "where": "keychain",
            "reason": f"deposited to {hades.backend_name()}; "
                      f"config.json sentinel'd"}


def apply_to_environment() -> dict[str, str]:
    """If config specifies an anthropic key and ANTHROPIC_API_KEY is
    not set, expose it so the SDK picks it up. Returns the dict of
    keys actually set (for audit). Env vars are NEVER overwritten.

    Per Delphi 2026-05-19-hades-arc.md: key resolution goes through
    `effective_anthropic_api_key()` so Hades is honored before legacy
    plaintext."""
    cfg = load()
    set_now: dict[str, str] = {}
    if cfg.llm.provider == "anthropic" \
       and not os.environ.get("ANTHROPIC_API_KEY"):
        key = effective_anthropic_api_key()
        if key:
            os.environ["ANTHROPIC_API_KEY"] = key
            # Where did we read from? (kept generic for the audit dict
            # — full detail is in hades.event records)
            set_now["ANTHROPIC_API_KEY"] = "(resolved by effective_*)"
    # OLYMPUS_LLM follows the same rule
    if cfg.llm.provider and not os.environ.get("OLYMPUS_LLM"):
        os.environ["OLYMPUS_LLM"] = cfg.llm.provider
        set_now["OLYMPUS_LLM"] = cfg.llm.provider
    return set_now
