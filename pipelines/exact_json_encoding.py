#!/usr/bin/env python3
"""Deterministic container encoding for exact finite JSON values."""

from __future__ import annotations

import json
import math
from collections.abc import Callable, Iterable
from typing import Any, NamedTuple


class EncoderState(NamedTuple):
    """Formatting and numeric hooks threaded through the exact encoder."""

    ensure_ascii: bool
    sort_keys: bool
    indent: int | None
    exact_float_type: type[float]
    render_integer: Callable[[int], str]
    max_nesting_depth: int


def encode_exact_json(value: Any, state: EncoderState) -> str:
    """Encode one JSON value using the supplied exact-number hooks."""
    try:
        return _encode_exact_json(value, state, set(), 0)
    except RecursionError as exc:
        raise ValueError("JSON nesting exceeds the operational recursion limit") from exc


def _container_separators(state: EncoderState, depth: int) -> tuple[str, str, str]:
    """Return ``(open, item, close)`` joiners for one container level."""
    if state.indent is None:
        return "", ",", ""
    inner = "\n" + " " * (state.indent * (depth + 1))
    outer = "\n" + " " * (state.indent * depth)
    return inner, "," + inner, outer


def _encode_exact_json(
    value: Any,
    state: EncoderState,
    active: set[int],
    depth: int,
) -> str:
    if isinstance(value, (list, tuple)):
        _validate_container_depth(depth, state.max_nesting_depth)
        return _encode_sequence(value, state, active, depth)
    if isinstance(value, dict):
        _validate_container_depth(depth, state.max_nesting_depth)
        return _encode_mapping(value, state, active, depth)
    return _encode_scalar(value, state)


def _validate_container_depth(depth: int, max_nesting_depth: int) -> None:
    if depth >= max_nesting_depth:
        raise ValueError(f"JSON nesting exceeds the {max_nesting_depth}-level limit")


def _encode_scalar(value: Any, state: EncoderState) -> str:
    if value is None:
        return "null"
    if value is True:
        return "true"
    if value is False:
        return "false"
    if isinstance(value, (int, float)):
        return _encode_number(value, state)
    if isinstance(value, str):
        return _encode_json_string(value, state.ensure_ascii)
    raise TypeError(f"Object of type {type(value).__name__} is not JSON serializable")


def _encode_json_string(value: str, ensure_ascii: bool) -> str:
    """Encode one Unicode scalar string accepted by UTF-8 JSON output."""
    if any(0xD800 <= ord(character) <= 0xDFFF for character in value):
        raise ValueError("unpaired UTF-16 surrogate in JSON string")
    return json.dumps(value, ensure_ascii=ensure_ascii)


def _encode_number(value: int | float, state: EncoderState) -> str:
    """Encode one JSON number after booleans have been dispatched."""
    if isinstance(value, state.exact_float_type):
        return value.json_token
    if isinstance(value, int):
        return state.render_integer(value)
    if isinstance(value, float):
        if not math.isfinite(value):
            raise ValueError("Out of range float values are not JSON compliant")
        return json.dumps(value, allow_nan=False)
    raise TypeError(f"Object of type {type(value).__name__} is not a JSON number")


def _encode_sequence(
    value: list[Any] | tuple[Any, ...],
    state: EncoderState,
    active: set[int],
    depth: int,
) -> str:
    identity = id(value)
    if identity in active:
        raise ValueError("Circular reference detected")
    if not value:
        return "[]"
    opened, joiner, closed = _container_separators(state, depth)
    active.add(identity)
    try:
        return (
            "["
            + opened
            + joiner.join(_encode_exact_json(entry, state, active, depth + 1) for entry in value)
            + closed
            + "]"
        )
    finally:
        active.remove(identity)


def _encode_mapping(
    value: dict[str, Any],
    state: EncoderState,
    active: set[int],
    depth: int,
) -> str:
    identity = id(value)
    if identity in active:
        raise ValueError("Circular reference detected")
    keys = _mapping_keys(value, state.sort_keys)
    if not value:
        return "{}"
    active.add(identity)
    try:
        formatting = _container_separators(state, depth)
        key_separator = ":" if state.indent is None else ": "
        return _encode_mapping_items(
            value,
            keys,
            formatting,
            lambda key, entry: (
                f"{_encode_json_string(key, state.ensure_ascii)}{key_separator}"
                f"{_encode_exact_json(entry, state, active, depth + 1)}"
            ),
        )
    finally:
        active.remove(identity)


def _mapping_keys(value: dict[str, Any], sort_keys: bool) -> Iterable[str]:
    if not all(isinstance(key, str) for key in value):
        raise TypeError("JSON object keys must be strings")
    return sorted(value) if sort_keys else value


def _encode_mapping_items(
    value: dict[str, Any],
    keys: Iterable[str],
    formatting: tuple[str, str, str],
    encode_item: Callable[[str, Any], str],
) -> str:
    opened, joiner, closed = formatting
    return "{" + opened + joiner.join(encode_item(key, value[key]) for key in keys) + closed + "}"
