"""Themis — JSON Schema publishing + validation.

The claim being tested: schemas() returns every registered schema as
parseable JSON Schema; validate_record() catches missing-required and
type-mismatch violations; the focused validator handles oneOf,
required, additionalProperties, format=date-time, and pattern.
"""
from __future__ import annotations

import pathlib as _pl
import sys as _sys
_ROOT = _pl.Path(__file__).resolve().parent.parent
_SRC = _ROOT / "src"
if str(_SRC) not in _sys.path:
    _sys.path.insert(0, str(_SRC))

import unittest


class TestThemisSchemas(unittest.TestCase):

    def test_schemas_loads_all_registered(self):
        from olympus.titans.themis import themis
        schemas = themis.schemas()
        # Should include at least the envelope and the kinds we ship
        for required in ("mnemosyne-record",
                         "prophecy-verified",
                         "action-ratified",
                         "action-rejected",
                         "session-completed",
                         "invariant-violated",
                         "atlas-bear"):
            self.assertIn(required, schemas,
                f"schema {required!r} missing from themis.schemas()")

    def test_every_schema_has_id_and_title(self):
        from olympus.titans.themis import themis
        for name, schema in themis.schemas().items():
            self.assertIn("$id", schema, f"{name} missing $id")
            self.assertIn("title", schema, f"{name} missing title")
            self.assertIn("$schema", schema)

    def test_validate_record_passes_well_formed(self):
        from olympus.titans.themis import themis
        body = {"prediction": "test-name", "accepted": True,
                "statement": "x", "horizon": "2026-01-01"}
        errors = themis.validate_record("prophecy.verified", body)
        self.assertEqual(errors, [],
            f"valid body should produce no errors, got: {errors}")

    def test_validate_record_catches_missing_required(self):
        from olympus.titans.themis import themis
        body = {"statement": "missing prediction + accepted"}
        errors = themis.validate_record("prophecy.verified", body)
        self.assertGreaterEqual(len(errors), 2)
        joined = " ".join(errors)
        self.assertIn("prediction", joined)
        self.assertIn("accepted", joined)

    def test_validate_record_catches_type_mismatch(self):
        from olympus.titans.themis import themis
        body = {"prediction": 42, "accepted": True}  # prediction must be string
        errors = themis.validate_record("prophecy.verified", body)
        self.assertGreaterEqual(len(errors), 1)
        self.assertTrue(any("prediction" in e for e in errors))

    def test_oneof_works_for_nullable_horizon(self):
        from olympus.titans.themis import themis
        # Both string and null should be valid for horizon
        body1 = {"prediction": "p", "accepted": True, "horizon": "2026-01-01"}
        body2 = {"prediction": "p", "accepted": True, "horizon": None}
        self.assertEqual(themis.validate_record("prophecy.verified", body1), [])
        self.assertEqual(themis.validate_record("prophecy.verified", body2), [])

    def test_pattern_constraint(self):
        from olympus.titans.themis import themis
        body_ok = {"invariant_id": "S1"}
        body_bad = {"invariant_id": "X9-not-valid"}
        self.assertEqual(themis.validate_record("invariant.violated", body_ok),
                         [])
        errors = themis.validate_record("invariant.violated", body_bad)
        self.assertGreaterEqual(len(errors), 1)
        self.assertTrue(any("pattern" in e for e in errors))

    def test_unknown_kind_is_permissive(self):
        """If no schema is registered for a kind, validation returns []."""
        from olympus.titans.themis import themis
        self.assertEqual(
            themis.validate_record("unknown.kind", {"any": "shape"}),
            [],
        )

    def test_date_time_format_validates(self):
        """Some envelope fields use format=date-time; bad ts is rejected."""
        from olympus.titans.themis import themis
        envelope_schema = themis.schemas()["mnemosyne-record"]
        from olympus.titans.themis import _validate
        # Bad envelope (remembered_at is not date-time)
        bad = {"kind": "x", "actor": "y", "summary": "z",
               "remembered_at": "definitely-not-a-date"}
        errors = _validate(bad, envelope_schema, "$")
        self.assertGreaterEqual(len(errors), 1)
        self.assertTrue(any("format" in e for e in errors))


class TestThemisSchemasAgainstRealRecords(unittest.TestCase):
    """Sanity: actual records in state/mnemosyne/ should pass
    validation against their registered schemas (mostly)."""

    def test_recent_records_validate(self):
        from olympus.titans.themis import themis
        from olympus.titans.mnemosyne import mnemosyne
        # Test the kinds we ship schemas for
        kinds_with_schemas = themis.kinds_with_schemas()
        # Map kind-with-hyphens back to dotted
        for hyphenated in kinds_with_schemas:
            dotted = hyphenated.replace("-", ".")
            records = mnemosyne.recall(dotted)
            if not records:
                continue
            # Validate the most recent record's body
            last = records[-1]
            errors = themis.validate_record(dotted, last.body or {})
            self.assertEqual(errors, [],
                f"recent {dotted} record failed schema validation: {errors} "
                f"(body: {last.body})")


if __name__ == "__main__":
    unittest.main()
