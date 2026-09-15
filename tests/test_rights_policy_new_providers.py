#!/usr/bin/env python3
"""Fail-closed behavior for the local and placeholder rights profiles."""

from __future__ import annotations

import unittest

from test_rights_policy import (
    RIGHTS_POLICY_SPEC,
    RightsPolicyTestCase,
    mutable_policy_document,
    rights_policy,
)


@unittest.skipIf(RIGHTS_POLICY_SPEC is None, "rights policy runtime is not implemented")
class RightsPolicyNewProviderTests(RightsPolicyTestCase):
    def test_new_local_and_placeholder_profiles_keep_defining_reason_codes(self):
        cases = (
            (
                "procedural",
                "local",
                rights_policy.PROCEDURAL_PROFILE_ID,
                "training_candidate",
                "allowed",
                ("PROCEDURAL_ATTESTED_LOCAL",),
            ),
            (
                "simulator",
                "local",
                rights_policy.SIMULATOR_PROFILE_ID,
                "training_candidate",
                "allowed",
                ("SIMULATOR_ORACLE_PINNED",),
            ),
            (
                "deepseek",
                "api",
                rights_policy.DEEPSEEK_PLACEHOLDER_PROFILE_ID,
                "research_only",
                "blocked",
                ("DEEPSEEK_TERMS_SNAPSHOT_PENDING",),
            ),
            (
                "nemotron",
                "api",
                rights_policy.NEMOTRON_PLACEHOLDER_PROFILE_ID,
                "research_only",
                "blocked",
                ("NEMOTRON_TERMS_SNAPSHOT_PENDING",),
            ),
        )
        for provider, channel, profile, intended_use, policy, reasons in cases:
            with self.subTest(provider=provider):
                decision = self.classify(provider, channel, profile)
                self.assertEqual(decision.intended_use, intended_use)
                self.assertEqual(decision.project_training_policy, policy)
                self.assertEqual(decision.reason_codes, reasons)
                self.assertEqual(decision.rights_profile_id, profile)

        blocked_unknown = self.classify(
            "procedural", "consumer", rights_policy.UNKNOWN_PROVENANCE_PROFILE_ID
        )
        self.assertEqual(blocked_unknown.intended_use, "research_only")
        self.assertEqual(blocked_unknown.project_training_policy, "blocked")
        self.assertEqual(blocked_unknown.reason_codes, ("UNKNOWN_PROVENANCE",))

    def test_placeholder_profiles_stay_blocked_even_with_a_snapshot_hash(self):
        document = mutable_policy_document()
        profile = next(
            item
            for item in document["profiles"]
            if item["id"] == rights_policy.DEEPSEEK_PLACEHOLDER_PROFILE_ID
        )
        self.assertIsNone(profile[rights_policy.UNBLOCK_TERMS_SNAPSHOT_FIELD])
        profile[rights_policy.UNBLOCK_TERMS_SNAPSHOT_FIELD] = "sha256:" + "b" * 64
        validated = rights_policy.validate_rights_policy(document)
        self.assertEqual(profile["intended_use"], "research_only")
        self.assertEqual(profile["project_training_policy"], "blocked")
        self.assertIs(validated, document)

        profile["intended_use"] = "training_candidate"
        profile["project_training_policy"] = "allowed"
        with self.assertRaisesRegex(
            rights_policy.RightsPolicyError,
            "must remain a blocked terms placeholder",
        ):
            rights_policy.validate_rights_policy(document)

    def test_unauthorized_new_provider_hosted_frontier_route_fails_closed(self):
        with self.assertRaisesRegex(
            rights_policy.RightsPolicyError,
            "not authorized by policy",
        ):
            self.classify("procedural", "local", rights_policy.HOSTED_FRONTIER_PROFILE_ID)


if __name__ == "__main__":
    unittest.main()
