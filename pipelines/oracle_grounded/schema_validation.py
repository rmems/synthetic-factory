"""Small, stdlib-only JSON Schema validator for oracle-grounded records.

The repository publishes Draft 2020-12 schemas, but the runnable factory has a
stdlib-only contract.  Pulling in ``jsonschema`` just for the curation gate
would make validation depend on an optional environment package, so this
module implements the deliberately small keyword subset used by the checked-in
schemas.  A schema object carrying any keyword outside that subset (plus the
allowed annotations) is itself a finding from ``validate_record_schemas``, so
a future schema cannot silently weaken the gate by using an assertion this
validator does not enforce.
"""

import json
import math
import operator
import re
from functools import lru_cache
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
BASE_SCHEMA_PATH = REPO_ROOT / "schemas" / "oracle-grounded-v1.schema.json"
FAMILY_SCHEMA_DIR = REPO_ROOT / "schemas" / "oracle-grounded"
# Per-frame cap on accumulated findings. Anything past this on one array or
# object adds a single summary line instead of one string per element.
MAX_SCHEMA_FINDINGS = 100

# The assertion keywords ``_validate`` enforces, and the annotation keywords
# the checked-in schemas deliberately carry.  Any other keyword on a schema
# object would be an assertion this validator silently skips, so its presence
# is itself a finding: records must never validate against a weaker gate than
# the schema on disk declares.
ENFORCED_KEYWORDS = frozenset(
    {
        "$ref",
        "anyOf",
        "not",
        "const",
        "enum",
        "type",
        "minimum",
        "maximum",
        "exclusiveMinimum",
        "exclusiveMaximum",
        "minLength",
        "pattern",
        "minItems",
        "maxItems",
        "uniqueItems",
        "items",
        "minProperties",
        "required",
        "properties",
        "additionalProperties",
    }
)
ANNOTATION_KEYWORDS = frozenset({"$schema", "$id", "$defs", "title", "description"})


def _reject_constant(value):
    raise ValueError(f"non-finite JSON number {value!r}")


def _parse_finite_float(text):
    """parse_constant only sees the bare NaN/Infinity tokens; a numeric
    literal that merely overflows to inf (1e400) must be refused here."""
    parsed = float(text)
    if not math.isfinite(parsed):
        raise ValueError(f"JSON numeric literal is not finitely representable: {text}")
    return parsed


@lru_cache(maxsize=None)
def _load_schema(path):
    with Path(path).open(encoding="utf-8") as handle:
        return json.load(
            handle, parse_constant=_reject_constant, parse_float=_parse_finite_float
        )


def _json_equal(left, right):
    """JSON-value equality, keeping booleans distinct from numbers."""
    if isinstance(left, bool) or isinstance(right, bool):
        return _boolean_equal(left, right)
    if isinstance(left, (int, float)) and isinstance(right, (int, float)):
        return left == right
    if type(left) is not type(right):
        return False
    return _same_type_equal(left, right)


def _boolean_equal(left, right):
    return isinstance(left, bool) and isinstance(right, bool) and left is right


def _same_type_equal(left, right):
    if isinstance(left, list):
        return _list_equal(left, right)
    if isinstance(left, dict):
        return _mapping_equal(left, right)
    return left == right


def _list_equal(left, right):
    return len(left) == len(right) and all(
        _json_equal(a, b) for a, b in zip(left, right, strict=True)
    )


def _mapping_equal(left, right):
    return left.keys() == right.keys() and all(
        _json_equal(left[key], right[key]) for key in left
    )


def _unique_item_key(value):
    """Hashable key with JSON uniqueItems equality (bools ≠ numbers, 1 == 1.0)."""
    if isinstance(value, bool):
        return ("bool", value)
    if value is None:
        return ("null",)
    if isinstance(value, str):
        return ("str", value)
    if isinstance(value, (int, float)):
        return _numeric_item_key(value)
    return _compound_item_key(value)


def _compound_item_key(value):
    if isinstance(value, list):
        return ("arr", tuple(_unique_item_key(item) for item in value))
    if isinstance(value, dict):
        return (
            "obj",
            tuple(sorted((key, _unique_item_key(item)) for key, item in value.items())),
        )
    return ("other", type(value).__name__, repr(value))


def _numeric_item_key(value):
    if isinstance(value, float) and not math.isfinite(value):
        return ("num", _nonfinite_key(value))
    if value == math.trunc(value):
        return ("num", int(math.trunc(value)))
    return ("num", float(value))


def _nonfinite_key(value):
    if math.isnan(value):
        return "nan"
    return "inf" if value > 0 else "-inf"


def _finite_number(value):
    return (isinstance(value, (int, float)) and not isinstance(value, bool)
            and (not isinstance(value, float) or math.isfinite(value)))


def _type_matches(value, expected):
    if expected == "number":
        return _finite_number(value)
    if expected == "integer":
        # Draft integers include finite integral floats, but never booleans.
        return _finite_number(value) and value == math.trunc(value)
    classes = {"null": type(None), "boolean": bool, "string": str,
               "array": list, "object": dict}
    expected_class = classes.get(expected) if isinstance(expected, str) else None
    return expected_class is not None and isinstance(value, expected_class)


def _display_type(value):
    if isinstance(value, float):
        return "number" if math.isfinite(value) else "non-finite number"
    for expected_class, label in ((type(None), "null"), (bool, "boolean"),
                                  (int, "integer"), (str, "string"),
                                  (list, "array"), (dict, "object")):
        if isinstance(value, expected_class):
            return label
    return type(value).__name__


def _resolve_pointer(root, reference):
    if not reference.startswith("#/"):
        raise ValueError(f"only local schema references are supported: {reference!r}")
    value = root
    for raw in reference[2:].split("/"):
        token = raw.replace("~1", "/").replace("~0", "~")
        value = value[token]
    return value


def _path_key(path, key):
    return f"{path}.{key}" if isinstance(key, str) and key.isidentifier() else f"{path}[{key!r}]"


def _literal_errors(value, schema, path):
    errors = []
    if "const" in schema and not _json_equal(value, schema["const"]):
        errors.append(f"{path} must equal {schema['const']!r}")
    if "enum" in schema and not any(_json_equal(value, item) for item in schema["enum"]):
        errors.append(f"{path} must be one of {schema['enum']!r}")
    return errors


def _combinator_errors(value, schema, root, path):
    """const, enum, not and anyOf, preserving refusal order."""
    errors = _literal_errors(value, schema, path)
    if "not" in schema and not _validate(value, schema["not"], root, path):
        errors.append(f"{path} matches a forbidden schema")
    if "anyOf" in schema and not any(
        not _validate(value, option, root, path) for option in schema["anyOf"]
    ):
        errors.append(f"{path} does not match any allowed schema")
    return errors


def _numeric_errors(value, schema, path):
    """minimum, maximum and their exclusive forms, in declaration order."""
    if not isinstance(value, (int, float)) or isinstance(value, bool):
        return []
    bounds = (("minimum", operator.lt, ">="), ("maximum", operator.gt, "<="),
              ("exclusiveMinimum", operator.le, ">"), ("exclusiveMaximum", operator.ge, "<"))
    return [f"{path} must be {relation} {schema[key]!r}"
            for key, violates, relation in bounds if key in schema and violates(value, schema[key])]


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


def _extend_bounded(errors, members, path, findings):
    for member in members:
        if _budget_exhausted(errors, path):
            break
        errors.extend(findings(member))


def _array_errors(value, schema, root, path):
    """minItems, maxItems, uniqueItems and items."""
    if not isinstance(value, list):
        return []
    errors = _array_bounds(value, schema, path)
    if schema.get("uniqueItems"):
        errors.extend(_unique_items_errors(value, path))
    item_schema = schema.get("items")
    if isinstance(item_schema, dict):
        _extend_bounded(errors, enumerate(value), path,
                        lambda pair: _validate(pair[1], item_schema, root, f"{path}[{pair[0]}]"))
    return errors


def _array_bounds(value, schema, path):
    errors = []
    if "minItems" in schema and len(value) < schema["minItems"]:
        errors.append(f"{path} must contain at least {schema['minItems']} items")
    if "maxItems" in schema and len(value) > schema["maxItems"]:
        errors.append(f"{path} must contain at most {schema['maxItems']} items")
    return errors


def _object_errors(value, schema, root, path):
    """minProperties, required, properties and additionalProperties."""
    if not isinstance(value, dict):
        return []
    errors = _required_property_errors(value, schema, path)
    properties = schema.get("properties", {})
    errors.extend(_declared_property_errors(value, properties, root, path))
    additional = schema.get("additionalProperties", True)
    extras = [key for key in value if key not in properties]
    if additional is False:
        _extend_bounded(errors, extras, path, lambda key: [f"{_path_key(path, key)} is not allowed"])
    elif isinstance(additional, dict):
        _extend_bounded(errors, extras, path,
                        lambda key: _validate(value[key], additional, root, _path_key(path, key)))
    return errors


def _required_property_errors(value, schema, path):
    errors = []
    if "minProperties" in schema and len(value) < schema["minProperties"]:
        errors.append(f"{path} must contain at least {schema['minProperties']} properties")
    errors.extend(f"{_path_key(path, key)} is required"
                  for key in schema.get("required", ()) if key not in value)
    return errors


def _declared_property_errors(value, properties, root, path):
    errors = []
    for key, child_schema in properties.items():
        if key in value:
            errors.extend(_validate(value[key], child_schema, root, _path_key(path, key)))
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
    if not isinstance(schema, dict):
        return [f"{path}: schema must be an object; Boolean schemas are unsupported"]
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


def _value_children(value, path):
    if isinstance(value, dict):
        return ((item, _path_key(path, key)) for key, item in value.items())
    if isinstance(value, list):
        return ((item, f"{path}[{index}]") for index, item in enumerate(value))
    return ()


def _nonfinite_errors(value, path="$"):
    if isinstance(value, float) and not math.isfinite(value):
        return [f"{path} contains a non-finite number"]
    errors = []
    for item, child_path in _value_children(value, path):
        errors.extend(_nonfinite_errors(item, child_path))
    return errors


def _schema_mapping_children(schema, path):
    for name in ("$defs", "properties"):
        members = schema.get(name)
        if isinstance(members, dict):
            yield from ((sub, f"{path}/{name}/{key}") for key, sub in members.items())


def _schema_children(schema, path):
    yield from _schema_mapping_children(schema, path)
    for name in ("items", "not", "additionalProperties"):
        if name not in schema:
            continue
        child = schema[name]
        if name == "additionalProperties" and isinstance(child, bool):
            continue
        yield child, f"{path}/{name}"
    options = schema.get("anyOf")
    if isinstance(options, list):
        yield from ((sub, f"{path}/anyOf/{index}") for index, sub in enumerate(options))


def _unsupported_keyword_errors(schema, path="#"):
    """Schema objects that carry keywords ``_validate`` does not enforce."""
    if not isinstance(schema, dict):
        return [f"schema at {path} must be an object; Boolean schemas are unsupported"]
    errors = []
    unknown = sorted(set(schema) - ENFORCED_KEYWORDS - ANNOTATION_KEYWORDS)
    if unknown:
        errors.append(
            f"schema object at {path} uses unenforced keywords: {', '.join(unknown)}"
        )
    for sub, child_path in _schema_children(schema, path):
        errors.extend(_unsupported_keyword_errors(sub, child_path))
    return errors


@lru_cache(maxsize=None)
def _schema_keyword_findings(path):
    """Cached whole-document keyword audit for one schema file."""
    return tuple(_unsupported_keyword_errors(_load_schema(path)))


def validate_record_schemas(instance, family, include_validation=True):
    """Return base- and family-schema findings for one record.

    ``build_record`` assesses a provisional envelope before its validation
    block exists.  In that one mode the base schema ignores only the
    ``validation`` property; all other required and family semantics still run.
    """
    findings = _nonfinite_errors(instance)
    findings.extend(f"base schema: {item}" for item in _document_findings(
        instance, BASE_SCHEMA_PATH, include_validation,
    ))
    scenario = instance.get('scenario')
    profile = scenario.get('profile') if isinstance(scenario, dict) else None
    if profile is not None:
        from .native_profiles import PROFILES
        if PROFILES.get(family) != profile:
            return findings + ['unsupported crate-native family/profile combination']
    family_path = FAMILY_SCHEMA_DIR / f"{profile or family}.schema.json"
    findings.extend(f"family schema: {item}" for item in _document_findings(instance, family_path))
    return findings


def _document_findings(instance, path, include_validation=True):
    findings = list(_schema_keyword_findings(str(path)))
    if findings:
        return findings
    schema = _load_schema(str(path))
    if not include_validation:
        schema = dict(schema)
        schema["required"] = [key for key in schema.get("required", ()) if key != "validation"]
        properties = dict(schema.get("properties", {}))
        # Provisional envelopes keep the validation key allowed without its completed shape.
        properties["validation"] = {"type": "object"}
        schema["properties"] = properties
    return _validate(instance, schema, schema, "$")
