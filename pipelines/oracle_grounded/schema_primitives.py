"""Value- and schema-document-level primitives for the schema validator.

JSON's value model is not Python's: booleans are not numbers, ``1`` and
``1.0`` are the same number, and non-finite floats do not exist at all.
Every comparison the schema walker makes has to route through the helpers
here so those distinctions are applied the same way for ``const``, ``enum``,
``uniqueItems``, and ``type`` checks alike.

The schema-document side lives here too: strict loading, pointer resolution,
and the keyword audit that reports any assertion keyword the walker does not
enforce. None of these functions walk an instance against a schema — that is
``schema_validation``'s job.
"""

import json
import math
from functools import lru_cache
from pathlib import Path

# The assertion keywords the walker enforces, and the annotation keywords
# the checked-in schemas deliberately carry.  Any other keyword on a schema
# object would be an assertion the walker silently skips, so its presence
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


def _bools_equal(left, right):
    """Booleans compare only to booleans, never to 0/1."""
    return isinstance(left, bool) and isinstance(right, bool) and left is right


def _scalar_json_equal(left, right):
    """Decide bool, number, and mismatched-type equality; None means the
    values are same-typed containers (or opaque values) still to compare."""
    if isinstance(left, bool) or isinstance(right, bool):
        return _bools_equal(left, right)
    if isinstance(left, (int, float)) and isinstance(right, (int, float)):
        return left == right
    if type(left) is not type(right):
        return False
    return None


def _sequence_equal(left, right):
    return len(left) == len(right) and all(
        _json_equal(a, b) for a, b in zip(left, right, strict=True)
    )


def _mapping_equal(left, right):
    return left.keys() == right.keys() and all(
        _json_equal(left[key], right[key]) for key in left
    )


def _json_equal(left, right):
    """JSON-value equality, keeping booleans distinct from numbers."""
    scalar = _scalar_json_equal(left, right)
    if scalar is not None:
        return scalar
    if isinstance(left, list):
        return _sequence_equal(left, right)
    if isinstance(left, dict):
        return _mapping_equal(left, right)
    return left == right


def _numeric_key(value):
    """uniqueItems equality treats ``1`` and ``1.0`` as the same number."""
    if isinstance(value, float) and not math.isfinite(value):
        return "nan" if math.isnan(value) else ("inf" if value > 0 else "-inf")
    if value == math.trunc(value):
        return int(math.trunc(value))
    return float(value)


def _scalar_key(value):
    if isinstance(value, bool):
        return "bool", value
    if value is None:
        return ("null",)
    if isinstance(value, str):
        return "str", value
    if isinstance(value, (int, float)):
        return "num", _numeric_key(value)
    return None


def _container_key(value):
    if isinstance(value, list):
        return "arr", tuple(_unique_item_key(item) for item in value)
    if isinstance(value, dict):
        return (
            "obj",
            tuple(sorted((key, _unique_item_key(item)) for key, item in value.items())),
        )
    return None


def _unique_item_key(value):
    """Hashable key with JSON uniqueItems equality (bools ≠ numbers, 1 == 1.0)."""
    scalar = _scalar_key(value)
    if scalar is not None:
        return scalar
    container = _container_key(value)
    if container is not None:
        return container
    return "other", type(value).__name__, repr(value)


def _is_json_integer(value):
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


def _is_json_number(value):
    return (
        isinstance(value, (int, float))
        and not isinstance(value, bool)
        and (not isinstance(value, float) or math.isfinite(value))
    )


_TYPE_CHECKS = {
    "null": lambda value: value is None,
    "boolean": lambda value: isinstance(value, bool),
    "integer": _is_json_integer,
    "number": _is_json_number,
    "string": lambda value: isinstance(value, str),
    "array": lambda value: isinstance(value, list),
    "object": lambda value: isinstance(value, dict),
}


def _type_matches(value, expected):
    check = _TYPE_CHECKS.get(expected)
    return check(value) if check is not None else False


def _float_display(value):
    # A non-finite float fails the "number" type check, so displaying it
    # as plain "number" would produce a self-contradictory finding.
    return "number" if math.isfinite(value) else "non-finite number"


# Order matters: ``bool`` must be tested before ``int`` because Python bools
# are int subclasses, while the remaining types are mutually disjoint.
_DISPLAY_TYPES = (
    (bool, "boolean"),
    (int, "integer"),
    (str, "string"),
    (list, "array"),
    (dict, "object"),
)


def _display_type(value):
    if value is None:
        return "null"
    if isinstance(value, float):
        return _float_display(value)
    for kind, name in _DISPLAY_TYPES:
        if isinstance(value, kind):
            return name
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


def _mapping_nonfinite_errors(value, path):
    errors = []
    for key, item in value.items():
        errors.extend(_nonfinite_errors(item, _path_key(path, key)))
    return errors


def _sequence_nonfinite_errors(value, path):
    errors = []
    for index, item in enumerate(value):
        errors.extend(_nonfinite_errors(item, f"{path}[{index}]"))
    return errors


def _nonfinite_errors(value, path="$"):
    """Every non-finite float in ``value``, found without a schema."""
    if isinstance(value, float) and not math.isfinite(value):
        return [f"{path} contains a non-finite number"]
    if isinstance(value, dict):
        return _mapping_nonfinite_errors(value, path)
    if isinstance(value, list):
        return _sequence_nonfinite_errors(value, path)
    return []


def _unknown_keyword_errors(schema, path):
    """The one-object check: keywords outside the enforced + annotation sets."""
    unknown = sorted(set(schema) - ENFORCED_KEYWORDS - ANNOTATION_KEYWORDS)
    if not unknown:
        return []
    return [f"schema object at {path} uses unenforced keywords: {', '.join(unknown)}"]


def _member_map_keyword_errors(members, prefix):
    """Audit one named-children mapping ($defs or properties)."""
    if not isinstance(members, dict):
        return []
    errors = []
    for key, sub in members.items():
        errors.extend(_unsupported_keyword_errors(sub, f"{prefix}/{key}"))
    return errors


def _named_member_keyword_errors(schema, path):
    """$defs and properties hold named child schemas."""
    errors = []
    for name in ("$defs", "properties"):
        errors.extend(_member_map_keyword_errors(schema.get(name), f"{path}/{name}"))
    return errors


def _direct_child_keyword_errors(schema, path):
    """items, not and additionalProperties hold one child schema each."""
    errors = []
    for name in ("items", "not", "additionalProperties"):
        errors.extend(_unsupported_keyword_errors(schema.get(name), f"{path}/{name}"))
    return errors


def _any_of_keyword_errors(schema, path):
    """anyOf holds a list of child schemas."""
    errors = []
    options = schema.get("anyOf")
    if isinstance(options, list):
        for index, sub in enumerate(options):
            errors.extend(_unsupported_keyword_errors(sub, f"{path}/anyOf/{index}"))
    return errors


def _unsupported_keyword_errors(schema, path="#"):
    """Schema objects that carry keywords the walker does not enforce."""
    if not isinstance(schema, dict):
        return []
    errors = _unknown_keyword_errors(schema, path)
    errors.extend(_named_member_keyword_errors(schema, path))
    errors.extend(_direct_child_keyword_errors(schema, path))
    errors.extend(_any_of_keyword_errors(schema, path))
    return errors


@lru_cache(maxsize=None)
def _schema_keyword_findings(path):
    """Cached whole-document keyword audit for one schema file."""
    return tuple(_unsupported_keyword_errors(_load_schema(path)))
