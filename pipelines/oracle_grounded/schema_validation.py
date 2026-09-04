"""Small, stdlib-only JSON Schema validator for oracle-grounded records.

The repository publishes Draft 2020-12 schemas, but the runnable factory has a
stdlib-only contract.  Pulling in ``jsonschema`` just for the curation gate
would make validation depend on an optional environment package, so this
module implements the deliberately small keyword subset used by the checked-in
schemas.  A schema object carrying any keyword outside that subset (plus the
allowed annotations) is itself a finding from ``validate_record_schemas``, so
a future schema cannot silently weaken the gate by using an assertion this
validator does not enforce.

Value-level JSON semantics (equality, type checks, uniqueItems keys), strict
schema loading, and the schema-document keyword audit live in
``schema_primitives``; this module walks an instance against a schema object
and collects findings.
"""

import math
import re
from functools import lru_cache
from pathlib import Path

from .schema_primitives import (
    _display_type,
    _json_equal,
    _load_schema,
    _nonfinite_errors,
    _path_key,
    _resolve_pointer,
    _schema_keyword_findings,
    _type_matches,
    _unique_item_key,
    _unsupported_keyword_errors,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
BASE_SCHEMA_PATH = REPO_ROOT / "schemas" / "oracle-grounded-v1.schema.json"
FAMILY_SCHEMA_DIR = REPO_ROOT / "schemas" / "oracle-grounded"
# Per-frame cap on accumulated findings. Anything past this on one array or
# object adds a single summary line instead of one string per element.
MAX_SCHEMA_FINDINGS = 100


def _const_enum_errors(value, schema, path):
    """const and enum."""
    errors = []
    if "const" in schema and not _json_equal(value, schema["const"]):
        errors.append(f"{path} must equal {schema['const']!r}")
    if "enum" in schema and not any(_json_equal(value, item) for item in schema["enum"]):
        errors.append(f"{path} must be one of {schema['enum']!r}")
    return errors


def _matches_any_option(value, options, root, path):
    return any(not _validate(value, option, root, path) for option in options)


def _subschema_errors(value, schema, root, path):
    """not and anyOf."""
    errors = []
    if "not" in schema and not _validate(value, schema["not"], root, path):
        errors.append(f"{path} matches a forbidden schema")
    if "anyOf" in schema and not _matches_any_option(value, schema["anyOf"], root, path):
        errors.append(f"{path} does not match any allowed schema")
    return errors


def _combinator_errors(value, schema, root, path):
    """const, enum, not and anyOf."""
    return _const_enum_errors(value, schema, path) + _subschema_errors(
        value, schema, root, path
    )


# Each bound is (keyword, symbol used in the finding, violation predicate).
_NUMERIC_BOUNDS = (
    ("minimum", ">=", lambda value, bound: value < bound),
    ("maximum", "<=", lambda value, bound: value > bound),
    ("exclusiveMinimum", ">", lambda value, bound: value <= bound),
    ("exclusiveMaximum", "<", lambda value, bound: value >= bound),
)


def _numeric_errors(value, schema, path):
    """minimum, maximum and their exclusive forms."""
    if not isinstance(value, (int, float)) or isinstance(value, bool):
        return []
    errors = []
    for keyword, symbol, violates in _NUMERIC_BOUNDS:
        if keyword in schema and violates(value, schema[keyword]):
            errors.append(f"{path} must be {symbol} {schema[keyword]!r}")
    return errors


def _string_errors(value, schema, path):
    """minLength and pattern."""
    if not isinstance(value, str):
        return []
    errors = []
    if "minLength" in schema and len(value) < schema["minLength"]:
        errors.append(f"{path} must contain at least {schema['minLength']} characters")
    if "pattern" in schema and re.search(schema["pattern"], value) is None:
        errors.append(f"{path} does not match pattern {schema['pattern']!r}")
    return errors


def _unique_items_errors(value, path):
    """uniqueItems, reported once for the first repeat."""
    seen = set()
    for item in value:
        key = _unique_item_key(item)
        if key in seen:
            return [f"{path} must contain unique items"]
        seen.add(key)
    return []


def _budget_exhausted(errors, path):
    """Bound one frame's findings so untrusted element counts stay bounded.

    A finding still rejects the record, so suppressing repeats past the cap
    loses no fail-closed behavior; without it a multi-million-item array of
    wrong-typed values would retain one error string per element and turn
    the bounded validation CLI into a memory sink.
    """
    if len(errors) < MAX_SCHEMA_FINDINGS:
        return False
    errors.append(f"{path}: further findings suppressed after {MAX_SCHEMA_FINDINGS}")
    return True


def _array_bound_errors(value, schema, path):
    """minItems, maxItems and uniqueItems."""
    errors = []
    if "minItems" in schema and len(value) < schema["minItems"]:
        errors.append(f"{path} must contain at least {schema['minItems']} items")
    if "maxItems" in schema and len(value) > schema["maxItems"]:
        errors.append(f"{path} must contain at most {schema['maxItems']} items")
    if schema.get("uniqueItems"):
        errors.extend(_unique_items_errors(value, path))
    return errors


def _item_errors(value, item_schema, frame):
    """Per-element item validation, capped by the shared frame budget."""
    root, path, errors = frame
    for index, item in enumerate(value):
        if _budget_exhausted(errors, path):
            break
        errors.extend(_validate(item, item_schema, root, f"{path}[{index}]"))


def _array_errors(value, schema, root, path):
    """minItems, maxItems, uniqueItems and items."""
    if not isinstance(value, list):
        return []
    errors = _array_bound_errors(value, schema, path)
    item_schema = schema.get("items")
    if isinstance(item_schema, dict):
        _item_errors(value, item_schema, (root, path, errors))
    return errors


def _property_presence_errors(value, schema, path):
    """minProperties and required."""
    errors = []
    if "minProperties" in schema and len(value) < schema["minProperties"]:
        errors.append(f"{path} must contain at least {schema['minProperties']} properties")
    for key in schema.get("required", ()):
        if key not in value:
            errors.append(f"{_path_key(path, key)} is required")
    return errors


def _declared_property_errors(value, properties, frame):
    """Validate every present, declared property against its child schema."""
    root, path, errors = frame
    for key, child_schema in properties.items():
        if key in value:
            errors.extend(_validate(value[key], child_schema, root, _path_key(path, key)))


def _forbidden_extra_errors(extras, frame):
    """additionalProperties: false — every undeclared key is a finding."""
    _root, path, errors = frame
    for key in extras:
        if _budget_exhausted(errors, path):
            break
        errors.append(f"{_path_key(path, key)} is not allowed")


def _schema_checked_extra_errors(value, extras, additional, frame):
    """additionalProperties as a schema — validate every undeclared key."""
    root, path, errors = frame
    for key in extras:
        if _budget_exhausted(errors, path):
            break
        errors.extend(_validate(value[key], additional, root, _path_key(path, key)))


def _extra_property_errors(value, schema, properties, frame):
    """Dispatch on the two enforced forms of additionalProperties."""
    additional = schema.get("additionalProperties", True)
    extras = [key for key in value if key not in properties]
    if additional is False:
        _forbidden_extra_errors(extras, frame)
    elif isinstance(additional, dict):
        _schema_checked_extra_errors(value, extras, additional, frame)


def _object_errors(value, schema, root, path):
    """minProperties, required, properties and additionalProperties."""
    if not isinstance(value, dict):
        return []
    errors = _property_presence_errors(value, schema, path)
    frame = (root, path, errors)
    properties = schema.get("properties", {})
    _declared_property_errors(value, properties, frame)
    _extra_property_errors(value, schema, properties, frame)
    return errors


def _type_errors(value, schema, path):
    """The declared type, which short-circuits every later keyword."""
    expected = schema.get("type")
    if expected is None:
        return []
    allowed = [expected] if isinstance(expected, str) else expected
    if any(_type_matches(value, item) for item in allowed):
        return []
    return [f"{path} must have type {allowed!r}, got {_display_type(value)!r}"]


def _validate(value, schema, root, path):
    errors = []

    reference = schema.get("$ref")
    if reference is not None:
        errors.extend(_validate(value, _resolve_pointer(root, reference), root, path))

    errors.extend(_combinator_errors(value, schema, root, path))

    type_errors = _type_errors(value, schema, path)
    if type_errors:
        errors.extend(type_errors)
        return errors

    if isinstance(value, float) and not math.isfinite(value):
        errors.append(f"{path} contains a non-finite number")
        return errors

    errors.extend(_numeric_errors(value, schema, path))
    errors.extend(_string_errors(value, schema, path))
    errors.extend(_array_errors(value, schema, root, path))
    errors.extend(_object_errors(value, schema, root, path))
    return errors


def _without_validation_requirement(base):
    """Relax the base schema for ``build_record``'s pre-assessment mode.

    The validation block is missing or provisional in that mode. Keep the
    key allowed so additionalProperties:false does not reject it, but do
    not enforce the completed validation schema.
    """
    base = dict(base)
    base["required"] = [key for key in base.get("required", ()) if key != "validation"]
    properties = dict(base.get("properties", {}))
    properties["validation"] = {"type": "object"}
    base["properties"] = properties
    return base


def _document_findings(instance, path, label, include_validation):
    """Keyword-audit findings plus instance findings for one schema file."""
    findings = [f"{label}: {item}" for item in _schema_keyword_findings(path)]
    schema = _load_schema(path)
    if not include_validation:
        schema = _without_validation_requirement(schema)
    findings.extend(f"{label}: {item}" for item in _validate(instance, schema, schema, "$"))
    return findings


def validate_record_schemas(instance, family, include_validation=True):
    """Return base- and family-schema findings for one record.

    ``build_record`` assesses a provisional envelope before its validation
    block exists.  In that one mode the base schema ignores only the
    ``validation`` property; all other required and family semantics still run.
    """
    findings = _nonfinite_errors(instance)
    findings.extend(
        _document_findings(instance, str(BASE_SCHEMA_PATH), "base schema", include_validation)
    )
    family_path = FAMILY_SCHEMA_DIR / f"{family}.schema.json"
    findings.extend(_document_findings(instance, str(family_path), "family schema", True))
    return findings
