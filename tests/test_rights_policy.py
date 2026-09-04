#!/usr/bin/env python3
"""Fail-closed behavior tests for rights-policy v1."""

# pylint: disable=too-many-lines

from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
import sys
import tempfile
import unittest
from collections.abc import Mapping
from contextlib import contextmanager
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


def mutable_policy_document():
    """Return a mutable copy decoded from the committed policy bytes."""
    return json.loads(rights_policy.RIGHTS_POLICY_BYTES)


def plain_policy_value(value):
    """Convert the exported immutable tree to ordinary JSON containers."""
    if isinstance(value, Mapping):
        return {key: plain_policy_value(item) for key, item in value.items()}
    if isinstance(value, tuple):
        return [plain_policy_value(item) for item in value]
    return value


@contextmanager
def mutated_loaded_policy():
    """Attempt mutation, then restore mutable implementations for test isolation."""
    profile = _policy_item(
        "profiles", rights_policy.HOSTED_FRONTIER_PROFILE_ID
    )
    rule = _policy_item("rules", "HOSTED_ANTHROPIC_CONSUMER")
    original_profile = plain_policy_value(profile)
    original_rule = plain_policy_value(rule)
    try:
        _assert_policy_mutations_rejected(profile, rule)
        yield
    finally:
        _restore_policy(profile, rule, original_profile, original_rule)


def _policy_item(collection: str, identifier: str):
    item = next(
        (
            candidate
            for candidate in rights_policy.RIGHTS_POLICY[collection]
            if candidate["id"] == identifier
        ),
        None,
    )
    if item is None:
        raise AssertionError(f"missing policy test fixture {identifier}")
    return item


def _assert_policy_mutations_rejected(profile, rule):
    attempts = (
        (
            "profile verdict",
            lambda: profile.update(
                intended_use="training_candidate",
                project_training_policy="allowed",
            ),
        ),
        (
            "profile evidence statuses",
            lambda: profile["evidence_statuses"].update(
                {field: "allowed" for field in rights_policy.EVIDENCE_STATUS_FIELDS}
            ),
        ),
        (
            "rule verdict",
            lambda: rule.update(
                intended_use="training_candidate",
                project_training_policy="allowed",
                reason_codes=["UNKNOWN_PROVENANCE"],
            ),
        ),
    )
    for label, mutate in attempts:
        try:
            mutate()
        except (AttributeError, TypeError):
            continue
        raise AssertionError(f"loaded policy mutation unexpectedly succeeded: {label}")


def _restore_policy(profile, rule, original_profile, original_rule):
    try:
        profile.clear()
        profile.update(original_profile)
        rule.clear()
        rule.update(original_rule)
    except (AttributeError, TypeError):
        pass


class RightsPolicyTestCase(unittest.TestCase):
    SOURCE_BYTES = b'{"id":"record-1"}\n'
    REGISTRY_BYTES = b'{"schema_version":"factory-registry-v0.1"}\n'
    SOURCE_SHA256 = digest(SOURCE_BYTES)
    REGISTRY_SHA256 = digest(REGISTRY_BYTES)

    def route(self, provider="anthropic", channel="consumer", profile=None):
        return rights_classifier.RightsRoute(
            provider=provider,
            channel=channel,
            rights_profile_id=(
                profile
                if profile is not None
                else rights_policy.HOSTED_FRONTIER_PROFILE_ID
            ),
        )

    def classify(self, provider="anthropic", channel="consumer", profile=None):
        return rights_classifier.classify_rights(
            self.route(provider, channel, profile),
            source_sha256=self.SOURCE_SHA256,
            factory_registry_sha256=self.REGISTRY_SHA256,
        )

    def verification(self, *, route=None, policy_bytes=None):
        return rights_classifier.RightsVerification(
            expected_route=self.route() if route is None else route,
            policy_bytes=policy_bytes,
        )

    def write_bytes(self, directory: str, name: str, payload: bytes) -> Path:
        path = Path(directory) / name
        path.write_bytes(payload)
        return path


@unittest.skipIf(RIGHTS_POLICY_SPEC is None, "rights policy runtime is not implemented")
class RightsPolicyTests(RightsPolicyTestCase):

    def test_committed_policy_is_loaded_and_bound_to_its_exact_bytes(self):
        document = json.loads(MAPPING.read_text(encoding="utf-8"))

        self.assertEqual(plain_policy_value(rights_policy.RIGHTS_POLICY), document)
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

    def test_classification_accepts_explicit_route_keywords(self):
        decision = rights_classifier.classify_rights(
            provider="anthropic",
            channel="consumer",
            rights_profile_id=rights_policy.HOSTED_FRONTIER_PROFILE_ID,
            source_sha256=self.SOURCE_SHA256,
            factory_registry_sha256=self.REGISTRY_SHA256,
        )

        self.assertEqual(decision, self.classify())

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
        document = mutable_policy_document()
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
        with mutated_loaded_policy():
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
                    verification=self.verification(policy_bytes=MAPPING.read_bytes()),
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

    def test_compiled_authorizations_have_no_writable_instance_dict(self):
        authorization = self.classify().authorization

        with self.assertRaises(AttributeError):
            authorization.__dict__
        with self.assertRaises(AttributeError):
            authorization.evidence_statuses.__dict__

    def test_decision_is_immutable(self):
        decision = self.classify()

        # Frozen slotted dataclasses raise either exception across supported
        # Python releases when assigning a delegated attribute.
        with self.assertRaises((FrozenInstanceError, TypeError)):
            decision.project_training_policy = "allowed"
        with self.assertRaises(TypeError):
            decision.public_payload["project_training_policy"] = "allowed"
        with self.assertRaises(TypeError):
            decision.public_payload["reason_codes"][0] = "UNKNOWN_PROVENANCE"

    def test_policy_validation_rejects_identity_and_exact_vocabulary_drift(self):
        cases = []
        for field, value in (
            ("document_type", "other_policy"),
            ("policy_version", "rights-policy-v2"),
            ("mapping_version", "rights-mapping-v2"),
        ):
            document = mutable_policy_document()
            document[field] = value
            cases.append(document)

        for vocabulary, value in (
            ("providers", ["anthropic", "meta", "openai"]),
            ("channels", ["api", "consumer", "enterprise", "local", "other"]),
            ("intended_use", ["research_only"]),
            ("project_training_policy", ["allowed", "blocked", "maybe"]),
            ("evidence_status", ["allowed", "restricted"]),
        ):
            document = mutable_policy_document()
            document["vocabularies"][vocabulary] = value
            cases.append(document)

        for document in cases:
            with self.subTest(document=document):
                with self.assertRaises(rights_policy.RightsPolicyError):
                    rights_policy.validate_rights_policy(document)

    def test_policy_validation_rejects_duplicate_ids(self):
        for collection in ("profiles", "rules", "reason_codes"):
            document = mutable_policy_document()
            document[collection].append(copy.deepcopy(document[collection][0]))
            with self.subTest(collection=collection):
                with self.assertRaisesRegex(
                    rights_policy.RightsPolicyError, "duplicate"
                ):
                    rights_policy.validate_rights_policy(document)

    def test_policy_validation_rejects_missing_or_extra_status_fields(self):
        for status_change in ("missing", "extra"):
            document = mutable_policy_document()
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
        orphan = mutable_policy_document()
        orphan["reason_codes"].append(
            {"id": "UNUSED_REASON", "description": "never emitted"}
        )
        with self.assertRaisesRegex(rights_policy.RightsPolicyError, "not covered"):
            rights_policy.validate_rights_policy(orphan)

        uncatalogued = mutable_policy_document()
        uncatalogued["rules"][0]["reason_codes"] = ["NOT_CATALOGUED"]
        with self.assertRaisesRegex(
            rights_policy.RightsPolicyError, "unknown reason"
        ):
            rights_policy.validate_rights_policy(uncatalogued)

    def test_policy_validation_requires_provider_coverage(self):
        document = mutable_policy_document()
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

    def test_policy_validation_requires_a_path_for_every_required_profile(self):
        document = mutable_policy_document()
        document["rules"] = [
            rule
            for rule in document["rules"]
            if rule["rights_profile_id"]
            != rights_policy.UNKNOWN_PROVENANCE_PROFILE_ID
        ]
        hosted_profile = next(
            profile
            for profile in document["profiles"]
            if profile["id"] == rights_policy.HOSTED_FRONTIER_PROFILE_ID
        )
        hosted_profile["reason_codes"].append("UNKNOWN_PROVENANCE")
        for rule in document["rules"]:
            rule["reason_codes"].append("UNKNOWN_PROVENANCE")

        checks = (
            ("object validation", lambda: rights_policy.validate_rights_policy(document)),
            (
                "byte loading",
                lambda: rights_policy.load_rights_policy_bytes(
                    json.dumps(document).encode("utf-8")
                ),
            ),
        )
        for label, check in checks:
            with self.subTest(check=label):
                with self.assertRaisesRegex(
                    rights_policy.RightsPolicyError,
                    "required profile.*authorization path",
                ):
                    check()

    def test_required_profiles_retain_their_defining_reason_codes(self):
        document = mutable_policy_document()
        profiles = {
            profile["id"]: profile
            for profile in document["profiles"]
        }
        hosted_id = rights_policy.HOSTED_FRONTIER_PROFILE_ID
        fallback_id = rights_policy.UNKNOWN_PROVENANCE_PROFILE_ID
        profiles[hosted_id]["reason_codes"] = ["UNKNOWN_PROVENANCE"]
        profiles[fallback_id]["reason_codes"] = ["HOSTED_FRONTIER_RESEARCH_ONLY"]
        for rule in document["rules"]:
            if rule["rights_profile_id"] == hosted_id:
                rule["reason_codes"] = ["UNKNOWN_PROVENANCE"]
            elif rule["rights_profile_id"] == fallback_id:
                rule["reason_codes"] = ["HOSTED_FRONTIER_RESEARCH_ONLY"]

        with self.assertRaisesRegex(
            rights_policy.RightsPolicyError,
            "required defining reason",
        ):
            rights_policy.validate_rights_policy(document)

    def test_unknown_provenance_rule_covers_every_provider_channel_route(self):
        document = mutable_policy_document()
        fallback = next(
            rule
            for rule in document["rules"]
            if rule["rights_profile_id"]
            == rights_policy.UNKNOWN_PROVENANCE_PROFILE_ID
        )
        fallback["providers"] = ["xai"]
        fallback["channels"] = ["local"]

        with self.assertRaisesRegex(
            rights_policy.RightsPolicyError,
            "unknown-provenance.*provider/channel coverage",
        ):
            rights_policy.validate_rights_policy(document)

    def test_direct_policy_validation_rejects_unpaired_surrogates(self):
        document = mutable_policy_document()
        document["reason_codes"][0]["description"] = "invalid-\ud800"

        with self.assertRaisesRegex(
            rights_policy.RightsPolicyError,
            "invalid rights policy Unicode.*unpaired surrogate",
        ):
            rights_policy.validate_rights_policy(document)

    def test_policy_validation_rejects_profile_or_rule_verdict_drift(self):
        inconsistent_profile = mutable_policy_document()
        inconsistent_profile["profiles"][1]["project_training_policy"] = "allowed"
        with self.assertRaisesRegex(rights_policy.RightsPolicyError, "inconsistent"):
            rights_policy.validate_rights_policy(inconsistent_profile)

        drifting_rule = mutable_policy_document()
        drifting_rule["rules"][0]["project_training_policy"] = "allowed"
        with self.assertRaisesRegex(
            rights_policy.RightsPolicyError, "outside profile"
        ):
            rights_policy.validate_rights_policy(drifting_rule)

    def test_hosted_profile_must_keep_all_evidence_unresolved(self):
        document = mutable_policy_document()
        document["profiles"].reverse()
        hosted_profile = next(
            profile
            for profile in document["profiles"]
            if profile["id"] == rights_policy.HOSTED_FRONTIER_PROFILE_ID
        )
        hosted_profile["evidence_statuses"][
            "provider_training_status"
        ] = "allowed"

        with self.assertRaisesRegex(
            rights_policy.RightsPolicyError, "hosted-frontier.*unresolved"
        ):
            rights_policy.validate_rights_policy(document)

    def test_explicit_loader_rejects_every_malformed_input_class(self):
        with self.assertRaisesRegex(
            rights_policy.RightsPolicyError,
            "policy path",
        ):
            rights_policy.load_rights_policy(1)
        with self.assertRaisesRegex(
            rights_policy.RightsPolicyError,
            "policy input must be bytes",
        ):
            rights_policy.load_rights_policy_bytes("not bytes")
        for invalid_path in ("\x00", "\ud800"):
            with self.subTest(invalid_path=ascii(invalid_path)):
                with self.assertRaisesRegex(
                    rights_policy.RightsPolicyError,
                    "rights policy is unreadable",
                ):
                    rights_policy.load_rights_policy(invalid_path)

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

class RightsPolicyAvailabilityTests(unittest.TestCase):
    def test_rights_policy_runtime_exists(self):
        self.assertIsNotNone(
            RIGHTS_POLICY_SPEC,
            "rights_policy runtime does not exist yet",
        )


if __name__ == "__main__":
    unittest.main()
