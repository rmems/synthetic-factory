#!/usr/bin/env python3
"""Comparing a recorded metric against a freshly derived one.

Split from the checks that use it because the question "are these two numbers
the same to within METRIC_TOL" is shared by five validators and is the kind of
thing that must have exactly one answer.
"""

from __future__ import annotations

import math
import sys

if __package__:
    # Import-twin helpers join the package import lock; import-order tests cover this edge.
    from . import _assert_direct_sibling, _expose_package_sibling  # pylint: disable=cyclic-import

    _assert_direct_sibling("hardware_parity_validate_equality")
    from .hardware_parity_terms import METRIC_TOL  # noqa: E402
else:
    getattr(sys.modules.get("pipelines"), "_join_package_sibling", lambda name: None)(
        "hardware_parity_validate_equality"
    )
    from hardware_parity_terms import METRIC_TOL  # noqa: E402

def _metric_mismatch(path, where, recorded, recomputed):
    """The one mismatch message shared by every scalar branch below."""
    return (
        f"{where}: {path} recorded {recorded!r} but traces give {recomputed!r} "
        "[PARITY_METRIC_MISMATCH]"
    )


def _metrics_equal_dict(recorded, recomputed, path, where):
    if not isinstance(recorded, dict):
        return [f"{where}: {path} must be an object [PARITY_METRIC_MISMATCH]"]
    errors = [
        f"{where}: {path}.{key} is unexpected [PARITY_METRIC_MISMATCH]"
        for key in recorded.keys() - recomputed.keys()
    ]
    for key, value in recomputed.items():
        if key not in recorded:
            errors.append(f"{where}: {path}.{key} is missing [PARITY_METRIC_MISMATCH]")
            continue
        errors += _metrics_equal(recorded[key], value, f"{path}.{key}", where)
    return errors


def _metrics_equal_list(recorded, recomputed, path, where):
    if not isinstance(recorded, list):
        return [f"{where}: {path} must be an array [PARITY_METRIC_MISMATCH]"]
    errors = []
    if len(recorded) != len(recomputed):
        errors.append(
            f"{where}: {path} has {len(recorded)} items but traces give "
            f"{len(recomputed)} [PARITY_METRIC_MISMATCH]"
        )
    for index, (left, right) in enumerate(zip(recorded, recomputed)):
        errors += _metrics_equal(left, right, f"{path}[{index}]", where)
    return errors


def _metrics_equal_float(recorded, recomputed, path, where):
    """Exact-typed finite floats compared under the metric tolerance."""
    if not isinstance(recorded, float) or not math.isfinite(recorded):
        return [
            f"{where}: {path} must be a finite float matching {recomputed!r}, got "
            f"{recorded!r} [PARITY_METRIC_MISMATCH]"
        ]
    if not math.isfinite(recomputed) or abs(recorded - recomputed) > METRIC_TOL:
        return [_metric_mismatch(path, where, recorded, recomputed)]
    return []


def _metrics_equal_scalar(recorded, recomputed, path, where):
    # JSON numbers still arrive as distinct Python integer and float values,
    # while `bool` is a subclass of `int`. Keep those types exact and reject
    # non-finite floats before applying a tolerance; otherwise True can stand
    # in for 1 and NaN compares equal to every finite metric here.
    if isinstance(recomputed, bool):
        matched = isinstance(recorded, bool) and recorded is recomputed
    elif isinstance(recomputed, int):
        matched = (
            isinstance(recorded, int)
            and not isinstance(recorded, bool)
            and recorded == recomputed
        )
    elif isinstance(recomputed, float):
        return _metrics_equal_float(recorded, recomputed, path, where)
    else:
        matched = recorded == recomputed
    if matched:
        return []
    return [_metric_mismatch(path, where, recorded, recomputed)]


def _metrics_equal(recorded, recomputed, path, where):
    """Deep-compare a recorded metric block against a recomputed one."""
    if isinstance(recomputed, dict):
        return _metrics_equal_dict(recorded, recomputed, path, where)
    if isinstance(recomputed, list):
        return _metrics_equal_list(recorded, recomputed, path, where)
    return _metrics_equal_scalar(recorded, recomputed, path, where)


if __package__:
    _expose_package_sibling(__name__)
