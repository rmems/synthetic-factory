#!/usr/bin/env python3
"""Tests for card-schema declaration and feature validation.

Covers ``card_schema.validate`` (and the ``card_schema_validate`` internals
it delegates to): declaration-level rejection rules, nested feature
validation, and dataset-name-shaped path safety.
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

MALFORMED_DECLARATION_CASES = (
    ({**MINIMAL, "version": 2}, "version must be 1"),
    ({**MINIMAL, "dataset": "other"}, "does not match"),
    ({**MINIMAL, "note": "   "}, "non-empty 'note'"),
    ({**MINIMAL, "surprise": 1}, "unknown declaration key"),
    ({**MINIMAL, "data_files": ["../etc/passwd"]}, "repo-relative"),
    ({**MINIMAL, "data_files": ["/data/raw/x.jsonl"]}, "repo-relative"),
    ({**MINIMAL, "data_files": ["data/**"]}, "repo-relative data/raw/"),
    ({**MINIMAL, "data_files": ["data/*.jsonl"]}, "repo-relative data/raw/"),
    (
        {**MINIMAL, "data_files": ["data/metadata/NOTES-r*.md"]},
        "repo-relative data/raw/",
    ),
    ({**MINIMAL, "data_files": []}, "non-empty"),
    (
        {**MINIMAL, "data_files": ["data/raw/***.jsonl"]},
        "must occupy an entire path segment",
    ),
    (
        {**MINIMAL, "data_files": ["data/raw/pre**post.jsonl"]},
        "must occupy an entire path segment",
    ),
    ({**MINIMAL, "issues": [0]}, "positive integers"),
    (
        {**MINIMAL, "features": [{"name": "a", "dtype": "decimal"}]},
        "unsupported dtype",
    ),
    (
        {**MINIMAL, "features": [{"name": "a", "dtype": "string", "x": 1}]},
        "unknown feature key",
    ),
    (
        {**MINIMAL, "features": [{"name": "a"}]},
        "exactly one of dtype/struct/list",
    ),
    (
        {
            **MINIMAL,
            "features": [{"name": "a", "dtype": "string", "struct": []}],
        },
        "exactly one of dtype/struct/list",
    ),
    (
        {**MINIMAL, "features": [{"name": "a", "struct": []}]},
        "non-empty list of features",
    ),
    (
        {
            **MINIMAL,
            "features": [
                {"name": "a", "dtype": "string"},
                {"name": "a", "dtype": "string"},
            ],
        },
        "duplicate feature name",
    ),
    (
        {
            **MINIMAL,
            "features": [
                {"name": "a", "dtype": "string", "optional": "yes"}
            ],
        },
        "optional on a must be a boolean",
    ),
    ({**MINIMAL, "disclosures": [""]}, "must not be empty"),
    ({**MINIMAL, "disclosures": [{"ids": []}]}, "non-empty 'summary'"),
    (
        {**MINIMAL, "disclosures": [{"summary": "s", "nope": 1}]},
        "unknown disclosure key",
    ),
)


class DeclarationValidationTests(unittest.TestCase):
    def test_minimal_declaration_normalizes_defaults(self):
        declaration = card_schema.validate(MINIMAL, "example-trajectories")
        self.assertEqual(declaration["config_name"], "default")
        self.assertEqual(declaration["split"], "train")
        self.assertEqual(declaration["data_files"], ["data/raw/batch-*.jsonl"])
        self.assertEqual(declaration["disclosures"], [])
        self.assertEqual(declaration["issues"], [])

    def test_declaration_rejects_malformed_payloads(self):
        for payload, message in MALFORMED_DECLARATION_CASES:
            with self.subTest(message=message):
                with self.assertRaisesRegex(card_schema.CardSchemaError, message):
                    card_schema.validate(payload, "example-trajectories")

    def test_nested_features_validate_and_reject_bad_children(self):
        declaration = card_schema.validate(
            {
                **MINIMAL,
                "features": [
                    {
                        "name": "steps",
                        "list": [
                            {"name": "n", "dtype": "int64"},
                            {
                                "name": "tool_call",
                                "struct": [
                                    {"name": "name", "dtype": "string"},
                                    {"name": "args", "dtype": "json"},
                                ],
                            },
                        ],
                    },
                    {"name": "tags", "list": "string"},
                ],
            },
            "example-trajectories",
        )
        self.assertEqual(
            card_schema.json_columns(declaration["features"]),
            ["steps[].tool_call.args"],
        )
        with self.assertRaisesRegex(card_schema.CardSchemaError, "unsupported list dtype"):
            card_schema.validate(
                {**MINIMAL, "features": [{"name": "tags", "list": "decimal"}]},
                "example-trajectories",
            )

    def test_declaration_path_rejects_a_traversing_dataset_name(self):
        for name in ("../escape", "Upper", "", "a/b"):
            with self.subTest(name=name):
                with self.assertRaisesRegex(
                    card_schema.CardSchemaError, "invalid Hub dataset name"
                ):
                    card_schema.declaration_path(name)


if __name__ == "__main__":
    unittest.main()
