#!/usr/bin/env python3
"""Canonical immutable parsers for the reward ontology contract.

Units, vocabulary entries, policy-reference hashes, finite numeric values, and
arithmetic-signature compatibility are validated here so mapping, policy,
vocabulary, units, and document modules do not re-state those fail-closed
checks. Refusal messages stay byte-stable; callers pass the existing codes.
"""

from __future__ import annotations

import math
import re
import sys
from decimal import Decimal, InvalidOperation

if __package__:
    from . import _assert_direct_sibling, _expose_package_sibling

    _assert_direct_sibling("reward_parse")
else:
    getattr(sys.modules.get("pipelines"), "_join_package_sibling", lambda name: None)(
        "reward_parse"
    )


class RewardOntologyError(ValueError):
    """Raised when a reward document violates ontology-v1 invariants."""


class MagnitudeNotComparable(RewardOntologyError):
    """Raised when a caller asks an uncalibrated record for magnitudes."""


SHA256_RE = re.compile(r"^sha256:[0-9a-f]{64}$")
ARITHMETIC_STATUSES = frozenset({"valid", "invalid", "unsupported"})
_SHAPE_STATUS_METHODS = {
    "valid": {
        "declared_weighted_sum",
        "unweighted_component_sum",
    },
    "invalid": {
        "declared_weighted_sum",
        "unweighted_component_sum",
    },
    "unsupported": {
        "declared_weighted_sum_unresolved",
        "unweighted_component_sum_unresolved",
        "no_numeric_total",
        "non_object_reward",
    },
}


def _policy_error(where, message):
    return RewardOntologyError(f"{where}: {message}")


def _unique_nonempty_strings(value, *, require_text=False):
    if not isinstance(value, list) or not value:
        return None
    if not all(isinstance(item, str) for item in value):
        return None
    if require_text and not all(item.strip() for item in value):
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


def _reject_nonfinite_numbers(value, *, where):
    if isinstance(value, float) and not math.isfinite(value):
        raise RewardOntologyError(f"{where}: non-finite JSON number")
    if isinstance(value, dict):
        for child in value.values():
            _reject_nonfinite_numbers(child, where=where)
    elif isinstance(value, list):
        for child in value:
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


def _mapping_positive(container, key, where):
    value = container.get(key)
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise _policy_error(where, f"{key} must be a number")
    try:
        number = Decimal(str(value))
    except InvalidOperation as exc:
        raise _policy_error(where, f"{key} must be a finite number") from exc
    if not number.is_finite() or number <= 0:
        raise _policy_error(where, f"{key} must be positive and finite")
    return number


def _require_integer(value, message, *, minimum=0):
    if isinstance(value, bool) or not isinstance(value, int) or value < minimum:
        raise RewardOntologyError(message)
    return value


def _mapping_integer(container, key, where, *, minimum=0):
    value = container.get(key)
    if isinstance(value, bool) or not isinstance(value, int) or value < minimum:
        qualifier = "nonnegative" if minimum == 0 else f">= {minimum}"
        raise _policy_error(where, f"{key} must be an integer {qualifier}")
    return value


def _require_sha256(value, message):
    token = str(value)
    if not SHA256_RE.fullmatch(token):
        raise RewardOntologyError(message)
    return token


def _unknown_members(values, catalog):
    return sorted(set(values) - set(catalog))


def _require_distinct(left, right, where, message):
    if left == right:
        raise _policy_error(where, message)


def _require_disjoint(seen, members, where, message):
    if seen.intersection(members):
        raise _policy_error(where, message)
    seen.update(members)


def _add_unique(item, seen, error):
    if item in seen:
        raise error
    seen.add(item)
    return item


def _require_named_object(
    key, entry, *, names_where, names_message, entry_where, entry_message
):
    if not isinstance(key, str) or not key:
        raise _policy_error(names_where, names_message)
    if not isinstance(entry, dict) or not entry:
        raise _policy_error(entry_where, entry_message)
    return entry


def _pattern_numeric_group(compiled, key, where):
    haystacks = (
        "rounded to 3-decimal 1 reward unit = USD 10,000.5 abc",
        "xyz",
        "rounded to xyz decimal",
    )
    saw_numeric = False
    for haystack in haystacks:
        match = compiled.search(haystack)
        if match is None:
            continue
        try:
            Decimal(str(match.group(1)).replace(",", ""))
        except (InvalidOperation, TypeError, IndexError, ArithmeticError) as exc:
            raise _policy_error(
                where, f"{key} capture group must be numeric"
            ) from exc
        saw_numeric = True
    if not saw_numeric:
        raise _policy_error(
            where, f"{key} capture group must match a numeric sample"
        )


def _mapping_pattern(container, key, where, *, groups=0, numeric_group=False):
    pattern = _mapping_str(container, key, where)
    try:
        compiled = re.compile(pattern, re.I)
    except re.error as exc:
        raise _policy_error(
            where, f"{key} is not a valid regular expression: {exc}"
        ) from exc
    if compiled.groups != groups:
        raise _policy_error(where, f"{key} must declare exactly {groups} capture group(s)")
    if numeric_group:
        _pattern_numeric_group(compiled, key, where)
    return compiled


def _numeric_capture(match, *, integer=False):
    try:
        token = str(match.group(1)).replace(",", "")
        value = int(token) if integer else Decimal(token)
    except (InvalidOperation, TypeError, ValueError, IndexError, ArithmeticError) as exc:
        raise RewardOntologyError("numeric regex capture is not a number") from exc
    return value


def _escape_signature_token(token):
    return str(token).replace("\\", "\\\\").replace("|", "\\|").replace(":", "\\:")


def _unescape_signature_token(token):
    out = []
    escaped = False
    for character in token:
        if escaped:
            out.append(character)
            escaped = False
        elif character == "\\":
            escaped = True
        else:
            out.append(character)
    if escaped:
        out.append("\\")
    return "".join(out)


def _split_signature(signature, separator):
    parts = []
    buf = []
    escaped = False
    for character in signature:
        if escaped:
            buf.append(character)
            escaped = False
            continue
        if character == "\\":
            buf.append(character)
            escaped = True
            continue
        if character == separator:
            parts.append("".join(buf))
            buf = []
            continue
        buf.append(character)
    parts.append("".join(buf))
    return parts


def _signature_members(signature, where):
    members = {}
    for part in _split_signature(signature, "|"):
        pieces = _split_signature(part, ":")
        if len(pieces) != 2:
            raise _policy_error(where, "signature contains an invalid member")
        key = _unescape_signature_token(pieces[0])
        member_type = _unescape_signature_token(pieces[1])
        if not member_type or key in members:
            raise _policy_error(where, "signature contains an invalid member")
        members[key] = member_type
    return members


def _arithmetic_methods_for_signature(signature, arithmetic, where):
    """Return the arithmetic methods the structural signature can select."""
    if signature == "":
        return frozenset({"no_numeric_total"})
    if ":" not in signature:
        return frozenset({"non_object_reward"})

    members = _signature_members(signature, where)
    total_type = members.get(arithmetic["declared_total_field"])
    if total_type not in {"int", "float"}:
        return frozenset({"no_numeric_total"})
    if members.get(arithmetic["weights_field"]) == "object":
        return frozenset(
            {"declared_weighted_sum", "declared_weighted_sum_unresolved"}
        )
    return frozenset(
        {"unweighted_component_sum", "unweighted_component_sum_unresolved"}
    )


def _require_arithmetic_status_method(
    status,
    method,
    *,
    methods,
    where,
    allowed_methods=None,
    check_status_pair=False,
):
    if status not in ARITHMETIC_STATUSES:
        raise _policy_error(where, f"unknown arithmetic status {status!r}")
    if method not in methods:
        raise _policy_error(where, f"unknown arithmetic method {method!r}")
    if allowed_methods is not None and method not in allowed_methods:
        raise _policy_error(
            where,
            f"arithmetic method {method!r} is incompatible with signature",
        )
    if check_status_pair and method not in _SHAPE_STATUS_METHODS.get(status, ()):
        raise _policy_error(
            where,
            f"arithmetic status {status!r} is incompatible with method {method!r}",
        )
    return status, method


if __package__:
    _expose_package_sibling(__name__)
