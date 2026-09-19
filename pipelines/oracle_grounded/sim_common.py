"""Shared numerical helpers for deterministic reference simulators."""

import math

ENERGY_PJ_PER_SPIKE = 23.0
ENCODINGS = ("rate", "latency", "delta", "temporal")
WEIGHT_UPDATE_EPS = 5e-6


def clamp(value, low, high):
    if value < low:
        return low
    if value > high:
        return high
    return value


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
    if not var_l or not var_r:
        return None
    return cov / (var_l * var_r)


def rmse(left, right):
    count = len(left)
    if count != len(right) or not count:
        raise ValueError("rmse requires two non-empty, equal-length series")
    return math.sqrt(sum((a - b) ** 2 for a, b in zip(left, right, strict=True)) / count)

