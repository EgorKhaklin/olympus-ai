"""olympus.runtime.plugins — entry-point-based plugin loader.

The claim being tested: discover() reads importlib.metadata for the
documented groups; load_all() registers each entry-point into its
target registry; failures (bad import, bad type) are isolated; the
loader never raises.
"""
from __future__ import annotations

import pathlib as _pl
import sys as _sys
_ROOT = _pl.Path(__file__).resolve().parent.parent
_SRC = _ROOT / "src"
if str(_SRC) not in _sys.path:
    _sys.path.insert(0, str(_SRC))

import importlib.metadata
import unittest
from unittest.mock import patch


class _FakeEP:
    """A drop-in stand-in for importlib.metadata.EntryPoint."""
    def __init__(self, *, group: str, name: str, value: str,
                 loader=None) -> None:
        self.group = group
        self.name = name
        self.value = value
        self._loader = loader

    def load(self):
        if isinstance(self._loader, Exception):
            raise self._loader
        return self._loader


class TestPluginLoader(unittest.TestCase):

    def test_groups_constant_lists_expected_entry_point_groups(self):
        from olympus.runtime.plugins import GROUPS
        for expected in (
            "olympus.prometheus_handlers",
            "olympus.asclepius_healers",
            "olympus.argos_eyes",
            "olympus.apollo_predictions",
            "olympus.cli_errands",
        ):
            self.assertIn(expected, GROUPS)

    def test_no_plugins_yields_empty_manifest(self):
        """When no entry-points are registered, the loader returns
        an empty manifest without raising."""
        from olympus.runtime.plugins import load_all
        with patch("olympus.runtime.plugins.discover", return_value=[]):
            manifest = load_all(record_to_mnemosyne=False)
        self.assertEqual(manifest.total_loaded, 0)
        self.assertEqual(manifest.total_failed, 0)

    def test_prometheus_handler_plugin_registers(self):
        from olympus.runtime.plugins import load_all
        from olympus.heroes.prometheus import prometheus

        def handler(_a):
            return ({"x": 0}, {"x": 1})

        ep = _FakeEP(
            group="olympus.prometheus_handlers",
            name="test-plugin-handler",
            value="x:y",
            loader=handler,
        )
        with patch("olympus.runtime.plugins.discover", return_value=[ep]):
            manifest = load_all(record_to_mnemosyne=False)
        self.assertEqual(manifest.total_loaded, 1)
        self.assertEqual(manifest.total_failed, 0)
        # Verify the registry now has it
        self.assertIn("test-plugin-handler", prometheus.handlers())

    def test_asclepius_healer_plugin_registers(self):
        from olympus.runtime.plugins import load_all
        from olympus.olympians.asclepius import asclepius

        def healer():
            return (True, False, "test")

        ep = _FakeEP(
            group="olympus.asclepius_healers",
            name="test-plugin-healer",
            value="x:y",
            loader=healer,
        )
        with patch("olympus.runtime.plugins.discover", return_value=[ep]):
            manifest = load_all(record_to_mnemosyne=False)
        self.assertEqual(manifest.total_loaded, 1)
        self.assertIn("test-plugin-healer", asclepius.healers())

    def test_import_failure_captured(self):
        from olympus.runtime.plugins import load_all
        ep = _FakeEP(
            group="olympus.prometheus_handlers",
            name="broken",
            value="x:y",
            loader=ImportError("simulated"),
        )
        with patch("olympus.runtime.plugins.discover", return_value=[ep]):
            manifest = load_all(record_to_mnemosyne=False)
        self.assertEqual(manifest.total_loaded, 0)
        self.assertEqual(manifest.total_failed, 1)
        self.assertIn("import-failed", manifest.failed[0].detail)

    def test_register_failure_captured(self):
        from olympus.runtime.plugins import load_all
        # Pass a non-callable to a callable-only group → register error
        ep = _FakeEP(
            group="olympus.prometheus_handlers",
            name="bad-type",
            value="x:y",
            loader=42,
        )
        with patch("olympus.runtime.plugins.discover", return_value=[ep]):
            manifest = load_all(record_to_mnemosyne=False)
        self.assertEqual(manifest.total_failed, 1)
        self.assertIn("register-failed", manifest.failed[0].detail)

    def test_unknown_group_rejected(self):
        from olympus.runtime.plugins import _register
        with self.assertRaises(ValueError):
            _register("olympus.not_a_real_group", "x", lambda: None)


if __name__ == "__main__":
    unittest.main()
