#!/usr/bin/env python3
"""Canonical reward-contract parser tests.

These pin the fail-closed parsers in ``reward_parse`` so unknown units,
duplicate vocabulary keys, non-finite numbers, malformed mappings, and
policy mismatches keep their existing refusal codes.
"""

from __future__ import annotations

import copy
import math
import sys
import unittest
from decimal import Decimal
from pathlib import Path

_TESTS = Path(__file__).resolve().parent
if str(_TESTS) not in sys.path:
    sys.path.insert(0, str(_TESTS))

from reward_test_helpers import PIPELINES  # noqa: E402

if str(PIPELINES) not in sys.path:
    sys.path.insert(0, str(PIPELINES))

import curate_rewards  # noqa: E402
import reward_parse  # noqa: E402
import reward_units  # noqa: E402


class RewardParseOwnershipTests(unittest.TestCase):
    def test_mapping_reexports_the_canonical_error_and_parsers(self):
        self.assertIs(curate_rewards.RewardOntologyError, reward_parse.RewardOntologyError)
        self.assertIs(curate_rewards._decimal, reward_parse._decimal)
        self.assertIs(
            curate_rewards.ARITHMETIC_STATUSES, reward_parse.ARITHMETIC_STATUSES
        )


class FiniteNumericParserTests(unittest.TestCase):
    def test_nonfinite_floats_are_not_numeric_terms(self):
        for value in (float("nan"), float("inf"), float("-inf")):
            with self.subTest(value=value):
                self.assertIsNone(reward_parse._decimal(value))
                with self.assertRaisesRegex(
                    reward_parse.RewardOntologyError, "non-finite JSON number"
                ):
                    reward_parse._reject_nonfinite_numbers(value, where="probe")

    def test_positive_and_finite_mapping_numbers_fail_closed(self):
        with self.assertRaisesRegex(
            reward_parse.RewardOntologyError, "must be positive and finite"
        ):
            reward_parse._mapping_positive({"n": 0}, "n", "policy")
        with self.assertRaisesRegex(
            reward_parse.RewardOntologyError, "must be positive and finite"
        ):
            reward_parse._mapping_positive({"n": float("inf")}, "n", "policy")
        with self.assertRaisesRegex(
            reward_parse.RewardOntologyError, "must be a number"
        ):
            reward_parse._mapping_positive({"n": True}, "n", "policy")

    def test_positive_decimal_rejects_missing_and_non_positive_units(self):
        with self.assertRaisesRegex(
            reward_parse.RewardOntologyError, "source_unit_usd must be positive"
        ):
            reward_parse._require_positive_decimal(
                None, "source_unit_usd must be positive"
            )
        with self.assertRaisesRegex(
            reward_parse.RewardOntologyError, "source_unit_usd must be positive"
        ):
            reward_parse._require_positive_decimal(
                0, "source_unit_usd must be positive"
            )
        self.assertEqual(
            reward_parse._require_positive_decimal(10000, "unused"),
            Decimal("10000"),
        )


class VocabularyAndCompatibilityParserTests(unittest.TestCase):
    def test_duplicate_and_blank_vocabulary_lists_are_refused(self):
        with self.assertRaisesRegex(
            reward_parse.RewardOntologyError,
            "scope_keys must be a unique nonempty list of strings",
        ):
            reward_parse._mapping_str_list(
                {"scope_keys": ["reward", "reward"]}, "scope_keys", "policy"
            )
        with self.assertRaisesRegex(
            reward_parse.RewardOntologyError, "reason_codes must be nonempty and unique"
        ):
            reward_parse._require_unique_string_codes(
                ["a", "a"], empty_message="reason_codes must be nonempty and unique"
            )
        with self.assertRaisesRegex(
            reward_parse.RewardOntologyError, "reason_codes must be nonempty and unique"
        ):
            reward_parse._require_unique_string_codes(
                [], empty_message="reason_codes must be nonempty and unique"
            )

    def test_unknown_members_are_sorted_and_stable(self):
        self.assertEqual(
            reward_parse._unknown_members(["b", "a", "b"], {"c"}),
            ["a", "b"],
        )
        self.assertEqual(reward_parse._unknown_members(["ok"], {"ok"}), [])

    def test_incompatible_arithmetic_status_and_method_fail_closed(self):
        methods = curate_rewards.ARITHMETIC_METHODS
        with self.assertRaisesRegex(
            reward_parse.RewardOntologyError, "incompatible with method"
        ):
            reward_parse._require_arithmetic_status_method(
                "unsupported",
                "declared_weighted_sum",
                contract=reward_parse.ArithmeticContract(methods, "shape", check_status_pair=True),
            )
        with self.assertRaisesRegex(
            reward_parse.RewardOntologyError, "incompatible with signature"
        ):
            reward_parse._require_arithmetic_status_method(
                "valid",
                "declared_weighted_sum",
                contract=reward_parse.ArithmeticContract(
                    methods, "shape", frozenset({"unweighted_component_sum"}), True),
            )

    def test_duplicate_keys_and_distinct_fields_fail_closed(self):
        seen = set()
        reward_parse._add_unique("a", seen, reward_parse.RewardOntologyError("duplicate"))
        with self.assertRaisesRegex(reward_parse.RewardOntologyError, "duplicate"):
            reward_parse._add_unique(
                "a", seen, reward_parse.RewardOntologyError("duplicate")
            )
        with self.assertRaisesRegex(
            reward_parse.RewardOntologyError, "fields must be distinct"
        ):
            reward_parse._require_distinct(
                "unit_usd", "unit_usd", "policy", "fields must be distinct"
            )


class PolicyReferenceAndUnitTests(unittest.TestCase):
    def test_malformed_policy_hashes_are_refused(self):
        with self.assertRaisesRegex(
            reward_parse.RewardOntologyError, "invalid source_sidecar_id"
        ):
            reward_parse._require_sha256("not-a-hash", "invalid source_sidecar_id")
        token = "sha256:" + "0" * 64
        self.assertEqual(reward_parse._require_sha256(token, "unused"), token)

    def test_policy_mismatch_keeps_the_existing_refusal_code(self):
        document = copy.deepcopy(curate_rewards.CONVERSION_POLICY)
        document["mapping_version"] = "reward-mapping-v9"
        with self.assertRaisesRegex(
            curate_rewards.RewardOntologyError, "unknown reward mapping version"
        ):
            curate_rewards.validate_conversion_policy(document)

    def test_missing_and_invalid_units_keep_their_status_codes(self):
        missing = reward_units._extract_unit_usd({"total": 1.0})
        self.assertEqual(missing[1], "missing_unit_calibration")
        invalid = reward_units._extract_unit_usd({"unit_usd": 0, "total": 1.0})
        self.assertEqual(invalid[1], "invalid_structured_unit_usd")
        calibration = {"source_unit_usd": float("nan"), "evidence_ref": "ref"}
        with self.assertRaisesRegex(
            reward_parse.RewardOntologyError, "source_unit_usd must be positive"
        ):
            reward_units._normalize_calibration(calibration)

    def test_nested_nonfinite_record_values_remain_rejected(self):
        with self.assertRaisesRegex(
            reward_parse.RewardOntologyError, "non-finite JSON number"
        ):
            reward_parse._reject_nonfinite_numbers(
                {"reward_components": {"total": math.inf}},
                where="record.jsonl",
            )


class SignatureEscapingTests(unittest.TestCase):
    def test_noncanonical_escapes_cannot_select_arithmetic_methods(self):
        arithmetic = {"declared_total_field": "total", "weights_field": "weights"}
        signatures = (r"\total:int", r"total:\int", "total:int\\", r"total:int|\weights:object")
        for signature in signatures:
            with self.subTest(signature=signature):
                with self.assertRaisesRegex(
                    reward_parse.RewardOntologyError,
                    "shape: signature contains an invalid member",
                ):
                    reward_parse._arithmetic_methods_for_signature(signature, arithmetic, "shape")

    def test_canonical_escaped_keys_roundtrip_without_aliasing(self):
        keys = (r"\total", "a|b", "a:b", "trailing\\", "total")
        for key in keys:
            with self.subTest(key=key):
                signature = reward_parse._escape_signature_token(key) + ":int"
                self.assertEqual(reward_parse._signature_members(signature, "shape"), {key: "int"})


if __name__ == "__main__":
    unittest.main()
