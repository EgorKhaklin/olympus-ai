"""Tests for olympus.meta + olympus.llm."""
from __future__ import annotations

import pathlib as _pl
import sys as _sys
_ROOT = _pl.Path(__file__).resolve().parent.parent
_SRC = _ROOT / 'src'
if str(_SRC) not in _sys.path:
    _sys.path.insert(0, str(_SRC))

import unittest


class TestMeta(unittest.TestCase):

    def test_portrait_renders(self):
        from olympus.meta import portrait
        p = portrait()
        self.assertIsNotNone(p.composed_at)
        self.assertGreaterEqual(len(p.tiers), 10)
        self.assertEqual(len(p.invariants), 8)
        self.assertGreaterEqual(len(p.hydra_heads), 9)
        self.assertGreaterEqual(len(p.argos_eyes), 9)
        text = p.as_text()
        self.assertIn("Olympus self-portrait", text)
        self.assertIn("HYDRA", text)


class TestLLMAdapter(unittest.TestCase):

    def test_null_adapter_returns_empty(self):
        from olympus.llm import null_adapter
        out = null_adapter.complete(system="x", user="y", max_tokens=64)
        self.assertEqual(out, "")

    def test_anthropic_adapter_raises_if_sdk_missing(self):
        """Without the optional SDK, the factory should raise a clear error."""
        try:
            import anthropic  # noqa: F401
            self.skipTest("anthropic SDK installed; cannot test missing case")
        except ImportError:
            from olympus.llm import anthropic_adapter
            with self.assertRaises(RuntimeError) as ctx:
                anthropic_adapter(api_key="fake")
            self.assertIn("anthropic", str(ctx.exception).lower())


if __name__ == "__main__":
    unittest.main()
