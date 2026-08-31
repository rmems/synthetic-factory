#!/usr/bin/env python3
"""Frozen source-vocabulary, shape, and fixture-regression tests."""

import collections
import copy
import hashlib
import io
import json
import sys
import tempfile
import unittest
from pathlib import Path
from contextlib import redirect_stderr, redirect_stdout

_TESTS = Path(__file__).resolve().parent
if str(_TESTS) not in sys.path:
    sys.path.insert(0, str(_TESTS))

from reward_test_helpers import (  # noqa: E402
    EXCLUDED,
    FIXTURES,
    FIXTURE_DECISIONS,
    FIXTURE_SHA256,
    MAGNITUDE,
    ORDER_ONLY,
    PIPELINES,
    all_fixture_records,
)

if str(PIPELINES) not in sys.path:
    sys.path.insert(0, str(PIPELINES))

import curate_rewards  # noqa: E402


class SourceVocabularyMappingTests(unittest.TestCase):
    """The frozen 510-key / 140-shape mapping is checkable without the raw run."""

    def setUp(self):
        self.vocabulary = curate_rewards.CONVERSION_POLICY["source_vocabulary"]

    def test_the_mapping_covers_the_five_hundred_ten_keys_and_hundred_forty_shapes(self):
        self.assertEqual(self.vocabulary["run"], "2026-08-17")
        self.assertEqual(self.vocabulary["unique_component_keys"], 510)
        self.assertEqual(self.vocabulary["unique_shapes"], 140)
        self.assertEqual(len(self.vocabulary["component_keys"]), 510)
        self.assertEqual(len(self.vocabulary["shapes"]), 140)
        self.assertEqual(
            sum(self.vocabulary["dispositions"].values()),
            self.vocabulary["unique_component_keys"],
        )

    def test_every_recorded_disposition_follows_the_declared_rules(self):
        recorded = collections.Counter()
        for key, entry in self.vocabulary["component_keys"].items():
            expected = curate_rewards.disposition_for_observed_types(
                key, entry["observed_types"]
            )
            self.assertEqual(
                entry["disposition"],
                expected,
                f"{key} is mapped as {entry['disposition']}, not {expected}",
            )
            self.assertIn(entry["disposition"], curate_rewards.COMPONENT_DISPOSITIONS)
            recorded[entry["disposition"]] += 1
        self.assertEqual(dict(recorded), self.vocabulary["dispositions"])

    def test_no_narrative_or_structural_key_is_mapped_as_a_magnitude_term(self):
        for key, entry in self.vocabulary["component_keys"].items():
            if entry["disposition"] != curate_rewards.DISPOSITION_MAGNITUDE_TERM:
                continue
            self.assertNotIn(key, curate_rewards.UNWEIGHTED_EXCLUDE)
            self.assertTrue(
                set(entry["observed_types"]) <= {"number", "value-object"},
                f"{key} is a magnitude term but was observed as "
                f"{entry['observed_types']}",
            )

    def test_every_shape_selects_the_arithmetic_branch_its_signature_implies(self):
        for row in self.vocabulary["shapes"]:
            members = dict(
                part.split(":", 1) for part in row["signature"].split("|") if ":" in part
            )
            method = row["arithmetic_method"]
            self.assertIn(method, curate_rewards.ARITHMETIC_METHODS)
            self.assertIn(row["arithmetic_status"], curate_rewards.ARITHMETIC_STATUSES)
            total = members.get(curate_rewards.DECLARED_TOTAL_KEY)
            if total not in {"int", "float"}:
                self.assertEqual(method, "no_numeric_total", row["signature"])
                continue
            if curate_rewards.WEIGHTS_FIELD in members:
                self.assertTrue(
                    method.startswith("declared_weighted_sum"), row["signature"]
                )
            else:
                self.assertTrue(
                    method.startswith("unweighted_component_sum"), row["signature"]
                )

    def test_policy_rejects_shape_methods_incompatible_with_the_signature(self):
        document = curate_rewards.CONVERSION_POLICY
        cases = []
        for expected_method, incompatible_method in (
            ("no_numeric_total", "declared_weighted_sum"),
            ("declared_weighted_sum", "unweighted_component_sum"),
            ("unweighted_component_sum", "declared_weighted_sum"),
        ):
            shape = next(
                copy.deepcopy(row)
                for row in document["source_vocabulary"]["shapes"]
                if row.get("arithmetic_method") == expected_method
            )
            shape["arithmetic_method"] = incompatible_method
            cases.append((expected_method, shape))

        for name, shape in cases:
            with self.subTest(name=name):
                malformed = copy.deepcopy(document)
                index = next(
                    index
                    for index, row in enumerate(
                        malformed["source_vocabulary"]["shapes"]
                    )
                    if row["signature"] == shape["signature"]
                )
                malformed["source_vocabulary"]["shapes"][index] = shape
                with self.assertRaisesRegex(
                    curate_rewards.RewardOntologyError,
                    "incompatible with signature",
                ):
                    curate_rewards.validate_conversion_policy(malformed)

    def test_census_emits_and_policy_accepts_plural_arithmetic_outcomes(self):
        census = curate_rewards.reward_census(
            [
                {
                    "reward_components": {
                        "review_probe_component": 1.0,
                        "total": 1.0,
                    }
                },
                {
                    "reward_components": {
                        "review_probe_component": 1.0,
                        "total": 2.0,
                    }
                },
            ]
        )
        self.assertEqual(len(census["shapes"]), 1)
        shape = census["shapes"][0]
        self.assertNotIn("arithmetic_status", shape)
        self.assertNotIn("arithmetic_method", shape)
        self.assertEqual(
            shape["arithmetic_outcomes"],
            [
                {"status": "invalid", "method": "unweighted_component_sum"},
                {"status": "valid", "method": "unweighted_component_sum"},
            ],
        )

        document = copy.deepcopy(curate_rewards.CONVERSION_POLICY)
        document["source_vocabulary"]["shapes"][0] = shape
        document["source_vocabulary"]["reward_instances"] = sum(
            item["occurrences"] for item in document["source_vocabulary"]["shapes"]
        )
        document["source_vocabulary"]["arithmetic"] = [
            {
                "status": "valid",
                "method": "unweighted_component_sum",
                "occurrences": document["source_vocabulary"]["reward_instances"],
            }
        ]
        self.assertIs(curate_rewards.validate_conversion_policy(document), document)

    def test_malformed_shape_arithmetic_outcomes_are_refused(self):
        document = curate_rewards.CONVERSION_POLICY
        base_shape = copy.deepcopy(document["source_vocabulary"]["shapes"][0])
        outcome = {
            "status": base_shape["arithmetic_status"],
            "method": base_shape["arithmetic_method"],
        }
        cases = {
            "singular and plural": (
                {**base_shape, "arithmetic_outcomes": [outcome]},
                "exactly one",
            ),
            "half singular": (
                {key: value for key, value in base_shape.items()
                 if key != "arithmetic_method"},
                "arithmetic_method",
            ),
            "empty plural": (
                {
                    "signature": base_shape["signature"],
                    "occurrences": base_shape["occurrences"],
                    "arithmetic_outcomes": [],
                },
                "nonempty list",
            ),
            "duplicate plural": (
                {
                    "signature": base_shape["signature"],
                    "occurrences": base_shape["occurrences"],
                    "arithmetic_outcomes": [outcome, copy.deepcopy(outcome)],
                },
                "duplicate arithmetic outcome",
            ),
        }
        for name, (shape, message) in cases.items():
            with self.subTest(name=name):
                malformed = copy.deepcopy(document)
                malformed["source_vocabulary"]["shapes"][0] = shape
                with self.assertRaisesRegex(
                    curate_rewards.RewardOntologyError, message
                ):
                    curate_rewards.validate_conversion_policy(malformed)

    def test_by_factory_census_must_reconcile_with_global_counts(self):
        document = curate_rewards.CONVERSION_POLICY
        factory = "agentic-coding-trajectory-factory"

        wrong_records = copy.deepcopy(document)
        entry = wrong_records["expected_classification"]["by_factory"][factory]
        entry["records"] += 1
        entry["comparability"]["exclude_from_reward_training"] += 1
        with self.assertRaisesRegex(
            curate_rewards.RewardOntologyError,
            "by_factory records must sum to records",
        ):
            curate_rewards.validate_conversion_policy(wrong_records)

        wrong_classes = copy.deepcopy(document)
        entry = wrong_classes["expected_classification"]["by_factory"][factory]
        entry["comparability"]["exclude_from_reward_training"] -= 1
        entry["comparability"]["sign_order_only"] = 1
        with self.assertRaisesRegex(
            curate_rewards.RewardOntologyError,
            "by_factory comparability counts must match",
        ):
            curate_rewards.validate_conversion_policy(wrong_classes)

        wrong_reasons = copy.deepcopy(document)
        entry = wrong_reasons["expected_classification"]["by_factory"][factory]
        entry["reason_codes"]["magnitude_calibration_missing"] -= 1
        entry["reason_codes"]["explicit_usd_unit_calibration"] = 1
        with self.assertRaisesRegex(
            curate_rewards.RewardOntologyError,
            "by_factory reason-code counts must match",
        ):
            curate_rewards.validate_conversion_policy(wrong_reasons)

    def test_the_frozen_classification_census_is_internally_consistent(self):
        expected = curate_rewards.CONVERSION_POLICY["expected_classification"]
        self.assertEqual(expected["run"], "2026-08-17")
        self.assertEqual(sum(expected["comparability"].values()), expected["records"])
        self.assertTrue(
            set(expected["comparability"]) <= curate_rewards.COMPARABILITY_CLASSES
        )
        self.assertTrue(set(expected["reason_codes"]) <= curate_rewards.REASON_CODES)
        by_factory = expected["by_factory"]
        self.assertEqual(
            sum(entry["records"] for entry in by_factory.values()), expected["records"]
        )
        rolled = collections.Counter()
        for entry in by_factory.values():
            rolled.update(entry["comparability"])
        self.assertEqual(dict(rolled), expected["comparability"])
        self.assertEqual(
            expected["comparability"],
            {
                "exclude_from_reward_training": 153,
                "magnitude_comparable": 34,
                "sign_order_only": 8,
            },
        )


class RewardShapeVocabularyTests(unittest.TestCase):
    def test_reward_signature_matches_the_training_audits_shape_vocabulary(self):
        import training_audit

        seen = 0
        for _name, _line, record in all_fixture_records():
            for _path, reward in training_audit.walk_key(record, "reward_components"):
                seen += 1
                self.assertEqual(
                    curate_rewards.reward_signature(reward),
                    training_audit.reward_shape(reward),
                )
        self.assertGreater(seen, 0)

    def test_disposition_and_summation_never_disagree(self):
        probes = [
            ("task_progress", 0.5),
            ("task_progress", {"value": 0.5, "note": "rich"}),
            ("task_progress", {"note": "no numeric value"}),
            ("task_progress", "0.5"),
            ("task_progress", True),
            ("task_progress", None),
            ("task_progress", [0.5]),
            ("components", {"task": 0.5}),
            ("components", 0.5),
            ("actual", {"task": 0.5}),
            ("summary", {"note": "text"}),
            ("total", 1.0),
            ("unit_usd", 20000),
            ("rounding_decimals", 4),
            ("notes", "free text"),
            ("weights", {"task": 1.0}),
        ]
        for key, value in probes:
            disposition = curate_rewards.component_disposition(key, value)
            self.assertEqual(
                disposition == curate_rewards.DISPOSITION_MAGNITUDE_TERM,
                curate_rewards.contributes_to_total(key, value),
                f"{key}={value!r} is {disposition}",
            )

    def test_an_unseen_key_is_never_promoted_to_a_magnitude_term(self):
        self.assertEqual(
            curate_rewards.component_disposition("never_seen_in_any_run"),
            curate_rewards.DISPOSITION_AMBIGUOUS,
        )
        self.assertEqual(
            curate_rewards.component_disposition("task_progress"),
            curate_rewards.DISPOSITION_MAGNITUDE_TERM,
        )
        self.assertEqual(
            curate_rewards.component_disposition("total"),
            curate_rewards.DISPOSITION_DECLARED_TOTAL,
        )

    def test_nonfinite_values_are_never_numeric_magnitude_terms(self):
        for value in (float("nan"), float("inf"), float("-inf")):
            self.assertEqual(curate_rewards.value_type(value), "unknown")
            self.assertEqual(
                curate_rewards.component_disposition("new_component", value),
                curate_rewards.DISPOSITION_AMBIGUOUS,
            )
            self.assertFalse(
                curate_rewards.contributes_to_total("new_component", value)
            )
            self.assertEqual(
                curate_rewards.value_type({"value": value}), "object"
            )

    def test_jsonl_loader_rejects_nonfinite_numeric_constants(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "nonfinite.jsonl"
            path.write_text('{"reward_components":{"total":NaN}}\n', encoding="utf-8")
            with self.assertRaisesRegex(
                curate_rewards.RewardOntologyError,
                r"non-standard JSON numeric constant NaN",
            ):
                list(curate_rewards._load_jsonl(path))


class RewardOntologyFixtureRegression(unittest.TestCase):
    """Bind the mapped layout families to deterministic ontology decisions."""

    def test_fixture_bytes_are_pinned(self):
        for name, digest in FIXTURE_SHA256.items():
            data = (FIXTURES / name).read_bytes()
            self.assertEqual(
                hashlib.sha256(data).hexdigest(),
                digest,
                f"{name} changed; re-derive FIXTURE_DECISIONS before repinning",
            )

    def test_every_fixture_line_maps_to_its_declared_rule(self):
        seen = set()
        for name, line_number, record in all_fixture_records():
            key = (name, line_number)
            self.assertIn(key, FIXTURE_DECISIONS, f"undocumented fixture line {key}")
            rule_id, comparability, reasons = FIXTURE_DECISIONS[key]
            curated, sidecar = curate_rewards.curate_record(
                record, source_path=name, source_line=line_number
            )
            annotation = curated[curate_rewards.ANNOTATION_FIELD]
            self.assertEqual(annotation["comparability"], comparability, key)
            self.assertEqual(annotation["reason_codes"], reasons, key)
            self.assertEqual(
                sidecar["classification"],
                {"comparability": comparability, "reason_codes": reasons},
                key,
            )
            rule = curate_rewards.comparability_rule(rule_id)
            self.assertEqual(rule["comparability"], comparability, key)
            self.assertTrue(
                set(rule["reason_codes"]) <= set(reasons),
                f"{key} does not carry rule {rule_id}'s reason codes",
            )
            seen.add(key)
        self.assertEqual(seen, set(FIXTURE_DECISIONS))

    def test_the_fixture_corpus_exercises_every_declared_rule_and_method(self):
        rules = set()
        methods = set()
        for name, line_number, record in all_fixture_records():
            _curated, sidecar = curate_rewards.curate_record(
                record, source_path=name, source_line=line_number
            )
            _c, _r, _p, rule_id = curate_rewards._classify(
                sidecar["source_rewards"], sidecar["arithmetic"]
            )
            rules.add(rule_id)
            methods.update(entry["method"] for entry in sidecar["arithmetic"])
        self.assertEqual(
            rules,
            {rule["id"] for rule in curate_rewards.COMPARABILITY_RULES},
        )
        self.assertEqual(methods, set(curate_rewards.REQUIRED_ARITHMETIC_METHODS))

    def test_every_retained_record_declares_a_comparability_class(self):
        classes = collections.Counter()
        for name, line_number, record in all_fixture_records():
            curated, _sidecar = curate_rewards.curate_record(
                record, source_path=name, source_line=line_number
            )
            self.assertIn(curate_rewards.ANNOTATION_FIELD, curated)
            classes[curate_rewards.comparability_of(curated)] += 1
        self.assertEqual(sum(classes.values()), len(FIXTURE_DECISIONS))
        self.assertEqual(classes[MAGNITUDE], 3)
        self.assertEqual(classes[ORDER_ONLY], 3)
        self.assertEqual(classes[EXCLUDED], len(FIXTURE_DECISIONS) - 6)

    def test_curation_is_deterministic_idempotent_and_non_mutating(self):
        for name, line_number, record in all_fixture_records():
            before = json.dumps(record, sort_keys=True)
            first, first_sidecar = curate_rewards.curate_record(
                record, source_path=name, source_line=line_number
            )
            second, second_sidecar = curate_rewards.curate_record(
                record, source_path=name, source_line=line_number
            )
            self.assertEqual(first, second)
            self.assertEqual(first_sidecar, second_sidecar)
            again, again_sidecar = curate_rewards.curate_record(
                first, source_path=name, source_line=line_number
            )
            self.assertEqual(again, first)
            self.assertEqual(again_sidecar, first_sidecar)
            self.assertEqual(json.dumps(record, sort_keys=True), before)

    def test_every_source_reward_stays_recoverable(self):
        for name, line_number, record in all_fixture_records():
            curated, sidecar = curate_rewards.curate_record(
                record, source_path=name, source_line=line_number
            )
            self.assertEqual(
                curate_rewards.restore_source_record(curated, sidecar), record
            )
            self.assertEqual(
                curated[curate_rewards.ANNOTATION_FIELD]["source_reward_count"],
                len(sidecar["source_rewards"]),
            )
            for entry in sidecar["source_rewards"]:
                self.assertIn("value", entry)

    def test_classify_jsonl_summarises_each_layout_family(self):
        summary = curate_rewards.classify_jsonl(FIXTURES / "ffpc-preferences.jsonl")
        self.assertEqual(summary["records"], 9)
        self.assertEqual(
            summary["comparability"],
            {MAGNITUDE: 2, ORDER_ONLY: 3, EXCLUDED: 4},
        )
        swarm = curate_rewards.classify_jsonl(FIXTURES / "swarm-trajectories.jsonl")
        self.assertEqual(swarm["comparability"], {EXCLUDED: 5})

    def test_the_census_cli_reproduces_the_fixture_vocabulary(self):
        census = curate_rewards.census_jsonl(
            [FIXTURES / name for name in sorted(FIXTURE_SHA256)]
        )
        self.assertEqual(census["records"], len(FIXTURE_DECISIONS))
        self.assertEqual(census["scope_keys"], ["reward_components"])
        self.assertEqual(
            sum(census["dispositions"].values()), census["unique_component_keys"]
        )
        for key, entry in census["component_keys"].items():
            self.assertEqual(
                entry["disposition"],
                curate_rewards.disposition_for_observed_types(
                    key, entry["observed_types"]
                ),
            )
        # Two bare `reward` scopes live outside the census scope but inside the
        # ontology's, and neither is dropped.
        self.assertEqual(
            census["ontology_scope_instances"] - census["reward_instances"], 2
        )
        self.assertEqual(
            set(census["dispositions"]),
            set(curate_rewards.COMPONENT_DISPOSITIONS),
        )

    def test_census_rejects_non_object_records(self):
        with self.assertRaisesRegex(
            curate_rewards.RewardOntologyError, "census records must be objects"
        ):
            curate_rewards.reward_census(["not-an-object"])

    def test_census_scope_key_accepts_reward_and_rejects_unknown(self):
        records = []
        for _name, _line, record in all_fixture_records():
            records.append(record)
        census = curate_rewards.reward_census(records, scope_keys=["reward"])
        self.assertEqual(census["scope_keys"], ["reward"])
        self.assertGreater(census["reward_instances"], 0)
        with self.assertRaisesRegex(
            curate_rewards.RewardOntologyError,
            "census scope names non-reward keys",
        ):
            curate_rewards.reward_census(records, scope_keys=["not_a_reward"])

    def test_census_cli_scope_key_and_unknown_scope(self):
        with tempfile.TemporaryDirectory() as td:
            source = Path(td) / "in.jsonl"
            source.write_text(
                json.dumps({"id": "r1", "reward": 1.0}) + "\n",
                encoding="utf-8",
            )
            stdout = io.StringIO()
            with redirect_stdout(stdout):
                code = curate_rewards.main(
                    ["census", str(source), "--scope-key", "reward"]
                )
            self.assertEqual(code, 0)
            summary = json.loads(stdout.getvalue())
            self.assertEqual(summary["scope_keys"], ["reward"])
            self.assertEqual(summary["reward_instances"], 1)
            self.assertNotIn("component_keys", summary)
            stderr = io.StringIO()
            with redirect_stdout(io.StringIO()), redirect_stderr(stderr):
                code = curate_rewards.main(
                    ["census", str(source), "--scope-key", "not_a_reward"]
                )
            self.assertEqual(code, 2)
            self.assertIn("census scope names non-reward keys", stderr.getvalue())


if __name__ == '__main__':
    unittest.main()
