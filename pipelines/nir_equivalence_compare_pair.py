#!/usr/bin/env python3
"""Comparing one pair of runtime entries.

Attribution is deliberately conservative: a convention is named as a candidate
cause only when the graph contains the construct it governs, and the record
says that is a candidate rather than a proven cause.
"""

from __future__ import annotations

import sys
from pathlib import Path

_PIPELINES = Path(__file__).resolve().parent
if str(_PIPELINES) not in sys.path:
    sys.path.insert(0, str(_PIPELINES))

from nir_equivalence_execute import _executed  # noqa: E402
from nir_equivalence_terms import (  # noqa: E402
    NUMERIC_TOL,
)

def convention_delta(entries):
    """Which declared conventions differ between the executed runtimes."""
    executed = _executed(entries)
    keys = set()
    for entry in executed:
        keys.update(entry.get("conventions") or {})
    delta = []
    for key in sorted(keys):
        values = {
            entry["runtime"]: (entry.get("conventions") or {}).get(key)
            for entry in executed
        }
        if len(set(values.values())) > 1:
            delta.append({"convention": key, "values": values})
    return delta


CONVENTION_REASON = {
    "reset": "DIVERGENCE_RESET_CONVENTION",
    "delay_unit": "DIVERGENCE_DELAY_SEMANTICS",
    "cycle_break_order": "DIVERGENCE_RECURRENT_ORDER",
}

def relevant_conventions(graph, entries):
    """Which differing conventions this graph can actually exercise.

    Two runtimes may declare several different conventions while a given graph
    contains no construct that any of them govern. Listing all of them as
    candidate causes of an observed divergence would be noise dressed as
    analysis, so a convention is only a candidate when the graph contains the
    construct it applies to and, for reset, when a spike actually fired.
    """
    nodes = (graph or {}).get("nodes") or {}
    types = {node.get("type") for node in nodes.values()}
    executed = _executed(entries)
    spiked = any(
        ((entry.get("outputs") or {}).get("spike_count") or 0) > 0 for entry in executed
    )
    has_recurrence = any(
        (entry.get("outputs") or {}).get("recurrent_edges") for entry in executed
    )
    relevant = set()
    if types & {"LIF", "IF"} and spiked:
        relevant.add("reset")
    if "Delay" in types:
        relevant.add("delay_unit")
    if has_recurrence:
        relevant.add("cycle_break_order")
    return relevant


def _candidate_causes(delta, relevant, output_agree, state_agree):
    """Declared convention differences this graph could have diverged over.

    A candidate explanation for an observed divergence, never a proven cause,
    and empty while nothing has diverged.
    """
    if output_agree is not False and state_agree is not False:
        return []
    return [
        CONVENTION_REASON[item["convention"]]
        for item in delta
        if item["convention"] in CONVENTION_REASON and item["convention"] in relevant
    ]


def _state_error(entry_a, entry_b):
    """Largest end-of-window membrane difference across shared nodes.

    Returns ``(max_error, comparable)``. Nodes present on only one side make
    the comparison incomparable rather than silently partial.
    """
    state_a = (entry_a.get("outputs") or {}).get("final_membrane") or {}
    state_b = (entry_b.get("outputs") or {}).get("final_membrane") or {}
    if set(state_a) != set(state_b):
        return None, False
    max_error = 0.0
    for name, blob_a in state_a.items():
        values_a = blob_a.get("v") or []
        values_b = (state_b[name] or {}).get("v") or []
        if len(values_a) != len(values_b):
            return None, False
        for value_a, value_b in zip(values_a, values_b):
            max_error = max(max_error, abs(value_a - value_b))
    return max_error, True


def _compare_pair(entry_a, entry_b):
    # Executed entries are shape-checked by _check_runtimes before validation
    # reaches here, but compare_runtimes is also called on freshly generated
    # entries, so missing keys degrade to "not comparable" rather than raising
    # and taking down the scan of a whole run directory.
    trace_a = (entry_a.get("outputs") or {}).get("output_trace")
    trace_b = (entry_b.get("outputs") or {}).get("output_trace")
    if not isinstance(trace_a, list) or not isinstance(trace_b, list):
        return _incomparable_pair(entry_a, entry_b)
    pair = _pair_identity(entry_a, entry_b)
    if _trace_shapes_differ(trace_a, trace_b):
        pair.update(
            {
                "agree": False,
                "shape_match": False,
                "first_divergent_step": 0,
                "max_abs_error": None,
                "reason_codes": ["COMPARISON_MISMATCH"],
            }
        )
        return pair
    first_divergent, max_error = _trace_divergence(trace_a, trace_b)
    events_agree = _spike_events_agree(entry_a, entry_b)
    reason_codes = _pair_reason_codes(pair, events_agree, max_error)
    behavioural = [
        code for code in reason_codes if code != "DIVERGENCE_INTERNAL_STATE"
    ]
    pair.update(
        {
            # Whole-output digests are evidence identifiers, not a numerical
            # comparator: traces that differ within NUMERIC_TOL legitimately
            # hash differently. Event streams remain exact, while numeric
            # traces use the declared tolerance.
            "agree": not behavioural and events_agree,
            "shape_match": True,
            "first_divergent_step": first_divergent,
            "max_abs_error": max_error,
            "reason_codes": sorted(set(reason_codes)),
        }
    )
    return pair


def _incomparable_pair(entry_a, entry_b):
    """A pair one side of which has no usable trace: reported, never dropped."""
    return {
        "a": entry_a.get("runtime"),
        "b": entry_b.get("runtime"),
        "agree": False,
        "shape_match": False,
        "spike_count_a": (entry_a.get("outputs") or {}).get("spike_count"),
        "spike_count_b": (entry_b.get("outputs") or {}).get("spike_count"),
        "digest_a": entry_a.get("output_digest"),
        "digest_b": entry_b.get("output_digest"),
        "state_comparable": False,
        "max_abs_state_error": None,
        "state_agree": False,
        "first_divergent_step": 0,
        "max_abs_error": None,
        "reason_codes": ["COMPARISON_MISMATCH"],
    }


def _pair_identity(entry_a, entry_b):
    """Runtime names, spike counts, output digests, and end-of-window state."""
    state_error, state_comparable = _state_error(entry_a, entry_b)
    return {
        "a": entry_a["runtime"],
        "b": entry_b["runtime"],
        "spike_count_a": entry_a["outputs"]["spike_count"],
        "spike_count_b": entry_b["outputs"]["spike_count"],
        "digest_a": entry_a["output_digest"],
        "digest_b": entry_b["output_digest"],
        "state_comparable": state_comparable,
        "max_abs_state_error": state_error,
        "state_agree": bool(state_comparable and state_error <= NUMERIC_TOL),
    }


def _trace_shapes_differ(trace_a, trace_b):
    """Whether the two traces disagree on window length or channel width."""
    return bool(
        len(trace_a) != len(trace_b)
        or (trace_a and trace_b and len(trace_a[0]) != len(trace_b[0]))
    )


def _trace_divergence(trace_a, trace_b):
    """First step that diverges beyond tolerance, and the largest error seen."""
    first_divergent = None
    max_error = 0.0
    for step, (row_a, row_b) in enumerate(zip(trace_a, trace_b)):
        for value_a, value_b in zip(row_a, row_b):
            error = abs(value_a - value_b)
            max_error = max(max_error, error)
            if error > NUMERIC_TOL and first_divergent is None:
                first_divergent = step
    return first_divergent, max_error


def _spike_events_agree(entry_a, entry_b):
    """Event streams are compared exactly; only numeric traces get a tolerance."""
    return entry_a["outputs"].get("spike_events") == entry_b["outputs"].get(
        "spike_events"
    )


def _pair_reason_codes(pair, events_agree, max_error):
    """Every divergence this pair shows, before any verdict policy is applied."""
    reason_codes = []
    if not events_agree:
        reason_codes.append("DIVERGENCE_EVENT_STREAM")
    if pair["spike_count_a"] != pair["spike_count_b"]:
        reason_codes.append("DIVERGENCE_SPIKE_COUNT")
    if max_error > NUMERIC_TOL:
        reason_codes.append("DIVERGENCE_NUMERIC_TOLERANCE")
    # Internal state divergence is reported but does not by itself make the
    # verdict a mismatch: the verdict is about the event stream that leaves the
    # graph, which is what a downstream consumer sees.
    if not pair["state_agree"]:
        reason_codes.append("DIVERGENCE_INTERNAL_STATE")
    return reason_codes
