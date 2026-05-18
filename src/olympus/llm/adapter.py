"""olympus.llm.adapter — abstract LLM interface + reference adapters."""
from __future__ import annotations

from typing import Any


class LLMAdapter:
    """The abstract adapter. Implementations override `complete()`."""

    def complete(self, *, system: str, user: str,
                 max_tokens: int = 1024, **kwargs: Any) -> str:
        raise NotImplementedError


class NullAdapter(LLMAdapter):
    """Returns an empty string. Default adapter; preserves Olympus's
    LLM-free claim. Tests, dry runs, and substrate-only deployments
    use this."""

    def complete(self, *, system: str, user: str,
                 max_tokens: int = 1024, **kwargs: Any) -> str:
        return ""


null_adapter = NullAdapter()


def anthropic_adapter(api_key: str,
                      model: str = "claude-opus-4-7") -> LLMAdapter:
    """Returns an LLMAdapter backed by Anthropic's SDK.
    Requires `pip install anthropic`. Lazy-imports so Olympus does
    not depend on the SDK."""
    try:
        from anthropic import Anthropic
    except ImportError as exc:
        raise RuntimeError(
            "anthropic SDK not installed — `pip install anthropic` to use"
        ) from exc

    client = Anthropic(api_key=api_key)

    class _AnthropicAdapter(LLMAdapter):
        def complete(self, *, system: str, user: str,
                     max_tokens: int = 1024, **kwargs: Any) -> str:
            msg = client.messages.create(
                model=model,
                max_tokens=max_tokens,
                system=system,
                messages=[{"role": "user", "content": user}],
                **kwargs,
            )
            # Concatenate text blocks (covers thinking + final response shape)
            return "".join(
                block.text for block in msg.content
                if getattr(block, "type", None) == "text"
            )

    return _AnthropicAdapter()


def openai_adapter(api_key: str, model: str = "gpt-4o") -> LLMAdapter:
    """Returns an LLMAdapter backed by the OpenAI SDK.
    Requires `pip install openai`. Provided as an example of how other
    vendors slot in; Olympus is vendor-neutral."""
    try:
        from openai import OpenAI
    except ImportError as exc:
        raise RuntimeError(
            "openai SDK not installed — `pip install openai` to use"
        ) from exc

    client = OpenAI(api_key=api_key)

    class _OpenAIAdapter(LLMAdapter):
        def complete(self, *, system: str, user: str,
                     max_tokens: int = 1024, **kwargs: Any) -> str:
            resp = client.chat.completions.create(
                model=model,
                max_tokens=max_tokens,
                messages=[
                    {"role": "system", "content": system},
                    {"role": "user", "content": user},
                ],
                **kwargs,
            )
            return resp.choices[0].message.content or ""

    return _OpenAIAdapter()
