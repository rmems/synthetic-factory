"""Tests for the duration-weighted (LPT) shard assignment in ``scripts/ci_shard_tests.py``."""

from __future__ import annotations

import contextlib
import json
import sys
import tempfile
import unittest
from io import StringIO
from pathlib import Path
from unittest import mock

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "scripts"))

import ci_shard_tests

ShardWeights = ci_shard_tests.ShardWeights
ShardPlanError = ci_shard_tests.ShardPlanError


def _loads(plan, weights):
    return [sum(weights.of(module) for module in shard) for shard in plan]


def _round_robin(modules, shards):
    ordered = sorted(modules)
    return [ordered[index::shards] for index in range(shards)]


class AssignmentDeterminismTests(unittest.TestCase):
    def test_same_inputs_give_the_same_plan_in_any_input_order(self):
        weights = ShardWeights(
            {f"test_m{index:02d}": float(index % 7 + 1) for index in range(40)}, 2.0
        )
        modules = [f"test_m{index:02d}" for index in range(45)]
        expected = ci_shard_tests.assign_shards(modules, 4, weights)

        permutations = (
            modules,
            list(reversed(modules)),
            modules[17:] + modules[:17],
            modules[1::2] + modules[::2],
            sorted(modules, key=lambda name: name[::-1]),
        )
        for candidate in permutations:
            self.assertEqual(ci_shard_tests.assign_shards(candidate, 4, weights), expected)

    def test_equal_weights_break_ties_by_module_name_then_shard_index(self):
        weights = ShardWeights({}, 1.0)
        modules = ["test_d", "test_b", "test_e", "test_a", "test_c"]

        plan = ci_shard_tests.assign_shards(modules, 2, weights)

        self.assertEqual(plan, [["test_a", "test_c", "test_e"], ["test_b", "test_d"]])

    def test_each_shard_lists_its_modules_in_name_order(self):
        weights = ShardWeights({"test_z": 9.0, "test_a": 1.0, "test_m": 5.0}, 1.0)

        plan = ci_shard_tests.assign_shards(["test_m", "test_a", "test_z"], 1, weights)

        self.assertEqual(plan, [["test_a", "test_m", "test_z"]])


class AssignmentCompletenessTests(unittest.TestCase):
    def test_every_module_lands_in_exactly_one_shard(self):
        weights = ShardWeights({"test_heavy": 50.0, "test_mid": 10.0}, 0.5)
        modules = ["test_heavy", "test_mid"] + [f"test_light_{index}" for index in range(9)]
        for shards in range(1, 15):
            with self.subTest(shards=shards):
                plan = ci_shard_tests.plan_shards(modules, shards, weights)
                assigned = [module for shard in plan for module in shard]

                self.assertEqual(len(plan), shards)
                self.assertEqual(sorted(assigned), sorted(modules))

    def test_shard_count_below_one_is_refused(self):
        weights = ShardWeights({}, 1.0)
        modules = ["test_a"]

        with self.assertRaisesRegex(ShardPlanError, "at least 1"):
            ci_shard_tests.assign_shards(modules, 0, weights)

    def test_shard_index_outside_the_shard_count_is_refused(self):
        weights = ShardWeights({}, 1.0)
        modules = ["test_a", "test_b", "test_c"]
        shards = 4
        for shard in (-1, shards, shards + 1):
            with self.subTest(shard=shard):
                with self.assertRaises(ShardPlanError) as raised:
                    ci_shard_tests.shard_modules(modules, shard, shards, weights)
                self.assertEqual(
                    str(raised.exception), f"shard must satisfy 0 <= shard < 4, got {shard}"
                )

    def test_cli_still_rejects_an_out_of_range_shard_before_planning(self):
        for argv in (["--shard", "-1", "--shards", "4"], ["--shard", "4", "--shards", "4"]):
            with (
                self.subTest(argv=argv),
                mock.patch.object(ci_shard_tests, "shard_modules") as planner,
                contextlib.redirect_stderr(StringIO()) as stderr,
                self.assertRaises(SystemExit) as raised,
            ):
                ci_shard_tests.main(argv)
            self.assertEqual(raised.exception.code, 2)
            self.assertIn("--shard must satisfy 0 <= shard < shards", stderr.getvalue())
            planner.assert_not_called()

    def test_partition_check_fails_closed_on_missing_extra_and_repeated_modules(self):
        modules = ["test_a", "test_b", "test_c"]
        broken_plans = {
            "missing=['test_c']": [["test_a"], ["test_b"]],
            "extra=['test_x']": [["test_a", "test_x"], ["test_b", "test_c"]],
            "repeated=['test_a']": [["test_a", "test_b"], ["test_a", "test_c"]],
        }
        for reason, plan in broken_plans.items():
            with self.subTest(reason=reason):
                with self.assertRaises(ShardPlanError) as raised:
                    ci_shard_tests.check_partition(modules, plan)
                self.assertIn(reason, str(raised.exception))

    def test_partition_check_accepts_a_true_partition(self):
        self.assertIsNone(
            ci_shard_tests.check_partition(["test_a", "test_b"], [["test_b"], [], ["test_a"]])
        )

    def test_list_output_partitions_the_discovered_modules(self):
        listed = []
        for shard in range(4):
            output = StringIO()
            with contextlib.redirect_stdout(output):
                result = ci_shard_tests.main(["--shard", str(shard), "--shards", "4", "--list"])
            self.assertEqual(result, 0)
            listed.append(output.getvalue().splitlines())

        flattened = [module for shard in listed for module in shard]
        self.assertEqual(sorted(flattened), ci_shard_tests.discover_modules())
        self.assertEqual(len(flattened), len(set(flattened)))
        for shard in listed:
            self.assertEqual(shard, sorted(shard))


class DefaultWeightTests(unittest.TestCase):
    def test_unrecorded_module_takes_the_default_weight(self):
        weights = ShardWeights({"test_known": 12.5}, 0.75)

        self.assertEqual(weights.of("test_known"), 12.5)
        self.assertEqual(weights.of("test_brand_new"), 0.75)

    def test_unrecorded_modules_are_packed_by_default_weight_and_name(self):
        weights = ShardWeights({"test_big": 3.0}, 1.0)
        modules = ["test_new_b", "test_big", "test_new_a", "test_new_c"]

        plan = ci_shard_tests.assign_shards(modules, 2, weights)

        self.assertEqual(plan, [["test_big"], ["test_new_a", "test_new_b", "test_new_c"]])

    def test_new_module_is_assigned_under_the_committed_table(self):
        weights = ci_shard_tests.load_weights()
        brand_new = "test_zz_module_without_a_recorded_weight"
        self.assertNotIn(brand_new, weights.table)
        modules = ci_shard_tests.discover_modules() + [brand_new]

        plan = ci_shard_tests.plan_shards(modules, 4, weights)

        self.assertEqual(sum(shard.count(brand_new) for shard in plan), 1)
        self.assertEqual(plan, ci_shard_tests.plan_shards(list(reversed(modules)), 4, weights))


class LptBalanceTests(unittest.TestCase):
    def test_lpt_places_heaviest_first_into_the_lightest_shard(self):
        weights = ShardWeights(
            {
                "test_a": 7.0,
                "test_b": 6.0,
                "test_c": 5.0,
                "test_d": 4.0,
                "test_e": 3.0,
                "test_f": 2.0,
                "test_g": 1.0,
            },
            1.0,
        )

        plan = ci_shard_tests.assign_shards(sorted(weights.table), 3, weights)

        self.assertEqual(
            plan, [["test_a", "test_f", "test_g"], ["test_b", "test_e"], ["test_c", "test_d"]]
        )
        self.assertEqual(_loads(plan, weights), [10.0, 9.0, 9.0])
        self.assertEqual(_loads(_round_robin(weights.table, 3), weights), [12.0, 9.0, 7.0])

    def test_three_heavy_modules_no_longer_decide_the_balance(self):
        table = {"test_h1": 300.0, "test_h2": 250.0, "test_h3": 200.0}
        table.update({f"test_l{index:02d}": 10.0 for index in range(60)})
        weights = ShardWeights(table, 10.0)

        lpt = _loads(ci_shard_tests.assign_shards(table, 4, weights), weights)
        round_robin = _loads(_round_robin(table, 4), weights)

        self.assertEqual(sorted(lpt), [330.0, 340.0, 340.0, 340.0])
        self.assertEqual(sorted(round_robin), [150.0, 350.0, 400.0, 450.0])

    def test_committed_table_keeps_every_shard_within_one_module_of_the_others(self):
        weights = ci_shard_tests.load_weights()
        modules = ci_shard_tests.discover_modules()

        loads = _loads(ci_shard_tests.plan_shards(modules, 4, weights), weights)

        heaviest = max(weights.of(module) for module in modules)
        self.assertLessEqual(max(loads) - min(loads), heaviest)


def _weights_document(**overrides):
    document = {"schema": ci_shard_tests.WEIGHTS_SCHEMA, "default_weight": 1.0, "weights": {}}
    document.update(overrides)
    return document


class WeightsTableTests(unittest.TestCase):
    def test_committed_table_is_valid_and_names_test_modules(self):
        weights = ci_shard_tests.load_weights()

        self.assertGreater(weights.default, 0)
        self.assertTrue(weights.table)
        self.assertTrue(all(module.startswith("test_") for module in weights.table))

    def test_integer_and_decimal_seconds_are_accepted(self):
        weights = ci_shard_tests.parse_weights(
            _weights_document(default_weight=2, weights={"test_a": 3, "test_b": 0.25})
        )

        self.assertEqual(weights, ShardWeights({"test_a": 3.0, "test_b": 0.25}, 2.0))

    def test_malformed_tables_fail_closed(self):
        bad_documents = {
            "not an object": [],
            "wrong schema": _weights_document(schema="ci-shard-weights-v0"),
            "weights not an object": _weights_document(weights=[["test_a", 1.0]]),
            "missing default": {"schema": ci_shard_tests.WEIGHTS_SCHEMA, "weights": {}},
            "boolean weight": _weights_document(weights={"test_a": True}),
            "string weight": _weights_document(weights={"test_a": "1.5"}),
            "zero weight": _weights_document(weights={"test_a": 0}),
            "negative default": _weights_document(default_weight=-1.0),
            "nan weight": _weights_document(weights={"test_a": float("nan")}),
            "infinite weight": _weights_document(weights={"test_a": float("inf")}),
        }
        for reason, document in bad_documents.items():
            with self.subTest(reason=reason), self.assertRaises(ShardPlanError):
                ci_shard_tests.parse_weights(document)

    def test_huge_json_integer_weight_is_refused_without_overflow(self):
        huge = "9" * 400
        text = (
            '{"schema": "ci-shard-weights-v1", "default_weight": 1,'
            f' "weights": {{"test_a": {huge}}}}}'
        )
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "weights.json"
            path.write_text(text, encoding="utf-8")

            with self.assertRaises(ShardPlanError) as raised:
                ci_shard_tests.load_weights(path)

        self.assertEqual(
            str(raised.exception),
            "weights['test_a'] must be above 0 and at most 86400 seconds",
        )

    def test_weights_up_to_the_ceiling_are_accepted_and_above_it_refused(self):
        ceiling = ci_shard_tests.MAX_WEIGHT_SECONDS
        accepted = _weights_document(weights={"test_a": ceiling, "test_b": 1e-9})
        refused = _weights_document(default_weight=ceiling + 1)

        self.assertEqual(ci_shard_tests.parse_weights(accepted).of("test_a"), 86400.0)
        with self.assertRaisesRegex(ShardPlanError, "^default_weight must be above 0"):
            ci_shard_tests.parse_weights(refused)

    def test_non_number_message_names_the_type_not_the_value(self):
        document = _weights_document(weights={"test_a": ["not", "seconds"]})

        with self.assertRaises(ShardPlanError) as raised:
            ci_shard_tests.parse_weights(document)

        self.assertEqual(
            str(raised.exception), "weights['test_a'] must be a number of seconds, got list"
        )

    def test_repeated_module_key_is_refused(self):
        text = (
            '{"schema": "ci-shard-weights-v1", "default_weight": 1,'
            ' "weights": {"test_a": 1, "test_a": 2}}'
        )
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "weights.json"
            path.write_text(text, encoding="utf-8")

            with self.assertRaisesRegex(ShardPlanError, r"repeats keys: \['test_a'\]"):
                ci_shard_tests.load_weights(path)

    def test_load_weights_reads_an_explicit_path(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "weights.json"
            path.write_text(
                json.dumps(_weights_document(weights={"test_a": 4.5})), encoding="utf-8"
            )

            weights = ci_shard_tests.load_weights(path)

        self.assertEqual(weights, ShardWeights({"test_a": 4.5}, 1.0))

    def test_cli_exits_with_usage_error_when_the_table_is_invalid_or_missing(self):
        with tempfile.TemporaryDirectory() as tmp:
            invalid = Path(tmp) / "invalid.json"
            invalid.write_text('{"schema": "other"}', encoding="utf-8")
            for path in (invalid, Path(tmp) / "missing.json"):
                with (
                    self.subTest(path=path.name),
                    mock.patch.object(ci_shard_tests, "WEIGHTS_PATH", path),
                    contextlib.redirect_stderr(StringIO()) as stderr,
                    self.assertRaises(SystemExit) as raised,
                ):
                    ci_shard_tests.main(["--shard", "0", "--shards", "4", "--list"])
                self.assertEqual(raised.exception.code, 2)
                self.assertIn("cannot plan the test shards", stderr.getvalue())


if __name__ == "__main__":
    unittest.main()
