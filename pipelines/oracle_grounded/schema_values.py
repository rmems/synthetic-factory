"""JSON-value algebra for the oracle-grounded schema validator.

Value equality, ``uniqueItems`` keys, type checks, and the non-finite walk
are pure functions over decoded JSON; they carry no schema state, so they
sit apart from the keyword assertions in ``schema_keywords``.
"""

import math


def _path_key(path, key):
    return f"{path}.{key}" if isinstance(key, str) and key.isidentifier() else f"{path}[{key!r}]"


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
        return ("null", None)
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
    return ("other", (type(value).__name__, repr(value)))


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
