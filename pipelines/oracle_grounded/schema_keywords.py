"""Assertion keywords of the oracle-grounded schema subset.

Each ``_*_error(s)`` helper owns one keyword and returns human-readable
findings; ``_validate`` dispatches them in the schema's refusal order. The
JSON-value algebra itself lives in ``schema_values``.
"""

import math
import operator
import re

from .schema_values import (
    _display_type,
    _json_equal,
    _path_key,
    _type_matches,
    _unique_item_key,
)

# Per-frame cap on accumulated findings. Anything past this on one array or
# object adds a single summary line instead of one string per element.
MAX_SCHEMA_FINDINGS = 100
# Bound on a string fed to ``re.search`` for a ``pattern`` keyword.  The
# pattern itself comes from a reviewed schema, but the subject comes from an
# untrusted record, so an unbounded subject would let a catastrophic pattern
# (or merely an expensive one) burn unbounded CPU on the validation gate.
MAX_PATTERN_SUBJECT_CHARS = 10000


def _resolve_pointer(root, reference):
    if not reference.startswith("#/"):
        raise ValueError(f"only local schema references are supported: {reference!r}")
    value = root
    for raw in reference[2:].split("/"):
        token = raw.replace("~1", "/").replace("~0", "~")
        value = value[token]
    return value


def _literal_errors(value, schema, path):
    return _const_errors(value, schema, path) + _enum_errors(value, schema, path)


def _const_errors(value, schema, path):
    if "const" in schema and not _json_equal(value, schema["const"]):
        return [f"{path} must equal {schema['const']!r}"]
    return []


def _enum_errors(value, schema, path):
    if "enum" in schema and not any(_json_equal(value, item) for item in schema["enum"]):
        return [f"{path} must be one of {schema['enum']!r}"]
    return []


def _combinator_errors(value, schema, root, path):
    """const, enum, not and anyOf, preserving refusal order."""
    errors = _literal_errors(value, schema, path)
    errors.extend(_not_errors(value, schema, root, path))
    errors.extend(_any_of_errors(value, schema, root, path))
    return errors


def _not_errors(value, schema, root, path):
    if "not" in schema and not _validate(value, schema["not"], root, path):
        return [f"{path} matches a forbidden schema"]
    return []


def _any_of_errors(value, schema, root, path):
    if "anyOf" not in schema:
        return []
    if any(not _validate(value, option, root, path) for option in schema["anyOf"]):
        return []
    return [f"{path} does not match any allowed schema"]


_NUMERIC_BOUNDS = (
    ("minimum", operator.lt, ">="),
    ("maximum", operator.gt, "<="),
    ("exclusiveMinimum", operator.le, ">"),
    ("exclusiveMaximum", operator.ge, "<"),
)


def _numeric_errors(value, schema, path):
    """minimum, maximum and their exclusive forms, in declaration order."""
    if not isinstance(value, (int, float)) or isinstance(value, bool):
        return []
    return _bound_errors(value, schema, path)


def _bound_errors(value, schema, path):
    return [f"{path} must be {relation} {schema[key]!r}"
            for key, violates, relation in _NUMERIC_BOUNDS
            if key in schema and violates(value, schema[key])]


def _string_errors(value, schema, path):
    """minLength and pattern."""
    if not isinstance(value, str):
        return []
    errors = _min_length_errors(value, schema, path)
    errors.extend(_pattern_errors(value, schema, path))
    return errors


def _min_length_errors(value, schema, path):
    if "minLength" in schema and len(value) < schema["minLength"]:
        return [f"{path} must contain at least {schema['minLength']} characters"]
    return []


def _pattern_errors(value, schema, path):
    if "pattern" not in schema:
        return []
    if len(value) > MAX_PATTERN_SUBJECT_CHARS:
        return [f"{path} exceeds the {MAX_PATTERN_SUBJECT_CHARS}-character pattern-check bound"]
    if re.search(schema["pattern"], value) is None:
        return [f"{path} does not match pattern {schema['pattern']!r}"]
    return []


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


def _extend_bounded(errors, members, path, findings):
    for member in members:
        if _budget_exhausted(errors, path):
            break
        errors.extend(findings(member))


def _bounded_member_errors(members, path, findings):
    errors = []
    _extend_bounded(errors, members, path, findings)
    return errors


def _array_errors(value, schema, root, path):
    """minItems, maxItems, uniqueItems and items."""
    if not isinstance(value, list):
        return []
    errors = _array_bounds(value, schema, path)
    if schema.get("uniqueItems"):
        errors.extend(_unique_items_errors(value, path))
    errors.extend(_item_schema_errors(value, schema, root, path))
    return errors


def _array_bounds(value, schema, path):
    return _min_items_error(value, schema, path) + _max_items_error(value, schema, path)


def _min_items_error(value, schema, path):
    if "minItems" in schema and len(value) < schema["minItems"]:
        return [f"{path} must contain at least {schema['minItems']} items"]
    return []


def _max_items_error(value, schema, path):
    if "maxItems" in schema and len(value) > schema["maxItems"]:
        return [f"{path} must contain at most {schema['maxItems']} items"]
    return []


def _item_schema_errors(value, schema, root, path):
    item_schema = schema.get("items")
    if not isinstance(item_schema, dict):
        return []
    return _bounded_member_errors(
        enumerate(value), path,
        lambda pair: _validate(pair[1], item_schema, root, f"{path}[{pair[0]}]"))


def _object_errors(value, schema, root, path):
    """minProperties, required, properties and additionalProperties."""
    if not isinstance(value, dict):
        return []
    errors = _required_property_errors(value, schema, path)
    errors.extend(_declared_property_errors(value, schema.get("properties", {}), root, path))
    errors.extend(_extra_property_errors(value, schema, root, path))
    return errors


def _extra_property_errors(value, schema, root, path):
    additional = schema.get("additionalProperties", True)
    extras = [key for key in value if key not in schema.get("properties", {})]
    if additional is False:
        return _bounded_member_errors(
            extras, path, lambda key: [f"{_path_key(path, key)} is not allowed"])
    if isinstance(additional, dict):
        return _bounded_member_errors(
            extras, path,
            lambda key: _validate(value[key], additional, root, _path_key(path, key)))
    return []


def _required_property_errors(value, schema, path):
    errors = _min_properties_error(value, schema, path)
    errors.extend(f"{_path_key(path, key)} is required"
                  for key in schema.get("required", ()) if key not in value)
    return errors


def _min_properties_error(value, schema, path):
    if "minProperties" in schema and len(value) < schema["minProperties"]:
        return [f"{path} must contain at least {schema['minProperties']} properties"]
    return []


def _declared_property_errors(value, properties, root, path):
    errors = []
    for key, child_schema in properties.items():
        if key in value:
            errors.extend(_validate(value[key], child_schema, root, _path_key(path, key)))
    return errors


def _allowed_types(expected):
    return [expected] if isinstance(expected, str) else expected


def _type_errors(value, schema, path):
    """The declared type, which short-circuits every later keyword."""
    expected = schema.get("type")
    if expected is None:
        return []
    allowed = _allowed_types(expected)
    if any(_type_matches(value, item) for item in allowed):
        return []
    return [f"{path} must have type {allowed!r}, got {_display_type(value)!r}"]


def _validate(value, schema, root, path):
    if not isinstance(schema, dict):
        return [f"{path}: schema must be an object; Boolean schemas are unsupported"]
    errors = _reference_errors(value, schema, root, path)
    errors.extend(_combinator_errors(value, schema, root, path))
    type_errors = _type_errors(value, schema, path)
    if type_errors:
        return errors + type_errors
    return errors + _concrete_errors(value, schema, root, path)


def _reference_errors(value, schema, root, path):
    reference = schema.get("$ref")
    if reference is None:
        return []
    return _validate(value, _resolve_pointer(root, reference), root, path)


def _concrete_errors(value, schema, root, path):
    if isinstance(value, float) and not math.isfinite(value):
        return [f"{path} contains a non-finite number"]
    errors = _numeric_errors(value, schema, path)
    errors.extend(_string_errors(value, schema, path))
    errors.extend(_array_errors(value, schema, root, path))
    errors.extend(_object_errors(value, schema, root, path))
    return errors
