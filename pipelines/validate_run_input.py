#!/usr/bin/env python3
"""Bounded parsing for physical JSONL records validated by ``validate_run``."""

from __future__ import annotations

import json
import sys
from typing import Any, Optional, Tuple

if __package__:
    from . import _assert_direct_sibling, _expose_package_sibling

    _assert_direct_sibling("validate_run_input")
else:
    getattr(sys.modules.get("pipelines"), "_join_package_sibling", lambda name: None)(
        "validate_run_input"
    )


if __package__:
    from .exact_json import dumps_exact_json, parse_finite_json_float, parse_json_integer
else:
    from exact_json import dumps_exact_json, parse_finite_json_float, parse_json_integer


def parse_exact_json_record(line: str) -> Tuple[Any, Optional[str]]:
    """Return a decoded record or one bounded parse/serialization error."""

    try:
        obj = json.loads(
            line,
            parse_constant=reject_json_constant,
            parse_float=parse_finite_json_float,
            parse_int=parse_json_integer,
        )
    except (RecursionError, ValueError) as exc:
        return None, f"JSON parse error: {exc}"
    try:
        dumps_exact_json(obj, ensure_ascii=False, sort_keys=False)
    except (RecursionError, ValueError) as exc:
        return None, f"exact JSON contract error: {exc}"
    return obj, None


def reject_json_constant(token: str) -> None:
    """Reject non-standard NaN and Infinity tokens during JSON decoding."""

    raise ValueError(f"non-standard JSON numeric constant {token}")


if __package__:
    _expose_package_sibling(__name__)
