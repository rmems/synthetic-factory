#!/usr/bin/env python3
"""The JSON-schema subset tool arguments are validated against.

Supports ``type`` (object, string, integer, number, boolean, array, null),
``required``, ``properties``, ``additionalProperties: false``, ``enum``,
``minimum`` / ``maximum``, ``minLength``, and ``items``. A boolean is never an
integer. The validator returns prose findings in document order so a schema
error observation is deterministic.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

from ._contract import bind_import_twin

__all__ = ["SUPPORTED_KEYWORDS", "check_schema", "validate_args"]

SUPPORTED_KEYWORDS = frozenset(
    {
        "type",
        "required",
        "properties",
        "additionalProperties",
        "enum",
        "minimum",
        "maximum",
        "minLength",
        "items",
        "description",
    }
)
_TYPES = ("object", "string", "integer", "number", "boolean", "array", "null")


def _is_int(value: Any) -> bool:
    return isinstance(value, int) and not isinstance(value, bool)


def _type_matches(expected: str, value: Any) -> bool:
    checks = {
        "object": lambda item: isinstance(item, Mapping),
        "string": lambda item: isinstance(item, str),
        "integer": _is_int,
        "number": lambda item: _is_int(item) or isinstance(item, float),
        "boolean": lambda item: isinstance(item, bool),
        "array": lambda item: isinstance(item, list),
        "null": lambda item: item is None,
    }
    return checks[expected](value)


def check_schema(schema: Any, where: str = "schema") -> list[str]:
    """Findings about a schema that uses keywords outside the subset."""
    if not isinstance(schema, Mapping):
        return [f"{where}: schema must be an object"]
    findings = [
        f"{where}: unsupported keyword {key!r}" for key in schema if key not in SUPPORTED_KEYWORDS
    ]
    declared = schema.get("type")
    if declared is not None and declared not in _TYPES:
        findings.append(f"{where}: unsupported type {declared!r}")
    properties = schema.get("properties")
    if properties is not None:
        if not isinstance(properties, Mapping):
            findings.append(f"{where}: properties must be an object")
        else:
            for name, child in properties.items():
                findings.extend(check_schema(child, f"{where}.{name}"))
    if "items" in schema:
        findings.extend(check_schema(schema["items"], f"{where}.items"))
    return findings


def _enum_findings(schema: Mapping[str, Any], value: Any, where: str) -> list[str]:
    allowed = schema.get("enum")
    if allowed is None or value in allowed:
        return []
    return [f"{where}: must be one of {list(allowed)!r}"]


def _is_number(value: Any) -> bool:
    return _is_int(value) or isinstance(value, float)


def _is_str(value: Any) -> bool:
    return isinstance(value, str)


# (keyword, the values it bounds, how a value breaks it, the finding it yields)
_BOUNDS = (
    ("minimum", _is_number, lambda value, bound: value < bound, "must be at least {}"),
    ("maximum", _is_number, lambda value, bound: value > bound, "must be at most {}"),
    (
        "minLength",
        _is_str,
        lambda value, bound: len(value) < bound,
        "must be at least {} characters",
    ),
)


def _bounds_findings(schema: Mapping[str, Any], value: Any, where: str) -> list[str]:
    return [
        f"{where}: {message.format(schema[keyword])}"
        for keyword, applies, broken, message in _BOUNDS
        if keyword in schema and applies(value) and broken(value, schema[keyword])
    ]


def _missing_findings(schema: Mapping[str, Any], value: Mapping[str, Any], where: str) -> list[str]:
    return [
        f"{where}: missing required property {name!r}"
        for name in schema.get("required") or ()
        if name not in value
    ]


def _unexpected_findings(
    schema: Mapping[str, Any], value: Mapping[str, Any], where: str
) -> list[str]:
    if schema.get("additionalProperties") is not False:
        return []
    properties = schema.get("properties") or {}
    return [f"{where}: unexpected property {name!r}" for name in value if name not in properties]


def _property_findings(
    schema: Mapping[str, Any], value: Mapping[str, Any], where: str
) -> list[str]:
    findings = []
    for name, child in (schema.get("properties") or {}).items():
        if name in value:
            findings.extend(validate_args(child, value[name], f"{where}.{name}"))
    return findings


def _object_findings(schema: Mapping[str, Any], value: Mapping[str, Any], where: str) -> list[str]:
    return (
        _missing_findings(schema, value, where)
        + _unexpected_findings(schema, value, where)
        + _property_findings(schema, value, where)
    )


def _array_findings(schema: Mapping[str, Any], value: Sequence[Any], where: str) -> list[str]:
    item_schema = schema.get("items")
    if item_schema is None:
        return []
    findings = []
    for index, item in enumerate(value):
        findings.extend(validate_args(item_schema, item, f"{where}[{index}]"))
    return findings


def validate_args(schema: Mapping[str, Any], value: Any, where: str = "args") -> list[str]:
    """Findings for ``value`` against ``schema``; empty means the value conforms."""
    declared = schema.get("type")
    if declared is not None and not _type_matches(declared, value):
        return [f"{where}: expected {declared}, got {type(value).__name__}"]
    findings = _enum_findings(schema, value, where) + _bounds_findings(schema, value, where)
    if isinstance(value, Mapping):
        findings.extend(_object_findings(schema, value, where))
    elif isinstance(value, list):
        findings.extend(_array_findings(schema, value, where))
    return findings


bind_import_twin(__name__)
