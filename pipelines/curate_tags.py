#!/usr/bin/env python3
"""Map free-form corpus tags onto the controlled taxonomy in tag-taxonomy-v1.

The 2026-08-17 raw corpus carries a free-form tag surface of roughly 2790
distinct strings, most of them used exactly once.  This transform replaces that
surface with the compact versioned vocabulary declared in
``schemas/tag-taxonomy-v1.json``.

The mapping is deterministic and conservative:

* a source tag becomes canonical only through an alias or an anchored pattern
  rule declared in the taxonomy file;
* alias and pattern lookup run on a purely lexical normal form, so case and
  separator variants fold together without inventing meaning;
* every canonical tag maps to itself, which makes the transform idempotent;
* a source tag with no declared mapping is never guessed at.  It is dropped
  from the curated tag list, reported explicitly, and preserved verbatim in the
  record's ``tag_provenance`` so the original vocabulary stays recoverable.

``curate_jsonl`` returns curated records, a reversible manifest, an explicit
unmapped-tag report, and vocabulary-entropy summary counts.  The optional CLI
writes only to new, non-raw files.
"""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import math
import os
import re
from collections import Counter
from pathlib import Path
from re import _parser as _re_parser
from typing import Any


TRANSFORM_NAME = "tag_taxonomy"
TRANSFORM_VERSION = "1"

TAGS_KEY = "tags"
TAG_PROVENANCE_FIELD = "tag_provenance"
UNMAPPED_MARKER_TAG = "curation:unmapped_source_tags"

DEFAULT_TAXONOMY_PATH = (
    Path(__file__).resolve().parents[1] / "schemas" / "tag-taxonomy-v1.json"
)

RULE_CANONICAL = "canonical"
RULE_ALIAS = "alias"
RULE_PATTERN_PREFIX = "pattern:"
RULE_TRANSFORM = "transform"

REASON_TAG_CANONICAL = "tag_already_canonical"
REASON_TAG_ALIAS = "tag_mapped_alias"
REASON_TAG_PATTERN = "tag_mapped_pattern"
REASON_TAG_MAPPING_AMBIGUOUS = "tag_mapping_ambiguous"
REASON_TAG_UNMAPPED = "tag_unmapped"
REASON_TAG_NOT_STRING = "tag_not_a_string"
REASON_TAG_EMPTY = "tag_empty_after_normalization"

REASON_TAGS_MAPPED = "tags_mapped"
REASON_TAGS_UNMAPPED = "tags_unmapped_present"
REASON_TAGS_DEDUPLICATED = "tags_deduplicated"
REASON_TAGS_PROVENANCE_REUSED = "tags_provenance_reused"

REASON_RECORD_NOT_OBJECT = "tag_record_not_object"
REASON_TAGS_NOT_LIST = "tag_container_not_list"
REASON_PROVENANCE_CONFLICT = "tag_provenance_conflict"
REASON_INVALID_JSON = "tag_invalid_json"
REASON_INVALID_UTF8 = "tag_invalid_utf8"
REASON_RECORD_TOO_DEEP = "tag_record_too_deep"

_NON_ALNUM_RE = re.compile(r"[^a-z0-9]+")

# Taxonomy regexes run against source-controlled data, so merely compiling is
# not enough: Python's backtracking engine can take exponential time on valid
# patterns such as ``^(a+)+$``.  The accepted subset keeps the shipped grammar
# while excluding constructs that can repeatedly revisit variable-length
# subexpressions:
#
# * literals, character classes, ``.``, anchors, grouping, and deterministic
#   unquantified alternation are allowed;
# * lookarounds, backreferences, conditionals, and other zero-width control
#   constructs are rejected;
# * a repeat with an upper bound above one may cover only one consuming atom,
#   never a group, branch, or another repeat;
# * variable repeats that can become adjacent through nullable groups must
#   start with disjoint character domains, and multiple unbounded repeats in
#   one sequence need a mandatory boundary the earlier repeat cannot consume.
#
# The parser is private to ``re`` but stable across the supported CPython
# 3.12+ range.  Keeping validation on its parsed opcode tree avoids writing a
# second, subtly different regex parser.
_MAX_SAFE_REGEX_LENGTH = 8_192
_MAX_SAFE_REGEX_REPEATS = 64
_MAX_SAFE_REGEX_BRANCHES = 64
_MAX_SAFE_BOUNDED_REPEAT = 10_000
_REGEX_RESOURCE_ERRORS = (OverflowError, RecursionError, MemoryError)
_REGEX_REPEAT_OPS = frozenset(
    {
        _re_parser.MAX_REPEAT,
        _re_parser.MIN_REPEAT,
        _re_parser.POSSESSIVE_REPEAT,
    }
)
_REGEX_CONSUMING_ATOMS = frozenset(
    {
        _re_parser.LITERAL,
        _re_parser.NOT_LITERAL,
        _re_parser.ANY,
        _re_parser.IN,
        _re_parser.CATEGORY,
    }
)
_RegexDomain = tuple[bool, tuple[tuple[int, int], ...]] | None


class _UnsafeRegexError(ValueError):
    """Raised internally when a regex leaves the supported linear subset."""


def _merge_ranges(ranges: list[tuple[int, int]]) -> tuple[tuple[int, int], ...]:
    merged: list[list[int]] = []
    for lower, upper in sorted(ranges):
        if not merged or lower > merged[-1][1] + 1:
            merged.append([lower, upper])
        else:
            merged[-1][1] = max(merged[-1][1], upper)
    return tuple((lower, upper) for lower, upper in merged)


def _regex_atom_domain(
    item: tuple[Any, Any],
) -> _RegexDomain:
    """Return an exact finite/complement character domain when available."""
    operation, argument = item
    if operation is _re_parser.LITERAL:
        return False, ((argument, argument),)
    if operation is _re_parser.NOT_LITERAL:
        return True, ((argument, argument),)
    if operation in {_re_parser.ANY, _re_parser.CATEGORY}:
        return None
    if operation is not _re_parser.IN:
        return None

    negated = False
    ranges: list[tuple[int, int]] = []
    for class_operation, class_argument in argument:
        if class_operation is _re_parser.NEGATE:
            negated = True
        elif class_operation is _re_parser.LITERAL:
            ranges.append((class_argument, class_argument))
        elif class_operation is _re_parser.RANGE:
            ranges.append(class_argument)
        else:
            # Unicode categories and bitmap opcodes are safe as atoms, but
            # treating their domains as unknown keeps boundary proofs sound.
            return None
    return negated, _merge_ranges(ranges)


def _ranges_intersect(
    left: tuple[tuple[int, int], ...], right: tuple[tuple[int, int], ...]
) -> bool:
    left_index = 0
    right_index = 0
    while left_index < len(left) and right_index < len(right):
        left_lower, left_upper = left[left_index]
        right_lower, right_upper = right[right_index]
        if left_upper < right_lower:
            left_index += 1
        elif right_upper < left_lower:
            right_index += 1
        else:
            return True
    return False


def _ranges_are_subset(
    candidate: tuple[tuple[int, int], ...], container: tuple[tuple[int, int], ...]
) -> bool:
    container_index = 0
    for candidate_lower, candidate_upper in candidate:
        while (
            container_index < len(container)
            and container[container_index][1] < candidate_lower
        ):
            container_index += 1
        if container_index == len(container):
            return False
        container_lower, container_upper = container[container_index]
        if container_lower > candidate_lower or container_upper < candidate_upper:
            return False
    return True


def _regex_domains_are_disjoint(
    left: _RegexDomain,
    right: _RegexDomain,
) -> bool:
    if left is None or right is None:
        return False
    left_negated, left_ranges = left
    right_negated, right_ranges = right
    if not left_negated and not right_negated:
        return not _ranges_intersect(left_ranges, right_ranges)
    if left_negated and right_negated:
        return False
    if left_negated:
        return _ranges_are_subset(right_ranges, left_ranges)
    return _ranges_are_subset(left_ranges, right_ranges)


def _regex_leading_domain(
    items: Any,
) -> _RegexDomain:
    """Return a provable first-character domain for a repeated body."""
    for operation, argument in items:
        if operation is _re_parser.AT:
            continue
        if operation in _REGEX_CONSUMING_ATOMS:
            return _regex_atom_domain((operation, argument))
        if operation is _re_parser.SUBPATTERN:
            _group, add_flags, del_flags, body = argument
            if add_flags or del_flags:
                return None
            return _regex_leading_domain(body)
        if operation is _re_parser.BRANCH:
            return None
        if operation in _REGEX_REPEAT_OPS:
            minimum, _maximum, body = argument
            if minimum == 0:
                return None
            return _regex_leading_domain(body)
        return None
    return None


def _regex_sequence_is_nullable(items: Any) -> bool:
    """Whether a parsed sequence can consume no characters."""
    for operation, argument in items:
        if operation is _re_parser.AT:
            continue
        if operation in _REGEX_CONSUMING_ATOMS:
            return False
        if operation is _re_parser.SUBPATTERN:
            _group, add_flags, del_flags, body = argument
            if add_flags or del_flags or not _regex_sequence_is_nullable(body):
                return False
            continue
        if operation is _re_parser.BRANCH:
            _none, branches = argument
            if not any(_regex_sequence_is_nullable(branch) for branch in branches):
                return False
            continue
        if operation in _REGEX_REPEAT_OPS:
            minimum, _maximum, body = argument
            if minimum and not _regex_sequence_is_nullable(body):
                return False
            continue
        return False
    return True


def _append_regex_domain(domains: list[_RegexDomain], domain: _RegexDomain) -> None:
    if domain not in domains:
        domains.append(domain)


def _has_safe_repeat_boundary(
    repeated_domain: _RegexDomain,
    between: Any,
) -> bool:
    """Whether a mandatory atom fixes the end of an earlier unbounded repeat."""
    for operation, argument in between:
        if operation in _REGEX_CONSUMING_ATOMS and _regex_domains_are_disjoint(
            repeated_domain, _regex_atom_domain((operation, argument))
        ):
            return True
    return False


def _validate_linear_regex_sequence(
    items: Any,
    counters: dict[str, int],
    inherited_variables: tuple[_RegexDomain, ...] = (),
) -> tuple[_RegexDomain, ...]:
    """Validate a sequence and return variable-repeat domains at its tail.

    A nullable operation retains inherited domains because an earlier repeat
    can still border the next consuming token when that operation is skipped.
    Passing the domains into and back out of subpatterns makes capturing groups
    safety-transparent, matching the parser's treatment of noncapturing groups.
    """
    previous_variables = list(inherited_variables)
    previous_unbounded: tuple[int, _RegexDomain] | None = None

    for index, (operation, argument) in enumerate(items):
        if operation in _REGEX_CONSUMING_ATOMS:
            current_domain = _regex_atom_domain((operation, argument))
            if any(
                not _regex_domains_are_disjoint(previous_domain, current_domain)
                for previous_domain in previous_variables
            ):
                raise _UnsafeRegexError(
                    "a variable repeat overlaps its following token"
                )
            previous_variables = []
            continue
        if operation is _re_parser.AT:
            continue
        if operation is _re_parser.SUBPATTERN:
            _group, add_flags, del_flags, body = argument
            if add_flags or del_flags:
                raise _UnsafeRegexError("inline flags are not supported")
            previous_variables = list(
                _validate_linear_regex_sequence(
                    body,
                    counters,
                    tuple(previous_variables),
                )
            )
            continue
        if operation is _re_parser.BRANCH:
            _none, branches = argument
            if previous_variables:
                raise _UnsafeRegexError(
                    "a variable repeat may not be followed by alternation"
                )
            counters["branches"] += len(branches)
            if counters["branches"] > _MAX_SAFE_REGEX_BRANCHES:
                raise _UnsafeRegexError("too many alternation branches")
            branch_domains = []
            branch_tail_variables: list[_RegexDomain] = []
            for branch in branches:
                domain = _regex_leading_domain(branch)
                if domain is None or any(
                    not _regex_domains_are_disjoint(domain, prior)
                    for prior in branch_domains
                ):
                    raise _UnsafeRegexError(
                        "alternation branches need disjoint leading domains"
                    )
                branch_domains.append(domain)
                for tail_domain in _validate_linear_regex_sequence(branch, counters):
                    _append_regex_domain(branch_tail_variables, tail_domain)
            previous_variables = branch_tail_variables
            continue
        if operation not in _REGEX_REPEAT_OPS:
            raise _UnsafeRegexError(
                f"unsupported regex operation {operation!s}"
            )

        counters["repeats"] += 1
        if counters["repeats"] > _MAX_SAFE_REGEX_REPEATS:
            raise _UnsafeRegexError("too many repeat operations")
        minimum, maximum, body = argument
        if maximum is not _re_parser.MAXREPEAT and maximum > _MAX_SAFE_BOUNDED_REPEAT:
            raise _UnsafeRegexError(
                f"repeat upper bound exceeds {_MAX_SAFE_BOUNDED_REPEAT}"
            )

        body_tail_variables = _validate_linear_regex_sequence(body, counters)
        if maximum > 1 and (
            len(body) != 1 or body[0][0] not in _REGEX_CONSUMING_ATOMS
        ):
            raise _UnsafeRegexError(
                "a repeat above one may cover only one consuming atom"
            )

        variable = minimum != maximum
        leading_domain = _regex_leading_domain(body)
        if maximum and any(
            not _regex_domains_are_disjoint(previous_domain, leading_domain)
            for previous_domain in previous_variables
        ):
            if variable:
                raise _UnsafeRegexError(
                    "adjacent variable repeats have overlapping character domains"
                )
            raise _UnsafeRegexError(
                "a variable repeat overlaps its following fixed repeat"
            )

        repeat_is_nullable = minimum == 0 or _regex_sequence_is_nullable(body)
        next_variables = list(previous_variables) if repeat_is_nullable else []
        for tail_domain in body_tail_variables:
            _append_regex_domain(next_variables, tail_domain)
        if variable and maximum:
            _append_regex_domain(next_variables, leading_domain)
        previous_variables = next_variables

        if maximum is _re_parser.MAXREPEAT:
            if previous_unbounded is not None:
                previous_index, repeated_domain = previous_unbounded
                if not _has_safe_repeat_boundary(
                    repeated_domain, items[previous_index + 1 : index]
                ):
                    raise _UnsafeRegexError(
                        "unbounded repeats lack a deterministic boundary"
                    )
            previous_unbounded = (index, leading_domain)

    return tuple(previous_variables)


def _compile_taxonomy_regex(pattern: str, *, label: str, source: str) -> re.Pattern[str]:
    """Validate and compile one taxonomy regex with bounded failure behavior."""
    if len(pattern) > _MAX_SAFE_REGEX_LENGTH:
        raise TagTaxonomyError(
            f"{source}: {label} is outside the supported linear-time regex "
            f"subset: pattern exceeds {_MAX_SAFE_REGEX_LENGTH} characters"
        )
    try:
        parsed = _re_parser.parse(pattern, 0)
    except re.error as exc:
        raise TagTaxonomyError(f"{source}: {label} is not a valid regex: {exc}") from exc
    except _REGEX_RESOURCE_ERRORS as exc:
        raise TagTaxonomyError(
            f"{source}: {label} is not a valid regex: parser resource limit exceeded"
        ) from exc

    try:
        if parsed.state.flags != re.UNICODE:
            raise _UnsafeRegexError("inline flags are not supported")
        _validate_linear_regex_sequence(parsed, {"repeats": 0, "branches": 0})
    except _UnsafeRegexError as exc:
        raise TagTaxonomyError(
            f"{source}: {label} is outside the supported linear-time regex subset: {exc}"
        ) from exc
    except _REGEX_RESOURCE_ERRORS as exc:
        raise TagTaxonomyError(
            f"{source}: {label} is not a valid regex: validator resource limit exceeded"
        ) from exc

    try:
        return re.compile(pattern)
    except re.error as exc:
        raise TagTaxonomyError(f"{source}: {label} is not a valid regex: {exc}") from exc
    except _REGEX_RESOURCE_ERRORS as exc:
        raise TagTaxonomyError(
            f"{source}: {label} is not a valid regex: compiler resource limit exceeded"
        ) from exc


class TagTaxonomyError(ValueError):
    """Raised when a taxonomy document violates its own declared contract."""


def normalize_tag(tag: str) -> str:
    """Fold a source tag to its lexical normal form.

    The fold is lexical only: case and separator variants collapse, nothing
    else.  It never assigns meaning to a label.
    """
    return _NON_ALNUM_RE.sub("_", tag.strip().lower()).strip("_")


def canonical_json(value: Any) -> str:
    """Return the stable JSON representation used for output hashes."""
    return json.dumps(
        value,
        allow_nan=False,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    )


def _tag_identity(value: Any) -> tuple[str, str]:
    """Type-sensitive identity so 1, 1.0, True, and \"1\" stay distinct."""
    return (type(value).__name__, canonical_json(value))


def _count_tag(
    counts: Counter,
    tag: Any,
    originals: dict[tuple[str, str], Any] | None = None,
) -> None:
    ident = _tag_identity(tag)
    counts[ident] += 1
    if originals is not None:
        originals.setdefault(ident, tag)


def _canonical_json_equal(left: Any, right: Any) -> bool:
    """Compare JSON values without Python's bool/number coercion."""
    try:
        return canonical_json(left) == canonical_json(right)
    except (TypeError, ValueError):
        return False


def _reject_json_constant(value: str) -> None:
    """Reject Python-only numeric constants accepted by ``json.loads``."""
    raise ValueError(f"non-standard JSON numeric constant: {value}")


def hash_value(value: Any) -> str:
    """Hash a parsed value deterministically."""
    return hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest()


def vocabulary_entropy(counts: Counter | dict[str, int]) -> float:
    """Return the Shannon entropy, in bits, of a tag-use distribution."""
    total = sum(count for count in counts.values() if count > 0)
    if total <= 0:
        return 0.0
    entropy = 0.0
    for count in counts.values():
        if count <= 0:
            continue
        share = count / total
        entropy -= share * math.log2(share)
    return round(entropy, 6)


class Taxonomy:
    """A loaded, validated controlled tag vocabulary."""

    def __init__(self, document: dict[str, Any], *, source: str) -> None:
        self.source = source
        self.version = _require_str(document, "version", source)
        canonical_pattern = _require_str(document, "canonical_tag_pattern", source)
        self._canonical_re = _compile_taxonomy_regex(
            canonical_pattern,
            label="canonical_tag_pattern",
            source=source,
        )

        facets = document.get("facets")
        if not isinstance(facets, list) or not facets:
            raise TagTaxonomyError(f"{source}: facets must be a nonempty array")

        self.facet_of: dict[str, str] = {}
        self.definition_of: dict[str, str] = {}
        self.alias_index: dict[str, str] = {}
        alias_owner: dict[str, str] = {}

        for facet in facets:
            if not isinstance(facet, dict):
                raise TagTaxonomyError(f"{source}: every facet must be an object")
            facet_id = _require_str(facet, "id", source)
            terms = facet.get("terms")
            if not isinstance(terms, list) or not terms:
                raise TagTaxonomyError(
                    f"{source}: facet {facet_id} must declare a nonempty terms array"
                )
            for term in terms:
                if not isinstance(term, dict):
                    raise TagTaxonomyError(
                        f"{source}: every term in facet {facet_id} must be an object"
                    )
                tag = _require_str(term, "tag", source)
                if self._canonical_re.fullmatch(tag) is None:
                    raise TagTaxonomyError(
                        f"{source}: canonical tag {tag!r} does not match "
                        f"canonical_tag_pattern"
                    )
                if not tag.startswith(f"{facet_id}:"):
                    raise TagTaxonomyError(
                        f"{source}: canonical tag {tag!r} is not in facet {facet_id}"
                    )
                if tag in self.facet_of:
                    raise TagTaxonomyError(
                        f"{source}: canonical tag {tag!r} is declared twice"
                    )
                self.facet_of[tag] = facet_id
                self.definition_of[tag] = _require_str(term, "definition", source)

                aliases = term.get("aliases", [])
                if not isinstance(aliases, list):
                    raise TagTaxonomyError(
                        f"{source}: aliases for {tag!r} must be an array"
                    )
                for alias in [tag, *aliases]:
                    if not isinstance(alias, str) or not alias.strip():
                        raise TagTaxonomyError(
                            f"{source}: alias for {tag!r} must be a nonempty string"
                        )
                    _require_utf8(alias, f"alias for {tag!r}", source)
                    key = normalize_tag(alias)
                    if not key:
                        raise TagTaxonomyError(
                            f"{source}: alias {alias!r} for {tag!r} normalizes to nothing"
                        )
                    owner = alias_owner.get(key)
                    if owner is not None and owner != tag:
                        raise TagTaxonomyError(
                            f"{source}: alias {alias!r} maps to both {owner!r} and {tag!r}"
                        )
                    alias_owner[key] = tag
                    self.alias_index[key] = tag

        rules = document.get("pattern_rules", [])
        if not isinstance(rules, list):
            raise TagTaxonomyError(f"{source}: pattern_rules must be an array")
        self.pattern_rules: list[tuple[str, str, re.Pattern[str]]] = []
        seen_rule_ids: set[str] = set()
        for rule in rules:
            if not isinstance(rule, dict):
                raise TagTaxonomyError(f"{source}: every pattern rule must be an object")
            rule_id = _require_str(rule, "id", source)
            if rule_id in seen_rule_ids:
                raise TagTaxonomyError(
                    f"{source}: pattern rule id {rule_id!r} is declared twice"
                )
            seen_rule_ids.add(rule_id)
            tag = _require_str(rule, "tag", source)
            if tag not in self.facet_of:
                raise TagTaxonomyError(
                    f"{source}: pattern rule {rule_id!r} targets undeclared tag {tag!r}"
                )
            pattern = _require_str(rule, "pattern", source)
            if not pattern.startswith("^") or not pattern.endswith("$"):
                raise TagTaxonomyError(
                    f"{source}: pattern rule {rule_id!r} must be anchored with ^ and $"
                )
            compiled = _compile_taxonomy_regex(
                pattern,
                label=f"pattern rule {rule_id!r}",
                source=source,
            )
            self.pattern_rules.append((rule_id, tag, compiled))

        emitted = document.get("transform_emitted_tags", [])
        if not isinstance(emitted, list):
            raise TagTaxonomyError(
                f"{source}: transform_emitted_tags must be an array"
            )
        if not all(isinstance(tag, str) and tag for tag in emitted):
            raise TagTaxonomyError(
                f"{source}: transform_emitted_tags must contain nonempty strings"
            )
        for tag in emitted:
            _require_utf8(tag, "transform_emitted_tags entry", source)
        if len(emitted) != len(set(emitted)):
            raise TagTaxonomyError(
                f"{source}: transform_emitted_tags must not contain duplicates"
            )
        for tag in emitted:
            if tag not in self.facet_of:
                raise TagTaxonomyError(
                    f"{source}: transform_emitted_tags names undeclared tag {tag!r}"
                )
        self.transform_emitted_tags = tuple(emitted)
        for rule_id, tag, _compiled in self.pattern_rules:
            if tag in self.transform_emitted_tags:
                raise TagTaxonomyError(
                    f"{source}: pattern rule {rule_id!r} targets "
                    f"transform-emitted tag {tag!r}"
                )
        if UNMAPPED_MARKER_TAG not in self.facet_of:
            raise TagTaxonomyError(
                f"{source}: taxonomy must declare {UNMAPPED_MARKER_TAG!r}"
            )
        if UNMAPPED_MARKER_TAG not in self.transform_emitted_tags:
            raise TagTaxonomyError(
                f"{source}: transform_emitted_tags must include "
                f"{UNMAPPED_MARKER_TAG!r}"
            )

    @property
    def canonical_tags(self) -> frozenset[str]:
        """Every canonical tag the taxonomy declares."""
        return frozenset(self.facet_of)

    def is_canonical(self, tag: Any) -> bool:
        """Return whether a value is a declared canonical tag."""
        return isinstance(tag, str) and tag in self.facet_of

    def map_tag(self, tag: Any) -> dict[str, Any]:
        """Map one source tag and explain the decision."""
        if not isinstance(tag, str):
            return {
                "source": tag,
                "normalized": None,
                "canonical": None,
                "rule": None,
                "reason": REASON_TAG_NOT_STRING,
            }
        normalized = normalize_tag(tag)
        if not normalized:
            return {
                "source": tag,
                "normalized": normalized,
                "canonical": None,
                "rule": None,
                "reason": REASON_TAG_EMPTY,
            }
        canonical = self.alias_index.get(normalized)
        pattern_matches = [
            (rule_id, mapped)
            for rule_id, mapped, compiled in self.pattern_rules
            if compiled.fullmatch(normalized)
        ]
        candidate_targets = {mapped for _rule_id, mapped in pattern_matches}
        if canonical is not None:
            candidate_targets.add(canonical)
        if len(candidate_targets) > 1:
            return {
                "source": tag,
                "normalized": normalized,
                "canonical": None,
                "rule": None,
                "reason": REASON_TAG_MAPPING_AMBIGUOUS,
            }
        if canonical in self.transform_emitted_tags:
            canonical = None
        pattern_matches = [
            (rule_id, mapped)
            for rule_id, mapped in pattern_matches
            if mapped not in self.transform_emitted_tags
        ]
        if canonical is not None:
            reason = (
                REASON_TAG_CANONICAL if tag == canonical else REASON_TAG_ALIAS
            )
            rule = RULE_CANONICAL if tag == canonical else RULE_ALIAS
            return {
                "source": tag,
                "normalized": normalized,
                "canonical": canonical,
                "rule": rule,
                "reason": reason,
            }
        if pattern_matches:
            rule_id, mapped = min(pattern_matches)
            return {
                "source": tag,
                "normalized": normalized,
                "canonical": mapped,
                "rule": f"{RULE_PATTERN_PREFIX}{rule_id}",
                "reason": REASON_TAG_PATTERN,
            }
        return {
            "source": tag,
            "normalized": normalized,
            "canonical": None,
            "rule": None,
            "reason": REASON_TAG_UNMAPPED,
        }


def _require_str(container: dict[str, Any], key: str, source: str) -> str:
    value = container.get(key)
    if not isinstance(value, str) or not value.strip():
        raise TagTaxonomyError(f"{source}: {key} must be a nonempty string")
    return _require_utf8(value, key, source)


def _require_utf8(value: str, label: str, source: str) -> str:
    try:
        value.encode("utf-8")
    except UnicodeEncodeError as exc:
        raise TagTaxonomyError(f"{source}: {label} must be valid UTF-8") from exc
    return value


def load_taxonomy(path: str | Path | None = None) -> Taxonomy:
    """Load and validate a taxonomy document."""
    resolved = Path(path) if path is not None else DEFAULT_TAXONOMY_PATH
    try:
        document = json.loads(
            resolved.read_text(encoding="utf-8"),
            parse_constant=_reject_json_constant,
        )
    except RecursionError as exc:
        raise TagTaxonomyError(
            f"{resolved}: taxonomy JSON is nested too deeply"
        ) from exc
    except ValueError as exc:
        raise TagTaxonomyError(f"{resolved}: invalid JSON: {exc}") from exc
    if not isinstance(document, dict):
        raise TagTaxonomyError(f"{resolved}: taxonomy document must be an object")
    return Taxonomy(document, source=str(resolved))


def _pointer(tokens: list[str]) -> str:
    escaped = [token.replace("~", "~0").replace("/", "~1") for token in tokens]
    return "/" + "/".join(escaped)


def _collect_tag_containers(
    node: Any, tokens: list[str], found: list[tuple[list[str], Any, Any]]
) -> None:
    if isinstance(node, dict):
        for key, value in node.items():
            if not tokens and key == TAG_PROVENANCE_FIELD:
                continue
            if key == TAGS_KEY:
                found.append((tokens + [key], node, key))
                continue
            _collect_tag_containers(value, tokens + [key], found)
    elif isinstance(node, list):
        for index, item in enumerate(node):
            _collect_tag_containers(item, tokens + [str(index)], found)


def map_tags(tags: list[Any], taxonomy: Taxonomy) -> dict[str, Any]:
    """Map one tag list and return its reversible provenance entry."""
    mappings = [taxonomy.map_tag(tag) for tag in tags]
    canonical: list[str] = []
    seen: set[str] = set()
    duplicates = 0
    for mapping in mappings:
        tag = mapping["canonical"]
        if tag is None:
            continue
        if tag in seen:
            duplicates += 1
            continue
        seen.add(tag)
        canonical.append(tag)

    unmapped = [
        mapping["source"] for mapping in mappings if mapping["canonical"] is None
    ]
    if unmapped and UNMAPPED_MARKER_TAG not in seen:
        seen.add(UNMAPPED_MARKER_TAG)
        canonical.append(UNMAPPED_MARKER_TAG)
        mappings.append(
            {
                "source": None,
                "normalized": None,
                "canonical": UNMAPPED_MARKER_TAG,
                "rule": RULE_TRANSFORM,
                "reason": REASON_TAGS_UNMAPPED,
            }
        )

    return {
        "source_tags": copy.deepcopy(tags),
        "canonical_tags": sorted(canonical),
        "mappings": mappings,
        "unmapped_tags": unmapped,
        "duplicates_collapsed": duplicates,
    }


def _existing_provenance(
    record: dict[str, Any], taxonomy: Taxonomy
) -> tuple[dict[str, dict[str, Any]], bool, bool]:
    """Return reusable provenance entries by pointer, a conflict flag, and presence.

    A record that already carries this transform's provenance is only reusable
    when the stored entries still describe the record exactly.  Recomputing over
    already-curated tags would make the curated vocabulary look like the source
    vocabulary, so a stale or malformed sidecar is a conflict, not an invitation
    to guess.
    """
    if TAG_PROVENANCE_FIELD not in record:
        return {}, False, False
    stored = record[TAG_PROVENANCE_FIELD]
    if not isinstance(stored, dict):
        return {}, True, True
    if (
        stored.get("transform") != TRANSFORM_NAME
        or stored.get("transform_version") != TRANSFORM_VERSION
    ):
        return {}, True, True
    if stored.get("taxonomy_version") != taxonomy.version:
        return {}, True, True
    containers = stored.get("containers")
    if not isinstance(containers, list):
        return {}, True, True
    reusable: dict[str, dict[str, Any]] = {}
    for entry in containers:
        if not isinstance(entry, dict):
            return {}, True, True
        pointer = entry.get("json_pointer")
        if not isinstance(pointer, str) or pointer in reusable:
            return {}, True, True
        for key in ("source_tags", "canonical_tags", "mappings", "unmapped_tags"):
            if not isinstance(entry.get(key), list):
                return {}, True, True
        expected = map_tags(entry["source_tags"], taxonomy)
        for key in (
            "canonical_tags",
            "mappings",
            "unmapped_tags",
            "duplicates_collapsed",
        ):
            if not _canonical_json_equal(entry.get(key), expected[key]):
                return {}, True, True
        reusable[pointer] = entry
    return reusable, False, True


def _base_manifest(
    *,
    source_path: str,
    source_line: int,
    source_hash: str,
    taxonomy_version: str,
) -> dict[str, Any]:
    return {
        "source_path": source_path,
        "source_line": source_line,
        "source_hash": source_hash,
        "transform": TRANSFORM_NAME,
        "transform_version": TRANSFORM_VERSION,
        "taxonomy_version": taxonomy_version,
        "action": "excluded",
        "reason_codes": [],
        "output_id": None,
        "output_hash": None,
        "tag_counts": {
            "containers": 0,
            "source_uses": 0,
            "source_unique": 0,
            "canonical_uses": 0,
            "canonical_unique": 0,
            "mapped_uses": 0,
            "unmapped_uses": 0,
        },
        "unmapped_tags": [],
        "containers": [],
    }


def _record_id(record: Any) -> str | None:
    if not isinstance(record, dict):
        return None
    value = record.get("id")
    if isinstance(value, str) and value.strip():
        return value.strip()
    meta = record.get("meta")
    if isinstance(meta, dict):
        value = meta.get("id")
        if isinstance(value, str) and value.strip():
            return value.strip()
    return None


def curate_record(
    record: Any,
    *,
    taxonomy: Taxonomy | None = None,
    source_path: str = "<memory>",
    source_line: int = 1,
    source_hash: str | None = None,
) -> tuple[dict[str, Any] | None, dict[str, Any]]:
    """Curate one record's tags and emit a deterministic manifest entry."""
    vocabulary = taxonomy if taxonomy is not None else load_taxonomy()
    digest = source_hash or hash_value(record)
    manifest = _base_manifest(
        source_path=source_path,
        source_line=source_line,
        source_hash=digest,
        taxonomy_version=vocabulary.version,
    )
    if not isinstance(record, dict):
        manifest["reason_codes"] = [REASON_RECORD_NOT_OBJECT]
        return None, manifest

    reusable, conflict, has_provenance = _existing_provenance(record, vocabulary)
    if conflict:
        manifest["reason_codes"] = [REASON_PROVENANCE_CONFLICT]
        return None, manifest

    curated = copy.deepcopy(record)
    found: list[tuple[list[str], Any, Any]] = []
    _collect_tag_containers(curated, [], found)
    found.sort(key=lambda item: _pointer(item[0]))

    if has_provenance and set(reusable) != {_pointer(tokens) for tokens, _, _ in found}:
        manifest["reason_codes"] = [REASON_PROVENANCE_CONFLICT]
        return None, manifest

    entries: list[dict[str, Any]] = []
    container_manifests: list[dict[str, Any]] = []
    source_uses = Counter()
    source_total = 0
    canonical_uses = Counter()
    unmapped_uses = Counter()
    unmapped_originals: dict[tuple[str, str], Any] = {}
    unmapped_total = 0
    mapped_total = 0
    duplicates_total = 0
    reused_any = False

    for tokens, parent, key in found:
        pointer = _pointer(tokens)
        tags = parent[key]
        if not isinstance(tags, list):
            manifest["reason_codes"] = [REASON_TAGS_NOT_LIST]
            return None, manifest

        prior = reusable.get(pointer)
        if prior is not None:
            if not _canonical_json_equal(prior["canonical_tags"], tags):
                # The stored sidecar no longer describes this container, so the
                # original tags are not recoverable from the record.
                manifest["reason_codes"] = [REASON_PROVENANCE_CONFLICT]
                return None, manifest
            entry = copy.deepcopy(prior)
            reused_any = True
        else:
            entry = map_tags(tags, vocabulary)

        entry["json_pointer"] = pointer
        parent[key] = list(entry["canonical_tags"])
        entries.append(entry)

        source_total += len(entry["source_tags"])
        for tag in entry["source_tags"]:
            _count_tag(source_uses, tag)
        for tag in entry["canonical_tags"]:
            canonical_uses[tag] += 1
        for tag in entry["unmapped_tags"]:
            unmapped_total += 1
            _count_tag(unmapped_uses, tag, unmapped_originals)
        mapped_total += sum(
            1
            for mapping in entry["mappings"]
            if mapping.get("canonical") is not None
            and mapping.get("rule") != RULE_TRANSFORM
        )
        duplicates_total += int(entry.get("duplicates_collapsed") or 0)

        container_manifests.append(
            {
                "json_pointer": pointer,
                "source_tag_count": len(entry["source_tags"]),
                "canonical_tag_count": len(entry["canonical_tags"]),
                "unmapped_tag_count": len(entry["unmapped_tags"]),
                "unmapped_tags": list(entry["unmapped_tags"]),
            }
        )

    if entries:
        curated[TAG_PROVENANCE_FIELD] = {
            "taxonomy_version": vocabulary.version,
            "transform": TRANSFORM_NAME,
            "transform_version": TRANSFORM_VERSION,
            "containers": entries,
        }
    elif TAG_PROVENANCE_FIELD in curated:
        del curated[TAG_PROVENANCE_FIELD]

    reasons: list[str] = []
    if mapped_total:
        reasons.append(REASON_TAGS_MAPPED)
    if unmapped_total:
        reasons.append(REASON_TAGS_UNMAPPED)
    if duplicates_total:
        reasons.append(REASON_TAGS_DEDUPLICATED)
    if reused_any:
        reasons.append(REASON_TAGS_PROVENANCE_REUSED)

    manifest["tag_counts"] = {
        "containers": len(entries),
        "source_uses": source_total,
        "source_unique": len(source_uses),
        "canonical_uses": sum(canonical_uses.values()),
        "canonical_unique": len(canonical_uses),
        "mapped_uses": mapped_total,
        "unmapped_uses": unmapped_total,
    }
    manifest["unmapped_tags"] = sorted(
        (unmapped_originals[ident] for ident in unmapped_uses),
        key=lambda item: (0, item) if isinstance(item, str) else (1, canonical_json(item)),
    )
    manifest["containers"] = container_manifests
    manifest["reason_codes"] = reasons
    manifest["action"] = "modified" if curated != record else "unchanged"
    manifest["output_id"] = _record_id(curated)
    manifest["output_hash"] = hash_value(curated)

    leftover = [
        tag
        for entry in entries
        for tag in entry["canonical_tags"]
        if not vocabulary.is_canonical(tag)
    ]
    if leftover:
        raise AssertionError(f"tag curation emitted noncanonical tags: {leftover!r}")
    return curated, manifest


def _excluded_line_manifest(
    *,
    source_path: str,
    source_line: int,
    source_hash: str,
    taxonomy_version: str,
    reason: str,
) -> dict[str, Any]:
    manifest = _base_manifest(
        source_path=source_path,
        source_line=source_line,
        source_hash=source_hash,
        taxonomy_version=taxonomy_version,
    )
    manifest["reason_codes"] = [reason]
    return manifest


def curate_jsonl(
    source_path: str | Path, taxonomy: Taxonomy | None = None
) -> dict[str, Any]:
    """Read a JSONL source without mutation and curate every nonblank line."""
    vocabulary = taxonomy if taxonomy is not None else load_taxonomy()
    source = Path(source_path)
    display_path = str(source).encode("utf-8", "replace").decode("utf-8")
    records: list[dict[str, Any]] = []
    manifests: list[dict[str, Any]] = []
    source_uses = Counter()
    source_total = 0
    canonical_uses = Counter()
    unmapped_uses = Counter()
    unmapped_originals: dict[tuple[str, str], Any] = {}
    rule_uses = Counter()
    nonstring_uses = 0

    with source.open("rb") as handle:
        for line_number, terminated_line in enumerate(handle, 1):
            raw_line = terminated_line.rstrip(b"\r\n")
            if not raw_line.strip():
                continue
            line_hash = hashlib.sha256(raw_line).hexdigest()
            try:
                text = raw_line.decode("utf-8")
            except UnicodeDecodeError:
                manifests.append(
                    _excluded_line_manifest(
                        source_path=display_path,
                        source_line=line_number,
                        source_hash=line_hash,
                        taxonomy_version=vocabulary.version,
                        reason=REASON_INVALID_UTF8,
                    )
                )
                continue
            try:
                record = json.loads(text, parse_constant=_reject_json_constant)
            except RecursionError:
                manifests.append(
                    _excluded_line_manifest(
                        source_path=display_path,
                        source_line=line_number,
                        source_hash=line_hash,
                        taxonomy_version=vocabulary.version,
                        reason=REASON_RECORD_TOO_DEEP,
                    )
                )
                continue
            except ValueError:
                manifests.append(
                    _excluded_line_manifest(
                        source_path=display_path,
                        source_line=line_number,
                        source_hash=line_hash,
                        taxonomy_version=vocabulary.version,
                        reason=REASON_INVALID_JSON,
                    )
                )
                continue
            try:
                canonical_json(record).encode("utf-8")
            except RecursionError:
                manifests.append(
                    _excluded_line_manifest(
                        source_path=display_path,
                        source_line=line_number,
                        source_hash=line_hash,
                        taxonomy_version=vocabulary.version,
                        reason=REASON_RECORD_TOO_DEEP,
                    )
                )
                continue
            except (TypeError, ValueError, UnicodeEncodeError):
                manifests.append(
                    _excluded_line_manifest(
                        source_path=display_path,
                        source_line=line_number,
                        source_hash=line_hash,
                        taxonomy_version=vocabulary.version,
                        reason=REASON_INVALID_JSON,
                    )
                )
                continue

            try:
                curated, manifest = curate_record(
                    record,
                    taxonomy=vocabulary,
                    source_path=display_path,
                    source_line=line_number,
                    source_hash=line_hash,
                )
            except RecursionError:
                manifests.append(
                    _excluded_line_manifest(
                        source_path=display_path,
                        source_line=line_number,
                        source_hash=line_hash,
                        taxonomy_version=vocabulary.version,
                        reason=REASON_RECORD_TOO_DEEP,
                    )
                )
                continue
            manifests.append(manifest)
            if curated is None:
                continue
            records.append(curated)
            provenance = curated.get(TAG_PROVENANCE_FIELD)
            containers = provenance.get("containers", []) if provenance else []
            for entry in containers:
                source_total += len(entry["source_tags"])
                for tag in entry["source_tags"]:
                    _count_tag(source_uses, tag)
                for tag in entry["canonical_tags"]:
                    canonical_uses[tag] += 1
                for tag in entry["unmapped_tags"]:
                    if not isinstance(tag, str):
                        nonstring_uses += 1
                    _count_tag(unmapped_uses, tag, unmapped_originals)
                for mapping in entry["mappings"]:
                    rule = mapping.get("rule")
                    if rule:
                        rule_uses[rule] += 1

    source_entropy = vocabulary_entropy(source_uses)
    canonical_entropy = vocabulary_entropy(canonical_uses)
    unmapped_report = [
        {"tag": unmapped_originals[ident], "count": count}
        for ident, count in sorted(
            unmapped_uses.items(),
            key=lambda kv: (
                -kv[1],
                (0, unmapped_originals[kv[0]])
                if isinstance(unmapped_originals[kv[0]], str)
                else (1, kv[0][1]),
            ),
        )
    ]
    summary = {
        "source_path": display_path,
        "taxonomy_version": vocabulary.version,
        "taxonomy_size": len(vocabulary.canonical_tags),
        "input_records": len(manifests),
        "output_records": len(records),
        "excluded_records": sum(item["action"] == "excluded" for item in manifests),
        "tag_containers": sum(
            item["tag_counts"]["containers"] for item in manifests
        ),
        "source_tag_uses": source_total,
        "source_unique_tags": len(source_uses),
        "canonical_tag_uses": sum(canonical_uses.values()),
        "canonical_unique_tags": len(canonical_uses),
        "mapped_tag_uses": sum(
            count for rule, count in rule_uses.items() if rule != RULE_TRANSFORM
        ),
        "unmapped_tag_uses": sum(unmapped_uses.values()),
        "unmapped_unique_tags": len(unmapped_uses),
        "nonstring_tag_uses": nonstring_uses,
        "entropy_bits": {
            "source": source_entropy,
            "canonical": canonical_entropy,
            "reduction": round(source_entropy - canonical_entropy, 6),
        },
        "rule_uses": dict(sorted(rule_uses.items())),
        "canonical_tag_counts": dict(sorted(canonical_uses.items())),
        "unmapped_tags": unmapped_report,
    }
    return {
        "records": records,
        "manifest": manifests,
        "unmapped": unmapped_report,
        "summary": summary,
    }


def _has_raw_tree_components(path: Path) -> bool:
    """Whether normalized ``path`` names an ``outputs/raw`` tree."""
    parts = path.parts
    return any(
        parts[index : index + 2] == ("outputs", "raw")
        for index in range(len(parts) - 1)
    )


def _is_under_raw(path: Path) -> bool:
    """Whether ``path`` lexically names or resolves inside ``outputs/raw``."""
    lexical_path = Path(os.path.abspath(path))
    return _has_raw_tree_components(lexical_path) or _has_raw_tree_components(
        path.resolve(strict=False)
    )


def _unlink_created_file(path: Path, identity: tuple[int, int]) -> None:
    """Remove ``path`` only when it still names the file this run created."""
    try:
        current = path.lstat()
    except FileNotFoundError:
        return
    if (current.st_dev, current.st_ino) == identity:
        path.unlink()


def _write_new_jsonl(
    path: Path, values: list[dict[str, Any]]
) -> tuple[int, int]:
    """Write one JSONL file without replacing any pre-existing path."""
    if _is_under_raw(path):
        raise ValueError(f"refusing to write inside immutable raw evidence: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    # O_EXCL is the atomic no-clobber gate; preflight is only an early diagnostic.
    try:
        descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o644)
    except FileExistsError as exc:
        raise FileExistsError(
            f"refusing to replace existing destination: {path}"
        ) from exc
    state = os.fstat(descriptor)
    identity = (state.st_dev, state.st_ino)
    if _is_under_raw(path) or _is_under_raw(path.resolve(strict=False)):
        os.close(descriptor)
        _unlink_created_file(path, identity)
        raise ValueError(f"refusing to write inside immutable raw evidence: {path}")
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            for value in values:
                handle.write(canonical_json(value))
                handle.write("\n")
    except BaseException:
        _unlink_created_file(path, identity)
        raise
    return identity


def _preflight_destinations(paths: list[Path]) -> None:
    resolved = [path.resolve(strict=False) for path in paths]
    if len(set(resolved)) != len(resolved):
        raise ValueError("output destinations must be distinct")
    for index, path in enumerate(resolved):
        for other in resolved[index + 1 :]:
            if path in other.parents or other in path.parents:
                raise ValueError("output destinations must not contain one another")
    for path in paths:
        if _is_under_raw(path):
            raise ValueError(f"refusing to write inside immutable raw evidence: {path}")
        if path.exists():
            raise FileExistsError(f"refusing to replace existing destination: {path}")


def _write_destinations(
    destinations: list[tuple[Path, list[dict[str, Any]]]],
) -> None:
    """Publish a destination set, rolling back this run's files on failure."""
    for path, _values in destinations:
        path.parent.mkdir(parents=True, exist_ok=True)

    created: list[tuple[Path, tuple[int, int]]] = []
    try:
        for path, values in destinations:
            identity = _write_new_jsonl(path, values)
            created.append((path, identity))
    except BaseException:
        for path, identity in reversed(created):
            _unlink_created_file(path, identity)
        raise


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path, help="JSONL corpus to inspect")
    parser.add_argument("--taxonomy", type=Path, default=None)
    parser.add_argument("--output-jsonl", type=Path)
    parser.add_argument("--manifest-jsonl", type=Path)
    parser.add_argument("--unmapped-jsonl", type=Path)
    args = parser.parse_args(argv)

    if (
        args.output_jsonl is not None
        and args.output_jsonl.resolve(strict=False) == args.source.resolve()
    ):
        parser.error("output must not replace the source")
    destinations = [
        path
        for path in (args.output_jsonl, args.manifest_jsonl, args.unmapped_jsonl)
        if path is not None
    ]
    try:
        _preflight_destinations(destinations)
    except (FileExistsError, ValueError) as exc:
        parser.error(str(exc))

    try:
        taxonomy = load_taxonomy(args.taxonomy)
    except (TagTaxonomyError, OSError) as exc:
        parser.error(str(exc))

    try:
        result = curate_jsonl(args.source, taxonomy)
    except OSError as exc:
        parser.error(str(exc))
    try:
        _write_destinations(
            [
                (path, values)
                for path, values in (
                    (args.output_jsonl, result["records"]),
                    (args.manifest_jsonl, result["manifest"]),
                    (args.unmapped_jsonl, result["unmapped"]),
                )
                if path is not None
            ]
        )
    except (OSError, FileExistsError, ValueError) as exc:
        parser.error(str(exc))
    print(
        json.dumps(
            result["summary"],
            allow_nan=False,
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
