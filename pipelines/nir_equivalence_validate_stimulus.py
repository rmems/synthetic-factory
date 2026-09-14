#!/usr/bin/env python3
"""The recorded stimulus must be a well-formed grid of the declared shape.
"""

from __future__ import annotations

import math
import sys
from pathlib import Path

_PIPELINES = Path(__file__).resolve().parent

if __package__:
    # Import-twin helpers join the package import lock; import-order tests cover this edge.
    from . import _assert_direct_sibling, _expose_package_sibling  # pylint: disable=cyclic-import

    _assert_direct_sibling("nir_equivalence_validate_stimulus")
else:
    getattr(sys.modules.get("pipelines"), "_join_package_sibling", lambda name: None)(
        "nir_equivalence_validate_stimulus"
    )
    if str(_PIPELINES) not in sys.path:
        sys.path.insert(0, str(_PIPELINES))

def _check_stimulus_shape(stimulus, where):
    """Validate the execution window before any runtime indexes into it."""
    if not isinstance(stimulus, dict):
        return [f"{where}: scenario.stimulus must be an object [ENVELOPE_MALFORMED]"]
    errors = _stimulus_header_errors(stimulus, where)
    events = stimulus.get("events")
    if not isinstance(events, list):
        errors.append(
            f"{where}: scenario.stimulus.events must be an array [ENVELOPE_MALFORMED]"
        )
        return errors
    steps = stimulus.get("steps")
    if isinstance(steps, int) and not isinstance(steps, bool) and len(events) != steps:
        errors.append(
            f"{where}: scenario.stimulus.steps disagrees with len(events) "
            "[ENVELOPE_MALFORMED]"
        )
    channels = stimulus.get("channels")
    for index, row in enumerate(events):
        errors += _stimulus_row_errors(row, index, channels, where)
    return errors


def _stimulus_header_errors(stimulus, where):
    """The stimulus name, encoding, and its two declared window dimensions."""
    errors = []
    name = stimulus.get("name")
    steps = stimulus.get("steps")
    channels = stimulus.get("channels")
    if not isinstance(name, str) or not name.strip():
        errors.append(
            f"{where}: scenario.stimulus.name must be a non-empty string "
            "[ENVELOPE_MALFORMED]"
        )
    if stimulus.get("encoding") != "binary_event_grid":
        errors.append(
            f"{where}: scenario.stimulus.encoding must be 'binary_event_grid' "
            "[ENVELOPE_MALFORMED]"
        )
    if not isinstance(steps, int) or isinstance(steps, bool) or steps < 1:
        errors.append(
            f"{where}: scenario.stimulus.steps must be an integer >= 1 "
            "[ENVELOPE_MALFORMED]"
        )
    if not isinstance(channels, int) or isinstance(channels, bool) or channels < 1:
        errors.append(
            f"{where}: scenario.stimulus.channels must be an integer >= 1 "
            "[ENVELOPE_MALFORMED]"
        )
    return errors


def _stimulus_row_errors(row, index, channels, where):
    """One event row: an array of exactly `channels` finite numbers."""
    if not isinstance(row, list):
        return [
            f"{where}: scenario.stimulus.events[{index}] must be an array "
            "[ENVELOPE_MALFORMED]"
        ]
    errors = []
    if (
        isinstance(channels, int)
        and not isinstance(channels, bool)
        and len(row) != channels
    ):
        errors.append(
            f"{where}: scenario.stimulus.events[{index}] must have {channels} "
            "channels [ENVELOPE_MALFORMED]"
        )
    if any(
        type(value) not in (int, float)
        or (type(value) is float and not math.isfinite(value))
        for value in row
    ):
        errors.append(
            f"{where}: scenario.stimulus.events[{index}] must contain finite "
            "numbers [ENVELOPE_MALFORMED]"
        )
    return errors


if __package__:
    _expose_package_sibling(__name__)
