"""Bridge event-stream classification for the corpus training audit."""

from __future__ import annotations

if __package__:
    from .validate_run import (
        BRIDGE_SPIKE_EVENT_KEYS,
        SPIKE_ORDER_MISMATCH,
        check_spike_order,
    )
else:
    from validate_run import (
        BRIDGE_SPIKE_EVENT_KEYS,
        SPIKE_ORDER_MISMATCH,
        check_spike_order,
    )


def event_stream_status(events, enclosing=None):
    """Classify presence, event validity, and global temporal order.

    Event-shape validity is delegated to the strict publish-gate validator.
    Only a pure chronological-order violation on an otherwise-valid stream is
    classified as ``unsorted``; all other validator errors are ``invalid``.

    ``enclosing`` is the record that owns the stream, including any clock
    declaration on the record or its ``meta`` mapping.
    """
    if not isinstance(events, list) or not events:
        return "missing"
    errors = check_spike_order(
        events,
        "",
        require_keys=BRIDGE_SPIKE_EVENT_KEYS,
        enclosing=enclosing,
    )
    order_error_prefix = f": {SPIKE_ORDER_MISMATCH} at index "
    if any(not error.startswith(order_error_prefix) for error in errors):
        return "invalid"
    return "unsorted" if errors else "sorted"
