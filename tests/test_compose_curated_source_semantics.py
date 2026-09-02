#!/usr/bin/env python3
"""Behavioral coverage for the extracted source-semantic boundary."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path


TESTS = Path(__file__).resolve().parent
PIPELINES = TESTS.parent / "pipelines"
for _path in (TESTS, PIPELINES):
    if str(_path) not in sys.path:
        sys.path.insert(0, str(_path))

import compose_curated_source  # noqa: E402
import compose_curated_source_semantics  # noqa: E402
from compose_contract import (  # noqa: E402
    ACTION_EXCLUDED,
    ACTION_RETAINED,
    ComposeDecision,
    ComposeError,
    REASON_DUPLICATE_CURATED_RECORD,
)


def _semantic_record():
    return {
        "id": "sfcur-root",
        "a/b": {"~id": "legacy-root"},
        "meta": {
            "factory": "source-factory",
            "generator": "generator",
            "generator_version": "1",
            "run": "run-1",
            "round": 7,
            "keep": "root-content",
        },
        "chosen": {
            "id": "sfcur-chosen",
            "old_id": "legacy-chosen",
            "meta": {"factory": "source-factory", "keep": "chosen-content"},
        },
        "rejected": {
            "id": "sfcur-rejected",
            "meta": "opaque-training-content",
        },
        "language_view": {"trajectory": {"meta": {"run": "run-1", "keep": "trajectory-content"}}},
        "reward_training": {
            "source_sidecar_id": "sha256:source-coordinate",
            "magnitude": {
                "values": [
                    {"calibration_source": "sidecar", "normalized": 0.5},
                    "opaque-training-content",
                ]
            },
        },
    }


def _identity_detail():
    return {
        "original_ids": [
            {"path": "/a~1b/~0id"},
            {"path": "not-a-pointer"},
            {"path": 7},
        ],
        "id_mappings": [
            {"owner_path": "/", "output_id": "sfcur-root"},
            {
                "owner_path": "/chosen",
                "output_id": "sfcur-chosen",
                "original_ids": [{"path": "/chosen/old_id"}],
            },
            {
                "owner_path": "/rejected",
                "output_id": "a-different-id",
                "original_ids": "/not-a-list",
            },
            {
                "owner_path": "/chosen/missing/child",
                "output_id": "unused",
                "original_ids": [{"path": "/rejected/child/id"}],
            },
            {"owner_path": "not-a-pointer", "output_id": "unused"},
            "not-a-mapping",
        ],
    }


def _capture_semantic_hash(record):
    captured = []

    def capture_semantic(semantic):
        captured.append(semantic)
        return "semantic-digest"

    decision = ComposeDecision(
        ACTION_RETAINED,
        record,
        (),
        (
            {"lane": "source", "detail": {}},
            {"lane": "identity", "detail": _identity_detail()},
        ),
        None,
        "sfcur-root",
    )
    context = compose_curated_source.SourceLineContext(
        "factory/batch-r01.jsonl",
        7,
        "f" * 64,
        canonical_sha256=capture_semantic,
    )
    digest = compose_curated_source_semantics._post_transform_semantic_sha256(decision, context)
    return digest, captured


class SourceSemanticNormalization(unittest.TestCase):
    def test_semantic_hash_removes_only_coordinate_derived_identity(self):
        """Deduplication must retain training content while erasing run coordinates."""

        digest, captured = _capture_semantic_hash(_semantic_record())

        self.assertEqual(digest, "semantic-digest")
        self.assertEqual(
            captured,
            [
                {
                    "a/b": {},
                    "meta": {"keep": "root-content"},
                    "chosen": {"meta": {"keep": "chosen-content"}},
                    "rejected": {
                        "id": "sfcur-rejected",
                        "meta": "opaque-training-content",
                    },
                    "language_view": {"trajectory": {"meta": {"keep": "trajectory-content"}}},
                    "reward_training": {
                        "magnitude": {
                            "values": [
                                {"normalized": 0.5},
                                "opaque-training-content",
                            ]
                        }
                    },
                }
            ],
        )

    def test_semantic_hash_does_not_mutate_source_identity(self):
        record = _semantic_record()
        _capture_semantic_hash(record)

        self.assertEqual(record["id"], "sfcur-root")
        self.assertEqual(record["chosen"]["old_id"], "legacy-chosen")

    def test_missing_curated_record_is_refused_before_semantic_hashing(self):
        decision = ComposeDecision(ACTION_EXCLUDED, None, (), (), None, None)
        context = compose_curated_source.SourceLineContext("factory/batch-r01.jsonl", 1, "f" * 64)

        with self.assertRaisesRegex(ComposeError, "missing curated record"):
            compose_curated_source_semantics._post_transform_semantic_sha256(decision, context)

    def test_post_transform_duplicate_is_excluded_with_first_source_evidence(self):
        record = {"payload": {"training": "same"}}
        retained = ComposeDecision(
            ACTION_RETAINED,
            record,
            (),
            ({"lane": "identity", "detail": {}},),
            None,
            None,
        )
        seen: dict[str, tuple[str, int]] = {}
        first_context = compose_curated_source.SourceLineContext(
            "factory/first.jsonl",
            3,
            "a" * 64,
            seen_curated_semantics=seen,
        )
        second_context = compose_curated_source.SourceLineContext(
            "factory/second.jsonl",
            9,
            "b" * 64,
            seen_curated_semantics=seen,
        )

        first = compose_curated_source_semantics._deduplicate_curated_record(
            retained, first_context
        )
        duplicate = compose_curated_source_semantics._deduplicate_curated_record(
            retained, second_context
        )

        self.assertIs(first, retained)
        self.assertEqual(duplicate.action, ACTION_EXCLUDED)
        self.assertEqual(duplicate.reason_codes, (REASON_DUPLICATE_CURATED_RECORD,))
        self.assertIsNone(duplicate.record)
        evidence = duplicate.stages[-1]
        self.assertEqual(evidence["lane"], "post_transform_dedup")
        self.assertEqual(evidence["first_source_path"], "factory/first.jsonl")
        self.assertEqual(evidence["first_source_line"], 3)


if __name__ == "__main__":
    unittest.main()
