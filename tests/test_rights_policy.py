#!/usr/bin/env python3
"""Fail-closed behavior tests for rights-policy v1."""

from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from dataclasses import FrozenInstanceError
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
PIPELINES = ROOT / "pipelines"
MAPPING = ROOT / "schemas" / "rights-policy-v1.mapping.json"

if str(PIPELINES) not in sys.path:
    sys.path.insert(0, str(PIPELINES))


RIGHTS_POLICY_SPEC = importlib.util.find_spec("rights_policy")
if RIGHTS_POLICY_SPEC is not None:
    import rights_classifier
    import rights_policy
else:  # The first RED is a missing behavior, not an import-time test error.
    rights_classifier = None
    rights_policy = None


def digest(payload: bytes) -> str:
    return "sha256:" + hashlib.sha256(payload).hexdigest()


@unittest.skipIf(RIGHTS_POLICY_SPEC is None, "rights policy runtime is not implemented")
class RightsPolicyTests(unittest.TestCase):
    SOURCE_BYTES = b'{"id":"record-1"}\n'
    REGISTRY_BYTES = b'{"schema_version":"factory-registry-v0.1"}\n'
    SOURCE_SHA256 = digest(SOURCE_BYTES)
    REGISTRY_SHA256 = digest(REGISTRY_BYTES)

    def classify(self, provider="anthropic", channel="consumer", profile=None):
        return rights_classifier.classify_rights(
            provider=provider,
            channel=channel,
            rights_profile_id=(
                profile or rights_policy.HOSTED_FRONTIER_PROFILE_ID
            ),
            source_sha256=self.SOURCE_SHA256,
            factory_registry_sha256=self.REGISTRY_SHA256,
        )

    def write_bytes(self, directory: str, name: str, payload: bytes) -> Path:
        path = Path(directory) / name
        path.write_bytes(payload)
        return path

    def test_committed_policy_is_loaded_and_bound_to_its_exact_bytes(self):
        document = json.loads(MAPPING.read_text(encoding="utf-8"))

        self.assertEqual(rights_policy.RIGHTS_POLICY, document)
        self.assertEqual(
            rights_policy.RIGHTS_POLICY_SHA256,
            digest(MAPPING.read_bytes()),
        )
        self.assertEqual(
            set(document["vocabularies"]["providers"]),
            {"anthropic", "meta", "openai", "xai"},
        )
        self.assertEqual(
            set(document["vocabularies"]["channels"]),
            {"consumer", "api", "enterprise", "local"},
        )
        self.assertEqual(
            document["evidence_status_fields"],
            [
                "research_retention_status",
                "research_evaluation_status",
                "redistribution_status",
                "provider_training_status",
                "weight_publication_status",
            ],
        )
        self.assertEqual(
            document["invariants"]["provider_training_status"],
            "evidence_only",
        )

    def test_each_canonical_hosted_provider_gets_the_static_blocked_decision(self):
        cases = {
            "anthropic": "consumer",
            "meta": "api",
            "openai": "consumer",
            "xai": "consumer",
        }
        for provider, channel in cases.items():
            with self.subTest(provider=provider):
                decision = self.classify(provider, channel)
                expected = {
                    "rights_profile_id": "hosted-frontier-research-only-v1",
                    "provider": provider,
                    "channel": channel,
                    "intended_use": "research_only",
                    "project_training_policy": "blocked",
                    "research_retention_status": "unresolved",
                    "research_evaluation_status": "unresolved",
                    "redistribution_status": "unresolved",
                    "provider_training_status": "unresolved",
                    "weight_publication_status": "unresolved",
                    "reason_codes": ["HOSTED_FRONTIER_RESEARCH_ONLY"],
                    "source_sha256": self.SOURCE_SHA256,
                    "factory_registry_sha256": self.REGISTRY_SHA256,
                    "rights_policy_sha256": digest(MAPPING.read_bytes()),
                }
                self.assertEqual(decision.to_public_payload(), expected)

    def test_unknown_provenance_has_an_explicit_fail_closed_path(self):
        decision = self.classify(
            "xai", "local", rights_policy.UNKNOWN_PROVENANCE_PROFILE_ID
        )

        self.assertEqual(decision.intended_use, "research_only")
        self.assertEqual(decision.project_training_policy, "blocked")
        self.assertEqual(decision.reason_codes, ("UNKNOWN_PROVENANCE",))
        self.assertEqual(
            {
                decision.research_retention_status,
                decision.research_evaluation_status,
                decision.redistribution_status,
                decision.provider_training_status,
                decision.weight_publication_status,
            },
            {"unresolved"},
        )

    def test_provider_training_evidence_cannot_promote_project_policy(self):
        document = copy.deepcopy(rights_policy.RIGHTS_POLICY)
        profile = next(
            item
            for item in document["profiles"]
            if item["id"] == rights_policy.UNKNOWN_PROVENANCE_PROFILE_ID
        )
        profile["evidence_statuses"]["provider_training_status"] = "allowed"

        validated = rights_policy.validate_rights_policy(document)

        self.assertEqual(
            profile["evidence_statuses"]["provider_training_status"], "allowed"
        )
        self.assertEqual(profile["project_training_policy"], "blocked")
        self.assertIs(validated, document)

    def test_mutating_loaded_policy_cannot_change_or_validate_bound_decision(self):
        profile = next(
            item
            for item in rights_policy.RIGHTS_POLICY["profiles"]
            if item["id"] == rights_policy.HOSTED_FRONTIER_PROFILE_ID
        )
        rule = next(
            item
            for item in rights_policy.RIGHTS_POLICY["rules"]
            if item["id"] == "HOSTED_ANTHROPIC_CONSUMER"
        )
        original_profile = copy.deepcopy(profile)
        original_rule = copy.deepcopy(rule)
        try:
            try:
                profile.update(
                    intended_use="training_candidate",
                    project_training_policy="allowed",
                )
                profile["evidence_statuses"].update(
                    {
                        field: "allowed"
                        for field in rights_policy.EVIDENCE_STATUS_FIELDS
                    }
                )
                rule.update(
                    intended_use="training_candidate",
                    project_training_policy="allowed",
                    reason_codes=["UNKNOWN_PROVENANCE"],
                )
            except (AttributeError, TypeError):
                # Deep-freezing is also a valid way to seal the imported state.
                pass

            decision = self.classify()
            promoted = decision.to_public_payload()
            promoted.update(
                intended_use="training_candidate",
                project_training_policy="allowed",
                research_retention_status="allowed",
                research_evaluation_status="allowed",
                redistribution_status="allowed",
                provider_training_status="allowed",
                weight_publication_status="allowed",
                reason_codes=["UNKNOWN_PROVENANCE"],
            )

            with self.assertRaises(rights_policy.RightsPolicyError):
                rights_classifier.verify_rights_envelope(
                    promoted,
                    source_bytes=self.SOURCE_BYTES,
                    factory_registry_bytes=self.REGISTRY_BYTES,
                    policy_bytes=MAPPING.read_bytes(),
                )
            self.assertEqual(
                (
                    decision.intended_use,
                    decision.project_training_policy,
                    decision.provider_training_status,
                    decision.reason_codes,
                ),
                (
                    "research_only",
                    "blocked",
                    "unresolved",
                    ("HOSTED_FRONTIER_RESEARCH_ONLY",),
                ),
            )
        finally:
            try:
                profile.clear()
                profile.update(original_profile)
                rule.clear()
                rule.update(original_rule)
            except (AttributeError, TypeError):
                pass

    def test_decision_is_immutable(self):
        decision = self.classify()

        with self.assertRaises(FrozenInstanceError):
            decision.project_training_policy = "allowed"
        with self.assertRaises(TypeError):
            decision.public_payload["project_training_policy"] = "allowed"

    def test_policy_validation_rejects_identity_and_exact_vocabulary_drift(self):
        cases = []
        for field, value in (
            ("document_type", "other_policy"),
            ("policy_version", "rights-policy-v2"),
            ("mapping_version", "rights-mapping-v2"),
        ):
            document = copy.deepcopy(rights_policy.RIGHTS_POLICY)
            document[field] = value
            cases.append(document)

        for vocabulary, value in (
            ("providers", ["anthropic", "meta", "openai"]),
            ("channels", ["api", "consumer", "enterprise", "local", "other"]),
            ("intended_use", ["research_only"]),
            ("project_training_policy", ["allowed", "blocked", "maybe"]),
            ("evidence_status", ["allowed", "restricted"]),
        ):
            document = copy.deepcopy(rights_policy.RIGHTS_POLICY)
            document["vocabularies"][vocabulary] = value
            cases.append(document)

        for document in cases:
            with self.subTest(document=document):
                with self.assertRaises(rights_policy.RightsPolicyError):
                    rights_policy.validate_rights_policy(document)

    def test_policy_validation_rejects_duplicate_ids(self):
        for collection in ("profiles", "rules", "reason_codes"):
            document = copy.deepcopy(rights_policy.RIGHTS_POLICY)
            document[collection].append(copy.deepcopy(document[collection][0]))
            with self.subTest(collection=collection):
                with self.assertRaisesRegex(
                    rights_policy.RightsPolicyError, "duplicate"
                ):
                    rights_policy.validate_rights_policy(document)

    def test_policy_validation_rejects_missing_or_extra_status_fields(self):
        for status_change in ("missing", "extra"):
            document = copy.deepcopy(rights_policy.RIGHTS_POLICY)
            statuses = document["profiles"][0]["evidence_statuses"]
            if status_change == "missing":
                statuses.pop("redistribution_status")
            else:
                statuses["copyright_status"] = "unresolved"
            with self.subTest(status_change=status_change):
                with self.assertRaisesRegex(
                    rights_policy.RightsPolicyError,
                    "evidence status fields",
                ):
                    rights_policy.validate_rights_policy(document)

    def test_policy_validation_rejects_uncovered_or_unknown_reasons(self):
        orphan = copy.deepcopy(rights_policy.RIGHTS_POLICY)
        orphan["reason_codes"].append(
            {"id": "UNUSED_REASON", "description": "never emitted"}
        )
        with self.assertRaisesRegex(rights_policy.RightsPolicyError, "not covered"):
            rights_policy.validate_rights_policy(orphan)

        uncatalogued = copy.deepcopy(rights_policy.RIGHTS_POLICY)
        uncatalogued["rules"][0]["reason_codes"] = ["NOT_CATALOGUED"]
        with self.assertRaisesRegex(
            rights_policy.RightsPolicyError, "unknown reason"
        ):
            rights_policy.validate_rights_policy(uncatalogued)

    def test_policy_validation_requires_provider_coverage(self):
        document = copy.deepcopy(rights_policy.RIGHTS_POLICY)
        for rule in document["rules"]:
            if rule["providers"] == ["anthropic"]:
                rule["providers"] = ["meta"]
            else:
                rule["providers"] = [
                    provider
                    for provider in rule["providers"]
                    if provider != "anthropic"
                ]

        with self.assertRaisesRegex(rights_policy.RightsPolicyError, "provider coverage"):
            rights_policy.validate_rights_policy(document)

    def test_policy_validation_rejects_profile_or_rule_verdict_drift(self):
        inconsistent_profile = copy.deepcopy(rights_policy.RIGHTS_POLICY)
        inconsistent_profile["profiles"][1]["project_training_policy"] = "allowed"
        with self.assertRaisesRegex(rights_policy.RightsPolicyError, "inconsistent"):
            rights_policy.validate_rights_policy(inconsistent_profile)

        drifting_rule = copy.deepcopy(rights_policy.RIGHTS_POLICY)
        drifting_rule["rules"][0]["project_training_policy"] = "allowed"
        with self.assertRaisesRegex(
            rights_policy.RightsPolicyError, "outside profile"
        ):
            rights_policy.validate_rights_policy(drifting_rule)

    def test_hosted_profile_must_keep_all_evidence_unresolved(self):
        document = copy.deepcopy(rights_policy.RIGHTS_POLICY)
        document["profiles"][0]["evidence_statuses"][
            "provider_training_status"
        ] = "allowed"

        with self.assertRaisesRegex(
            rights_policy.RightsPolicyError, "hosted-frontier.*unresolved"
        ):
            rights_policy.validate_rights_policy(document)

    def test_explicit_loader_rejects_every_malformed_input_class(self):
        with tempfile.TemporaryDirectory() as directory:
            malformed = {
                "non-utf-8.json": b"\xff",
                "duplicate.json": b'{"document_type":"a","document_type":"b"}',
                "non-finite.json": b'{"number":1e400}',
                "constant.json": b'{"number":NaN}',
                "malformed.json": b"{not json",
                "incomplete.json": b"{}",
                "surrogate.json": b'{"document_type":"\\ud800"}',
            }
            for name, payload in malformed.items():
                path = self.write_bytes(directory, name, payload)
                with self.subTest(name=name):
                    with self.assertRaises(rights_policy.RightsPolicyError):
                        rights_policy.load_rights_policy(path)

            missing = Path(directory) / "missing.json"
            with self.assertRaises(rights_policy.RightsPolicyError):
                rights_policy.load_rights_policy(missing)
            with self.assertRaises(rights_policy.RightsPolicyError):
                rights_policy.load_rights_policy(Path(directory))

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
        result = subprocess.run(
            [sys.executable, "-c", script],
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_classification_rejects_malformed_hashes(self):
        for field in ("source_sha256", "factory_registry_sha256"):
            arguments = {
                "provider": "anthropic",
                "channel": "consumer",
                "rights_profile_id": rights_policy.HOSTED_FRONTIER_PROFILE_ID,
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


class RightsPolicyAvailabilityTests(unittest.TestCase):
    def test_rights_policy_runtime_exists(self):
        self.assertIsNotNone(
            RIGHTS_POLICY_SPEC,
            "rights_policy runtime does not exist yet",
        )


if __name__ == "__main__":
    unittest.main()
