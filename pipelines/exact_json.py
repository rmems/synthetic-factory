#!/usr/bin/env python3
"""Exact finite JSON numbers and deterministic stdlib-only serialization.

Python's JSON decoder normally converts every non-integer number to a binary
``float``.  That is convenient for ordinary telemetry, but it can erase units
from a spike budget before a validator sees the original decimal token.  The
wrapper below remains a real ``float`` for compatibility while retaining the
token's exact rational value for contractual arithmetic and output.
"""

from __future__ import annotations

import math
import re
import sys
from fractions import Fraction
from typing import Any

if __package__:
    from .exact_json_encoding import EncoderState, encode_exact_json
else:
    if "pipelines.exact_json" in sys.modules:
        from pipelines import _join_package_sibling
        _join_package_sibling("exact_json")
    from exact_json_encoding import EncoderState, encode_exact_json


# Bound decimal expansion before Fraction construction.  Short tokens such as
# ``1e-100000000`` are valid JSON but otherwise amplify into enormous integer
# denominators.  The limit comfortably covers every finite IEEE-754 decimal
# while keeping parsing and exact serialization operationally bounded.
MAX_DECIMAL_DIGITS = 4096
MAX_JSON_NESTING_DEPTH = 128
_MAX_JSON_NUMBER_TOKEN_LENGTH = MAX_DECIMAL_DIGITS + 32
_MAX_EXPONENT_DIGITS = len(str(MAX_DECIMAL_DIGITS))
_MAX_DECIMAL_BITS = (MAX_DECIMAL_DIGITS * 3322 // 1000) + 8
_MAX_JSON_INTEGER_MAGNITUDE = 10**MAX_DECIMAL_DIGITS
_JSON_NUMBER_RE = re.compile(
    r"(?a)-?(?:0|[1-9]\d*)(?:\.\d+)?(?:[eE][+-]?\d+)?\Z"
)


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
    integer, _, fraction = coefficient.partition(".")
    return len(integer) + len(fraction), len(fraction)


def _validate_json_number_syntax(token: str) -> None:
    if not isinstance(token, str) or len(token) > _MAX_JSON_NUMBER_TOKEN_LENGTH:
        raise ValueError("JSON number token exceeds the exact-decimal limit")
    if _JSON_NUMBER_RE.fullmatch(token) is None:
        raise ValueError("invalid JSON number syntax")


def _validate_decimal_shape(mantissa: str, exponent: int) -> None:
    coefficient_digits, decimal_places = _decimal_shape(mantissa)
    if coefficient_digits > MAX_DECIMAL_DIGITS:
        raise ValueError("JSON number precision exceeds the exact-decimal limit")
    if abs(decimal_places - exponent) > MAX_DECIMAL_DIGITS:
        raise ValueError("JSON number scale exceeds the exact-decimal limit")


def _validate_decimal_token_bounds(token: str) -> None:
    """Reject a decimal token whose exact expansion exceeds fixed bounds."""

    _validate_json_number_syntax(token)
    mantissa, marker, exponent_text = token.lower().partition("e")
    exponent = _bounded_exponent(marker, exponent_text)
    _validate_decimal_shape(mantissa, exponent)


def json_integer_is_bounded(value: Any) -> bool:
    """Return whether an integer fits the exact JSON decimal-digit contract."""

    return (
        isinstance(value, int)
        and not isinstance(value, bool)
        and abs(value) < _MAX_JSON_INTEGER_MAGNITUDE
    )


def _validate_json_integer_bounds(value: int) -> None:
    if not json_integer_is_bounded(value):
        raise ValueError("JSON integer precision exceeds the exact-decimal limit")


def _render_json_integer(value: int) -> str:
    """Render a bounded integer without Python's process-wide digit cap."""

    _validate_json_integer_bounds(value)
    negative = value < 0
    remaining = abs(value)
    chunks = []
    while remaining:
        remaining, chunk = divmod(remaining, 1_000_000_000)
        chunks.append(chunk)
    if not chunks:
        return "0"
    rendered = str(chunks.pop()) + "".join(f"{chunk:09d}" for chunk in reversed(chunks))
    return "-" + rendered if negative else rendered


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

    fraction = None
    if isinstance(value, bool):
        return fraction
    if isinstance(value, ExactJSONFloat):
        fraction = value.fraction
    elif isinstance(value, int):
        fraction = Fraction(value)
    elif isinstance(value, float) and math.isfinite(value):
        fraction = Fraction(str(value))
    elif isinstance(value, Fraction):
        fraction = value
    return fraction


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
    digits = _render_json_integer(scaled)
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
        _validate_json_integer_bounds(value.numerator)
        return value.numerator
    return ExactJSONFloat(_finite_decimal_token(value))


def dumps_exact_json(
    value: Any,
    *,
    ensure_ascii: bool = False,
    sort_keys: bool = True,
    indent: int | None = None,
) -> str:
    """Serialize JSON data while emitting :class:`ExactJSONFloat` tokens raw.

    ``indent`` mirrors :func:`json.dumps`: ``None`` keeps the compact single
    line form, while a non-negative integer pretty-prints containers with that
    many spaces per nesting level.
    """

    if indent is not None and indent < 0:
        raise ValueError("indent must be None or a non-negative integer")
    state = EncoderState(
        ensure_ascii=ensure_ascii,
        sort_keys=sort_keys,
        indent=indent,
        exact_float_type=ExactJSONFloat,
        render_integer=_render_json_integer,
        max_nesting_depth=MAX_JSON_NESTING_DEPTH,
    )
    return encode_exact_json(value, state)
