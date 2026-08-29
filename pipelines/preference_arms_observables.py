#!/usr/bin/env python3
"""The reviewed machine-observable projection and the arm-distance metric."""

from __future__ import annotations

import math
from collections import Counter, defaultdict, deque
from functools import lru_cache
from typing import Any, Sequence

import sys
from pathlib import Path

_PIPELINES = Path(__file__).resolve().parent
if str(_PIPELINES) not in sys.path:
    sys.path.insert(0, str(_PIPELINES))

from curate_preferences import canonical_json  # noqa: E402

from preference_arms_text import (  # noqa: E402
    ListAlignmentError,
    _bounded_machine_identifier,
    _collect_terms,
    cosine_similarity,
)


#: Minimum lexical ``1 - cosine_similarity`` between the two arms'
#: contrastive surfaces. This is calibrated against the committed passing,
#: verbatim, light-edit, and multilingual fixtures. It intentionally does not
#: reuse the unrelated embedding threshold from ``quality_gate``.
DEFAULT_MIN_ARM_DISTANCE: float = 0.03


CONTRAST_FIELDS = frozenset({"executed_action", "future_outcome", "spike_events"})


LABEL_COPY_FIELDS = frozenset((*CONTRAST_FIELDS, "safety_decision"))


# Common leaf paths under executed behavior, its outcome, or a semantic spike
# identity must carry at least one machine-observable delta on both arms. Spike
# timestamps and amplitudes cannot establish behavioral independence. Keys present on only one side are
# ignored so an extension cannot manufacture independence. Free-form narrative
# strings are also ignored; compact identifier-like values count only when
# both sides use a bounded machine-token spelling.
MACHINE_OBSERVABLE_FIELDS = ("executed_action", "future_outcome", "spike_events")


_LIST_ITEM = "[]"


SPIKE_IDENTIFIER_KEYS = frozenset(
    {
        "channel",
        "event",
        "event_kind",
        "event_type",
        "kind",
        "neuron",
        "status",
        "unit",
    }
)


# The schema intentionally leaves executed_action/future_outcome open-ended,
# so publication cannot equate every nested scalar with behavioral evidence.
# These exact paths are the reviewed, machine-observable vocabulary used by
# both delta detection and distance scoring. New producer metrics must extend
# this registry and its regressions explicitly.
MACHINE_IDENTIFIER_PATHS = frozenset(
    {
        ("executed_action", "action"),
        ("executed_action", "outcome"),
        ("executed_action", "result"),
        ("executed_action", "status"),
        ("future_outcome", "outcome"),
        ("future_outcome", "result"),
        ("future_outcome", "status"),
        *(("spike_events", _LIST_ITEM, key) for key in SPIKE_IDENTIFIER_KEYS),
    }
)


MACHINE_NUMERIC_PATHS = frozenset(
    {
        ("executed_action", "attempts"),
        ("executed_action", "beacon_hits"),
        ("executed_action", "load_restored_via_tie"),
        ("executed_action", "new_setpoint_c"),
        ("executed_action", "silence_minutes"),
        ("executed_action", "speed_mps"),
        ("future_outcome", "crew_confirmed_clear_after_minutes"),
        ("future_outcome", "detected_after_minutes"),
        ("future_outcome", "doses_transferred"),
        ("future_outcome", "latency_ms"),
        ("future_outcome", "picker_detected_at_m"),
        ("future_outcome", "throughput_debt_minutes"),
    }
)


MACHINE_BOOLEAN_PATHS = frozenset(
    {
        ("future_outcome", "estop"),
        ("future_outcome", "near_miss"),
        ("future_outcome", "success"),
    }
)


# Lists are matched position-independently. Exact multiset members cancel
# first; only a small residual set may enter the deterministic minimum-cost
# matcher. Oversized residuals fail closed instead of falling back to
# positional zip.
MAX_ALIGNMENT_LIST_ITEMS = 256


MAX_ALIGNMENT_RESIDUAL_ITEMS = 12


_GATE_LABEL_PATHS = frozenset({("safety_decision", "decision")})


def _behavior_surface(arm: dict[str, Any]) -> dict[str, Any]:
    """Return fields used by the explicit gate-label-copy check."""

    return {key: arm[key] for key in arm if key in LABEL_COPY_FIELDS}


def _approved_observable_value(path: tuple[str, ...], value: Any) -> bool:
    """Whether one value occupies a reviewed machine-observable path."""

    if path in MACHINE_IDENTIFIER_PATHS:
        return isinstance(value, str) and _bounded_machine_identifier(value) is not None
    if path in MACHINE_BOOLEAN_PATHS:
        return type(value) is bool
    if path in MACHINE_NUMERIC_PATHS:
        return type(value) in (int, float) and (type(value) is int or math.isfinite(value))
    return False


def _normalized_observable_value(path: tuple[str, ...], value: Any) -> Any:
    """Return the comparison value used by both scoring and delta detection."""

    if path in MACHINE_IDENTIFIER_PATHS:
        return _bounded_machine_identifier(value)
    # JSON permits multiple spellings for one finite numeric value. Keep bools
    # distinct, but collapse integral floats (including negative zero) onto the
    # matching integer so 0, 0.0, and -0.0 cannot manufacture a delta or term.
    if type(value) is float and value.is_integer():
        return int(value)
    return value


def _mapping_observable_terms(value: dict[Any, Any], path: tuple[str, ...]) -> Counter[str]:
    """Project a mapping onto the vocabulary in canonical key order."""

    terms: Counter[str] = Counter()
    for key in sorted(value):
        terms.update(_single_observable_terms(value[key], (*path, str(key))))
    return terms


def _sequence_observable_terms(value: list[Any], path: tuple[str, ...]) -> Counter[str]:
    """Project a list onto the vocabulary under one shared item path."""

    terms: Counter[str] = Counter()
    for item in value:
        terms.update(_single_observable_terms(item, (*path, _LIST_ITEM)))
    return terms


def _leaf_observable_terms(value: Any, path: tuple[str, ...]) -> Counter[str]:
    """Project one scalar, keeping only reviewed machine-observable paths."""

    terms: Counter[str] = Counter()
    if _approved_observable_value(path, value):
        _collect_terms(
            _normalized_observable_value(path, value),
            "." + ".".join(path),
            terms,
        )
    return terms


def _single_observable_terms(
    value: Any,
    path: tuple[str, ...],
) -> Counter[str]:
    """Project one value onto the reviewed observable vocabulary."""

    if isinstance(value, dict):
        return _mapping_observable_terms(value, path)
    if isinstance(value, list):
        return _sequence_observable_terms(value, path)
    return _leaf_observable_terms(value, path)


def _alignment_item_terms(value: Any, path: tuple[str, ...]) -> Counter[str]:
    """Return only reviewed terms used to align unordered list items."""

    return _single_observable_terms(value, path)


def _alignment_signature(value: Any, path: tuple[str, ...]) -> str:
    return canonical_json(sorted(_alignment_item_terms(value, path).items()))


def _alignment_cost(left: Any, right: Any, path: tuple[str, ...]) -> float:
    return 1.0 - cosine_similarity(
        _alignment_item_terms(left, path),
        _alignment_item_terms(right, path),
    )


def _checked_residual_size(
    left: list[tuple[int, Any]],
    right: list[tuple[int, Any]],
) -> None:
    """Fail closed rather than approximate an oversized residual matching."""

    if max(len(left), len(right)) > MAX_ALIGNMENT_RESIDUAL_ITEMS:
        raise ListAlignmentError(
            "list alignment has too many non-identical residual items "
            f"({len(left)} by {len(right)}; max {MAX_ALIGNMENT_RESIDUAL_ITEMS})"
        )


def _signature_ordered(
    items: list[tuple[int, Any]],
    path: tuple[str, ...],
) -> list[tuple[int, Any]]:
    """Order residual items by canonical projection rather than position."""

    return sorted(items, key=lambda item: _alignment_signature(item[1], path))


def _alignment_cost_matrix(
    short: list[tuple[int, Any]],
    long: list[tuple[int, Any]],
    path: tuple[str, ...],
) -> tuple[tuple[float, ...], ...]:
    """Return every pairwise residual alignment cost, shortest side first."""

    return tuple(
        tuple(_alignment_cost(short_item, long_item, path) for _, long_item in long)
        for _, short_item in short
    )


def _better_assignment(
    candidate_cost: float,
    candidate_assignment: tuple[int, ...],
    best_cost: float,
    best_assignment: tuple[int, ...],
) -> bool:
    """Whether a candidate wins on cost, then on canonical assignment order."""

    if candidate_cost < best_cost - 1e-12:
        return True
    if not math.isclose(candidate_cost, best_cost, abs_tol=1e-12):
        return False
    return not best_assignment or candidate_assignment < best_assignment


def _minimum_cost_assignment(costs: tuple[tuple[float, ...], ...]) -> tuple[int, ...]:
    """Return the deterministic minimum-cost assignment over a cost matrix."""

    row_count = len(costs)

    @lru_cache(maxsize=None)
    def solve(index: int, used: int) -> tuple[float, tuple[int, ...]]:
        if index == row_count:
            return 0.0, ()
        best_cost = math.inf
        best_assignment: tuple[int, ...] = ()
        for long_index in range(len(costs[index])):
            bit = 1 << long_index
            if used & bit:
                continue
            tail_cost, tail_assignment = solve(index + 1, used | bit)
            candidate_cost = costs[index][long_index] + tail_cost
            candidate_assignment = (long_index, *tail_assignment)
            if _better_assignment(
                candidate_cost, candidate_assignment, best_cost, best_assignment
            ):
                best_cost = candidate_cost
                best_assignment = candidate_assignment
        return best_cost, best_assignment

    _, assignment = solve(0, 0)
    return assignment


def _sourced_pairs(
    short: list[tuple[int, Any]],
    long: list[tuple[int, Any]],
    assignment: tuple[int, ...],
    swapped: bool,
) -> tuple[tuple[int, int], ...]:
    """Restate an assignment as source index pairs in left/right order."""

    pairs = []
    for short_index, long_index in enumerate(assignment):
        short_source = short[short_index][0]
        long_source = long[long_index][0]
        pairs.append((long_source, short_source) if swapped else (short_source, long_source))
    return tuple(pairs)


def _minimum_cost_pairs(
    left: list[tuple[int, Any]],
    right: list[tuple[int, Any]],
    path: tuple[str, ...],
) -> tuple[tuple[int, int], ...]:
    """Return a deterministic minimum-cost residual matching."""

    if not left or not right:
        return ()
    _checked_residual_size(left, right)

    # Canonical projection order, not source position, owns every tie-break.
    # This keeps front/middle/tail insertions and list reordering from shifting
    # otherwise identical evidence onto different counterparts.
    left = _signature_ordered(left, path)
    right = _signature_ordered(right, path)
    swapped = len(left) > len(right)
    short, long = (right, left) if swapped else (left, right)
    assignment = _minimum_cost_assignment(_alignment_cost_matrix(short, long, path))
    return _sourced_pairs(short, long, assignment, swapped)


def _checked_list_size(left: list[Any], right: list[Any]) -> None:
    """Fail closed rather than align lists beyond the reviewed item limit."""

    if max(len(left), len(right)) > MAX_ALIGNMENT_LIST_ITEMS:
        raise ListAlignmentError(
            "list alignment exceeds item limit "
            f"({len(left)} by {len(right)}; max {MAX_ALIGNMENT_LIST_ITEMS})"
        )


def _exact_signature_pairs(
    left: list[Any],
    right: list[Any],
    item_path: tuple[str, ...],
) -> tuple[list[tuple[int, int]], set[int], set[int]]:
    """Cancel identically projecting items as a multiset, earliest side first."""

    right_by_payload: dict[str, deque[int]] = defaultdict(deque)
    try:
        for right_index, item in enumerate(right):
            right_by_payload[_alignment_signature(item, item_path)].append(right_index)
        exact_pairs: list[tuple[int, int]] = []
        used_left: set[int] = set()
        used_right: set[int] = set()
        for left_index, item in enumerate(left):
            candidates = right_by_payload[_alignment_signature(item, item_path)]
            if not candidates:
                continue
            right_index = candidates.popleft()
            exact_pairs.append((left_index, right_index))
            used_left.add(left_index)
            used_right.add(right_index)
    except (TypeError, ValueError) as exc:
        raise ListAlignmentError(f"list item is not canonical JSON: {exc}") from exc
    return exact_pairs, used_left, used_right


def _residual_items(items: list[Any], used: set[int]) -> list[tuple[int, Any]]:
    """Return the source-indexed items left over after exact cancellation."""

    return [(index, item) for index, item in enumerate(items) if index not in used]


def _aligned_list_pairs(
    left: list[Any],
    right: list[Any],
    path: tuple[str, ...],
) -> tuple[tuple[Any, Any], ...]:
    """Align unordered common list content without admitting one-sided items."""

    _checked_list_size(left, right)

    item_path = (*path, _LIST_ITEM)
    exact_pairs, used_left, used_right = _exact_signature_pairs(left, right, item_path)
    residual_pairs = _minimum_cost_pairs(
        _residual_items(left, used_left),
        _residual_items(right, used_right),
        item_path,
    )
    index_pairs = sorted((*exact_pairs, *residual_pairs))
    return tuple((left[left_index], right[right_index]) for left_index, right_index in index_pairs)


def _approved_observable_leaf(path: tuple[str, ...], left: Any, right: Any) -> bool:
    """Whether both values occupy one reviewed machine-observable path."""

    return _approved_observable_value(path, left) and _approved_observable_value(path, right)


def _common_mapping_leaves(
    left: dict[Any, Any],
    right: dict[Any, Any],
    path: tuple[str, ...],
) -> list[tuple[tuple[str, ...], Any, Any]]:
    """Descend only shared keys so an extension cannot manufacture evidence."""

    result: list[tuple[tuple[str, ...], Any, Any]] = []
    for key in sorted(set(left) & set(right)):
        result.extend(_common_observable_leaves(left[key], right[key], (*path, str(key))))
    return result


def _common_sequence_leaves(
    left: list[Any],
    right: list[Any],
    path: tuple[str, ...],
) -> list[tuple[tuple[str, ...], Any, Any]]:
    """Descend list content through the position-independent alignment."""

    result: list[tuple[tuple[str, ...], Any, Any]] = []
    for left_item, right_item in _aligned_list_pairs(left, right, path):
        result.extend(_common_observable_leaves(left_item, right_item, (*path, _LIST_ITEM)))
    return result


def _both_mappings(left: Any, right: Any) -> bool:
    """Whether both arms present a mapping at this path."""

    return isinstance(left, dict) and isinstance(right, dict)


def _both_sequences(left: Any, right: Any) -> bool:
    """Whether both arms present a list at this path."""

    return isinstance(left, list) and isinstance(right, list)


def _common_observable_leaves(
    left: Any,
    right: Any,
    path: tuple[str, ...],
) -> list[tuple[tuple[str, ...], Any, Any]]:
    """Return aligned leaves from the reviewed behavioral projection."""

    if _both_mappings(left, right):
        return _common_mapping_leaves(left, right, path)
    if _both_sequences(left, right):
        return _common_sequence_leaves(left, right, path)
    return [(path, left, right)] if _approved_observable_leaf(path, left, right) else []


def _common_arm_observable_leaves(
    chosen: dict[str, Any], rejected: dict[str, Any]
) -> list[tuple[tuple[str, ...], Any, Any]]:
    leaves: list[tuple[tuple[str, ...], Any, Any]] = []
    for field_name in MACHINE_OBSERVABLE_FIELDS:
        if field_name in chosen and field_name in rejected:
            leaves.extend(
                _common_observable_leaves(
                    chosen[field_name],
                    rejected[field_name],
                    (field_name,),
                )
            )
    return leaves


def _observable_terms(
    leaves: Sequence[tuple[tuple[str, ...], Any, Any]],
) -> tuple[Counter[str], Counter[str]]:
    left_terms: Counter[str] = Counter()
    right_terms: Counter[str] = Counter()
    for path, left, right in leaves:
        term_path = "." + ".".join(path)
        _collect_terms(_normalized_observable_value(path, left), term_path, left_terms)
        _collect_terms(_normalized_observable_value(path, right), term_path, right_terms)
    return left_terms, right_terms


def _observable_deltas_from_leaves(
    leaves: Sequence[tuple[tuple[str, ...], Any, Any]],
) -> tuple[str, ...]:
    return tuple(
        ".".join(path)
        for path, left, right in leaves
        if canonical_json(_normalized_observable_value(path, left))
        != canonical_json(_normalized_observable_value(path, right))
    )


def machine_observable_deltas(chosen: dict[str, Any], rejected: dict[str, Any]) -> tuple[str, ...]:
    """Return changed paths from the reviewed, aligned observable projection."""

    return _observable_deltas_from_leaves(_common_arm_observable_leaves(chosen, rejected))


def _without_gate_labels(value: Any, path: tuple[str, ...] = ()) -> Any:
    """Return a comparison value with only recognized gate labels removed."""

    if isinstance(value, dict):
        result = {}
        for key, item in value.items():
            child_path = (*path, str(key))
            if child_path in _GATE_LABEL_PATHS:
                continue
            result[key] = _without_gate_labels(item, child_path)
        return result
    if isinstance(value, list):
        return [_without_gate_labels(item, path) for item in value]
    return value


def differs_only_by_gate_label(chosen: dict[str, Any], rejected: dict[str, Any]) -> bool:
    """Whether the sole contrastive change is a safety gate decision label."""

    chosen_surface = _behavior_surface(chosen)
    rejected_surface = _behavior_surface(rejected)
    if canonical_json(chosen_surface) == canonical_json(rejected_surface):
        return False
    return canonical_json(_without_gate_labels(chosen_surface)) == canonical_json(
        _without_gate_labels(rejected_surface)
    )


def arm_terms(arm: dict[str, Any]) -> Counter[str]:
    """Return one arm's path-scoped, reviewed observable projection."""

    terms: Counter[str] = Counter()
    for field_name in MACHINE_OBSERVABLE_FIELDS:
        if field_name in arm:
            terms.update(_single_observable_terms(arm[field_name], (field_name,)))
    return terms


def arm_distance(chosen: dict[str, Any], rejected: dict[str, Any]) -> float:
    """Return distance over the same aligned projection used for deltas."""

    chosen_terms, rejected_terms = _observable_terms(
        _common_arm_observable_leaves(chosen, rejected)
    )
    return 1.0 - cosine_similarity(chosen_terms, rejected_terms)


def _validated_distance_floor(value: Any) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"arm-distance floor must be numeric: {value!r}")
    value = float(value)
    if not math.isfinite(value) or not 0.0 <= value < 1.0:
        raise ValueError(f"arm-distance floor must be a finite value in [0, 1): {value!r}")
    return value
