"""Shared numeric helpers for the reference simulators.

These are the few primitives every simulator family leans on: clamping,
series statistics, optional-value deltas, and the energy constant that keeps
spike-count energy figures comparable across families. Everything here is
pure and deterministic: same inputs, same floats.
"""

import math

# Loihi-2-class energy constant, the same 23 pJ/spike already used by
# schemas/raster.schema.json so the two families report comparable numbers.
ENERGY_PJ_PER_SPIKE = 23.0


def clamp(value, low, high):
    return low if value < low else (high if value > high else value)


def pearson(left, right):
    """Pearson r, or None when either series is constant (r undefined)."""
    count = len(left)
    if count != len(right) or count < 2:
        return None
    mean_l = sum(left) / count
    mean_r = sum(right) / count
    cov = sum((a - mean_l) * (b - mean_r) for a, b in zip(left, right, strict=True))
    var_l = math.sqrt(sum((a - mean_l) ** 2 for a in left))
    var_r = math.sqrt(sum((b - mean_r) ** 2 for b in right))
    if var_l == 0.0 or var_r == 0.0:
        return None
    return cov / (var_l * var_r)


def rmse(left, right):
    count = len(left)
    if count != len(right) or not count:
        raise ValueError("rmse requires two non-empty, equal-length series")
    return math.sqrt(sum((a - b) ** 2 for a, b in zip(left, right, strict=True)) / count)


def optional_delta(after, before):
    """``after - before``, or None when either side is not a number."""
    if after is None or before is None:
        return None
    return after - before
