#!/usr/bin/env python3
"""Canonical reward contract parsing facade and arithmetic compatibility."""

from __future__ import annotations

import sys
import re
from typing import NamedTuple

if __package__:
    from . import _assert_direct_sibling, _expose_package_sibling
    _assert_direct_sibling("reward_parse")
    from . import reward_parse_values as _values
    from . import reward_parse_patterns as _patterns
else:
    getattr(sys.modules.get("pipelines"), "_join_package_sibling", lambda name: None)(
        "reward_parse"
    )
    import reward_parse_values as _values
    import reward_parse_patterns as _patterns


RewardOntologyError = _values.RewardOntologyError
MagnitudeNotComparable = _values.MagnitudeNotComparable
_policy_error = _values._policy_error
_unique_nonempty_strings = _values._unique_nonempty_strings
_require_unique_string_codes = _values._require_unique_string_codes
_mapping_str = _values._mapping_str
_mapping_str_list = _values._mapping_str_list
_mapping_object = _values._mapping_object
_decimal = _values._decimal
_json_number = _values._json_number
_reject_nonfinite_numbers = _values._reject_nonfinite_numbers
_require_finite_decimal = _values._require_finite_decimal
_require_positive_decimal = _values._require_positive_decimal
_mapping_positive = _values._mapping_positive
_require_integer = _values._require_integer
_mapping_integer = _values._mapping_integer
_pattern_numeric_group = _patterns._pattern_numeric_group
_mapping_pattern = _patterns._mapping_pattern
_numeric_capture = _patterns._numeric_capture
_escape_signature_token = _patterns._escape_signature_token
_unescape_signature_token = _patterns._unescape_signature_token
_split_signature = _patterns._split_signature
_signature_members = _patterns._signature_members
_arithmetic_methods_for_signature = _patterns._arithmetic_methods_for_signature
PatternOptions = _patterns.PatternOptions


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


class NamedObjectContract(NamedTuple):
    """Error locations and messages for a named vocabulary entry."""

    names_where: str
    names_message: str
    entry_where: str
    entry_message: str


class ArithmeticContract(NamedTuple):
    """Method vocabulary and compatibility constraints for one arithmetic entry."""

    methods: object
    where: str
    allowed_methods: object = None
    check_status_pair: bool = False


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


def _require_named_object(key, entry, contract):
    if not isinstance(key, str) or not key:
        raise _policy_error(contract.names_where, contract.names_message)
    if not isinstance(entry, dict) or not entry:
        raise _policy_error(contract.entry_where, contract.entry_message)
    return entry


def _require_signature_method(method, contract):
    if contract.allowed_methods is None:
        return
    if method not in contract.allowed_methods:
        raise _policy_error(
            contract.where, f"arithmetic method {method!r} is incompatible with signature")


def _require_status_pair(status, method, contract):
    if not contract.check_status_pair:
        return
    if method not in _SHAPE_STATUS_METHODS.get(status, ()):
        raise _policy_error(
            contract.where, f"arithmetic status {status!r} is incompatible with method {method!r}")


def _require_arithmetic_status_method(status, method, contract):
    if status not in ARITHMETIC_STATUSES:
        raise _policy_error(contract.where, f"unknown arithmetic status {status!r}")
    if method not in contract.methods:
        raise _policy_error(contract.where, f"unknown arithmetic method {method!r}")
    _require_signature_method(method, contract)
    _require_status_pair(status, method, contract)
    return status, method


if __package__:
    _expose_package_sibling(__name__)
