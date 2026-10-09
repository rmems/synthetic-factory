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


def _bounds_findings(schema: Mapping[str, Any], value: Any, where: str) -> list[str]:
    findings = []
    if (
        "minimum" in schema
        and (_is_int(value) or isinstance(value, float))
        and value < schema["minimum"]
    ):
        findings.append(f"{where}: must be at least {schema['minimum']}")
    if (
        "maximum" in schema
        and (_is_int(value) or isinstance(value, float))
        and value > schema["maximum"]
    ):
        findings.append(f"{where}: must be at most {schema['maximum']}")
    if "minLength" in schema and isinstance(value, str) and len(value) < schema["minLength"]:
        findings.append(f"{where}: must be at least {schema['minLength']} characters")
    return findings


def _object_findings(schema: Mapping[str, Any], value: Mapping[str, Any], where: str) -> list[str]:
    findings = []
    properties = schema.get("properties") or {}
    for name in schema.get("required") or ():
        if name not in value:
            findings.append(f"{where}: missing required property {name!r}")
    if schema.get("additionalProperties") is False:
        for name in value:
            if name not in properties:
                findings.append(f"{where}: unexpected property {name!r}")
    for name, child in properties.items():
        if name in value:
            findings.extend(validate_args(child, value[name], f"{where}.{name}"))
    return findings


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
