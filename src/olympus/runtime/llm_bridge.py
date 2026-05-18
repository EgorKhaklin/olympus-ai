"""olympus.runtime.llm_bridge — pluggable LLM provider interface.

Per Delphi 2026-05-18-oikoumene-arc.md.

This module is the **one place** in Olympus that talks to an external
LLM. Every other module that wants reasoning power calls
`bridge().call(...)` — they do not import any provider SDK directly.
This keeps the substrate provider-agnostic, makes tests deterministic
(via EchoBridge), and records every LLM call to Mnemosyne for S8
reconstructability.

Two built-in bridges:

  - **AnthropicBridge**: real LLM calls via the official `anthropic`
    SDK using Claude Opus 4.7 with adaptive thinking. Streams long
    responses via `.get_final_message()`.
  - **EchoBridge**: deterministic stub. Returns structured echo data.
    Used by tests; also the safe default when no provider is set.

Selection via env var:
  OLYMPUS_LLM=anthropic  → AnthropicBridge (requires `pip install
                           anthropic` + ANTHROPIC_API_KEY)
  OLYMPUS_LLM=echo (default) → EchoBridge

Plugins can register additional bridges via the
`olympus.llm_bridges` entry-point group.
"""
from __future__ import annotations

import hashlib
import os
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field, asdict
from typing import Any

from olympus.primordials.nyx import Nyx
from olympus.titans.mnemosyne import mnemosyne


DEFAULT_MODEL = "claude-opus-4-7"
DEFAULT_MAX_TOKENS = 4096


@dataclass
class LLMResponse:
    """One LLM call's structured outcome."""
    text: str                       # the final assistant text
    bridge: str                     # which bridge handled it
    model: str = ""
    input_tokens: int = 0
    output_tokens: int = 0
    elapsed_ms: float = 0.0
    error: str = ""
    raw: dict[str, Any] = field(default_factory=dict)


# ─────────────────────────────────────────────────────────
# Bridge ABC
# ─────────────────────────────────────────────────────────


class LLMBridge(ABC):
    """The substrate's pluggable LLM interface."""

    name: str = "abstract"

    @abstractmethod
    def call(self, *, system: str, user: str,
              max_tokens: int = DEFAULT_MAX_TOKENS,
              **extra: Any) -> LLMResponse:
        """Make one call. Subclasses MUST record to Mnemosyne via
        `_record_call(...)` so the audit-of-record is preserved."""

    # ─────────────────────────────────────────────────────────
    # Shared helper — record every call to Mnemosyne (S1 + S8)
    # ─────────────────────────────────────────────────────────

    def _record_call(self, *, system: str, user: str,
                      response: LLMResponse,
                      role: str = "") -> None:
        """Persist this call. The full prompts get hashed (to keep
        Mnemosyne records small + the head bytes recorded so the
        operator can verify what was asked)."""
        prompt_hash = hashlib.sha256(
            (system + "\n\n" + user).encode("utf-8")
        ).hexdigest()
        mnemosyne.remember(
            kind="llm.call",
            actor=f"llm-bridge:{self.name}" + (f":{role}" if role else ""),
            summary=(f"{self.name} model={response.model or '-'} "
                     f"in={response.input_tokens} out={response.output_tokens} "
                     f"{response.elapsed_ms:.0f}ms"
                     + (f" ERROR={response.error[:60]}"
                        if response.error else "")),
            bridge=self.name,
            role=role,
            model=response.model,
            system_head=system[:512],
            user_head=user[:1024],
            prompt_hash=prompt_hash,
            response_head=response.text[:1024],
            response_length=len(response.text),
            input_tokens=response.input_tokens,
            output_tokens=response.output_tokens,
            elapsed_ms=response.elapsed_ms,
            error=response.error,
        )


# ─────────────────────────────────────────────────────────
# EchoBridge — deterministic stub (always available)
# ─────────────────────────────────────────────────────────


class EchoBridge(LLMBridge):
    """Deterministic stub. Returns a structured echo of the prompt.
    Used by tests; also the safe default. Never hits the network."""

    name = "echo"

    def __init__(self, *, response_template: str | None = None) -> None:
        self.response_template = response_template

    def call(self, *, system: str, user: str,
              max_tokens: int = DEFAULT_MAX_TOKENS,
              role: str = "",
              **extra: Any) -> LLMResponse:
        started = time.perf_counter()
        # Default echo: a deterministic JSON-shaped reply naming the
        # role + the first 200 chars of user prompt
        if self.response_template:
            text = self.response_template
        else:
            text = (
                f'{{"bridge":"echo","role":"{role}",'
                f'"input_chars":{len(user)},'
                f'"system_head":"{system[:80].replace(chr(10), " ")}",'
                f'"user_head":"{user[:120].replace(chr(10), " ")}"}}'
            )
        elapsed_ms = (time.perf_counter() - started) * 1000.0
        response = LLMResponse(
            text=text, bridge=self.name, model="echo-1",
            input_tokens=len(user) // 4,  # rough estimate
            output_tokens=len(text) // 4,
            elapsed_ms=elapsed_ms,
        )
        self._record_call(system=system, user=user,
                           response=response, role=role)
        return response


# ─────────────────────────────────────────────────────────
# AnthropicBridge — real calls via the official SDK
# ─────────────────────────────────────────────────────────


class AnthropicBridge(LLMBridge):
    """Real LLM calls via the Anthropic SDK. Optional dependency.

    Defaults to claude-opus-4-7 with adaptive thinking. Long requests
    use streaming via the SDK's `messages.stream()` + final_message
    helper to avoid request-timeout issues.
    """

    name = "anthropic"

    def __init__(self, *,
                 model: str = DEFAULT_MODEL,
                 client: Any | None = None) -> None:
        self.model = model
        self._client = client  # injectable for tests

    def _get_client(self) -> Any:
        if self._client is not None:
            return self._client
        try:
            from anthropic import Anthropic  # type: ignore
        except ImportError as exc:
            raise RuntimeError(
                "AnthropicBridge requires `pip install anthropic`. "
                "Either install it or set OLYMPUS_LLM=echo."
            ) from exc
        self._client = Anthropic()
        return self._client

    def call(self, *, system: str, user: str,
              max_tokens: int = DEFAULT_MAX_TOKENS,
              role: str = "",
              **extra: Any) -> LLMResponse:
        started = time.perf_counter()
        response = LLMResponse(text="", bridge=self.name, model=self.model)
        try:
            client = self._get_client()
            # Use streaming for any potentially-long call to avoid
            # timeouts. .get_final_message() returns the full Message
            # once the stream completes.
            with client.messages.stream(
                model=self.model,
                max_tokens=max_tokens,
                system=system,
                messages=[{"role": "user", "content": user}],
                thinking={"type": "adaptive"},
            ) as stream:
                msg = stream.get_final_message()
            # Concatenate text blocks (thinking is omitted by default
            # on Opus 4.7; only text blocks reach .content)
            parts: list[str] = []
            for block in (msg.content or []):
                if getattr(block, "type", "") == "text":
                    parts.append(getattr(block, "text", ""))
            response.text = "".join(parts)
            usage = getattr(msg, "usage", None)
            if usage is not None:
                response.input_tokens = getattr(usage, "input_tokens", 0)
                response.output_tokens = getattr(usage, "output_tokens", 0)
            response.raw = {"stop_reason": getattr(msg, "stop_reason", "")}
        except Exception as exc:  # noqa: BLE001
            response.error = f"{type(exc).__name__}: {exc}"
        response.elapsed_ms = (time.perf_counter() - started) * 1000.0
        self._record_call(system=system, user=user,
                           response=response, role=role)
        return response


# ─────────────────────────────────────────────────────────
# Selection — module-level singleton dispatched by env var
# ─────────────────────────────────────────────────────────


_BRIDGE_REGISTRY: dict[str, type[LLMBridge]] = {
    "echo":      EchoBridge,
    "anthropic": AnthropicBridge,
}


def register_bridge(name: str, cls: type[LLMBridge]) -> None:
    """Plugins can register additional bridges via the
    olympus.llm_bridges entry-point group."""
    _BRIDGE_REGISTRY[name.lower()] = cls


_active_bridge: LLMBridge | None = None


def bridge() -> LLMBridge:
    """Return the active LLM bridge for this process.

    Honors OLYMPUS_LLM env var; defaults to EchoBridge so the
    substrate is safe by default (no surprise network calls)."""
    global _active_bridge
    if _active_bridge is not None:
        return _active_bridge
    name = os.environ.get("OLYMPUS_LLM", "echo").lower().strip()
    cls = _BRIDGE_REGISTRY.get(name)
    if cls is None:
        # Unknown bridge name — log and fall back to echo
        _active_bridge = EchoBridge()
        mnemosyne.remember(
            kind="llm.bridge-selection",
            actor="llm-bridge",
            summary=(f"unknown OLYMPUS_LLM={name!r}, falling back to echo"),
            requested=name, selected="echo",
        )
    else:
        try:
            _active_bridge = cls()
            mnemosyne.remember(
                kind="llm.bridge-selection",
                actor="llm-bridge",
                summary=f"selected bridge: {name}",
                requested=name, selected=name,
            )
        except Exception as exc:  # noqa: BLE001
            # If bridge instantiation fails (e.g., anthropic SDK not
            # installed), fall back to echo and record why
            _active_bridge = EchoBridge()
            mnemosyne.remember(
                kind="llm.bridge-selection",
                actor="llm-bridge",
                summary=(f"bridge {name!r} failed to init "
                         f"({type(exc).__name__}); fell back to echo"),
                requested=name, selected="echo",
                init_error=f"{type(exc).__name__}: {exc}",
            )
    return _active_bridge


def reset_bridge() -> None:
    """Tests use this to clear the module-level cache between
    swapping OLYMPUS_LLM."""
    global _active_bridge
    _active_bridge = None


def set_bridge(b: LLMBridge) -> None:
    """Direct injection — tests use this to install a stub bridge
    without round-tripping through env vars."""
    global _active_bridge
    _active_bridge = b
