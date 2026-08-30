#!/usr/bin/env python3
"""Exact finite JSON numbers and deterministic stdlib-only serialization.

Python's JSON decoder normally converts every non-integer number to a binary
``float``.  That is convenient for ordinary telemetry, but it can erase units
from a spike budget before a validator sees the original decimal token.  The
wrapper below remains a real ``float`` for compatibility while retaining the
token's exact rational value for contractual arithmetic and output.
"""

from __future__ import annotations

import json
import math
from fractions import Fraction
from typing import Any


class ExactJSONFloat(float):
    """A finite JSON float that retains its exact source token."""

    def __new__(cls, token: str) -> "ExactJSONFloat":
        value = float(token)
        if not math.isfinite(value):
            raise ValueError(f"non-finite JSON number {token}")
        instance = super().__new__(cls, value)
        instance._json_token = token
        instance._fraction = Fraction(token)
        return instance

    @property
    def json_token(self) -> str:
        return self._json_token

    @property
    def fraction(self) -> Fraction:
        return self._fraction

    def __repr__(self) -> str:
        return self._json_token

    def __str__(self) -> str:
        return self._json_token


def parse_finite_json_float(token: str) -> ExactJSONFloat:
    """Decode one finite JSON number without discarding its decimal value."""

    return ExactJSONFloat(token)


def exact_fraction(value: Any) -> Fraction | None:
    """Return the exact JSON-decimal value represented by ``value``."""

    if isinstance(value, bool):
        return None
    if isinstance(value, ExactJSONFloat):
        return value.fraction
    if isinstance(value, int):
        return Fraction(value)
    if isinstance(value, float) and math.isfinite(value):
        return Fraction(str(value))
    if isinstance(value, Fraction):
        return value
    return None


def exact_json_integer(value: Any) -> int | None:
    """Return an exact schema-integer value, including decimal spellings."""

    fraction = exact_fraction(value)
    if fraction is None or fraction.denominator != 1:
        return None
    return fraction.numerator


def _finite_decimal_token(value: Fraction) -> str:
    """Render a rational with a terminating decimal expansion exactly."""

    numerator = value.numerator
    denominator = value.denominator
    twos = 0
    fives = 0
    while denominator % 2 == 0:
        denominator //= 2
        twos += 1
    while denominator % 5 == 0:
        denominator //= 5
        fives += 1
    if denominator != 1:
        raise ValueError(f"JSON number has no finite decimal expansion: {value}")
    places = max(twos, fives)
    scaled = abs(numerator) * (2 ** (places - twos)) * (5 ** (places - fives))
    digits = str(scaled)
    sign = "-" if numerator < 0 else ""
    if places == 0:
        return f"{sign}{digits}"
    digits = digits.rjust(places + 1, "0")
    integer = digits[:-places]
    decimal = digits[-places:].rstrip("0")
    return f"{sign}{integer}.{decimal}" if decimal else f"{sign}{integer}"


def json_number_from_fraction(value: Fraction) -> int | ExactJSONFloat:
    """Return a JSON-compatible number that preserves ``value`` exactly."""

    if value.denominator == 1:
        return value.numerator
    return ExactJSONFloat(_finite_decimal_token(value))


def dumps_exact_json(
    value: Any,
    *,
    ensure_ascii: bool = False,
    sort_keys: bool = True,
) -> str:
    """Serialize JSON data while emitting :class:`ExactJSONFloat` tokens raw."""

    return _encode_exact_json(value, ensure_ascii, sort_keys, set())


def _encode_exact_json(
    value: Any,
    ensure_ascii: bool,
    sort_keys: bool,
    active: set[int],
) -> str:
    if isinstance(value, (list, tuple)):
        return _encode_sequence(value, ensure_ascii, sort_keys, active)
    if isinstance(value, dict):
        return _encode_mapping(value, ensure_ascii, sort_keys, active)
    return _encode_scalar(value, ensure_ascii)


def _encode_scalar(value: Any, ensure_ascii: bool) -> str:
    if value is None:
        return "null"
    if value is True:
        return "true"
    if value is False:
        return "false"
    if isinstance(value, ExactJSONFloat):
        return value.json_token
    if isinstance(value, int):
        return str(value)
    if isinstance(value, float):
        if not math.isfinite(value):
            raise ValueError("Out of range float values are not JSON compliant")
        return json.dumps(value, allow_nan=False)
    if isinstance(value, str):
        return json.dumps(value, ensure_ascii=ensure_ascii)
    raise TypeError(f"Object of type {type(value).__name__} is not JSON serializable")


def _encode_sequence(
    value: list[Any] | tuple[Any, ...],
    ensure_ascii: bool,
    sort_keys: bool,
    active: set[int],
) -> str:
    identity = id(value)
    if identity in active:
        raise ValueError("Circular reference detected")
    active.add(identity)
    try:
        return "[" + ",".join(
            _encode_exact_json(entry, ensure_ascii, sort_keys, active) for entry in value
        ) + "]"
    finally:
        active.remove(identity)


def _encode_mapping(
    value: dict[str, Any],
    ensure_ascii: bool,
    sort_keys: bool,
    active: set[int],
) -> str:
    identity = id(value)
    if identity in active:
        raise ValueError("Circular reference detected")
    if not all(isinstance(key, str) for key in value):
        raise TypeError("JSON object keys must be strings")
    active.add(identity)
    try:
        keys = sorted(value) if sort_keys else value
        return "{" + ",".join(
            f"{json.dumps(key, ensure_ascii=ensure_ascii)}:"
            f"{_encode_exact_json(value[key], ensure_ascii, sort_keys, active)}"
            for key in keys
        ) + "}"
    finally:
        active.remove(identity)
