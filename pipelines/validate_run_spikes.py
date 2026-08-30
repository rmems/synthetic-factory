#!/usr/bin/env python3
"""Schema-derived validation for trajectory and bridge spike streams."""

from __future__ import annotations

import json
import math
from pathlib import Path

from exact_json import exact_fraction


REPO = Path(__file__).resolve().parents[1]
SCHEMA_PATH = REPO / "schemas" / "thalamic-trajectory.schema.json"
THALAMIC_SCHEMA = json.loads(SCHEMA_PATH.read_text())

# Read the event contract from the schema so field and runtime validation
# cannot drift. Cross-event ordering and clock-domain rules remain code-level
# invariants because JSON Schema cannot express them.
SPIKE_EVENT_PROPERTIES = THALAMIC_SCHEMA["$defs"]["spike_event"]["properties"]
SPIKE_TIME_KEYS = tuple(
    key
    for branch in THALAMIC_SCHEMA["$defs"]["spike_event"]["oneOf"]
    for key in branch["required"]
)
SPIKE_EVENT_STRING_KEYS = tuple(
    key
    for key, definition in SPIKE_EVENT_PROPERTIES.items()
    if definition.get("type") == "string"
)
SPIKE_EVENT_NUMBER_KEYS = tuple(
    key
    for key, definition in SPIKE_EVENT_PROPERTIES.items()
    if definition.get("type") == "number"
)
BRIDGE_SPIKE_EVENT_KEYS = tuple(
    key
    for part in THALAMIC_SCHEMA["$defs"]["bridge_spike_event"]["allOf"]
    for key in part.get("required", ())
)

SPIKE_ORDER_MISMATCH = "spike_events not globally non-decreasing"
SPIKE_TIME_KEY_MISMATCH = "spike_events must use one timestamp key throughout"
SPIKE_CLOCK_DOMAIN_MISMATCH = "spike_events must declare one clock domain throughout"

# Kept in step with curate_bridge.CLOCK_DOMAIN_KEYS by a parity regression.
SPIKE_CLOCK_DOMAIN_KEYS = (
    "clock_id",
    "clock_domain",
    "timebase",
    "timebase_id",
    "source_clock",
    "source_clock_id",
)


def is_number(value):
    """Return whether a value is a finite JSON number, excluding booleans."""
    if not isinstance(value, (int, float)) or isinstance(value, bool):
        return False
    try:
        # math.isfinite converts integers to float. A syntactically valid JSON
        # integer may exceed that range, so fail it closed instead of raising.
        return math.isfinite(value)
    except OverflowError:
        return False


def event_time(event):
    """Return one supported finite timestamp without losing integer precision."""
    if not isinstance(event, dict):
        return None
    present = [key for key in SPIKE_TIME_KEYS if key in event]
    if len(present) != 1:
        return None
    key = present[0]
    value = event[key]
    return (key, value) if is_number(value) else None


def _enclosing_clock_containers(enclosing):
    if not isinstance(enclosing, dict):
        return ()
    meta = enclosing.get("meta")
    if isinstance(meta, dict):
        return enclosing, meta
    return (enclosing,)


def _event_clock_containers(events):
    return (event for event in events if isinstance(event, dict))


def _clock_domain_containers(events, enclosing):
    """Yield the record, record metadata, and event clock namespaces."""
    yield from _enclosing_clock_containers(enclosing)
    yield from _event_clock_containers(events)


def _clock_domain_marker(value):
    """Make an arbitrary JSON-compatible clock identifier comparable."""
    try:
        return json.dumps(value, sort_keys=True)
    except (TypeError, ValueError):
        return repr(value)


def _container_clock_domains(container):
    return {
        _clock_domain_marker(container[key])
        for key in SPIKE_CLOCK_DOMAIN_KEYS
        if key in container
    }


def declared_clock_domains(events, enclosing=None):
    """Return distinct clock identifiers from the stream and its owner."""
    domains = set()
    for container in _clock_domain_containers(events, enclosing):
        domains.update(_container_clock_domains(container))
    return domains


def _clock_domain_errors(events, where, enclosing=None):
    domains = declared_clock_domains(events, enclosing)
    if len(domains) <= 1:
        return []
    return [
        f"{where}: {SPIKE_CLOCK_DOMAIN_MISMATCH}; found {', '.join(sorted(domains))}"
    ]


def _missing_spike_event_key_errors(event, index, where, require_keys):
    return [
        f"{where}: spike_events[{index}] missing '{key}'"
        for key in require_keys
        if key not in event
    ]


def _invalid_spike_event_string_errors(event, index, where):
    return [
        f"{where}: spike_events[{index}].{key} must be a non-empty string"
        for key in SPIKE_EVENT_STRING_KEYS
        if key in event
        and (not isinstance(event[key], str) or not event[key].strip())
    ]


def _invalid_spike_event_number_errors(event, index, where):
    return [
        f"{where}: spike_events[{index}].{key} must be a finite number"
        for key in SPIKE_EVENT_NUMBER_KEYS
        if key in event and not is_number(event[key])
    ]


def _spike_event_field_errors(event, index, where, require_keys):
    return [
        *_missing_spike_event_key_errors(event, index, where, require_keys),
        *_invalid_spike_event_string_errors(event, index, where),
        *_invalid_spike_event_number_errors(event, index, where),
    ]


def _check_spike_event(event, index, where, require_keys):
    """Return this event's field errors and comparable timestamp, if any."""
    if not isinstance(event, dict):
        return [f"{where}: spike_events[{index}] must be an object"], None

    errors = _spike_event_field_errors(event, index, where, require_keys)
    present_time_keys = [key for key in SPIKE_TIME_KEYS if key in event]
    if not present_time_keys:
        errors.append(
            f"{where}: spike_events[{index}] needs finite "
            f"{' or '.join(SPIKE_TIME_KEYS)}"
        )
        return errors, None
    if len(present_time_keys) != 1:
        errors.append(
            f"{where}: spike_events[{index}] must use exactly one of "
            f"{' or '.join(SPIKE_TIME_KEYS)}"
        )
        return errors, None
    got = event_time(event)
    if got is None:
        return errors, None
    key, current = got
    return errors, (index, key, current)


def _spike_order_errors(timed, where):
    """Report only the first inversion in a comparable stream."""
    previous = None
    for index, key, current in timed:
        if previous is not None and exact_fraction(current) < exact_fraction(previous[1]):
            return [
                f"{where}: {SPIKE_ORDER_MISMATCH} at index "
                f"{index} ({key} {previous[1]} -> {current})"
            ]
        previous = (key, current)
    return []


def check_spike_order(
    events,
    where,
    require_keys=BRIDGE_SPIKE_EVENT_KEYS,
    *,
    enclosing=None,
):
    """Require schema-valid events on one globally ordered clock key."""
    errors = []
    timed = []
    for index, event in enumerate(events):
        event_errors, got = _check_spike_event(event, index, where, require_keys)
        errors.extend(event_errors)
        if got is not None:
            timed.append(got)

    stream_time_keys = {key for _, key, _ in timed}
    if len(stream_time_keys) > 1:
        errors.append(
            f"{where}: {SPIKE_TIME_KEY_MISMATCH}; found "
            f"{', '.join(sorted(stream_time_keys))}"
        )
        return errors

    domain_errors = _clock_domain_errors(events, where, enclosing)
    if domain_errors:
        return errors + domain_errors
    return errors + _spike_order_errors(timed, where)


def check_spike_stream(obj, where):
    """Check an optional trajectory-level spike train."""
    if "spike_events" not in obj:
        return []
    events = obj["spike_events"]
    if not isinstance(events, list):
        return [f"{where}: spike_events must be an array"]
    return check_spike_order(events, where, require_keys=(), enclosing=obj)
