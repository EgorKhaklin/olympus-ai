"""olympus.llm — optional LLM adapter pattern.

Olympus is LLM-agnostic. The substrate operates deterministically without
any language model. This subpackage provides an OPTIONAL adapter pattern
for deployments that want to invoke an LLM as part of Athena's brief
synthesis or Hephaestus's proposal authoring.

The substrate ships only the `NullAdapter` (returns ""). Real adapters
(Anthropic, OpenAI, local) are provided as factory functions that
require the operator to install the relevant SDK and pass credentials.

This is intentional: the LLM is an integration *point*, not an
integration. Olympus does not depend on any vendor.
"""

from olympus.llm.adapter import (
    LLMAdapter, NullAdapter, null_adapter,
    anthropic_adapter,
)

__all__ = [
    "LLMAdapter", "NullAdapter", "null_adapter",
    "anthropic_adapter",
]
