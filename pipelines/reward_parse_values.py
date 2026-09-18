#!/usr/bin/env python3
"""Finite values and scalar/collection shapes of the reward contract."""

from __future__ import annotations

import sys
import math
from decimal import Decimal, InvalidOperation

if __package__:
    from . import _assert_direct_sibling, _expose_package_sibling
    _assert_direct_sibling("reward_parse_values")
else:
    getattr(sys.modules.get("pipelines"), "_join_package_sibling", lambda name: None)(
        "reward_parse_values"
    )


class RewardOntologyError(ValueError):
    """Raised when a reward document violates ontology-v1 invariants."""


class MagnitudeNotComparable(RewardOntologyError):
    """Raised when a caller asks an uncalibrated record for magnitudes."""


def _policy_error(where, message):
    return RewardOntologyError(f"{where}: {message}")


def _string_list(value, require_text):
    if not isinstance(value, list) or not value:
        return False
    return all(_valid_string(item, require_text) for item in value)


def _valid_string(value, require_text):
    if not isinstance(value, str):
        return False
    return bool(value.strip()) if require_text else True


def _unique_nonempty_strings(value, *, require_text=False):
    if not _string_list(value, require_text):
        return None
    if len(set(value)) != len(value):
        return None
    return value


def _require_unique_string_codes(reasons, *, empty_message):
    if _unique_nonempty_strings(reasons) is None:
        raise RewardOntologyError(empty_message)
    return reasons


def _mapping_str(container, key, where, *, prefix=None):
    value = container.get(key)
    if not isinstance(value, str) or not value.strip():
        raise _policy_error(where, f"{key} must be a nonempty string")
    if prefix is not None and not value.startswith(prefix):
        raise _policy_error(where, f"{key} must start with {prefix!r}")
    return value


def _mapping_str_list(container, key, where):
    value = _unique_nonempty_strings(container.get(key), require_text=True)
    if value is None:
        raise _policy_error(where, f"{key} must be a unique nonempty list of strings")
    return tuple(value)


def _mapping_object(container, key, where):
    value = container.get(key)
    if not isinstance(value, dict) or not value:
        raise _policy_error(where, f"{key} must be a nonempty object")
    return value


def _decimal(value):
    if isinstance(value, bool) or not isinstance(value, (int, float, Decimal)):
        return None
    if isinstance(value, float) and not math.isfinite(value):
        return None
    try:
        result = Decimal(str(value))
    except InvalidOperation:
        return None
    return result if result.is_finite() else None


def _json_number(value: Decimal) -> float:
    return float(value)


def _numeric_children(value):
    if isinstance(value, dict):
        return value.values()
    return value if isinstance(value, list) else ()


def _reject_nonfinite_numbers(value, *, where):
    if isinstance(value, float) and not math.isfinite(value):
        raise RewardOntologyError(f"{where}: non-finite JSON number")
    for child in _numeric_children(value):
        _reject_nonfinite_numbers(child, where=where)


def _require_finite_decimal(value, message):
    number = _decimal(value)
    if number is None:
        raise RewardOntologyError(message)
    return number


def _require_positive_decimal(value, message):
    number = _require_finite_decimal(value, message)
    if number <= 0:
        raise RewardOntologyError(message)
    return number


def _positive_finite(number):
    if not number.is_finite():
        return False
    return number > 0


def _mapping_positive(container, key, where):
    value = container.get(key)
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise _policy_error(where, f"{key} must be a number")
    try:
        number = Decimal(str(value))
    except InvalidOperation as exc:
        raise _policy_error(where, f"{key} must be a finite number") from exc
    if not _positive_finite(number):
        raise _policy_error(where, f"{key} must be positive and finite")
    return number


def _integer_at_least(value, minimum):
    if isinstance(value, bool):
        return False
    if not isinstance(value, int):
        return False
    return value >= minimum


def _require_integer(value, message, *, minimum=0):
    if not _integer_at_least(value, minimum):
        raise RewardOntologyError(message)
    return value


def _mapping_integer(container, key, where, *, minimum=0):
    value = container.get(key)
    if not _integer_at_least(value, minimum):
        qualifier = "nonnegative" if minimum == 0 else f">= {minimum}"
        raise _policy_error(where, f"{key} must be an integer {qualifier}")
    return value

if __package__:
    _expose_package_sibling(__name__)
