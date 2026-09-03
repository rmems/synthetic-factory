#!/usr/bin/env python3
"""Fail-closed behavior tests for rights-policy classification."""

# pylint: disable=missing-class-docstring,missing-function-docstring

from __future__ import annotations

import copy
import subprocess  # nosec B404 -- tests execute only a fixed Python interpreter.
import sys
import unittest

from test_rights_policy import (
    MAPPING,
    PIPELINES,
    RIGHTS_POLICY_SPEC,
    ROOT,
    RightsPolicyTestCase,
    rights_classifier,
    rights_policy,
)


@unittest.skipIf(RIGHTS_POLICY_SPEC is None, "rights policy runtime is not implemented")
class RightsClassifierTests(RightsPolicyTestCase):
    def test_classification_rejects_unknown_or_unauthorized_inputs(self):
        cases = (
            {"provider": "other"},
            {"channel": "other"},
            {"profile": "other-profile"},
            {"provider": "meta", "channel": "consumer"},
        )
        for overrides in cases:
            arguments = {
                "provider": "anthropic",
                "channel": "consumer",
                "profile": rights_policy.HOSTED_FRONTIER_PROFILE_ID,
            }
            arguments.update(overrides)
            with self.subTest(arguments=arguments):
                with self.assertRaises(rights_policy.RightsPolicyError):
                    self.classify(**arguments)

    def test_malformed_semantic_types_raise_rights_policy_error(self):
        with self.assertRaises(rights_policy.RightsPolicyError):
            self.classify(provider=[])

        mutations = (
            lambda document: document["profiles"][0].update(intended_use=[]),
            lambda document: document["profiles"][0]["evidence_statuses"].update(
                redistribution_status=[]
            ),
            lambda document: document["rules"][0].update(rights_profile_id=[]),
        )
        for mutate in mutations:
            document = copy.deepcopy(rights_policy.RIGHTS_POLICY)
            mutate(document)
            with self.subTest(document=document):
                with self.assertRaises(rights_policy.RightsPolicyError):
                    rights_policy.validate_rights_policy(document)

    def test_package_first_and_direct_imports_share_module_objects(self):
        script = f"""
import sys
sys.path.insert(0, {str(ROOT)!r})
sys.path.insert(1, {str(PIPELINES)!r})
import pipelines.rights_classifier as package_classifier
import pipelines.rights_policy as package_policy
import rights_classifier
import rights_policy
assert package_classifier is rights_classifier
assert package_policy is rights_policy
assert package_policy.RightsPolicyError is rights_policy.RightsPolicyError
"""
        result = subprocess.run(  # nosec B603 -- argv contains no untrusted input.
            [sys.executable, "-c", script],
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_classification_rejects_malformed_hashes(self):
        for field in ("source_sha256", "factory_registry_sha256"):
            arguments = {
                "route": rights_classifier.RightsRoute(
                    "anthropic",
                    "consumer",
                    rights_policy.HOSTED_FRONTIER_PROFILE_ID,
                ),
                "source_sha256": self.SOURCE_SHA256,
                "factory_registry_sha256": self.REGISTRY_SHA256,
            }
            arguments[field] = "sha256:" + "A" * 64
            with self.subTest(field=field):
                with self.assertRaises(rights_policy.RightsPolicyError):
                    rights_classifier.classify_rights(**arguments)

    def test_envelope_verification_recomputes_all_three_bound_digests(self):
        payload = self.classify().to_public_payload()

        verified = rights_classifier.verify_rights_envelope(
            payload,
            source_bytes=self.SOURCE_BYTES,
            factory_registry_bytes=self.REGISTRY_BYTES,
            policy_bytes=MAPPING.read_bytes(),
        )

        self.assertEqual(verified, self.classify())

        digest_cases = {
            "source_sha256": "source_sha256",
            "factory_registry_sha256": "factory_registry_sha256",
            "rights_policy_sha256": "rights_policy_sha256",
        }
        for field, label in digest_cases.items():
            altered = copy.deepcopy(payload)
            altered[field] = "sha256:" + "0" * 64
            with self.subTest(field=field):
                with self.assertRaisesRegex(rights_policy.RightsPolicyError, label):
                    rights_classifier.verify_rights_envelope(
                        altered,
                        source_bytes=self.SOURCE_BYTES,
                        factory_registry_bytes=self.REGISTRY_BYTES,
                        policy_bytes=MAPPING.read_bytes(),
                    )

        byte_cases = {
            "source": {
                "source_bytes": self.SOURCE_BYTES + b" ",
                "factory_registry_bytes": self.REGISTRY_BYTES,
                "policy_bytes": MAPPING.read_bytes(),
            },
            "registry": {
                "source_bytes": self.SOURCE_BYTES,
                "factory_registry_bytes": self.REGISTRY_BYTES + b" ",
                "policy_bytes": MAPPING.read_bytes(),
            },
            "policy": {
                "source_bytes": self.SOURCE_BYTES,
                "factory_registry_bytes": self.REGISTRY_BYTES,
                "policy_bytes": MAPPING.read_bytes() + b"\n",
            },
        }
        for label, arguments in byte_cases.items():
            with self.subTest(bound_bytes=label):
                with self.assertRaises(rights_policy.RightsPolicyError):
                    rights_classifier.verify_rights_envelope(payload, **arguments)

    def test_envelope_verification_rejects_every_policy_controlled_drift(self):
        payload = self.classify().to_public_payload()
        mutations = {
            "unknown reason": lambda item: item.update(
                reason_codes=["NOT_CATALOGUED"]
            ),
            "profile drift": lambda item: item.update(
                rights_profile_id=rights_policy.UNKNOWN_PROVENANCE_PROFILE_ID
            ),
            "verdict drift": lambda item: item.update(
                project_training_policy="allowed"
            ),
            "status drift": lambda item: item.update(
                provider_training_status="allowed"
            ),
            "combination drift": lambda item: item.update(
                provider="meta", channel="consumer"
            ),
            "extra field": lambda item: item.update(unbound=True),
        }
        for label, mutate in mutations.items():
            altered = copy.deepcopy(payload)
            mutate(altered)
            with self.subTest(label=label):
                with self.assertRaises(rights_policy.RightsPolicyError):
                    rights_classifier.verify_rights_envelope(
                        altered,
                        source_bytes=self.SOURCE_BYTES,
                        factory_registry_bytes=self.REGISTRY_BYTES,
                    )


if __name__ == "__main__":
    unittest.main()
