#!/usr/bin/env python3
"""Focused guard-branch tests for the fail-closed rights policy."""

# pylint: disable=missing-class-docstring,missing-function-docstring

from __future__ import annotations

import copy
import unittest

from test_rights_policy import (
    RIGHTS_POLICY_SPEC,
    _policy_item,
    mutable_policy_document,
    rights_policy,
)


@unittest.skipIf(RIGHTS_POLICY_SPEC is None, "rights policy runtime is not implemented")
class RightsPolicyGuardTests(unittest.TestCase):
    def test_loaded_policy_tree_is_immutable(self):
        original_version = rights_policy.RIGHTS_POLICY["mapping_version"]
        try:
            with self.assertRaises(TypeError):
                rights_policy.RIGHTS_POLICY["mapping_version"] = "rights-mapping-v2"
        finally:
            try:
                rights_policy.RIGHTS_POLICY["mapping_version"] = original_version
            except TypeError:
                pass

        profile = _policy_item(
            "profiles", rights_policy.HOSTED_FRONTIER_PROFILE_ID
        )
        original_use = profile["intended_use"]
        try:
            with self.assertRaises(TypeError):
                profile["intended_use"] = "other"
        finally:
            try:
                profile["intended_use"] = original_use
            except TypeError:
                pass

        rules = rights_policy.RIGHTS_POLICY["rules"]
        original_length = len(rules)
        try:
            with self.assertRaises(AttributeError):
                rules.append({})
        finally:
            while len(rules) > original_length:
                rules.pop()

    def test_initialized_authorization_state_cannot_be_restored(self):
        authorization = next(iter(rights_policy.RIGHTS_AUTHORIZATIONS.values()))
        statuses = authorization.evidence_statuses
        attempts = (
            (
                authorization,
                [
                    "training_candidate",
                    "allowed",
                    statuses,
                    authorization.reason_codes,
                ],
            ),
            (statuses, ["allowed"] * len(rights_policy.EVIDENCE_STATUS_FIELDS)),
        )
        for target, replacement in attempts:
            slots = type(target).__slots__
            original = [object.__getattribute__(target, name) for name in slots]
            try:
                with self.subTest(target=type(target).__name__):
                    with self.assertRaisesRegex(TypeError, "initialized"):
                        target.__setstate__(replacement)
            finally:
                for name, value in zip(slots, original, strict=True):
                    object.__setattr__(target, name, value)

        self.assertEqual(copy.deepcopy(authorization), authorization)

    def test_policy_validation_requires_hosted_provider_coverage(self):
        document = mutable_policy_document()
        document["rules"] = [
            rule
            for rule in document["rules"]
            if rule["id"] != "HOSTED_ANTHROPIC_CONSUMER"
        ]

        with self.assertRaisesRegex(
            rights_policy.RightsPolicyError,
            "hosted rules.*provider coverage",
        ):
            rights_policy.validate_rights_policy(document)

    def test_policy_validation_rejects_duplicate_authorized_combinations(self):
        document = mutable_policy_document()
        duplicate = copy.deepcopy(document["rules"][0])
        duplicate["id"] = "HOSTED_ANTHROPIC_CONSUMER_DUPLICATE"
        document["rules"].append(duplicate)

        with self.assertRaisesRegex(
            rights_policy.RightsPolicyError,
            "duplicate authorized combination",
        ):
            rights_policy.validate_rights_policy(document)

    def test_policy_validation_rejects_unknown_rule_route_values(self):
        for field, value in (
            ("providers", ["unknown-provider"]),
            ("channels", ["unknown-channel"]),
        ):
            document = mutable_policy_document()
            document["rules"][0][field] = value
            with self.subTest(field=field):
                with self.assertRaisesRegex(
                    rights_policy.RightsPolicyError,
                    f"unknown {field}",
                ):
                    rights_policy.validate_rights_policy(document)

    def test_policy_validation_requires_every_declared_profile(self):
        document = mutable_policy_document()
        document["profiles"].pop()

        with self.assertRaisesRegex(
            rights_policy.RightsPolicyError,
            "profiles must declare every required profile",
        ):
            rights_policy.validate_rights_policy(document)

    def test_policy_validation_rejects_malformed_unique_string_lists(self):
        hosted = rights_policy.HOSTED_FRONTIER_PROFILE_ID
        cases = (
            "not-a-list",
            [],
            [hosted, hosted],
            ["   "],
            [1],
        )
        for required_profile_ids in cases:
            document = mutable_policy_document()
            document["required_profile_ids"] = required_profile_ids
            with self.subTest(required_profile_ids=required_profile_ids):
                with self.assertRaisesRegex(
                    rights_policy.RightsPolicyError,
                    "required_profile_ids must be a unique nonempty list of strings",
                ):
                    rights_policy.validate_rights_policy(document)

    def test_policy_validation_rejects_extra_shape_and_invariant_drift(self):
        cases = (
            lambda document: document.update(unexpected=True),
            lambda document: document["vocabularies"].update(unexpected=[]),
            lambda document: document["invariants"].update(unexpected=True),
            lambda document: document["invariants"].update(
                provider_training_status="policy_controlled"
            ),
            lambda document: document.update(invariants=[]),
        )
        for index, mutate in enumerate(cases):
            document = mutable_policy_document()
            mutate(document)
            with self.subTest(case=index):
                with self.assertRaises(rights_policy.RightsPolicyError):
                    rights_policy.validate_rights_policy(document)

    def test_policy_byte_loader_rejects_payloads_over_the_explicit_limit(self):
        payload = b" " * (rights_policy.MAX_RIGHTS_JSON_BYTES + 1)

        with self.assertRaisesRegex(
            rights_policy.RightsPolicyError,
            "exceeds the .*byte rights JSON limit",
        ):
            rights_policy.load_rights_policy_bytes(payload)


if __name__ == "__main__":
    unittest.main()
