#!/usr/bin/env python3
"""Type-sensitive comparisons for parsed exact JSON values."""

from __future__ import annotations

import sys
from typing import Any

from exact_json import ExactJSONFloat

if __package__:
    from . import _assert_direct_sibling, _expose_package_sibling

    _assert_direct_sibling("exact_json_compare")
else:
    getattr(sys.modules.get("pipelines"), "_join_package_sibling", lambda name: None)(
        "exact_json_compare"
    )


def same_exact_json(left: Any, right: Any) -> bool:
    """Return whether two JSON values agree without erasing numeric types."""

    if type(left) is not type(right):
        return False
    if isinstance(left, ExactJSONFloat):
        return left.fraction == right.fraction
    if isinstance(left, dict):
        return _same_mapping(left, right)
    if isinstance(left, list):
        return _same_list(left, right)
    return left == right


def _same_mapping(left: dict[Any, Any], right: dict[Any, Any]) -> bool:
    if len(left) != len(right):
        return False
    return all(key in right and same_exact_json(value, right[key]) for key, value in left.items())


def _same_list(left: list[Any], right: list[Any]) -> bool:
    if len(left) != len(right):
        return False
    return all(same_exact_json(left_item, right_item) for left_item, right_item in zip(left, right))


if __package__:
    _expose_package_sibling(__name__)
