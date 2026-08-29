"""Shared fixtures for tag-curation unit tests."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PIPELINES = ROOT / "pipelines"
if str(PIPELINES) not in sys.path:
    sys.path.insert(0, str(PIPELINES))

from curate_tags import (  # noqa: E402
    DEFAULT_TAXONOMY_PATH,
    REASON_INVALID_JSON,
    REASON_INVALID_UTF8,
    REASON_PROVENANCE_CONFLICT,
    REASON_RECORD_NOT_OBJECT,
    REASON_RECORD_TOO_DEEP,
    REASON_TAG_ALIAS,
    REASON_TAG_CANONICAL,
    REASON_TAG_EMPTY,
    REASON_TAG_NOT_STRING,
    REASON_TAG_PATTERN,
    REASON_TAG_MAPPING_AMBIGUOUS,
    REASON_TAG_UNMAPPED,
    REASON_TAGS_DEDUPLICATED,
    REASON_TAGS_MAPPED,
    REASON_TAGS_NOT_LIST,
    REASON_TAGS_PROVENANCE_REUSED,
    REASON_TAGS_UNMAPPED,
    TAG_PROVENANCE_FIELD,
    TRANSFORM_NAME,
    TRANSFORM_VERSION,
    UNMAPPED_MARKER_TAG,
    Taxonomy,
    TagTaxonomyError,
    _preflight_destinations,
    _write_destinations,
    canonical_json,
    curate_jsonl,
    curate_record,
    load_taxonomy,
    map_tags,
    normalize_tag,
    vocabulary_entropy,
)
from tag_taxonomy import SUPPORTED_NORMALIZATION_STEPS  # noqa: E402

__all__ = (
    "DEFAULT_TAXONOMY_PATH",
    "DEEP_REGEX_GROUPS",
    "GROUPED_OPTIONAL_REGEX_PATTERNS",
    "GROUPED_OPTIONAL_REPEATS",
    "INVALID_REGEX_PATTERNS",
    "MAX_CANONICAL_TAGS",
    "PIPELINES",
    "REASON_INVALID_JSON",
    "REASON_INVALID_UTF8",
    "REASON_PROVENANCE_CONFLICT",
    "REASON_RECORD_NOT_OBJECT",
    "REASON_RECORD_TOO_DEEP",
    "REASON_TAG_ALIAS",
    "REASON_TAG_CANONICAL",
    "REASON_TAG_EMPTY",
    "REASON_TAG_MAPPING_AMBIGUOUS",
    "REASON_TAG_NOT_STRING",
    "REASON_TAG_PATTERN",
    "REASON_TAG_UNMAPPED",
    "REASON_TAGS_DEDUPLICATED",
    "REASON_TAGS_MAPPED",
    "REASON_TAGS_NOT_LIST",
    "REASON_TAGS_PROVENANCE_REUSED",
    "REASON_TAGS_UNMAPPED",
    "REGEX_RESOURCE_EXCEPTION_TYPES",
    "ROOT",
    "SAFE_GROUP_BOUNDARY_CASES",
    "SUPPORTED_NORMALIZATION_STEPS",
    "TAG_PROVENANCE_FIELD",
    "TAXONOMY",
    "TRANSFORM_NAME",
    "TRANSFORM_VERSION",
    "UNMAPPED_MARKER_TAG",
    "UNSAFE_LINEAR_REGEX_PATTERNS",
    "Taxonomy",
    "TagTaxonomyError",
    "_preflight_destinations",
    "_write_destinations",
    "canonical_json",
    "curate_jsonl",
    "curate_record",
    "load_taxonomy",
    "map_tags",
    "minimal_taxonomy",
    "normalize_tag",
    "record",
    "run_tag_cli",
    "vocabulary_entropy",
    "write_tag_source",
)


MAX_CANONICAL_TAGS = 40
DEEP_REGEX_GROUPS = sys.getrecursionlimit() * 2
GROUPED_OPTIONAL_REPEATS = 28
INVALID_REGEX_PATTERNS = (
    ("re.error", "^($"),
    ("OverflowError", "^a{999999999999999999999999999999999999}$"),
    (
        "RecursionError",
        "^" + "(" * DEEP_REGEX_GROUPS + "a" + ")" * DEEP_REGEX_GROUPS + "$",
    ),
)
GROUPED_OPTIONAL_REGEX_PATTERNS = (
    (
        "capturing_grouped_optionals",
        "^" + "(a?)" * GROUPED_OPTIONAL_REPEATS + "a" * GROUPED_OPTIONAL_REPEATS + "$",
    ),
    (
        "noncapturing_grouped_optionals",
        "^"
        + "(?:a?)" * GROUPED_OPTIONAL_REPEATS
        + "a" * GROUPED_OPTIONAL_REPEATS
        + "$",
    ),
)
UNSAFE_LINEAR_REGEX_PATTERNS = (
    ("nested_repeat", "^(a+)+$"),
    ("repeated_alternation", "^(a|aa)+$"),
    ("overlapping_adjacent_repeats", "^a+a+$"),
    ("ambiguous_wildcard_boundary", "^.*x.*$"),
    ("overlapping_repeat_suffix", "^a+a$"),
    ("overlapping_optional_suffix", "^a?a$"),
    ("overlapping_alternation", "^(a|aa)b$"),
    *GROUPED_OPTIONAL_REGEX_PATTERNS,
    ("capturing_group_literal_suffix", "^(a?)a$"),
    ("noncapturing_group_literal_suffix", "^(?:a?)a$"),
    ("capturing_group_variable_repeat_suffix", "^(a?)a+$"),
    ("noncapturing_group_variable_repeat_suffix", "^(?:a?)a+$"),
    ("capturing_group_fixed_repeat_suffix", "^(a?)a{2}$"),
    ("noncapturing_group_fixed_repeat_suffix", "^(?:a?)a{2}$"),
    ("capturing_nullable_group_between_repeats", "^a+(b?)a$"),
    ("noncapturing_nullable_group_between_repeats", "^a+(?:b?)a$"),
    ("capturing_multiple_nullable_tails", "^(a?b?)a$"),
    ("noncapturing_multiple_nullable_tails", "^(?:a?b?)a$"),
)
SAFE_GROUP_BOUNDARY_CASES = (
    ("capturing_literal_boundary", "^(a?)b$", "ab"),
    ("noncapturing_literal_boundary", "^(?:a?)b$", "ab"),
    ("capturing_variable_repeat_boundary", "^(a?)b+$", "abbb"),
    ("noncapturing_variable_repeat_boundary", "^(?:a?)b+$", "abbb"),
    ("capturing_fixed_repeat_boundary", "^(a?)b{2}$", "abb"),
    ("noncapturing_fixed_repeat_boundary", "^(?:a?)b{2}$", "abb"),
    ("capturing_nullable_group_boundary", "^a+(b?)c$", "aaabc"),
    ("noncapturing_nullable_group_boundary", "^a+(?:b?)c$", "aaabc"),
)
REGEX_RESOURCE_EXCEPTION_TYPES = (OverflowError, RecursionError, MemoryError)

TAXONOMY = load_taxonomy()


def record(tags, **overrides):
    value = {
        "id": "ttf-r01-001",
        "meta": {"factory": "thalamic-trajectory-factory", "round": 1, "tags": tags},
    }
    value.update(overrides)
    return value


def minimal_taxonomy(**overrides):
    document = {
        "version": "tag-taxonomy-test",
        "canonical_tag_pattern": "^[a-z][a-z0-9_]*:[a-z][a-z0-9_]*$",
        "facets": [
            {
                "id": "decision",
                "description": "gate decision",
                "terms": [
                    {
                        "tag": "decision:accept",
                        "definition": "accept",
                        "aliases": ["accept"],
                    }
                ],
            },
            {
                "id": "curation",
                "description": "bookkeeping",
                "terms": [
                    {
                        "tag": UNMAPPED_MARKER_TAG,
                        "definition": "unmapped source tags were dropped",
                        "aliases": [],
                    }
                ],
            },
        ],
        "pattern_rules": [],
        "transform_emitted_tags": [UNMAPPED_MARKER_TAG],
        "normalization": {"steps": list(SUPPORTED_NORMALIZATION_STEPS)},
    }
    document.update(overrides)
    return document


def write_tag_source(root, tags=None, name="corpus.jsonl"):
    source = Path(root) / name
    payload = record(list(tags) if tags is not None else ["MODIFY", "tokamak"])
    source.write_text(json.dumps(payload, sort_keys=True) + "\n", encoding="utf-8")
    return source


def run_tag_cli(source, extra_args=(), timeout=None):
    command = [
        sys.executable,
        str(PIPELINES / "curate_tags.py"),
        str(source),
        *extra_args,
    ]
    return subprocess.run(
        command,
        capture_output=True,
        text=True,
        check=False,
        timeout=timeout,
    )
