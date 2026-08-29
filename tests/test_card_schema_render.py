#!/usr/bin/env python3
"""Tests for card-schema YAML and Markdown rendering.

Covers ``card_schema.metadata_yaml`` / ``yaml_features`` / ``_yaml_scalar``
(the ``configs`` / ``dataset_info`` front matter) and ``body_section`` /
``undeclared_body_section`` (the human-readable viewer-schema section).
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


class YamlEmissionTests(unittest.TestCase):
    def test_metadata_yaml_matches_the_hugging_face_feature_encoding(self):
        declaration = card_schema.validate(
            {
                **MINIMAL,
                "features": [
                    {"name": "id", "dtype": "string"},
                    {
                        "name": "steps",
                        "list": [
                            {"name": "n", "dtype": "int64", "optional": True},
                            {
                                "name": "tool_call",
                                "struct": [
                                    {"name": "name", "dtype": "string"},
                                    {"name": "args", "dtype": "json", "note": "varies"},
                                ],
                            },
                        ],
                    },
                ],
            },
            "example-trajectories",
        )
        self.assertEqual(
            card_schema.metadata_yaml(declaration),
            "configs:\n"
            "- config_name: default\n"
            "  data_files:\n"
            "  - split: train\n"
            '    path: "data/raw/batch-*.jsonl"\n'
            "dataset_info:\n"
            "  features:\n"
            "  - name: id\n"
            "    dtype: string\n"
            "  - name: steps\n"
            "    list:\n"
            '    - name: "n"\n'
            "      dtype: int64\n"
            "    - name: tool_call\n"
            "      struct:\n"
            "      - name: name\n"
            "        dtype: string\n"
            "      - name: args\n"
            "        dtype: json\n",
        )

    def test_card_only_annotations_never_reach_the_yaml(self):
        # datasets reads a feature's type from the first key left after `name`
        # is popped, so `optional` / `note` in the YAML would be read as a type.
        declaration = card_schema.validate(
            {
                **MINIMAL,
                "features": [
                    {
                        "name": "plan",
                        "dtype": "string",
                        "optional": True,
                        "note": "half the records",
                    }
                ],
            },
            "example-trajectories",
        )
        self.assertEqual(
            card_schema.yaml_features(declaration["features"]),
            [{"name": "plan", "dtype": "string"}],
        )
        yaml = card_schema.metadata_yaml(declaration)
        self.assertNotIn("optional", yaml)
        self.assertNotIn("note", yaml)

    def test_multiple_data_file_patterns_emit_one_split_with_a_path_list(self):
        declaration = card_schema.validate(
            {
                **MINIMAL,
                "data_files": ["data/raw/batch-*.jsonl", "data/raw/episodes.jsonl"],
            },
            "example-trajectories",
        )
        self.assertIn(
            "  - split: train\n"
            "    path:\n"
            '    - "data/raw/batch-*.jsonl"\n'
            '    - "data/raw/episodes.jsonl"\n',
            card_schema.metadata_yaml(declaration),
        )

    def test_named_config_is_repeated_in_dataset_info(self):
        declaration = card_schema.validate(
            {**MINIMAL, "config_name": "research"},
            "example-trajectories",
        )
        yaml = card_schema.metadata_yaml(declaration)
        self.assertIn("configs:\n- config_name: research\n", yaml)
        self.assertIn("dataset_info:\n- config_name: research\n  features:\n", yaml)

    def test_reserved_and_unsafe_yaml_scalars_are_quoted_or_refused(self):
        self.assertEqual(card_schema._yaml_scalar("n"), '"n"')
        self.assertEqual(card_schema._yaml_scalar("no"), '"no"')
        self.assertEqual(card_schema._yaml_scalar("data/raw/x.jsonl"), '"data/raw/x.jsonl"')
        self.assertEqual(card_schema._yaml_scalar("string"), "string")
        self.assertEqual(card_schema._yaml_scalar(True), "true")
        self.assertEqual(card_schema._yaml_scalar(7), "7")
        for value in ("a---b", "a\nb"):
            with self.subTest(value=value):
                with self.assertRaises(card_schema.CardSchemaError):
                    card_schema._yaml_scalar(value)

    def test_a_disclosure_only_declaration_emits_no_configs(self):
        declaration = card_schema.validate(
            {
                "version": 1,
                "dataset": "example-trajectories",
                "note": "The working viewer projection stays as published.",
                "disclosures": ["Sixteen rows are dest-stamped gate wraps."],
            },
            "example-trajectories",
        )
        self.assertEqual(card_schema.metadata_yaml(declaration), "")
        body = card_schema.body_section(declaration)
        self.assertIn("No default `configs` / `dataset_info` block", body)
        self.assertIn("Sixteen rows are dest-stamped gate wraps.", body)


class BodySectionTests(unittest.TestCase):
    def test_body_section_reports_json_columns_optionals_and_disclosures(self):
        declaration = card_schema.validate(
            {
                **MINIMAL,
                "issues": [36],
                "features": [
                    {"name": "id", "dtype": "string"},
                    {"name": "plan", "dtype": "string", "optional": True, "note": "half"},
                    {"name": "meta", "dtype": "json"},
                ],
                "disclosures": [
                    {"summary": "Two rows carry extra tags.", "ids": ["a-1"], "issues": [43]}
                ],
            },
            "example-trajectories",
        )
        body = card_schema.body_section(declaration)
        self.assertIn("## Dataset viewer schema", body)
        self.assertIn("issues/36", body)
        self.assertIn("`meta`", body)
        self.assertIn("| `plan` | optional | half |", body)
        self.assertIn("### Known payload disclosures", body)
        self.assertIn("Record ids: `a-1`.", body)
        self.assertIn("issues/43", body)

    def test_undeclared_section_states_the_risk_without_claiming_live_status(self):
        body = card_schema.undeclared_body_section("example-trajectories")
        self.assertIn("**Not declared yet.**", body)
        self.assertIn("index availability is unverified here", body)
        self.assertNotIn("stay false", body)
        self.assertIn("config/card-schemas/example-trajectories.json", body)


if __name__ == "__main__":
    unittest.main()
