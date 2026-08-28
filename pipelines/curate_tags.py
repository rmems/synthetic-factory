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
import json
import sys
from pathlib import Path

_PIPELINES = Path(__file__).resolve().parent
if str(_PIPELINES) not in sys.path:
    sys.path.insert(0, str(_PIPELINES))

from tag_constants import (  # noqa: E402
    DEFAULT_TAXONOMY_PATH,
    RAW_OUTPUT_ROOT,
    REASON_INVALID_JSON,
    REASON_INVALID_UTF8,
    REASON_PROVENANCE_CONFLICT,
    REASON_RECORD_NOT_OBJECT,
    REASON_RECORD_TOO_DEEP,
    REASON_TAG_ALIAS,
    REASON_TAG_CANONICAL,
    REASON_TAG_EMPTY,
    REASON_TAG_MAPPING_AMBIGUOUS,
    REASON_TAG_NOT_STRING,
    REASON_TAG_PATTERN,
    REASON_TAG_UNMAPPED,
    REASON_TAGS_DEDUPLICATED,
    REASON_TAGS_MAPPED,
    REASON_TAGS_NOT_LIST,
    REASON_TAGS_PROVENANCE_REUSED,
    REASON_TAGS_PROVENANCE_WRITTEN,
    REASON_TAGS_UNMAPPED,
    REPOSITORY_ROOT,
    RULE_ALIAS,
    RULE_CANONICAL,
    RULE_PATTERN_PREFIX,
    RULE_TRANSFORM,
    TAG_PROVENANCE_FIELD,
    TAGS_KEY,
    TRANSFORM_NAME,
    TRANSFORM_VERSION,
    UNMAPPED_MARKER_TAG,
    TagTaxonomyError,
)
from tag_io import (  # noqa: E402
    _preflight_destinations,
    _unlink_created_file,
    _write_destinations,
)
from tag_jsonl import curate_jsonl  # noqa: E402
from tag_jsonutil import (  # noqa: E402
    canonical_json,
    hash_value,
    normalize_tag,
    vocabulary_entropy,
)
from tag_record import curate_record  # noqa: E402
from tag_taxonomy import Taxonomy, load_taxonomy, map_tags  # noqa: E402

__all__ = (
    "DEFAULT_TAXONOMY_PATH",
    "RAW_OUTPUT_ROOT",
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
    "REASON_TAGS_PROVENANCE_WRITTEN",
    "REASON_TAGS_UNMAPPED",
    "REPOSITORY_ROOT",
    "RULE_ALIAS",
    "RULE_CANONICAL",
    "RULE_PATTERN_PREFIX",
    "RULE_TRANSFORM",
    "TAG_PROVENANCE_FIELD",
    "TAGS_KEY",
    "TRANSFORM_NAME",
    "TRANSFORM_VERSION",
    "UNMAPPED_MARKER_TAG",
    "TagTaxonomyError",
    "Taxonomy",
    "_preflight_destinations",
    "_unlink_created_file",
    "_write_destinations",
    "canonical_json",
    "curate_jsonl",
    "curate_record",
    "hash_value",
    "load_taxonomy",
    "main",
    "map_tags",
    "normalize_tag",
    "vocabulary_entropy",
)


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path, help="JSONL corpus to inspect")
    parser.add_argument("--taxonomy", type=Path, default=None)
    parser.add_argument("--output-jsonl", type=Path)
    parser.add_argument("--manifest-jsonl", type=Path)
    parser.add_argument("--unmapped-jsonl", type=Path)
    return parser


def _requested_destinations(args: argparse.Namespace) -> list[Path]:
    return [
        path
        for path in (args.output_jsonl, args.manifest_jsonl, args.unmapped_jsonl)
        if path is not None
    ]


def _reject_source_clobber(
    parser: argparse.ArgumentParser, args: argparse.Namespace
) -> None:
    if args.output_jsonl is None:
        return
    if args.output_jsonl.resolve(strict=False) == args.source.resolve():
        parser.error("output must not replace the source")


def _write_cli_outputs(
    parser: argparse.ArgumentParser,
    args: argparse.Namespace,
    result: dict,
) -> None:
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


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)
    _reject_source_clobber(parser, args)
    try:
        _preflight_destinations(_requested_destinations(args))
    except (FileExistsError, ValueError) as exc:
        parser.error(str(exc))
    try:
        taxonomy = load_taxonomy(args.taxonomy)
        result = curate_jsonl(args.source, taxonomy)
    except (TagTaxonomyError, OSError) as exc:
        parser.error(str(exc))
    else:
        _write_cli_outputs(parser, args, result)
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
