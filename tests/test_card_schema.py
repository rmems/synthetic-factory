#!/usr/bin/env python3
"""Tests for per-dataset Hugging Face card schema declarations.

Covers the declaration mechanism (validation, YAML emission, disclosure and
undeclared-visibility rendering, payload coverage) and the first concrete
dataset that uses it: `long-horizon-coding-trajectories` (issue #36).
"""

import io
import json
import sys
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from unittest import mock

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "pipelines"))
sys.path.insert(0, str(REPO / "scripts"))

import card_schema  # noqa: E402
import publish_grok46_hub as publisher  # noqa: E402

LONG_HORIZON = "long-horizon-coding-trajectories"
SECRET_SCAN = "secret-scan-remediation-trajectories"

MINIMAL = {
    "version": 1,
    "dataset": "example-trajectories",
    "note": "Declared because raw meta shapes vary.",
    "features": [
        {"name": "id", "dtype": "string"},
        {"name": "meta", "dtype": "json"},
    ],
}


def write_declaration(root: Path, dataset: str, payload: dict) -> Path:
    root.mkdir(parents=True, exist_ok=True)
    path = root / f"{dataset}.json"
    path.write_text(json.dumps(payload), encoding="utf-8")
    return path


class DeclarationValidationTests(unittest.TestCase):
    def test_minimal_declaration_normalizes_defaults(self):
        declaration = card_schema.validate(MINIMAL, "example-trajectories")
        self.assertEqual(declaration["config_name"], "default")
        self.assertEqual(declaration["split"], "train")
        self.assertEqual(declaration["data_files"], ["data/raw/batch-*.jsonl"])
        self.assertEqual(declaration["disclosures"], [])
        self.assertEqual(declaration["issues"], [])

    def test_declaration_rejects_malformed_payloads(self):
        for payload, message in (
            ({**MINIMAL, "version": 2}, "version must be 1"),
            ({**MINIMAL, "dataset": "other"}, "does not match"),
            ({**MINIMAL, "note": "   "}, "non-empty 'note'"),
            ({**MINIMAL, "surprise": 1}, "unknown declaration key"),
            ({**MINIMAL, "data_files": ["../etc/passwd"]}, "repo-relative"),
            ({**MINIMAL, "data_files": ["/data/raw/x.jsonl"]}, "repo-relative"),
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
        ):
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


class DeclarationLoadingTests(unittest.TestCase):
    def test_missing_declaration_returns_none_and_bad_one_raises(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td) / "card-schemas"
            root.mkdir()
            self.assertIsNone(card_schema.load("example-trajectories", root))

            write_declaration(root, "example-trajectories", {**MINIMAL, "version": 9})
            with self.assertRaisesRegex(card_schema.CardSchemaError, "version must be 1"):
                card_schema.load("example-trajectories", root)

            (root / "example-trajectories.json").write_text("{not json", encoding="utf-8")
            with self.assertRaisesRegex(card_schema.CardSchemaError, "cannot read"):
                card_schema.load("example-trajectories", root)

    def test_a_symlinked_declaration_is_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td) / "card-schemas"
            root.mkdir()
            outside = Path(td) / "outside.json"
            outside.write_text(json.dumps(MINIMAL), encoding="utf-8")
            (root / "example-trajectories.json").symlink_to(outside)
            with self.assertRaisesRegex(card_schema.CardSchemaError, "unsafe card schema entry"):
                card_schema.load("example-trajectories", root)
            with self.assertRaisesRegex(card_schema.CardSchemaError, "unsafe card schema"):
                card_schema.declared_datasets(root)

    def test_an_unsafe_schema_root_is_rejected_by_discovery_and_loading(self):
        with tempfile.TemporaryDirectory() as td:
            base = Path(td)
            outside = base / "outside"
            outside.mkdir()
            write_declaration(outside, "example-trajectories", MINIMAL)
            linked = base / "linked"
            linked.symlink_to(outside, target_is_directory=True)
            regular_file = base / "not-a-directory"
            regular_file.write_text("x", encoding="utf-8")

            for root in (linked, regular_file):
                with self.subTest(root=root):
                    with self.assertRaisesRegex(
                        card_schema.CardSchemaError, "unsafe card schema root"
                    ):
                        card_schema.declared_datasets(root)
                    with self.assertRaisesRegex(
                        card_schema.CardSchemaError, "unsafe card schema root"
                    ):
                        card_schema.load("example-trajectories", root)

            missing = base / "missing"
            self.assertEqual(card_schema.declared_datasets(missing), [])
            self.assertIsNone(card_schema.load("example-trajectories", missing))

    def test_declared_datasets_refuses_a_misnamed_file(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td) / "card-schemas"
            root.mkdir()
            write_declaration(root, "example-trajectories", MINIMAL)
            self.assertEqual(card_schema.declared_datasets(root), ["example-trajectories"])
            (root / "notes.yaml").write_text("x\n", encoding="utf-8")
            with self.assertRaisesRegex(
                card_schema.CardSchemaError, "expected <dataset>.json"
            ):
                card_schema.declared_datasets(root)


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
        self.assertIn("dataset_info:\n  config_name: research\n  features:\n", yaml)

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
            {**MINIMAL, "data_files": ["data/**/batch-*.jsonl"]},
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
        pattern = "data/" + "/".join(["**"] * 1200) + "/batch-*.jsonl"
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


class PublisherIntegrationTests(unittest.TestCase):
    """The publisher must consume declarations, and must never skip one silently."""

    def test_every_declaration_on_disk_is_valid_and_names_a_real_dataset(self):
        declared, _undeclared, orphaned = publisher.card_schema_audit()
        self.assertEqual(orphaned, [], "declaration files that name no known dataset")
        known = set(publisher.known_hub_names())
        for name in declared:
            with self.subTest(dataset=name):
                declaration = publisher.card_declaration(name)
                self.assertIsNotNone(declaration)
                self.assertIn(name, known)

    def test_schemas_command_is_loud_about_orphans_and_gaps(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td) / "card-schemas"
            write_declaration(root, "not-a-real-dataset", {**MINIMAL, "dataset": "x"})
            report = io.StringIO()
            errors = io.StringIO()
            with mock.patch.object(card_schema, "SCHEMA_ROOT", root), redirect_stdout(
                report
            ), redirect_stderr(errors):
                orphan_code = publisher.cmd_schemas()
                root.joinpath("not-a-real-dataset.json").unlink()
                clean_code = publisher.cmd_schemas()
                strict_code = publisher.cmd_schemas(strict=True)
            self.assertEqual((orphan_code, clean_code, strict_code), (2, 0, 1))
            self.assertIn("names no known dataset", errors.getvalue())
            self.assertIn("UNDECLARED  long-horizon-coding-trajectories", report.getvalue())

    def test_a_broken_declaration_fails_the_card_instead_of_degrading_it(self):
        item = {
            "slug": "long-horizon-coding-factory",
            "hub": LONG_HORIZON,
            "pretty": "Long Horizon Coding Trajectories",
            "blurb": "Test factory.",
            "tags": ["synthetic-data"],
        }
        with tempfile.TemporaryDirectory() as td:
            root = Path(td) / "card-schemas"
            write_declaration(root, LONG_HORIZON, {**MINIMAL, "dataset": LONG_HORIZON, "note": ""})
            with mock.patch.object(card_schema, "SCHEMA_ROOT", root):
                with self.assertRaisesRegex(SystemExit, "non-empty 'note'"):
                    publisher.render_card(
                        item,
                        records=2,
                        bytes_=10,
                        first="r01",
                        last="r02",
                        payload_names=["batch-r01.jsonl"],
                    )

    def test_render_card_refuses_a_declaration_that_misses_a_payload(self):
        item = {
            "slug": "long-horizon-coding-factory",
            "hub": LONG_HORIZON,
            "pretty": "Long Horizon Coding Trajectories",
            "blurb": "Test factory.",
            "tags": ["synthetic-data"],
        }
        with self.assertRaisesRegex(SystemExit, "does not cover the published payload"):
            publisher.render_card(
                item,
                records=2,
                bytes_=10,
                first=None,
                last=None,
                payload_names=["episodes.jsonl"],
            )

    def test_an_undeclared_dataset_card_carries_the_visible_placeholder(self):
        # Use a name that no published dataset owns so adding a declaration for
        # a real dataset cannot accidentally turn this fallback test green.
        item = {
            "slug": "still-undeclared-factory",
            "hub": "still-undeclared-trajectories",
            "pretty": "Still Undeclared Trajectories",
            "blurb": "Test factory.",
            "tags": ["synthetic-data"],
        }
        self.assertIsNone(card_schema.load(item["hub"]))
        card = publisher.render_card(
            item,
            records=2,
            bytes_=10,
            first="r01",
            last="r02",
            payload_names=["batch-r01.jsonl"],
        )
        front_matter = card.split("---", 2)[1]
        self.assertNotIn("configs:", front_matter)
        self.assertNotIn("dataset_info:", front_matter)
        self.assertIn("**Not declared yet.**", card)


class LongHorizonCodingDeclarationTests(unittest.TestCase):
    """Issue #36: the first dataset to use the mechanism end to end."""

    def setUp(self):
        self.declaration = card_schema.load(LONG_HORIZON)
        self.assertIsNotNone(self.declaration, "config/card-schemas is missing #36")
        self.item = {
            "slug": "long-horizon-coding-factory",
            "hub": LONG_HORIZON,
            "pretty": "Long Horizon Coding Trajectories",
            "blurb": "Long-horizon coding-agent leftover-bug episodes.",
            "tags": ["synthetic-data", "trajectories"],
        }
        self.card = publisher.render_card(
            self.item,
            records=9970,
            bytes_=94602148,
            first="r01",
            last="r4985",
            payload_names=["batch-r01.jsonl", "batch-r02.jsonl"],
        )

    def test_declaration_matches_the_observed_union_schema(self):
        names = {feature["name"]: feature for feature in self.declaration["features"]}
        self.assertEqual(
            set(names),
            {"id", "goal", "plan", "steps", "outcome", "reward", "meta"},
        )
        self.assertTrue(names["plan"]["optional"])
        self.assertEqual(names["meta"]["dtype"], "json")
        self.assertEqual(names["reward"]["dtype"], "json")
        steps = {feature["name"]: feature for feature in names["steps"]["list"]}
        self.assertEqual(
            set(steps), {"n", "decision_basis", "tool_call", "observation", "reflection"}
        )
        self.assertTrue(steps["reflection"]["optional"])
        tool_call = {feature["name"]: feature for feature in steps["tool_call"]["struct"]}
        self.assertEqual(tool_call["args"]["dtype"], "json")
        self.assertEqual(self.declaration["issues"], [36])

    def test_key_bag_columns_are_declared_json(self):
        self.assertEqual(
            card_schema.json_columns(self.declaration["features"]),
            ["steps[].tool_call.args", "reward", "meta"],
        )

    def test_card_front_matter_declares_the_default_config_over_raw_batches(self):
        front_matter = self.card.split("---", 2)[1]
        self.assertIn("configs:\n- config_name: default\n", front_matter)
        self.assertIn('    path: "data/raw/batch-*.jsonl"\n', front_matter)
        self.assertIn("dataset_info:\n  features:\n", front_matter)
        self.assertIn("  - name: meta\n    dtype: json\n", front_matter)
        # license/tags/status claims stay exactly where they were.
        self.assertIn("license: apache-2.0", front_matter)
        self.assertIn("**not training-ready**", self.card)

    def test_card_body_discloses_the_two_tagged_records(self):
        self.assertIn("## Dataset viewer schema", self.card)
        self.assertIn("`lhc-r02-lockfile-pin-c4e1`", self.card)
        self.assertIn("`lhc-r02-race-cache-9aa0`", self.card)
        self.assertIn("| `plan` | optional |", self.card)
        self.assertIn("| `steps[].reflection` | optional |", self.card)
        self.assertNotIn("**Not declared yet.**", self.card)


class SecretScanRemediationDeclarationTests(unittest.TestCase):
    """Issue #48: `reward` is not uniform, so the parquet index cannot be built.

    Every count asserted here was derived from the published mirror at
    `~/rmems/hf/grok-4.6/secret-scan-remediation-trajectories` (2068 records
    over 1034 raw shards, 31549 steps), not copied from the issue text.
    """

    def setUp(self):
        self.declaration = card_schema.load(SECRET_SCAN)
        self.assertIsNotNone(self.declaration, "config/card-schemas is missing #48")
        self.item = {
            "slug": "secret-scan-remediation-factory",
            "hub": SECRET_SCAN,
            "pretty": "Secret Scan Remediation Trajectories",
            "blurb": "Secret-scan leftover-allowlist / baseline remediation.",
            "tags": ["synthetic-data", "trajectories", "secrets", "security"],
        }
        self.card = publisher.render_card(
            self.item,
            records=2068,
            bytes_=16694229,
            first="r01",
            last="r1034",
            payload_names=["batch-r01.jsonl", "batch-r1034.jsonl"],
        )

    def test_declaration_matches_the_observed_union_schema(self):
        names = {feature["name"]: feature for feature in self.declaration["features"]}
        self.assertEqual(
            set(names),
            {"id", "goal", "plan", "steps", "outcome", "reward", "meta"},
        )
        # Unlike long-horizon-coding, `plan` is a string on all 2068 records.
        self.assertNotIn("optional", names["plan"])
        self.assertEqual(names["plan"]["dtype"], "string")
        self.assertEqual(names["reward"]["dtype"], "json")
        self.assertEqual(names["meta"]["dtype"], "json")
        steps = {feature["name"]: feature for feature in names["steps"]["list"]}
        self.assertEqual(
            set(steps), {"n", "decision_basis", "tool_call", "observation", "reflection"}
        )
        self.assertTrue(steps["reflection"]["optional"])
        for required in ("n", "decision_basis", "observation"):
            self.assertNotIn("optional", steps[required])
        tool_call = {feature["name"]: feature for feature in steps["tool_call"]["struct"]}
        self.assertEqual(set(tool_call), {"name", "args"})
        self.assertEqual(tool_call["args"]["dtype"], "json")
        self.assertEqual(self.declaration["issues"], [48])

    def test_key_bag_columns_are_declared_json(self):
        self.assertEqual(
            card_schema.json_columns(self.declaration["features"]),
            ["steps[].tool_call.args", "reward", "meta"],
        )

    def test_data_files_cover_the_published_batch_payload(self):
        # The mirror publishes only `batch-rNN.jsonl`; there is no legacy
        # `episodes.jsonl` to carry, so the default glob is the whole payload.
        self.assertEqual(self.declaration["data_files"], ["data/raw/batch-*.jsonl"])
        self.assertEqual(
            card_schema.payload_coverage_errors(
                self.declaration, ["batch-r01.jsonl", "batch-r1034.jsonl"]
            ),
            [],
        )

    def test_card_front_matter_declares_the_default_config_over_raw_batches(self):
        front_matter = self.card.split("---", 2)[1]
        self.assertIn("configs:\n- config_name: default\n", front_matter)
        self.assertIn('    path: "data/raw/batch-*.jsonl"\n', front_matter)
        self.assertIn("dataset_info:\n  features:\n", front_matter)
        self.assertIn("  - name: reward\n    dtype: json\n", front_matter)
        self.assertIn("  - name: meta\n    dtype: json\n", front_matter)
        self.assertIn("      - name: args\n        dtype: json\n", front_matter)
        # `optional` is a card annotation only; it must not reach the YAML.
        self.assertIn("    - name: reflection\n      dtype: string\n", front_matter)
        self.assertNotIn("optional", front_matter)
        # license/tags/status claims stay exactly where they were.
        self.assertIn("license: apache-2.0", front_matter)
        self.assertIn("**not training-ready**", self.card)

    def test_card_body_discloses_the_reward_variants_and_optional_reflection(self):
        self.assertIn("## Dataset viewer schema", self.card)
        self.assertNotIn("**Not declared yet.**", self.card)
        self.assertIn("| `steps[].reflection` | optional |", self.card)
        self.assertIn("present on 158 of 31549 steps", self.card)
        self.assertIn("`pr` on 1912, `handoff` on 967 and `xfailed` on 12", self.card)
        self.assertIn("### Known payload disclosures", self.card)
        self.assertIn("`reward` has five key sets", self.card)
        self.assertIn("no dest-stamped foreign payload", self.card)
        self.assertIn("`decision_basis`", self.card)


if __name__ == "__main__":
    unittest.main()
