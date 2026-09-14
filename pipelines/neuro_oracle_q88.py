#!/usr/bin/env python3
"""Q8.8 fixed-point arithmetic.

Pure arithmetic, no model and no adapter: the rounding mode and the saturation
policy are stated here as constants because a record has to name which ones it
ran under.
"""

from __future__ import annotations

from pathlib import Path
import math
import sys

_PIPELINES = Path(__file__).resolve().parent
if str(_PIPELINES) not in sys.path:
    sys.path.insert(0, str(_PIPELINES))



Q88_FRACTIONAL_BITS = 8
Q88_SCALE = 1 << Q88_FRACTIONAL_BITS
Q88_MIN_RAW = -(1 << 15)
Q88_MAX_RAW = (1 << 15) - 1
Q88_MIN_VALUE = Q88_MIN_RAW / Q88_SCALE
Q88_MAX_VALUE = Q88_MAX_RAW / Q88_SCALE
Q88_STEP = 1.0 / Q88_SCALE
Q88_ROUNDING = "half_away_from_zero"
Q88_SATURATION_POLICY = "saturate"


def _round_half_away(value):
    """Round half away from zero.

    Python's ``round`` is banker's rounding, which would make the float and
    fixed-point paths disagree for reasons unrelated to the format under test.
    Hardware Q8.8 converters overwhelmingly round half away from zero, so that
    is what the recorded conversion provenance claims -- and does.
    """
    if not math.isfinite(value):
        raise ValueError(f"cannot quantize non-finite value {value!r}")
    if value >= 0:
        return math.floor(value + 0.5)
    return math.ceil(value - 0.5)


def q88_quantize(value):
    """Quantize a float to Q8.8. Returns ``(raw_int, saturated_bool)``."""
    raw = _round_half_away(float(value) * Q88_SCALE)
    if raw < Q88_MIN_RAW:
        return Q88_MIN_RAW, True
    if raw > Q88_MAX_RAW:
        return Q88_MAX_RAW, True
    return raw, False


def q88_to_float(raw):
    """Exact dequantization of a Q8.8 raw integer."""
    return raw / Q88_SCALE


def q88_saturate(raw):
    """Clamp an accumulator to the Q8.8 range. Returns ``(raw, saturated)``."""
    if raw < Q88_MIN_RAW:
        return Q88_MIN_RAW, True
    if raw > Q88_MAX_RAW:
        return Q88_MAX_RAW, True
    return raw, False


def q88_mul(a_raw, b_raw):
    """Q8.8 * Q8.8 -> Q8.8 with round-half-away-from-zero and saturation."""
    product = a_raw * b_raw
    half = 1 << (Q88_FRACTIONAL_BITS - 1)
    if product >= 0:
        shifted = (product + half) >> Q88_FRACTIONAL_BITS
    else:
        shifted = -((-product + half) >> Q88_FRACTIONAL_BITS)
    return q88_saturate(shifted)
