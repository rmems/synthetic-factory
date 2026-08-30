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


# Bound decimal expansion before Fraction construction.  Short tokens such as
# ``1e-100000000`` are valid JSON but otherwise amplify into enormous integer
# denominators.  The limit comfortably covers every finite IEEE-754 decimal
# while keeping parsing and exact serialization operationally bounded.
MAX_DECIMAL_DIGITS = 4096
_MAX_JSON_NUMBER_TOKEN_LENGTH = MAX_DECIMAL_DIGITS + 32
_MAX_EXPONENT_DIGITS = len(str(MAX_DECIMAL_DIGITS))
_MAX_DECIMAL_BITS = (MAX_DECIMAL_DIGITS * 3322 // 1000) + 8


def _bounded_exponent(marker: str, exponent_text: str) -> int:
    if not marker:
        return 0
    exponent_digits = exponent_text.lstrip("+-")
    significant_digits = exponent_digits.lstrip("0") or "0"
    if not exponent_digits or len(significant_digits) > _MAX_EXPONENT_DIGITS:
        raise ValueError("JSON number exponent exceeds the exact-decimal limit")
    exponent = int(exponent_text)
    if abs(exponent) > MAX_DECIMAL_DIGITS:
        raise ValueError("JSON number exponent exceeds the exact-decimal limit")
    return exponent


def _decimal_shape(mantissa: str) -> tuple[int, int]:
    coefficient = mantissa.lstrip("-")
    integer, decimal_point, fraction = coefficient.partition(".")
    return len(integer) + len(fraction), len(fraction) if decimal_point else 0


def _validate_decimal_token_bounds(token: str) -> None:
    """Reject a decimal token whose exact expansion exceeds fixed bounds."""

    if not isinstance(token, str) or len(token) > _MAX_JSON_NUMBER_TOKEN_LENGTH:
        raise ValueError("JSON number token exceeds the exact-decimal limit")
    mantissa, marker, exponent_text = token.lower().partition("e")
    exponent = _bounded_exponent(marker, exponent_text)
    coefficient_digits, decimal_places = _decimal_shape(mantissa)
    if coefficient_digits > MAX_DECIMAL_DIGITS:
        raise ValueError("JSON number precision exceeds the exact-decimal limit")
    if abs(decimal_places - exponent) > MAX_DECIMAL_DIGITS:
        raise ValueError("JSON number scale exceeds the exact-decimal limit")


def _validate_fraction_bounds(value: Fraction) -> None:
    """Reject a rational too large to render as a bounded JSON decimal."""

    if abs(value.numerator).bit_length() > _MAX_DECIMAL_BITS:
        raise ValueError("JSON number numerator exceeds the exact-decimal limit")
    if value.denominator.bit_length() > _MAX_DECIMAL_BITS:
        raise ValueError("JSON number denominator exceeds the exact-decimal limit")


class ExactJSONFloat(float):
    """A finite JSON float that retains its exact source token."""

    def __new__(cls, token: str) -> "ExactJSONFloat":
        _validate_decimal_token_bounds(token)
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

    def __copy__(self) -> "ExactJSONFloat":
        return self

    def __deepcopy__(self, memo: dict[int, Any]) -> "ExactJSONFloat":
        return self

    def __reduce__(self) -> tuple[type["ExactJSONFloat"], tuple[str]]:
        return type(self), (self._json_token,)


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


def _decimal_factor_counts(denominator: int) -> tuple[int, int]:
    twos = 0
    fives = 0
    while denominator % 2 == 0:
        denominator //= 2
        twos += 1
    while denominator % 5 == 0:
        denominator //= 5
        fives += 1
    if denominator != 1:
        raise ValueError("JSON number has no finite decimal expansion")
    return twos, fives


def _render_scaled_decimal(numerator: int, scaled: int, places: int) -> str:
    digits = str(scaled)
    sign = "-" if numerator < 0 else ""
    if places == 0:
        return f"{sign}{digits}"
    digits = digits.rjust(places + 1, "0")
    integer = digits[:-places]
    decimal = digits[-places:].rstrip("0")
    return f"{sign}{integer}.{decimal}" if decimal else f"{sign}{integer}"


def _finite_decimal_token(value: Fraction) -> str:
    """Render a rational with a terminating decimal expansion exactly."""

    _validate_fraction_bounds(value)
    numerator = value.numerator
    twos, fives = _decimal_factor_counts(value.denominator)
    places = max(twos, fives)
    if places > MAX_DECIMAL_DIGITS:
        raise ValueError("JSON number scale exceeds the exact-decimal limit")
    scaled = abs(numerator) * (2 ** (places - twos)) * (5 ** (places - fives))
    if scaled.bit_length() > _MAX_DECIMAL_BITS:
        raise ValueError("JSON number expansion exceeds the exact-decimal limit")
    return _render_scaled_decimal(numerator, scaled, places)


def json_number_from_fraction(value: Fraction) -> int | ExactJSONFloat:
    """Return a JSON-compatible number that preserves ``value`` exactly."""

    _validate_fraction_bounds(value)
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
    if isinstance(value, (int, float)):
        return _encode_number(value)
    if isinstance(value, str):
        return json.dumps(value, ensure_ascii=ensure_ascii)
    raise TypeError(f"Object of type {type(value).__name__} is not JSON serializable")


def _encode_number(value: int | float) -> str:
    """Encode one JSON number after booleans have been dispatched."""

    if isinstance(value, ExactJSONFloat):
        return value.json_token
    if isinstance(value, int):
        return str(value)
    if isinstance(value, float):
        if not math.isfinite(value):
            raise ValueError("Out of range float values are not JSON compliant")
        return json.dumps(value, allow_nan=False)
    raise TypeError(f"Object of type {type(value).__name__} is not a JSON number")


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
