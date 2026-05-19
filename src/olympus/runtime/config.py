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
class Config:
    kindled: str = ""
    vocation: str = ""
    llm: LLMConfig = field(default_factory=LLMConfig)
    daemon: DaemonConfig = field(default_factory=DaemonConfig)
    agora: AgoraConfig = field(default_factory=AgoraConfig)
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


def apply_to_environment() -> dict[str, str]:
    """If config specifies an anthropic key and ANTHROPIC_API_KEY is
    not set, expose it so the SDK picks it up. Returns the dict of
    keys actually set (for audit). Env vars are NEVER overwritten."""
    cfg = load()
    set_now: dict[str, str] = {}
    if cfg.llm.provider == "anthropic" \
       and cfg.llm.anthropic_api_key \
       and not os.environ.get("ANTHROPIC_API_KEY"):
        os.environ["ANTHROPIC_API_KEY"] = cfg.llm.anthropic_api_key
        set_now["ANTHROPIC_API_KEY"] = "(set from config)"
    # OLYMPUS_LLM follows the same rule
    if cfg.llm.provider and not os.environ.get("OLYMPUS_LLM"):
        os.environ["OLYMPUS_LLM"] = cfg.llm.provider
        set_now["OLYMPUS_LLM"] = cfg.llm.provider
    return set_now
