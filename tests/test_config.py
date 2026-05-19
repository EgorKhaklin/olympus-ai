"""runtime/config.py — state/config.json load/save.

The claim being tested: missing file returns defaults; roundtrip
preserves values; env vars NEVER overwrite; apply_to_environment
only sets unset keys; effective_llm_provider follows the precedence.
"""
from __future__ import annotations

import pathlib as _pl
import sys as _sys
_ROOT = _pl.Path(__file__).resolve().parent.parent
_SRC = _ROOT / "src"
if str(_SRC) not in _sys.path:
    _sys.path.insert(0, str(_SRC))

import json
import os
import tempfile
import unittest
from unittest.mock import patch


class TestConfigLoadSave(unittest.TestCase):

    def test_load_default_when_missing(self):
        from olympus.runtime import config
        import pathlib
        tmp = pathlib.Path(tempfile.mkdtemp()) / "config.json"
        with patch("olympus.runtime.config._path", return_value=tmp):
            cfg = config.load()
        self.assertEqual(cfg.kindled, "")
        self.assertEqual(cfg.llm.provider, "")
        self.assertEqual(cfg.agora.port, 8765)

    def test_save_load_roundtrip(self):
        from olympus.runtime import config
        import pathlib
        tmp = pathlib.Path(tempfile.mkdtemp()) / "config.json"
        with patch("olympus.runtime.config._path", return_value=tmp):
            cfg = config.Config()
            cfg.kindled = "rt-test"
            cfg.vocation = "roundtrip"
            cfg.llm.provider = "echo"
            cfg.agora.port = 9999
            config.save(cfg)
            reloaded = config.load()
        self.assertEqual(reloaded.kindled, "rt-test")
        self.assertEqual(reloaded.vocation, "roundtrip")
        self.assertEqual(reloaded.llm.provider, "echo")
        self.assertEqual(reloaded.agora.port, 9999)

    def test_load_handles_malformed_json(self):
        from olympus.runtime import config
        import pathlib
        tmp = pathlib.Path(tempfile.mkdtemp()) / "config.json"
        tmp.write_text("this is not json {{", encoding="utf-8")
        with patch("olympus.runtime.config._path", return_value=tmp):
            cfg = config.load()
        # Returns defaults — never raises
        self.assertIsInstance(cfg, config.Config)
        self.assertEqual(cfg.kindled, "")


class TestConfigEnvPrecedence(unittest.TestCase):

    def setUp(self) -> None:
        # Save + clear env vars between tests
        self._saved = {
            k: os.environ.pop(k, None)
            for k in ("OLYMPUS_LLM", "ANTHROPIC_API_KEY")
        }

    def tearDown(self) -> None:
        for k, v in self._saved.items():
            if v is not None:
                os.environ[k] = v
            else:
                os.environ.pop(k, None)

    def test_env_var_wins_over_config(self):
        from olympus.runtime import config
        import pathlib
        tmp = pathlib.Path(tempfile.mkdtemp()) / "config.json"
        with patch("olympus.runtime.config._path", return_value=tmp):
            cfg = config.Config()
            cfg.llm.provider = "anthropic"
            config.save(cfg)
            os.environ["OLYMPUS_LLM"] = "echo"
            self.assertEqual(config.effective_llm_provider(), "echo")

    def test_config_wins_when_env_unset(self):
        from olympus.runtime import config
        import pathlib
        tmp = pathlib.Path(tempfile.mkdtemp()) / "config.json"
        with patch("olympus.runtime.config._path", return_value=tmp):
            cfg = config.Config()
            cfg.llm.provider = "anthropic"
            config.save(cfg)
            self.assertEqual(config.effective_llm_provider(), "anthropic")

    def test_default_echo_when_neither_set(self):
        from olympus.runtime import config
        import pathlib
        tmp = pathlib.Path(tempfile.mkdtemp()) / "config.json"
        with patch("olympus.runtime.config._path", return_value=tmp):
            self.assertEqual(config.effective_llm_provider(), "echo")

    def test_apply_to_environment_never_overwrites(self):
        from olympus.runtime import config
        import pathlib
        tmp = pathlib.Path(tempfile.mkdtemp()) / "config.json"
        with patch("olympus.runtime.config._path", return_value=tmp):
            cfg = config.Config()
            cfg.llm.provider = "anthropic"
            cfg.llm.anthropic_api_key = "sk-config-key"
            config.save(cfg)
            # Pre-existing env vars must be untouched
            os.environ["ANTHROPIC_API_KEY"] = "sk-env-key"
            os.environ["OLYMPUS_LLM"] = "echo"
            config.apply_to_environment()
            self.assertEqual(os.environ["ANTHROPIC_API_KEY"], "sk-env-key")
            self.assertEqual(os.environ["OLYMPUS_LLM"], "echo")

    def test_apply_to_environment_sets_when_unset(self):
        from olympus.runtime import config
        import pathlib
        tmp = pathlib.Path(tempfile.mkdtemp()) / "config.json"
        with patch("olympus.runtime.config._path", return_value=tmp):
            cfg = config.Config()
            cfg.llm.provider = "anthropic"
            cfg.llm.anthropic_api_key = "sk-config-key"
            config.save(cfg)
            applied = config.apply_to_environment()
        self.assertEqual(os.environ.get("ANTHROPIC_API_KEY"),
                         "sk-config-key")
        self.assertEqual(os.environ.get("OLYMPUS_LLM"), "anthropic")
        self.assertIn("ANTHROPIC_API_KEY", applied)


if __name__ == "__main__":
    unittest.main()
