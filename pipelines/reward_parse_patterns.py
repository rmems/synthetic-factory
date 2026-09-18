#!/usr/bin/env python3
"""Regex captures and escaped structural signatures for reward contracts."""

from __future__ import annotations

import sys
import re
from decimal import Decimal, InvalidOperation
from typing import NamedTuple

if __package__:
    from . import _assert_direct_sibling, _expose_package_sibling
    _assert_direct_sibling("reward_parse_patterns")
    from . import reward_parse_values as _values
else:
    getattr(sys.modules.get("pipelines"), "_join_package_sibling", lambda name: None)(
        "reward_parse_patterns"
    )
    import reward_parse_values as _values


RewardOntologyError = _values.RewardOntologyError
_policy_error = _values._policy_error
_mapping_str = _values._mapping_str


class PatternOptions(NamedTuple):
    """Capture requirements of one regular-expression contract."""

    groups: int = 0
    numeric_group: bool = False


def _require_numeric_match(match, key, where):
    try:
        Decimal(str(match.group(1)).replace(",", ""))
    except (InvalidOperation, TypeError, IndexError, ArithmeticError) as exc:
        raise _policy_error(where, f"{key} capture group must be numeric") from exc


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
        _require_numeric_match(match, key, where)
        saw_numeric = True
    if not saw_numeric:
        raise _policy_error(
            where, f"{key} capture group must match a numeric sample"
        )


def _compile_pattern(pattern, key, where):
    try:
        return re.compile(pattern, re.I)
    except re.error as exc:
        raise _policy_error(
            where, f"{key} is not a valid regular expression: {exc}"
        ) from exc


def _mapping_pattern(container, key, where, options=PatternOptions()):
    pattern = _mapping_str(container, key, where)
    compiled = _compile_pattern(pattern, key, where)
    if compiled.groups != options.groups:
        raise _policy_error(where, f"{key} must declare exactly {options.groups} capture group(s)")
    if options.numeric_group:
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


def _signature_member(part, where):
    pieces = _split_signature(part, ":")
    if len(pieces) != 2:
        raise _policy_error(where, "signature contains an invalid member")
    key = _unescape_signature_token(pieces[0])
    member_type = _unescape_signature_token(pieces[1])
    if not member_type:
        raise _policy_error(where, "signature contains an invalid member")
    return key, member_type


def _signature_members(signature, where):
    members = {}
    for part in _split_signature(signature, "|"):
        key, member_type = _signature_member(part, where)
        if key in members:
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

if __package__:
    _expose_package_sibling(__name__)
