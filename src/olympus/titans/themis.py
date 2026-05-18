"""Themis — titaness of divine law, custom, and natural order.

Themis is the personification of right order, sacred law that pre-dates
the Olympians. She gave humans the Oracle at Delphi before Apollo took
it over. In Olympus, Themis is the constitution: she enumerates the
substrate invariants (S1–S8) and answers "is this allowed?"

The COSMOGONY.md file names the substrate invariants in human-readable
form. This module makes them machine-checkable.
"""
from __future__ import annotations

import re
import pathlib
from dataclasses import dataclass
from typing import Callable

from olympus.primordials.gaia import root


@dataclass(frozen=True)
class Invariant:
    """A substrate invariant."""
    id: str            # e.g., "S1"
    name: str          # short name
    statement: str     # human-readable claim
    enforcement: str   # how it's checked


# The eight substrate invariants. Domain-specific invariants (C1–CN)
# live in DOMAIN.md (deployment-side) and are not enumerated here.
SUBSTRATE_INVARIANTS: tuple[Invariant, ...] = (
    Invariant(
        id="S1", name="Mnemosyne — append-only audit-of-record",
        statement="Every load-bearing decision writes to an append-only record.",
        enforcement="Styx chain hash + per-kind JSONL append in state/mnemosyne/",
    ),
    Invariant(
        id="S2", name="Argos — deterministic substrate",
        statement="No Argos Eye uses randomness in its scan logic.",
        enforcement="Eye.seed must be set; identical seed → identical pheromones",
    ),
    Invariant(
        id="S3", name="HYDRA — read-only observation",
        statement="HYDRA Heads never mutate state.",
        enforcement="Head.observe() returns findings; no writes from this module",
    ),
    Invariant(
        id="S4", name="Argos — decentralization",
        statement="No Eye imports another Eye. No host calls anything.",
        enforcement="Static analysis: imports under monsters/argos/eyes/ may only "
                    "reach monsters/argos/base and stdlib",
    ),
    Invariant(
        id="S5", name="Apollo — falsifiability",
        statement="Every Apollo prediction is a predicate that can be checked.",
        enforcement="Apollo predicates carry a `verify()` callable returning bool",
    ),
    Invariant(
        id="S6", name="Delphi — strategic-decision discipline",
        statement="MEDIUM and HIGH-risk decisions are recorded in oracles/delphi/.",
        enforcement="Pre-ship gate verifies a Delphi exists for any HIGH ship",
    ),
    Invariant(
        id="S7", name="Bounded autonomy",
        statement="LOW autonomous, MEDIUM proposal, HIGH requires Zeus authorization.",
        enforcement="Zeus.can_perform(risk_class) reads Styx oaths for HIGH/COMPOSITE",
    ),
    Invariant(
        id="S8", name="Continuity of Understanding",
        statement="Every load-bearing action is reconstructible — what was done, why, "
                  "and on whose authority — from the substrate's own records alone. "
                  "The substrate refuses changes that obscure its decision-making.",
        enforcement="Mnemosyne discipline + Styx oath chain + eye_understanding_gap "
                    "surfaces decisions without recorded rationale; Momus AP6 contests "
                    "proposals that reduce reconstructability",
    ),
)


SCHEMAS_DIR = "codex/schemas"


class Themis:
    """Custodian of the substrate constitution. Owns the S1–S8 invariants
    and (per compass-rose arc) the machine-readable JSON Schemas for
    load-bearing Mnemosyne record kinds."""

    def all(self) -> tuple[Invariant, ...]:
        return SUBSTRATE_INVARIANTS

    def by_id(self, sid: str) -> Invariant | None:
        for inv in SUBSTRATE_INVARIANTS:
            if inv.id == sid:
                return inv
        return None

    def cosmogony_path(self) -> pathlib.Path:
        return root.child("codex", "COSMOGONY.md")

    def cosmogony_mentions(self, invariant_id: str) -> bool:
        """True iff the constitutional document mentions this invariant id."""
        path = self.cosmogony_path()
        if not path.exists():
            return False
        text = path.read_text(encoding="utf-8")
        return bool(re.search(rf"\b{re.escape(invariant_id)}\b", text))

    # ─────────────────────────────────────────────────────────
    # JSON Schema publication (compass-rose arc)
    # ─────────────────────────────────────────────────────────

    def schemas_dir(self) -> pathlib.Path:
        return root.child(*SCHEMAS_DIR.split("/"))

    def schemas(self) -> dict[str, dict]:
        """Return all registered JSON Schemas, keyed by kind (with the
        '.schema.json' suffix stripped). Result includes the base
        Mnemosyne envelope under key 'mnemosyne-record'."""
        import json as _json
        out: dict[str, dict] = {}
        for path in sorted(self.schemas_dir().glob("*.schema.json")):
            name = path.stem.replace(".schema", "")
            try:
                out[name] = _json.loads(path.read_text(encoding="utf-8"))
            except _json.JSONDecodeError:
                continue
        return out

    def kinds_with_schemas(self) -> list[str]:
        """The Mnemosyne kinds that have a per-kind body schema. The
        kind 'prophecy.verified' maps to schema name 'prophecy-verified'."""
        return [k for k in self.schemas().keys() if k != "mnemosyne-record"]

    def validate_record(self, kind: str, body: dict) -> list[str]:
        """Validate a Mnemosyne body against the per-kind schema, if
        one is registered. Returns a list of error messages (empty =
        valid). If no schema is registered for the kind, returns
        empty (unknown kinds are not contractually constrained)."""
        schema_name = kind.replace(".", "-")
        schema = self.schemas().get(schema_name)
        if schema is None:
            return []
        return _validate(body, schema, "$")


# ─────────────────────────────────────────────────────────
# Minimal JSON-Schema validator — focused subset used by our schemas.
# stdlib only (no jsonschema dep). Supports:
#   type, required, properties, additionalProperties, oneOf,
#   pattern, minLength, maxLength, minimum, format=date-time
# ─────────────────────────────────────────────────────────


_TYPE_OK: dict[str, Callable[[object], bool]] = {
    "object":  lambda v: isinstance(v, dict),
    "array":   lambda v: isinstance(v, list),
    "string":  lambda v: isinstance(v, str),
    "integer": lambda v: isinstance(v, int) and not isinstance(v, bool),
    "number":  lambda v: isinstance(v, (int, float)) and not isinstance(v, bool),
    "boolean": lambda v: isinstance(v, bool),
    "null":    lambda v: v is None,
}


def _format_ok(value: object, fmt: str) -> bool:
    if fmt == "date-time":
        if not isinstance(value, str):
            return False
        try:
            # tolerate trailing 'Z' or +HH:MM offset
            value2 = value.replace("Z", "+00:00")
            import datetime as _dt
            _dt.datetime.fromisoformat(value2)
            return True
        except Exception:  # noqa: BLE001
            return False
    return True  # unknown formats are permissive


def _validate(value: object, schema: dict, path: str) -> list[str]:
    errors: list[str] = []

    if "oneOf" in schema:
        matches = []
        for i, sub in enumerate(schema["oneOf"]):
            sub_errors = _validate(value, sub, path)
            if not sub_errors:
                matches.append(i)
        if len(matches) != 1:
            errors.append(f"{path}: oneOf matched {len(matches)} schemas "
                          f"(expected 1)")
        return errors

    if "type" in schema:
        type_value = schema["type"]
        if isinstance(type_value, str):
            type_value = [type_value]
        if not any(_TYPE_OK.get(t, lambda _: False)(value) for t in type_value):
            errors.append(f"{path}: expected type {type_value}, got "
                          f"{type(value).__name__}")
            return errors  # if type is wrong, deeper checks won't help

    if "format" in schema and not _format_ok(value, schema["format"]):
        errors.append(f"{path}: invalid format {schema['format']!r}")

    if "pattern" in schema and isinstance(value, str):
        if not re.search(schema["pattern"], value):
            errors.append(f"{path}: does not match pattern "
                          f"{schema['pattern']!r}")

    if "minLength" in schema and isinstance(value, (str, list, dict)):
        if len(value) < schema["minLength"]:
            errors.append(f"{path}: length {len(value)} < minLength "
                          f"{schema['minLength']}")

    if "maxLength" in schema and isinstance(value, (str, list, dict)):
        if len(value) > schema["maxLength"]:
            errors.append(f"{path}: length {len(value)} > maxLength "
                          f"{schema['maxLength']}")

    if "minimum" in schema and isinstance(value, (int, float)):
        if value < schema["minimum"]:
            errors.append(f"{path}: {value} < minimum {schema['minimum']}")

    if isinstance(value, dict):
        for req in schema.get("required", []):
            if req not in value:
                errors.append(f"{path}: required property {req!r} missing")
        props = schema.get("properties", {})
        add_props = schema.get("additionalProperties", True)
        for k, v in value.items():
            if k in props:
                errors.extend(_validate(v, props[k], f"{path}.{k}"))
            elif add_props is False:
                errors.append(f"{path}: additional property {k!r} not allowed")

    return errors


themis = Themis()
