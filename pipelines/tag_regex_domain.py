"""Character-domain proofs for taxonomy regex atoms."""

from __future__ import annotations

from re import _parser as _re_parser
from typing import Any

RegexDomain = tuple[bool, tuple[tuple[int, int], ...]] | None

REGEX_CONSUMING_ATOMS = frozenset(
    {
        _re_parser.LITERAL,
        _re_parser.NOT_LITERAL,
        _re_parser.ANY,
        _re_parser.IN,
        _re_parser.CATEGORY,
    }
)
REGEX_REPEAT_OPS = frozenset(
    {
        _re_parser.MAX_REPEAT,
        _re_parser.MIN_REPEAT,
        _re_parser.POSSESSIVE_REPEAT,
    }
)


def merge_ranges(ranges: list[tuple[int, int]]) -> tuple[tuple[int, int], ...]:
    merged: list[list[int]] = []
    for span in sorted(ranges):
        _append_or_extend_range(merged, span)
    return tuple((lower, upper) for lower, upper in merged)


def _append_or_extend_range(merged: list[list[int]], span: tuple[int, int]) -> None:
    lower, upper = span
    if not merged:
        merged.append([lower, upper])
        return
    if lower > merged[-1][1] + 1:
        merged.append([lower, upper])
        return
    merged[-1][1] = max(merged[-1][1], upper)


def ranges_intersect(
    left: tuple[tuple[int, int], ...], right: tuple[tuple[int, int], ...]
) -> bool:
    state = [0, 0]
    while _both_in_range(state, left, right):
        if not _advance_if_disjoint(left, right, state):
            return True
    return False


def _both_in_range(
    state: list[int],
    left: tuple[tuple[int, int], ...],
    right: tuple[tuple[int, int], ...],
) -> bool:
    if state[0] >= len(left):
        return False
    return state[1] < len(right)


def _advance_if_disjoint(
    left: tuple[tuple[int, int], ...],
    right: tuple[tuple[int, int], ...],
    state: list[int],
) -> bool:
    _left_lower, left_upper = left[state[0]]
    right_lower, right_upper = right[state[1]]
    if left_upper < right_lower:
        state[0] += 1
        return True
    if right_upper < _left_lower:
        state[1] += 1
        return True
    return False


def ranges_are_subset(
    candidate: tuple[tuple[int, int], ...], container: tuple[tuple[int, int], ...]
) -> bool:
    container_index = 0
    for span in candidate:
        container_index = _advance_container(container, container_index, span[0])
        if not _span_covered(span, container, container_index):
            return False
    return True


def _advance_container(
    container: tuple[tuple[int, int], ...],
    container_index: int,
    candidate_lower: int,
) -> int:
    while container_index < len(container):
        if container[container_index][1] >= candidate_lower:
            break
        container_index += 1
    return container_index


def _span_covered(
    span: tuple[int, int],
    container: tuple[tuple[int, int], ...],
    container_index: int,
) -> bool:
    if container_index == len(container):
        return False
    container_lower, container_upper = container[container_index]
    if container_lower > span[0]:
        return False
    if container_upper < span[1]:
        return False
    return True


def regex_domains_are_disjoint(left: RegexDomain, right: RegexDomain) -> bool:
    if left is None:
        return False
    if right is None:
        return False
    left_negated, left_ranges = left
    right_negated, right_ranges = right
    if left_negated:
        return _disjoint_when_left_negated(left_ranges, right_negated, right_ranges)
    if right_negated:
        return ranges_are_subset(left_ranges, right_ranges)
    return not ranges_intersect(left_ranges, right_ranges)


def _disjoint_when_left_negated(
    left_ranges: tuple[tuple[int, int], ...],
    right_negated: bool,
    right_ranges: tuple[tuple[int, int], ...],
) -> bool:
    if right_negated:
        return False
    return ranges_are_subset(right_ranges, left_ranges)


def regex_atom_domain(item: tuple[Any, Any]) -> RegexDomain:
    """Return an exact finite/complement character domain when available."""
    operation, argument = item
    if operation is _re_parser.LITERAL:
        return False, ((argument, argument),)
    if operation is _re_parser.NOT_LITERAL:
        return True, ((argument, argument),)
    if operation is _re_parser.ANY:
        return None
    if operation is _re_parser.CATEGORY:
        return None
    if operation is _re_parser.IN:
        return _in_class_domain(argument)
    return None


def _in_class_domain(argument: Any) -> RegexDomain:
    negated = False
    ranges: list[tuple[int, int]] = []
    for class_operation, class_argument in argument:
        kind = _classify_in_item(class_operation, class_argument, ranges)
        if kind is None:
            return None
        negated = negated or kind
    return negated, merge_ranges(ranges)


def _classify_in_item(
    class_operation: Any,
    class_argument: Any,
    ranges: list[tuple[int, int]],
) -> bool | None:
    if class_operation is _re_parser.NEGATE:
        return True
    if class_operation is _re_parser.LITERAL:
        ranges.append((class_argument, class_argument))
        return False
    if class_operation is _re_parser.RANGE:
        ranges.append(class_argument)
        return False
    # Unicode categories and bitmap opcodes are safe as atoms, but treating
    # their domains as unknown keeps boundary proofs sound.
    return None


def overlaps_any_domain(domain: RegexDomain, domains: list[RegexDomain]) -> bool:
    for prior in domains:
        if not regex_domains_are_disjoint(domain, prior):
            return True
    return False
