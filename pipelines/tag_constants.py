"""Shared names for the tag-taxonomy transform."""

from __future__ import annotations

import sys
from pathlib import Path

if __package__:
    from . import _assert_direct_sibling, _expose_package_sibling

    _assert_direct_sibling("tag_constants")
else:
    getattr(sys.modules.get("pipelines"), "_join_package_sibling", lambda name: None)(
        "tag_constants"
    )

TRANSFORM_NAME = "tag_taxonomy"
TRANSFORM_VERSION = "1"

TAGS_KEY = "tags"
TAG_PROVENANCE_FIELD = "tag_provenance"
UNMAPPED_MARKER_TAG = "curation:unmapped_source_tags"

DEFAULT_TAXONOMY_PATH = (
    Path(__file__).resolve().parents[1] / "schemas" / "tag-taxonomy-v1.json"
)
REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
RAW_OUTPUT_ROOT = REPOSITORY_ROOT / "outputs" / "raw"

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
REASON_TAGS_PROVENANCE_WRITTEN = "tags_provenance_written"

REASON_RECORD_NOT_OBJECT = "tag_record_not_object"
REASON_TAGS_NOT_LIST = "tag_container_not_list"
REASON_PROVENANCE_CONFLICT = "tag_provenance_conflict"
REASON_INVALID_JSON = "tag_invalid_json"
REASON_INVALID_UTF8 = "tag_invalid_utf8"
REASON_RECORD_TOO_DEEP = "tag_record_too_deep"


class TagTaxonomyError(ValueError):
    """Raised when a taxonomy document violates its own declared contract."""


if __package__:
    # One module object for both import forms, so a TagTaxonomyError raised
    # through one name is caught through the other whichever form loads first.
    _expose_package_sibling(__name__)
