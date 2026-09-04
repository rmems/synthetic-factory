#!/usr/bin/env python3
"""Tests for declared-vs-published payload coverage.

Covers ``card_schema.payload_coverage_errors`` (and the Hub-style glob
matching it relies on): uncovered payload files, unused patterns, segment
boundaries, case sensitivity, and recursive ``**`` matching.
"""

import sys
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "pipelines"))
sys.path.insert(0, str(REPO / "scripts"))

import card_schema  # noqa: E402

MINIMAL = {
    "version": 1,
    "dataset": "example-trajectories",
    "note": "Declared because raw meta shapes vary.",
    "features": [
        {"name": "id", "dtype": "string"},
        {"name": "meta", "dtype": "json"},
    ],
}


class PayloadCoverageTests(unittest.TestCase):
    def test_uncovered_payload_and_unused_pattern_are_both_reported(self):
        declaration = card_schema.validate(MINIMAL, "example-trajectories")
        self.assertEqual(
            card_schema.payload_coverage_errors(declaration, ["batch-r01.jsonl"]), []
        )
        errors = card_schema.payload_coverage_errors(declaration, ["episodes.jsonl"])
        self.assertEqual(len(errors), 2)
        self.assertIn("not matched by any declared data_files pattern", errors[0])
        self.assertIn("data/raw/episodes.jsonl", errors[0])
        self.assertIn("matches no published payload", errors[1])

    def test_an_empty_payload_set_fails_a_declared_dataset(self):
        declaration = card_schema.validate(MINIMAL, "example-trajectories")
        self.assertTrue(card_schema.payload_coverage_errors(declaration, []))

    def test_single_segment_glob_does_not_cross_a_directory_boundary(self):
        declaration = card_schema.validate(
            {**MINIMAL, "data_files": ["data/raw/*.jsonl"]},
            "example-trajectories",
        )
        errors = card_schema.payload_coverage_errors(
            declaration, ["nested/batch-r01.jsonl"]
        )
        self.assertEqual(len(errors), 2)
        self.assertIn("data/raw/nested/batch-r01.jsonl", errors[0])
        self.assertIn("data/raw/*.jsonl", errors[1])

    def test_payload_globs_are_case_sensitive(self):
        declaration = card_schema.validate(
            {**MINIMAL, "data_files": ["data/raw/BATCH-*.jsonl"]},
            "example-trajectories",
        )
        self.assertTrue(
            card_schema.payload_coverage_errors(declaration, ["batch-r01.jsonl"])
        )

    def test_recursive_glob_consumes_complete_path_segments(self):
        declaration = card_schema.validate(
            {**MINIMAL, "data_files": ["data/raw/**/batch-*.jsonl"]},
            "example-trajectories",
        )
        self.assertEqual(
            card_schema.payload_coverage_errors(
                declaration, ["archive/2026/batch-r01.jsonl"]
            ),
            [],
        )

    def test_recursive_glob_may_consume_zero_or_consecutive_segments(self):
        for pattern in (
            "data/raw/**/batch-*.jsonl",
            "data/raw/**/**/batch-*.jsonl",
        ):
            with self.subTest(pattern=pattern):
                declaration = card_schema.validate(
                    {**MINIMAL, "data_files": [pattern]},
                    "example-trajectories",
                )
                self.assertEqual(
                    card_schema.payload_coverage_errors(
                        declaration, ["batch-r01.jsonl"]
                    ),
                    [],
                )

    def test_many_recursive_segments_do_not_recurse_in_python(self):
        pattern = "data/raw/" + "/".join(["**"] * 1200) + "/batch-*.jsonl"
        declaration = card_schema.validate(
            {**MINIMAL, "data_files": [pattern]},
            "example-trajectories",
        )
        self.assertEqual(
            card_schema.payload_coverage_errors(declaration, ["batch-r01.jsonl"]),
            [],
        )

    def test_a_disclosure_only_declaration_makes_no_payload_claim(self):
        declaration = card_schema.validate(
            {
                "version": 1,
                "dataset": "example-trajectories",
                "note": "Keep the published viewer projection.",
            },
            "example-trajectories",
        )
        self.assertEqual(card_schema.payload_coverage_errors(declaration, []), [])


if __name__ == "__main__":
    unittest.main()
