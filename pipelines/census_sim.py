#!/usr/bin/env python3
"""``sim_or_real`` label interpretation for census histograms.

Nested ``sim_or_real`` values found anywhere in a record are bucketed into the
census histogram labels: ``real``, ``real*`` (near-real claims), ``sim*``,
``hil*`` (hardware-in-the-loop), ``other``, and ``<missing>``.
"""

from collections import Counter


# Near-real labels: not the bare word ``real``, but still claiming a live or
# production run rather than a simulation.
_REAL_STAR_PREFIXES = ("real", "live")
_REAL_STAR_SUBSTRINGS = ("production", "actions live")


def _is_real_star(low):
    """True for a label that claims a live/production run without being ``real``."""
    if low.startswith(_REAL_STAR_PREFIXES):
        return True
    return any(fragment in low for fragment in _REAL_STAR_SUBSTRINGS)


def _is_hil(low):
    """True for a hardware-in-the-loop label."""
    return "hardware-in-the-loop" in low or low.startswith("hil")


def bucket_sim_or_real(value):
    if not isinstance(value, str):
        return "other"
    low = value.strip().lower()
    bucket = "other"
    if low == "real":
        bucket = "real"
    elif _is_real_star(low):
        bucket = "real*"
    elif "simulat" in low:
        bucket = "sim*"
    elif _is_hil(low):
        bucket = "hil*"
    return bucket


def _iter_mapping_sim_or_real(obj):
    """Yield ``sim_or_real`` values carried by one mapping and its children."""
    for key, val in obj.items():
        if key == "sim_or_real":
            yield val
        yield from iter_sim_or_real(val)


def iter_sim_or_real(obj):
    if isinstance(obj, dict):
        yield from _iter_mapping_sim_or_real(obj)
    elif isinstance(obj, list):
        for item in obj:
            yield from iter_sim_or_real(item)


def _record_simulation_buckets(obj) -> Counter:
    values = list(iter_sim_or_real(obj))
    if not values:
        return Counter({"<missing>": 1})
    return Counter(bucket_sim_or_real(value) for value in values)
