"""Load and apply the controlled tag taxonomy."""

from __future__ import annotations

import copy
import json
import re
from pathlib import Path
from typing import Any

from tag_constants import (
    DEFAULT_TAXONOMY_PATH,
    REASON_TAG_ALIAS,
    REASON_TAG_CANONICAL,
    REASON_TAG_EMPTY,
    REASON_TAG_MAPPING_AMBIGUOUS,
    REASON_TAG_NOT_STRING,
    REASON_TAG_PATTERN,
    REASON_TAG_UNMAPPED,
    REASON_TAGS_UNMAPPED,
    RULE_ALIAS,
    RULE_CANONICAL,
    RULE_PATTERN_PREFIX,
    RULE_TRANSFORM,
    UNMAPPED_MARKER_TAG,
    TagTaxonomyError,
)
from tag_jsonutil import load_strict_json, normalize_tag
from tag_regex import compile_taxonomy_regex

SUPPORTED_NORMALIZATION_STEPS = (
    "strip leading and trailing whitespace",
    "lowercase",
    "replace every run of characters outside [a-z0-9] with a single underscore",
    "strip leading and trailing underscores",
)


def require_utf8(value: str, label: str, source: str) -> str:
    try:
        value.encode("utf-8")
    except UnicodeEncodeError as exc:
        raise TagTaxonomyError(f"{source}: {label} must be valid UTF-8") from exc
    return value


def require_str(container: dict[str, Any], key: str, source: str) -> str:
    value = container.get(key)
    if not isinstance(value, str):
        raise TagTaxonomyError(f"{source}: {key} must be a nonempty string")
    if not value.strip():
        raise TagTaxonomyError(f"{source}: {key} must be a nonempty string")
    return require_utf8(value, key, source)


class _FacetIndex:
    def __init__(self, source: str, canonical_re: re.Pattern[str]) -> None:
        self.source = source
        self.canonical_re = canonical_re
        self.facet_of: dict[str, str] = {}
        self.definition_of: dict[str, str] = {}
        self.alias_index: dict[str, str] = {}
        self.alias_owner: dict[str, str] = {}

    def index_facets(self, facets: Any) -> None:
        if not isinstance(facets, list):
            raise TagTaxonomyError(f"{self.source}: facets must be a nonempty array")
        if not facets:
            raise TagTaxonomyError(f"{self.source}: facets must be a nonempty array")
        for facet in facets:
            self._index_facet(facet)

    def _index_facet(self, facet: Any) -> None:
        if not isinstance(facet, dict):
            raise TagTaxonomyError(f"{self.source}: every facet must be an object")
        facet_id = require_str(facet, "id", self.source)
        terms = facet.get("terms")
        self._index_terms(facet_id, terms)

    def _index_terms(self, facet_id: str, terms: Any) -> None:
        if not isinstance(terms, list):
            raise TagTaxonomyError(
                f"{self.source}: facet {facet_id} must declare a nonempty terms array"
            )
        if not terms:
            raise TagTaxonomyError(
                f"{self.source}: facet {facet_id} must declare a nonempty terms array"
            )
        for term in terms:
            self._index_term(facet_id, term)

    def _index_term(self, facet_id: str, term: Any) -> None:
        if not isinstance(term, dict):
            raise TagTaxonomyError(
                f"{self.source}: every term in facet {facet_id} must be an object"
            )
        tag = require_str(term, "tag", self.source)
        self._register_canonical(facet_id, tag, term)
        self._index_aliases(tag, term.get("aliases", []))

    def _register_canonical(self, facet_id: str, tag: str, term: dict[str, Any]) -> None:
        if self.canonical_re.fullmatch(tag) is None:
            raise TagTaxonomyError(
                f"{self.source}: canonical tag {tag!r} does not match "
                f"canonical_tag_pattern"
            )
        if not tag.startswith(f"{facet_id}:"):
            raise TagTaxonomyError(
                f"{self.source}: canonical tag {tag!r} is not in facet {facet_id}"
            )
        if tag in self.facet_of:
            raise TagTaxonomyError(
                f"{self.source}: canonical tag {tag!r} is declared twice"
            )
        self.facet_of[tag] = facet_id
        self.definition_of[tag] = require_str(term, "definition", self.source)

    def _index_aliases(self, tag: str, aliases: Any) -> None:
        if not isinstance(aliases, list):
            raise TagTaxonomyError(
                f"{self.source}: aliases for {tag!r} must be an array"
            )
        for alias in [tag, *aliases]:
            self._index_one_alias(tag, alias)

    def _index_one_alias(self, tag: str, alias: Any) -> None:
        if not isinstance(alias, str):
            raise TagTaxonomyError(
                f"{self.source}: alias for {tag!r} must be a nonempty string"
            )
        if not alias.strip():
            raise TagTaxonomyError(
                f"{self.source}: alias for {tag!r} must be a nonempty string"
            )
        require_utf8(alias, f"alias for {tag!r}", self.source)
        key = normalize_tag(alias)
        if not key:
            raise TagTaxonomyError(
                f"{self.source}: alias {alias!r} for {tag!r} normalizes to nothing"
            )
        owner = self.alias_owner.get(key)
        if owner is not None:
            self._reject_alias_conflict(alias, owner, tag)
        self.alias_owner[key] = tag
        self.alias_index[key] = tag

    def _reject_alias_conflict(self, alias: str, owner: str, tag: str) -> None:
        if owner == tag:
            return
        raise TagTaxonomyError(
            f"{self.source}: alias {alias!r} maps to both {owner!r} and {tag!r}"
        )


def _load_pattern_rules(
    rules: Any, source: str, facet_of: dict[str, str]
) -> list[tuple[str, str, re.Pattern[str]]]:
    if not isinstance(rules, list):
        raise TagTaxonomyError(f"{source}: pattern_rules must be an array")
    compiled: list[tuple[str, str, re.Pattern[str]]] = []
    seen_ids: set[str] = set()
    for rule in rules:
        compiled.append(_load_one_pattern_rule(rule, source, facet_of, seen_ids))
    return compiled


def _load_one_pattern_rule(
    rule: Any,
    source: str,
    facet_of: dict[str, str],
    seen_ids: set[str],
) -> tuple[str, str, re.Pattern[str]]:
    if not isinstance(rule, dict):
        raise TagTaxonomyError(f"{source}: every pattern rule must be an object")
    rule_id = require_str(rule, "id", source)
    _reject_duplicate_rule_id(rule_id, seen_ids, source)
    tag = require_str(rule, "tag", source)
    _require_declared_pattern_tag(rule_id, tag, facet_of, source)
    pattern = require_str(rule, "pattern", source)
    _require_anchored_pattern(rule_id, pattern, source)
    compiled = compile_taxonomy_regex(
        pattern, f"pattern rule {rule_id!r}", source
    )
    return rule_id, tag, compiled


def _reject_duplicate_rule_id(rule_id: str, seen_ids: set[str], source: str) -> None:
    if rule_id in seen_ids:
        raise TagTaxonomyError(
            f"{source}: pattern rule id {rule_id!r} is declared twice"
        )
    seen_ids.add(rule_id)


def _require_declared_pattern_tag(
    rule_id: str, tag: str, facet_of: dict[str, str], source: str
) -> None:
    if tag in facet_of:
        return
    raise TagTaxonomyError(
        f"{source}: pattern rule {rule_id!r} targets undeclared tag {tag!r}"
    )


def _require_anchored_pattern(rule_id: str, pattern: str, source: str) -> None:
    if not pattern.startswith("^"):
        raise TagTaxonomyError(
            f"{source}: pattern rule {rule_id!r} must be anchored with ^ and $"
        )
    if not pattern.endswith("$"):
        raise TagTaxonomyError(
            f"{source}: pattern rule {rule_id!r} must be anchored with ^ and $"
        )


def _load_emitted_tags(
    emitted: Any, source: str, facet_of: dict[str, str]
) -> tuple[str, ...]:
    if not isinstance(emitted, list):
        raise TagTaxonomyError(f"{source}: transform_emitted_tags must be an array")
    _require_nonempty_emitted_strings(emitted, source)
    if len(emitted) != len(set(emitted)):
        raise TagTaxonomyError(
            f"{source}: transform_emitted_tags must not contain duplicates"
        )
    loaded = tuple(emitted)
    for tag in loaded:
        _require_declared_emitted_tag(tag, facet_of, source)
    _require_only_implemented_emitted_tags(loaded, source)
    return loaded


def _require_nonempty_emitted_strings(emitted: list[Any], source: str) -> None:
    for tag in emitted:
        _require_one_emitted_string(tag, source)


def _require_one_emitted_string(tag: Any, source: str) -> None:
    if not isinstance(tag, str):
        raise TagTaxonomyError(
            f"{source}: transform_emitted_tags must contain nonempty strings"
        )
    if not tag:
        raise TagTaxonomyError(
            f"{source}: transform_emitted_tags must contain nonempty strings"
        )
    require_utf8(tag, "transform_emitted_tags entry", source)


def _require_declared_emitted_tag(
    tag: str, facet_of: dict[str, str], source: str
) -> None:
    if tag in facet_of:
        return
    raise TagTaxonomyError(
        f"{source}: transform_emitted_tags names undeclared tag {tag!r}"
    )


def _require_only_implemented_emitted_tags(
    emitted: tuple[str, ...], source: str
) -> None:
    extra = [tag for tag in emitted if tag != UNMAPPED_MARKER_TAG]
    if extra:
        raise TagTaxonomyError(
            f"{source}: transform_emitted_tags names tags this transform "
            f"cannot emit: {extra!r}"
        )


def _reject_emitted_pattern_targets(
    pattern_rules: list[tuple[str, str, re.Pattern[str]]],
    emitted: tuple[str, ...],
    source: str,
) -> None:
    for rule_id, tag, _compiled in pattern_rules:
        _reject_one_emitted_pattern_target(rule_id, tag, emitted, source)


def _reject_one_emitted_pattern_target(
    rule_id: str, tag: str, emitted: tuple[str, ...], source: str
) -> None:
    if tag not in emitted:
        return
    raise TagTaxonomyError(
        f"{source}: pattern rule {rule_id!r} targets transform-emitted tag {tag!r}"
    )


def _require_unmapped_marker(
    facet_of: dict[str, str], emitted: tuple[str, ...], source: str
) -> None:
    if UNMAPPED_MARKER_TAG not in facet_of:
        raise TagTaxonomyError(
            f"{source}: taxonomy must declare {UNMAPPED_MARKER_TAG!r}"
        )
    if UNMAPPED_MARKER_TAG not in emitted:
        raise TagTaxonomyError(
            f"{source}: transform_emitted_tags must include {UNMAPPED_MARKER_TAG!r}"
        )


class Taxonomy:
    """A loaded, validated controlled tag vocabulary."""

    def __init__(self, document: dict[str, Any], *, source: str) -> None:
        self.source = source
        self.version = require_str(document, "version", source)
        _require_supported_normalization(document, source)
        pattern = require_str(document, "canonical_tag_pattern", source)
        self._canonical_re = compile_taxonomy_regex(
            pattern, "canonical_tag_pattern", source
        )
        indexed = _FacetIndex(source, self._canonical_re)
        indexed.index_facets(document.get("facets"))
        self.facet_of = indexed.facet_of
        self.definition_of = indexed.definition_of
        self.alias_index = indexed.alias_index
        self.pattern_rules = _load_pattern_rules(
            document.get("pattern_rules", []), source, self.facet_of
        )
        self.transform_emitted_tags = _load_emitted_tags(
            document.get("transform_emitted_tags", []), source, self.facet_of
        )
        _reject_emitted_pattern_targets(
            self.pattern_rules, self.transform_emitted_tags, source
        )
        _require_unmapped_marker(self.facet_of, self.transform_emitted_tags, source)

    @property
    def canonical_tags(self) -> frozenset[str]:
        """Every canonical tag the taxonomy declares."""
        return frozenset(self.facet_of)

    def is_canonical(self, tag: Any) -> bool:
        """Return whether a value is a declared canonical tag."""
        if not isinstance(tag, str):
            return False
        return tag in self.facet_of

    def map_tag(self, tag: Any) -> dict[str, Any]:
        """Map one source tag and explain the decision."""
        if not isinstance(tag, str):
            return _mapping_result(tag, None, (None, None, REASON_TAG_NOT_STRING))
        normalized = normalize_tag(tag)
        if not normalized:
            return _mapping_result(
                tag, normalized, (None, None, REASON_TAG_EMPTY)
            )
        return _map_normalized_tag(self, tag, normalized)


def _mapping_result(
    source: Any, normalized: str | None, decision: tuple[Any, Any, str]
) -> dict[str, Any]:
    canonical, rule, reason = decision
    return {
        "source": source,
        "normalized": normalized,
        "canonical": canonical,
        "rule": rule,
        "reason": reason,
    }


def _map_normalized_tag(taxonomy: Taxonomy, tag: str, normalized: str) -> dict[str, Any]:
    canonical = taxonomy.alias_index.get(normalized)
    pattern_matches = _pattern_matches(taxonomy, normalized)
    targets = {mapped for _rule_id, mapped in pattern_matches}
    if canonical is not None:
        targets.add(canonical)
    if len(targets) > 1:
        return _mapping_result(
            tag, normalized, (None, None, REASON_TAG_MAPPING_AMBIGUOUS)
        )
    return _map_unique_target(taxonomy, tag, (normalized, canonical, pattern_matches))


def _pattern_matches(taxonomy: Taxonomy, normalized: str) -> list[tuple[str, str]]:
    matches = []
    for rule_id, mapped, compiled in taxonomy.pattern_rules:
        if compiled.fullmatch(normalized):
            matches.append((rule_id, mapped))
    return matches


def _map_unique_target(
    taxonomy: Taxonomy,
    tag: str,
    payload: tuple[str, str | None, list[tuple[str, str]]],
) -> dict[str, Any]:
    normalized, canonical, pattern_matches = payload
    if canonical in taxonomy.transform_emitted_tags:
        canonical = None
    usable = _drop_emitted_pattern_matches(taxonomy, pattern_matches)
    if canonical is not None:
        return _alias_or_canonical_mapping(tag, normalized, canonical)
    if usable:
        return _pattern_mapping(tag, normalized, usable)
    return _mapping_result(tag, normalized, (None, None, REASON_TAG_UNMAPPED))


def _drop_emitted_pattern_matches(
    taxonomy: Taxonomy, pattern_matches: list[tuple[str, str]]
) -> list[tuple[str, str]]:
    kept = []
    for rule_id, mapped in pattern_matches:
        if mapped in taxonomy.transform_emitted_tags:
            continue
        kept.append((rule_id, mapped))
    return kept


def _alias_or_canonical_mapping(
    tag: str, normalized: str, canonical: str
) -> dict[str, Any]:
    if tag == canonical:
        return _mapping_result(
            tag, normalized, (canonical, RULE_CANONICAL, REASON_TAG_CANONICAL)
        )
    return _mapping_result(
        tag, normalized, (canonical, RULE_ALIAS, REASON_TAG_ALIAS)
    )


def _pattern_mapping(
    tag: str, normalized: str, pattern_matches: list[tuple[str, str]]
) -> dict[str, Any]:
    rule_id, mapped = min(pattern_matches)
    return _mapping_result(
        tag,
        normalized,
        (mapped, f"{RULE_PATTERN_PREFIX}{rule_id}", REASON_TAG_PATTERN),
    )


def map_tags(tags: list[Any], taxonomy: Taxonomy) -> dict[str, Any]:
    """Map one tag list and return its reversible provenance entry."""
    mappings = [taxonomy.map_tag(tag) for tag in tags]
    canonical, seen, duplicates = _collapse_canonical(mappings)
    unmapped = [
        mapping["source"] for mapping in mappings if mapping["canonical"] is None
    ]
    _append_unmapped_marker(canonical, seen, mappings, unmapped)
    return {
        "source_tags": copy.deepcopy(tags),
        "canonical_tags": sorted(canonical),
        "mappings": mappings,
        "unmapped_tags": unmapped,
        "duplicates_collapsed": duplicates,
    }


def _collapse_canonical(
    mappings: list[dict[str, Any]],
) -> tuple[list[str], set[str], int]:
    canonical: list[str] = []
    seen: set[str] = set()
    duplicates = 0
    for mapping in mappings:
        duplicates += _take_canonical(mapping, canonical, seen)
    return canonical, seen, duplicates


def _take_canonical(
    mapping: dict[str, Any], canonical: list[str], seen: set[str]
) -> int:
    tag = mapping["canonical"]
    if tag is None:
        return 0
    if tag in seen:
        return 1
    seen.add(tag)
    canonical.append(tag)
    return 0


def _append_unmapped_marker(
    canonical: list[str],
    seen: set[str],
    mappings: list[dict[str, Any]],
    unmapped: list[Any],
) -> None:
    if not unmapped:
        return
    if UNMAPPED_MARKER_TAG in seen:
        return
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


def _require_supported_normalization(document: dict[str, Any], source: str) -> None:
    declared = document.get("normalization")
    if not isinstance(declared, dict):
        raise TagTaxonomyError(
            f"{source}: normalization must declare the implemented lexical fold"
        )
    if declared.get("steps") != list(SUPPORTED_NORMALIZATION_STEPS):
        raise TagTaxonomyError(
            f"{source}: normalization steps must match the implemented lexical fold"
        )


def load_taxonomy(path: str | Path | None = None) -> Taxonomy:
    """Load and validate a taxonomy document."""
    resolved = Path(path) if path is not None else DEFAULT_TAXONOMY_PATH
    document = _read_taxonomy_document(resolved)
    if not isinstance(document, dict):
        raise TagTaxonomyError(f"{resolved}: taxonomy document must be an object")
    return Taxonomy(document, source=str(resolved))


def _read_taxonomy_document(resolved: Path) -> Any:
    try:
        return load_strict_json(resolved.read_text(encoding="utf-8"))
    except RecursionError as exc:
        raise TagTaxonomyError(
            f"{resolved}: taxonomy JSON is nested too deeply"
        ) from exc
    except ValueError as exc:
        raise TagTaxonomyError(f"{resolved}: invalid JSON: {exc}") from exc
