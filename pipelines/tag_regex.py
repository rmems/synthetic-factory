"""Linear-time subset checks for taxonomy regexes.

Taxonomy regexes run against source-controlled data, so merely compiling is
not enough: Python's backtracking engine can take exponential time on valid
patterns such as ``^(a+)+$``.  The accepted subset keeps the shipped grammar
while excluding constructs that can repeatedly revisit variable-length
subexpressions.

The parser is private to ``re`` but stable across the supported CPython
3.12+ range.  Keeping validation on its parsed opcode tree avoids writing a
second, subtly different regex parser.
"""

from __future__ import annotations

import re
from re import _parser as _re_parser
from typing import Any

from tag_constants import TagTaxonomyError
from tag_regex_domain import (
    REGEX_CONSUMING_ATOMS,
    REGEX_REPEAT_OPS,
    RegexDomain,
    overlaps_any_domain,
    regex_atom_domain,
    regex_domains_are_disjoint,
)

_MAX_SAFE_REGEX_LENGTH = 8_192
_MAX_SAFE_REGEX_REPEATS = 64
_MAX_SAFE_REGEX_BRANCHES = 64
_MAX_SAFE_BOUNDED_REPEAT = 10_000
_REGEX_RESOURCE_ERRORS = (OverflowError, RecursionError, MemoryError)
_SKIP_LEADING = object()


class UnsafeRegexError(ValueError):
    """Raised internally when a regex leaves the supported linear subset."""


def regex_sequence_is_nullable(items: Any) -> bool:
    """Whether a parsed sequence can consume no characters."""
    for operation, argument in items:
        if not _regex_op_is_nullable(operation, argument):
            return False
    return True


def _regex_op_is_nullable(operation: Any, argument: Any) -> bool:
    if operation is _re_parser.AT:
        return True
    if operation in REGEX_CONSUMING_ATOMS:
        return False
    if operation is _re_parser.SUBPATTERN:
        return _nullable_subpattern(argument)
    if operation is _re_parser.BRANCH:
        return _nullable_branch(argument)
    if operation in REGEX_REPEAT_OPS:
        return _nullable_repeat(argument)
    return False


def _nullable_subpattern(argument: Any) -> bool:
    _group, add_flags, del_flags, body = argument
    if add_flags:
        return False
    if del_flags:
        return False
    return regex_sequence_is_nullable(body)


def _nullable_branch(argument: Any) -> bool:
    _none, branches = argument
    for branch in branches:
        if regex_sequence_is_nullable(branch):
            return True
    return False


def _nullable_repeat(argument: Any) -> bool:
    minimum, _maximum, body = argument
    if minimum == 0:
        return True
    return regex_sequence_is_nullable(body)


def regex_leading_domain(items: Any) -> RegexDomain:
    """Return a provable first-character domain for a repeated body."""
    for operation, argument in items:
        domain = _leading_op_domain(operation, argument)
        if domain is not _SKIP_LEADING:
            return domain
    return None


def _leading_op_domain(operation: Any, argument: Any) -> RegexDomain | object:
    if operation is _re_parser.AT:
        return _SKIP_LEADING
    if operation in REGEX_CONSUMING_ATOMS:
        return regex_atom_domain((operation, argument))
    if operation is _re_parser.SUBPATTERN:
        return _leading_subpattern_domain(argument)
    if operation is _re_parser.BRANCH:
        return None
    if operation in REGEX_REPEAT_OPS:
        return _leading_repeat_domain(argument)
    return None


def _leading_subpattern_domain(argument: Any) -> RegexDomain:
    _group, add_flags, del_flags, body = argument
    if add_flags:
        return None
    if del_flags:
        return None
    return regex_leading_domain(body)


def _leading_repeat_domain(argument: Any) -> RegexDomain:
    minimum, _maximum, body = argument
    if minimum == 0:
        return None
    return regex_leading_domain(body)


def append_regex_domain(domains: list[RegexDomain], domain: RegexDomain) -> None:
    if domain in domains:
        return
    domains.append(domain)


def has_safe_repeat_boundary(repeated_domain: RegexDomain, between: Any) -> bool:
    """Whether a mandatory atom fixes the end of an earlier unbounded repeat."""
    for item in between:
        if _item_is_disjoint_atom(repeated_domain, item):
            return True
    return False


def _item_is_disjoint_atom(repeated_domain: RegexDomain, item: tuple[Any, Any]) -> bool:
    operation, argument = item
    if operation not in REGEX_CONSUMING_ATOMS:
        return False
    atom = regex_atom_domain((operation, argument))
    return regex_domains_are_disjoint(repeated_domain, atom)


def validate_linear_regex_sequence(
    items: Any,
    counters: dict[str, int],
    inherited_variables: tuple[RegexDomain, ...] = (),
) -> tuple[RegexDomain, ...]:
    """Validate a sequence and return variable-repeat domains at its tail.

    A nullable operation retains inherited domains because an earlier repeat
    can still border the next consuming token when that operation is skipped.
    Passing the domains into and back out of subpatterns makes capturing groups
    safety-transparent, matching the parser's treatment of noncapturing groups.
    """
    return _LinearRegexSequence(items, counters, inherited_variables).validate()


class _LinearRegexSequence:
    def __init__(
        self,
        items: Any,
        counters: dict[str, int],
        inherited_variables: tuple[RegexDomain, ...],
    ) -> None:
        self.items = items
        self.counters = counters
        self.previous_variables = list(inherited_variables)
        self.previous_unbounded: tuple[int, RegexDomain] | None = None

    def validate(self) -> tuple[RegexDomain, ...]:
        for index, item in enumerate(self.items):
            self._validate_item(index, item)
        return tuple(self.previous_variables)

    def _validate_item(self, index: int, item: tuple[Any, Any]) -> None:
        operation, argument = item
        if operation in REGEX_CONSUMING_ATOMS:
            self._consume_atom(operation, argument)
            return
        if operation is _re_parser.AT:
            return
        if operation is _re_parser.SUBPATTERN:
            self._enter_subpattern(argument)
            return
        if operation is _re_parser.BRANCH:
            self._enter_branch(argument)
            return
        if operation in REGEX_REPEAT_OPS:
            self._enter_repeat(index, argument)
            return
        raise UnsafeRegexError(f"unsupported regex operation {operation!s}")

    def _consume_atom(self, operation: Any, argument: Any) -> None:
        current_domain = regex_atom_domain((operation, argument))
        if overlaps_any_domain(current_domain, self.previous_variables):
            raise UnsafeRegexError("a variable repeat overlaps its following token")
        self.previous_variables = []

    def _enter_subpattern(self, argument: Any) -> None:
        _group, add_flags, del_flags, body = argument
        if add_flags:
            raise UnsafeRegexError("inline flags are not supported")
        if del_flags:
            raise UnsafeRegexError("inline flags are not supported")
        inherited = tuple(self.previous_variables)
        self.previous_variables = list(
            validate_linear_regex_sequence(body, self.counters, inherited)
        )

    def _enter_branch(self, argument: Any) -> None:
        _none, branches = argument
        if self.previous_variables:
            raise UnsafeRegexError(
                "a variable repeat may not be followed by alternation"
            )
        self.counters["branches"] += len(branches)
        if self.counters["branches"] > _MAX_SAFE_REGEX_BRANCHES:
            raise UnsafeRegexError("too many alternation branches")
        self.previous_variables = _branch_tail_variables(branches, self.counters)

    def _enter_repeat(self, index: int, argument: Any) -> None:
        self.counters["repeats"] += 1
        if self.counters["repeats"] > _MAX_SAFE_REGEX_REPEATS:
            raise UnsafeRegexError("too many repeat operations")
        minimum, maximum, body = argument
        _reject_oversized_repeat(maximum)
        body_tails = validate_linear_regex_sequence(body, self.counters)
        _reject_non_atom_repeat(maximum, body)
        leading_domain = regex_leading_domain(body)
        _reject_adjacent_repeat_overlap(
            self.previous_variables, leading_domain, minimum, maximum
        )
        spec = (minimum, maximum, body, leading_domain)
        self.previous_variables = _next_repeat_variables(
            self.previous_variables, body_tails, spec
        )
        self.previous_unbounded = _next_unbounded(
            self.previous_unbounded, (maximum, leading_domain, self.items, index)
        )


def _reject_oversized_repeat(maximum: Any) -> None:
    if maximum is _re_parser.MAXREPEAT:
        return
    if maximum > _MAX_SAFE_BOUNDED_REPEAT:
        raise UnsafeRegexError(
            f"repeat upper bound exceeds {_MAX_SAFE_BOUNDED_REPEAT}"
        )


def _reject_non_atom_repeat(maximum: Any, body: Any) -> None:
    if maximum <= 1:
        return
    if len(body) != 1:
        raise UnsafeRegexError(
            "a repeat above one may cover only one consuming atom"
        )
    if body[0][0] not in REGEX_CONSUMING_ATOMS:
        raise UnsafeRegexError(
            "a repeat above one may cover only one consuming atom"
        )


def _reject_adjacent_repeat_overlap(
    previous_variables: list[RegexDomain],
    leading_domain: RegexDomain,
    minimum: int,
    maximum: Any,
) -> None:
    if not maximum:
        return
    if not overlaps_any_domain(leading_domain, previous_variables):
        return
    if minimum != maximum:
        raise UnsafeRegexError(
            "adjacent variable repeats have overlapping character domains"
        )
    raise UnsafeRegexError("a variable repeat overlaps its following fixed repeat")


def _next_repeat_variables(
    previous_variables: list[RegexDomain],
    body_tails: tuple[RegexDomain, ...],
    spec: tuple[int, Any, Any, RegexDomain],
) -> list[RegexDomain]:
    minimum, maximum, body, leading_domain = spec
    next_variables: list[RegexDomain] = []
    if _repeat_is_nullable(minimum, body):
        next_variables = list(previous_variables)
    for domain in body_tails:
        append_regex_domain(next_variables, domain)
    _append_variable_leading(next_variables, (minimum, maximum, leading_domain))
    return next_variables


def _repeat_is_nullable(minimum: int, body: Any) -> bool:
    if minimum == 0:
        return True
    return regex_sequence_is_nullable(body)


def _append_variable_leading(
    next_variables: list[RegexDomain], spec: tuple[int, Any, RegexDomain]
) -> None:
    minimum, maximum, leading_domain = spec
    if minimum == maximum:
        return
    if not maximum:
        return
    append_regex_domain(next_variables, leading_domain)


def _next_unbounded(
    previous_unbounded: tuple[int, RegexDomain] | None,
    spec: tuple[Any, RegexDomain, Any, int],
) -> tuple[int, RegexDomain] | None:
    maximum, leading_domain, items, index = spec
    if maximum is not _re_parser.MAXREPEAT:
        return previous_unbounded
    _reject_unbounded_without_boundary(previous_unbounded, (items, index))
    return index, leading_domain


def _reject_unbounded_without_boundary(
    previous: tuple[int, RegexDomain] | None,
    span: tuple[Any, int],
) -> None:
    if previous is None:
        return
    items, index = span
    previous_index, repeated_domain = previous
    between = items[previous_index + 1 : index]
    if has_safe_repeat_boundary(repeated_domain, between):
        return
    raise UnsafeRegexError("unbounded repeats lack a deterministic boundary")


def _branch_tail_variables(branches: Any, counters: dict[str, int]) -> list[RegexDomain]:
    branch_domains: list[RegexDomain] = []
    tails: list[RegexDomain] = []
    for branch in branches:
        _require_disjoint_leading(branch, branch_domains)
        _collect_branch_tails(tails, branch, counters)
    return tails


def _require_disjoint_leading(branch: Any, branch_domains: list[RegexDomain]) -> None:
    domain = regex_leading_domain(branch)
    if domain is None:
        raise UnsafeRegexError("alternation branches need disjoint leading domains")
    if overlaps_any_domain(domain, branch_domains):
        raise UnsafeRegexError("alternation branches need disjoint leading domains")
    branch_domains.append(domain)


def _collect_branch_tails(
    tails: list[RegexDomain], branch: Any, counters: dict[str, int]
) -> None:
    for tail_domain in validate_linear_regex_sequence(branch, counters):
        append_regex_domain(tails, tail_domain)


def compile_taxonomy_regex(pattern: str, label: str, source: str) -> re.Pattern[str]:
    """Validate and compile one taxonomy regex with bounded failure behavior."""
    _reject_long_pattern(pattern, label, source)
    parsed = _parse_taxonomy_pattern(pattern, label, source)
    _validate_parsed_pattern(parsed, label, source)
    return _compile_parsed_pattern(pattern, label, source)


def _reject_long_pattern(pattern: str, label: str, source: str) -> None:
    if len(pattern) <= _MAX_SAFE_REGEX_LENGTH:
        return
    raise TagTaxonomyError(
        f"{source}: {label} is outside the supported linear-time regex "
        f"subset: pattern exceeds {_MAX_SAFE_REGEX_LENGTH} characters"
    )


def _parse_taxonomy_pattern(pattern: str, label: str, source: str) -> Any:
    try:
        return _re_parser.parse(pattern, 0)
    except re.error as exc:
        raise TagTaxonomyError(
            f"{source}: {label} is not a valid regex: {exc}"
        ) from exc
    except _REGEX_RESOURCE_ERRORS as exc:
        raise TagTaxonomyError(
            f"{source}: {label} is not a valid regex: parser resource limit exceeded"
        ) from exc


def _validate_parsed_pattern(parsed: Any, label: str, source: str) -> None:
    try:
        _assert_linear_parsed(parsed)
    except UnsafeRegexError as exc:
        raise TagTaxonomyError(
            f"{source}: {label} is outside the supported linear-time regex subset: {exc}"
        ) from exc
    except _REGEX_RESOURCE_ERRORS as exc:
        raise TagTaxonomyError(
            f"{source}: {label} is not a valid regex: validator resource limit exceeded"
        ) from exc


def _assert_linear_parsed(parsed: Any) -> None:
    if parsed.state.flags != re.UNICODE:
        raise UnsafeRegexError("inline flags are not supported")
    validate_linear_regex_sequence(parsed, {"repeats": 0, "branches": 0})


def _compile_parsed_pattern(pattern: str, label: str, source: str) -> re.Pattern[str]:
    try:
        return re.compile(pattern)
    except re.error as exc:
        raise TagTaxonomyError(
            f"{source}: {label} is not a valid regex: {exc}"
        ) from exc
    except _REGEX_RESOURCE_ERRORS as exc:
        raise TagTaxonomyError(
            f"{source}: {label} is not a valid regex: compiler resource limit exceeded"
        ) from exc
