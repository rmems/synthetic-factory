#!/usr/bin/env python3
"""Focused guard-branch tests for the fail-closed rights policy."""

# pylint: disable=missing-class-docstring,missing-function-docstring

from __future__ import annotations

import copy
import unittest

from test_rights_policy import (
    RIGHTS_POLICY_SPEC,
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

        profile = next(
            item
            for item in rights_policy.RIGHTS_POLICY["profiles"]
            if item["id"] == rights_policy.HOSTED_FRONTIER_PROFILE_ID
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


if __name__ == "__main__":
    unittest.main()
