"""olympus.runtime.llm_bridge — pluggable LLM provider.

The tests never hit the network. They use EchoBridge (default) for
determinism and verify:
  - EchoBridge returns deterministic structured output
  - Every call is recorded to Mnemosyne under `llm.call`
  - Env-var selection works (OLYMPUS_LLM)
  - Unknown bridge name falls back to echo
  - AnthropicBridge raises a clear error if the SDK isn't installed
    (or, if installed, can be invoked with an injected client)
"""
from __future__ import annotations

import pathlib as _pl
import sys as _sys
_ROOT = _pl.Path(__file__).resolve().parent.parent
_SRC = _ROOT / "src"
if str(_SRC) not in _sys.path:
    _sys.path.insert(0, str(_SRC))

import os
import unittest


class TestEchoBridge(unittest.TestCase):

    def test_call_returns_structured_response(self):
        from olympus.runtime.llm_bridge import EchoBridge
        bridge = EchoBridge()
        resp = bridge.call(
            system="test system prompt",
            user="test user prompt",
            role="test-role",
        )
        self.assertEqual(resp.bridge, "echo")
        self.assertGreater(len(resp.text), 0)
        self.assertEqual(resp.error, "")
        self.assertGreater(resp.elapsed_ms, 0.0)

    def test_call_recorded_to_mnemosyne(self):
        from olympus.runtime.llm_bridge import EchoBridge
        from olympus.titans.mnemosyne import mnemosyne
        before = len(mnemosyne.recall("llm.call"))
        EchoBridge().call(
            system="rec test", user="rec test", role="rec",
        )
        after = len(mnemosyne.recall("llm.call"))
        self.assertGreater(after, before)

    def test_template_override(self):
        from olympus.runtime.llm_bridge import EchoBridge
        canned = '{"summary":"canned","confidence":0.42}'
        bridge = EchoBridge(response_template=canned)
        resp = bridge.call(system="x", user="y", role="z")
        self.assertEqual(resp.text, canned)


class TestBridgeSelection(unittest.TestCase):

    def setUp(self) -> None:
        from olympus.runtime.llm_bridge import reset_bridge
        reset_bridge()

    def tearDown(self) -> None:
        # Restore env + reset cache so other tests see EchoBridge
        from olympus.runtime.llm_bridge import reset_bridge
        os.environ.pop("OLYMPUS_LLM", None)
        reset_bridge()

    def test_default_is_echo(self):
        from olympus.runtime.llm_bridge import bridge, EchoBridge
        os.environ.pop("OLYMPUS_LLM", None)
        b = bridge()
        self.assertIsInstance(b, EchoBridge)

    def test_explicit_echo(self):
        from olympus.runtime.llm_bridge import bridge, EchoBridge
        os.environ["OLYMPUS_LLM"] = "echo"
        b = bridge()
        self.assertIsInstance(b, EchoBridge)

    def test_unknown_falls_back_to_echo(self):
        from olympus.runtime.llm_bridge import bridge, EchoBridge
        os.environ["OLYMPUS_LLM"] = "definitely-not-a-real-bridge"
        b = bridge()
        self.assertIsInstance(b, EchoBridge)

    def test_set_bridge_overrides(self):
        from olympus.runtime.llm_bridge import (
            bridge, set_bridge, EchoBridge,
        )
        custom = EchoBridge(response_template="custom")
        set_bridge(custom)
        self.assertIs(bridge(), custom)


class TestAnthropicBridge(unittest.TestCase):
    """The Anthropic SDK is optional. Without it installed,
    instantiating AnthropicBridge for a real call must raise a
    clear error; with it installed (and a mocked client), the call
    routes correctly."""

    def test_no_sdk_raises_clear_error_on_call(self):
        """If the SDK isn't installed, instantiating the bridge is OK
        (lazy import) but .call() raises a clear RuntimeError."""
        try:
            import anthropic  # noqa: F401
            self.skipTest("anthropic SDK is installed; cannot test "
                          "the no-SDK fallback path")
        except ImportError:
            pass
        from olympus.runtime.llm_bridge import AnthropicBridge
        bridge = AnthropicBridge()
        resp = bridge.call(system="s", user="u", role="r")
        # Error captured (not raised) — graceful degradation
        self.assertNotEqual(resp.error, "")
        self.assertIn("anthropic", resp.error.lower())

    def test_with_mock_client_routes_correctly(self):
        """Inject a fake client that mimics the SDK's
        messages.stream context manager."""
        from olympus.runtime.llm_bridge import AnthropicBridge

        class _FakeMsg:
            class _Block:
                type = "text"
                text = "structured reply"
            content = [_Block()]
            stop_reason = "end_turn"
            class _Usage:
                input_tokens = 12
                output_tokens = 5
            usage = _Usage()

        class _FakeStreamCtx:
            def __enter__(self): return self
            def __exit__(self, *a): pass
            def get_final_message(self): return _FakeMsg()

        class _FakeMessages:
            def stream(self, **kwargs):
                # Record kwargs for assertion
                _FakeMessages.last_kwargs = kwargs
                return _FakeStreamCtx()

        class _FakeClient:
            messages = _FakeMessages()

        bridge = AnthropicBridge(client=_FakeClient())
        resp = bridge.call(system="sys", user="usr", role="r",
                            max_tokens=99)
        self.assertEqual(resp.text, "structured reply")
        self.assertEqual(resp.input_tokens, 12)
        self.assertEqual(resp.output_tokens, 5)
        self.assertEqual(resp.error, "")
        # Confirm the substrate's chosen defaults reached the SDK
        kwargs = _FakeMessages.last_kwargs
        self.assertEqual(kwargs["system"], "sys")
        self.assertEqual(kwargs["max_tokens"], 99)
        self.assertEqual(kwargs["thinking"], {"type": "adaptive"})


if __name__ == "__main__":
    unittest.main()
