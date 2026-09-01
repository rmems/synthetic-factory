#!/usr/bin/env python3
"""Bridge event ordering, clock-domain, and record-locator primitives."""

from __future__ import annotations

from typing import Any, Sequence

if __package__:
    from . import _expose_package_sibling, _local_sibling_module
    if _local_sibling_module("curate_bridge_events", allow_initializing=True) is not None:
        import curate_bridge_events as _direct_curate_bridge_events
        del _direct_curate_bridge_events
    from .exact_json import dumps_exact_json, exact_fraction
else:
    from exact_json import dumps_exact_json, exact_fraction


TIME_KEYS = ("t_rel_ms", "t_ms")
CLOCK_DOMAIN_KEYS = (
    "clock_id",
    "clock_domain",
    "timebase",
    "timebase_id",
    "source_clock",
    "source_clock_id",
)
EXPLICIT_ORDER_KEYS = (
    "burst_id",
    "causal_group",
    "causal_group_id",
    "caused_by",
    "event_group",
    "event_group_id",
    "event_order",
    "event_ordering",
    "event_sequence",
    "follows",
    "group_id",
    "happens_before",
    "parent_event_id",
    "precedes",
    "predecessor_id",
    "segment_id",
    "sequence_id",
    "sequence_index",
    "trial_id",
)


def _nonblank_identifier(value: Any) -> str | None:
    return value if isinstance(value, str) and value.strip() else None


def _record_locator(record: Any) -> str | None:
    if not isinstance(record, dict):
        return None
    meta = record.get("meta")
    view = record.get("language_view")
    trajectory = view.get("trajectory") if isinstance(view, dict) else None
    state = trajectory.get("state") if isinstance(trajectory, dict) else None
    candidates = (
        record.get("id"),
        state.get("episode_id") if isinstance(state, dict) else None,
        meta.get("id") if isinstance(meta, dict) else None,
    )
    return next(filter(None, map(_nonblank_identifier, candidates)), None)


def _canonical_marker(value: Any) -> str:
    try:
        return dumps_exact_json(value, ensure_ascii=False, sort_keys=True)
    except (TypeError, ValueError):
        return repr(value)


def _record_containers(record: dict[str, Any], events: list[Any]) -> list[dict[str, Any]]:
    containers = [record]
    meta = record.get("meta")
    if isinstance(meta, dict):
        containers.append(meta)
    containers.extend(event for event in events if isinstance(event, dict))
    return containers


def _declared_clock_domains(record: dict[str, Any], events: list[Any]) -> list[str]:
    values = {
        f"{key}={_canonical_marker(container[key])}"
        for container in _record_containers(record, events)
        for key in CLOCK_DOMAIN_KEYS
        if key in container
    }
    return sorted(values)


def _explicit_order_fields(record: dict[str, Any], events: list[Any]) -> list[str]:
    return sorted(
        {
            key
            for container in _record_containers(record, events)
            for key in EXPLICIT_ORDER_KEYS
            if key in container
        }
    )


def _adjacent_descents(times: Sequence[Any]) -> list[dict[str, Any]]:
    return [
        {
            "left_index": index - 1,
            "right_index": index,
            "left_time": times[index - 1],
            "right_time": times[index],
        }
        for index in range(1, len(times))
        if exact_fraction(times[index]) < exact_fraction(times[index - 1])
    ]


if __package__:
    _expose_package_sibling(__name__)
