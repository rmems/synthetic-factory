"""Small, stdlib-only JSON Schema validator for oracle-grounded records.

The repository publishes Draft 2020-12 schemas, but the runnable factory has a
stdlib-only contract.  Pulling in ``jsonschema`` just for the curation gate
would make validation depend on an optional environment package, so this
module implements the deliberately small keyword subset used by the checked-in
schemas.  Unsupported schema keywords remain annotations; every assertion
keyword currently present in ``schemas/oracle-grounded*.json`` is enforced.
"""

import json
import math
import re
from functools import lru_cache
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
BASE_SCHEMA_PATH = REPO_ROOT / "schemas" / "oracle-grounded-v1.schema.json"
FAMILY_SCHEMA_DIR = REPO_ROOT / "schemas" / "oracle-grounded"


def _reject_constant(value):
    raise ValueError(f"non-finite JSON number {value!r}")


@lru_cache(maxsize=None)
def _load_schema(path):
    with Path(path).open(encoding="utf-8") as handle:
        return json.load(handle, parse_constant=_reject_constant)


def _json_equal(left, right):
    """JSON-value equality, keeping booleans distinct from numbers."""
    if isinstance(left, bool) or isinstance(right, bool):
        return isinstance(left, bool) and isinstance(right, bool) and left is right
    if isinstance(left, (int, float)) and isinstance(right, (int, float)):
        return left == right
    if type(left) is not type(right):
        return False
    if isinstance(left, list):
        return len(left) == len(right) and all(
            _json_equal(a, b) for a, b in zip(left, right, strict=True)
        )
    if isinstance(left, dict):
        return left.keys() == right.keys() and all(
            _json_equal(left[key], right[key]) for key in left
        )
    return left == right


def _type_matches(value, expected):
    if expected == "null":
        return value is None
    if expected == "boolean":
        return isinstance(value, bool)
    if expected == "integer":
        # Draft 2020-12 defines ``integer`` mathematically rather than by the
        # host language's concrete JSON decoder type.  Thus ``1.0`` is an
        # integer, while booleans (Python int subclasses), fractional values,
        # and non-finite floats are not.
        return (
            isinstance(value, (int, float))
            and not isinstance(value, bool)
            and (not isinstance(value, float) or math.isfinite(value))
            and value == math.trunc(value)
        )
    if expected == "number":
        return (
            isinstance(value, (int, float))
            and not isinstance(value, bool)
            and (not isinstance(value, float) or math.isfinite(value))
        )
    if expected == "string":
        return isinstance(value, str)
    if expected == "array":
        return isinstance(value, list)
    if expected == "object":
        return isinstance(value, dict)
    return False


def _display_type(value):
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "boolean"
    if isinstance(value, int):
        return "integer"
    if isinstance(value, float):
        return "number"
    if isinstance(value, str):
        return "string"
    if isinstance(value, list):
        return "array"
    if isinstance(value, dict):
        return "object"
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


def _validate(value, schema, root, path):
    errors = []

    reference = schema.get("$ref")
    if reference is not None:
        errors.extend(_validate(value, _resolve_pointer(root, reference), root, path))

    if "const" in schema and not _json_equal(value, schema["const"]):
        errors.append(f"{path} must equal {schema['const']!r}")
    if "enum" in schema and not any(_json_equal(value, item) for item in schema["enum"]):
        errors.append(f"{path} must be one of {schema['enum']!r}")

    if "not" in schema and not _validate(value, schema["not"], root, path):
        errors.append(f"{path} matches a forbidden schema")

    if "anyOf" in schema and not any(
        not _validate(value, option, root, path) for option in schema["anyOf"]
    ):
        errors.append(f"{path} does not match any allowed schema")

    expected = schema.get("type")
    if expected is not None:
        allowed = [expected] if isinstance(expected, str) else expected
        if not any(_type_matches(value, item) for item in allowed):
            errors.append(f"{path} must have type {allowed!r}, got {_display_type(value)!r}")
            return errors

    if isinstance(value, float) and not math.isfinite(value):
        errors.append(f"{path} contains a non-finite number")
        return errors

    if isinstance(value, (int, float)) and not isinstance(value, bool):
        if "minimum" in schema and value < schema["minimum"]:
            errors.append(f"{path} must be >= {schema['minimum']!r}")
        if "maximum" in schema and value > schema["maximum"]:
            errors.append(f"{path} must be <= {schema['maximum']!r}")
        if "exclusiveMinimum" in schema and value <= schema["exclusiveMinimum"]:
            errors.append(f"{path} must be > {schema['exclusiveMinimum']!r}")
        if "exclusiveMaximum" in schema and value >= schema["exclusiveMaximum"]:
            errors.append(f"{path} must be < {schema['exclusiveMaximum']!r}")

    if isinstance(value, str):
        if "minLength" in schema and len(value) < schema["minLength"]:
            errors.append(f"{path} must contain at least {schema['minLength']} characters")
        if "pattern" in schema and re.search(schema["pattern"], value) is None:
            errors.append(f"{path} does not match pattern {schema['pattern']!r}")

    if isinstance(value, list):
        if "minItems" in schema and len(value) < schema["minItems"]:
            errors.append(f"{path} must contain at least {schema['minItems']} items")
        if "maxItems" in schema and len(value) > schema["maxItems"]:
            errors.append(f"{path} must contain at most {schema['maxItems']} items")
        if schema.get("uniqueItems"):
            for index, item in enumerate(value):
                if any(_json_equal(item, earlier) for earlier in value[:index]):
                    errors.append(f"{path} must contain unique items")
                    break
        item_schema = schema.get("items")
        if isinstance(item_schema, dict):
            for index, item in enumerate(value):
                errors.extend(_validate(item, item_schema, root, f"{path}[{index}]"))

    if isinstance(value, dict):
        if "minProperties" in schema and len(value) < schema["minProperties"]:
            errors.append(f"{path} must contain at least {schema['minProperties']} properties")
        required = schema.get("required", ())
        for key in required:
            if key not in value:
                errors.append(f"{_path_key(path, key)} is required")
        properties = schema.get("properties", {})
        for key, child_schema in properties.items():
            if key in value:
                errors.extend(_validate(value[key], child_schema, root, _path_key(path, key)))
        additional = schema.get("additionalProperties", True)
        extras = [key for key in value if key not in properties]
        if additional is False:
            for key in extras:
                errors.append(f"{_path_key(path, key)} is not allowed")
        elif isinstance(additional, dict):
            for key in extras:
                errors.extend(_validate(value[key], additional, root, _path_key(path, key)))
    return errors


def _nonfinite_errors(value, path="$"):
    errors = []
    if isinstance(value, float) and not math.isfinite(value):
        return [f"{path} contains a non-finite number"]
    if isinstance(value, dict):
        for key, item in value.items():
            errors.extend(_nonfinite_errors(item, _path_key(path, key)))
    elif isinstance(value, list):
        for index, item in enumerate(value):
            errors.extend(_nonfinite_errors(item, f"{path}[{index}]"))
    return errors


def validate_record_schemas(instance, family, include_validation=True):
    """Return base- and family-schema findings for one record.

    ``build_record`` assesses a provisional envelope before its validation
    block exists.  In that one mode the base schema ignores only the
    ``validation`` property; all other required and family semantics still run.
    """
    findings = _nonfinite_errors(instance)
    base = _load_schema(str(BASE_SCHEMA_PATH))
    if not include_validation:
        base = dict(base)
        base["required"] = [key for key in base.get("required", ()) if key != "validation"]
        base["properties"] = {
            key: value for key, value in base.get("properties", {}).items() if key != "validation"
        }
    findings.extend(f"base schema: {item}" for item in _validate(instance, base, base, "$"))

    family_path = FAMILY_SCHEMA_DIR / f"{family}.schema.json"
    family_schema = _load_schema(str(family_path))
    findings.extend(
        f"family schema: {item}" for item in _validate(instance, family_schema, family_schema, "$")
    )
    return findings
