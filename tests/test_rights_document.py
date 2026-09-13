#!/usr/bin/env python3
"""Strict public ``rights.json`` 0.1.0 contract tests."""

from __future__ import annotations

import copy
import importlib.util
import json
import sys
import unittest
from pathlib import Path

from rights_test_support import SpoofedString


ROOT = Path(__file__).resolve().parent.parent
PIPELINES = ROOT / "pipelines"

if str(PIPELINES) not in sys.path:
    sys.path.insert(0, str(PIPELINES))


RIGHTS_DOCUMENT_SPEC = importlib.util.find_spec("rights_document")
if RIGHTS_DOCUMENT_SPEC is not None:
    import rights_document
    import rights_mapping
else:  # Keep the first RED focused on the missing production surface.
    rights_document = None
    rights_mapping = None


def anthropic_document() -> dict[str, object]:
    """Return a hand-authored literal equivalent to the public Fable sidecar."""

    return {
        "schema_version": "0.1.0",
        "dataset_id": "rmems/thalamic-relay-trajectories",
        "policy_source": "https://github.com/rmems/synthetic-factory/issues/161",
        "provider": "Anthropic",
        "model": "Claude Fable 5",
        "channel": "consumer",
        "subscription_plan": "Claude Max",
        "generation_surface": "Claude Code — Workflow tool subagents (Ultracode)",
        "generated_at": "2026-08-17/2026-08-18",
        "terms_document": None,
        "terms_effective_date": None,
        "terms_snapshot_sha256": None,
        "provider_output_attribution": (
            "Full contributor/role breakdown is preserved in provenance.json."
        ),
        "intended_use": "research_only",
        "project_training_policy": "blocked",
        "research_retention_status": "unresolved",
        "research_evaluation_status": "unresolved",
        "redistribution_status": "unresolved",
        "provider_training_status": "unresolved",
        "weight_publication_status": "unresolved",
        "status_basis": "Project policy is fail-closed pending terms evidence.",
        "reviewed_at": "2026-08-30",
        "original_release_license": "apache-2.0",
        "original_release_commit": "c9bb5444bd8c22550e0ddfaa2894203b38461656",
        "legacy_public_release": True,
        "notes": "Historical release provenance remains explicit.",
    }


def xai_document() -> dict[str, object]:
    """Return a hand-authored literal equivalent to the public Grok sidecar."""

    document = anthropic_document()
    document.update(
        dataset_id="rmems/api-contract-migration-trajectories",
        provider="xAI (SpaceXAI)",
        model="Grok 4.6",
        subscription_plan="SuperGrok Heavy",
        generation_surface="Grok Build — agentic factory snapshot lane",
        generated_at="2026-08-19 onward (see data/raw batch files)",
        original_release_commit="6d56463a88464c73a3f92bf320ecc2772233b8c3",
    )
    return document


def encode(document: object) -> bytes:
    return json.dumps(document, ensure_ascii=False).encode("utf-8")


class RightsDocumentRuntimeExistsTests(unittest.TestCase):
    def test_rights_document_runtime_exists(self):
        self.assertIsNotNone(
            RIGHTS_DOCUMENT_SPEC,
            "rights_document public-sidecar validator does not exist yet",
        )


@unittest.skipIf(
    RIGHTS_DOCUMENT_SPEC is None,
    "rights_document public-sidecar validator is not implemented",
)
class RightsDocumentLifecycleTests(unittest.TestCase):
    def test_incomplete_document_construction_fails(self):
        with self.assertRaises(TypeError):
            rights_document.RightsDocument()

    def test_initialized_document_values_reject_base_object_mutation(self):
        document = rights_document.load_rights_document_bytes(
            encode(anthropic_document())
        )
        attempts = (
            (document, "notes", "tampered"),
            (document.identity, "schema_version", "9.9.9"),
            (document.route, "provider", "Hacker"),
            (document.decision, "project_training_policy", "allowed"),
            (
                document.decision.evidence_statuses,
                "provider_training_status",
                "allowed",
            ),
            (document.evidence, "status_basis", "tampered"),
            (document.evidence.references, "terms_document", "tampered"),
            (document.legacy, "legacy_public_release", False),
        )

        for target, field, replacement in attempts:
            original = object.__getattribute__(target, field)
            try:
                with self.subTest(target=type(target).__name__, field=field):
                    with self.assertRaises((AttributeError, TypeError)):
                        object.__setattr__(target, field, replacement)
            finally:
                if object.__getattribute__(target, field) != original:
                    object.__setattr__(target, field, original)

        self.assertEqual(copy.deepcopy(document), document)


@unittest.skipIf(
    RIGHTS_DOCUMENT_SPEC is None,
    "rights_document public-sidecar validator is not implemented",
)
class RightsDocumentTests(unittest.TestCase):
    def load(self, document: object):
        return rights_document.load_rights_document_bytes(encode(document))

    def assert_rejected(self, document: object, pattern: str | None = None):
        context = (
            self.assertRaisesRegex(rights_document.RightsPolicyError, pattern)
            if pattern is not None
            else self.assertRaises(rights_document.RightsPolicyError)
        )
        with context:
            self.load(document)

    def _assert_field_values_rejected(self, field_values):
        for field, invalid in field_values:
            document = anthropic_document()
            document[field] = invalid
            with self.subTest(field=field, invalid=invalid):
                self.assert_rejected(document, field)

    def test_current_anthropic_and_xai_shapes_normalize_immutably(self):
        cases = (
            (anthropic_document(), "anthropic"),
            (xai_document(), "xai"),
        )
        for document, canonical_provider in cases:
            with self.subTest(provider=document["provider"]):
                result = self.load(document)
                self.assertEqual(result.canonical_provider, canonical_provider)
                self.assertEqual(result.provider, document["provider"])
                self.assertEqual(result.model, document["model"])
                self.assertEqual(result.generated_at, document["generated_at"])
                self.assertEqual(result.notes, document["notes"])
                with self.assertRaises((AttributeError, TypeError)):
                    result.project_training_policy = "allowed"

    def test_normalized_document_has_no_writable_instance_dict(self):
        result = self.load(anthropic_document())
        sections = (
            result,
            result.identity,
            result.route,
            result.decision,
            result.decision.evidence_statuses,
            result.evidence,
            result.evidence.references,
            result.legacy,
        )

        for section in sections:
            with self.subTest(section=type(section).__name__):
                with self.assertRaises(AttributeError):
                    section.__dict__

    def test_openai_and_meta_display_aliases_are_explicit(self):
        cases = (
            ("OpenAI", "GPT-5.6", "consumer", "openai"),
            ("Meta", "Muse Spark 1.2", "api", "meta"),
        )
        for provider, model, channel, canonical_provider in cases:
            document = anthropic_document()
            document.update(provider=provider, model=model, channel=channel)
            with self.subTest(provider=provider):
                result = self.load(document)
                self.assertEqual(result.canonical_provider, canonical_provider)
                self.assertEqual(result.provider, provider)
                self.assertEqual(result.model, model)

        self.assertEqual(
            set(rights_document.PROVIDER_ALIASES.values()),
            {"anthropic", "meta", "openai", "xai"},
        )
        self.assertEqual(
            len(rights_document.PROVIDER_ALIASES),
            len(rights_document.CANONICAL_PROVIDERS),
        )
        with self.assertRaises(TypeError):
            rights_document.PROVIDER_ALIASES["Anthropic"] = "xai"

    def test_direct_validation_rejects_spoofed_provider_string_subclasses(self):
        document = anthropic_document()
        document["provider"] = SpoofedString("Hacker", "Anthropic")
        with self.assertRaisesRegex(
            rights_document.RightsPolicyError,
            "unknown public provider",
        ):
            rights_document.validate_rights_document(document)

    def test_direct_validation_rejects_spoofed_closed_vocabulary_strings(self):
        cases = (
            ("schema_version", "9.9.9", "0.1.0"),
            ("channel", "api", "consumer"),
            ("intended_use", "training_candidate", "research_only"),
            ("project_training_policy", "allowed", "blocked"),
            ("provider_training_status", "allowed", "unresolved"),
        )
        for field, emitted, expected in cases:
            document = anthropic_document()
            document[field] = SpoofedString(emitted, expected)
            with self.subTest(field=field):
                with self.assertRaises(rights_document.RightsPolicyError):
                    rights_document.validate_rights_document(document)

    def test_direct_validation_rejects_spoofed_field_names(self):
        document = anthropic_document()
        provider = document.pop("provider")
        document[SpoofedString("hacker_provider", "provider")] = provider
        with self.assertRaisesRegex(
            rights_document.RightsPolicyError,
            "fields must be exactly",
        ):
            rights_document.validate_rights_document(document)

    def test_provider_aliases_have_no_casefold_substring_or_fallback_path(self):
        for provider in (
            "anthropic",
            "ANTHROPIC",
            "xAI",
            "SpaceXAI",
            "OpenAI API",
            "Meta Platforms",
            "unknown",
        ):
            document = anthropic_document()
            document["provider"] = provider
            with self.subTest(provider=provider):
                self.assert_rejected(document, "unknown public provider")

    def test_missing_required_fields_and_unknown_fields_fail(self):
        for field in rights_document.REQUIRED_FIELDS:
            document = anthropic_document()
            document.pop(field)
            with self.subTest(missing=field):
                self.assert_rejected(document, "fields must be exactly")

        document = anthropic_document()
        document["license_guess"] = "apache-2.0"
        self.assert_rejected(document, "fields must be exactly")

    def test_notes_is_the_only_optional_field_and_must_be_nonempty_text(self):
        document = anthropic_document()
        document.pop("notes")
        self.assertIsNone(self.load(document).notes)

        for invalid in (None, "", "   ", 1, []):
            document = anthropic_document()
            document["notes"] = invalid
            with self.subTest(invalid=invalid):
                self.assert_rejected(document, "notes must be a nonempty string")

    def test_schema_dataset_dates_and_hashes_are_exact(self):
        mutations = (
            ("schema_version", "0.2.0", "schema_version"),
            ("dataset_id", "rmems", "dataset_id"),
            ("dataset_id", "https://huggingface.co/rmems/data", "dataset_id"),
            ("dataset_id", "rmems/data/extra", "dataset_id"),
            ("dataset_id", "rmems/ data", "dataset_id"),
            ("reviewed_at", "2026-02-30", "reviewed_at"),
            ("reviewed_at", "20260830", "reviewed_at"),
        )
        for field, invalid, pattern in mutations:
            document = anthropic_document()
            document[field] = invalid
            with self.subTest(field=field, invalid=invalid):
                self.assert_rejected(document, pattern)

        evidenced = anthropic_document()
        evidenced.update(
            terms_document="https://example.invalid/terms",
            terms_effective_date="2026-02-30",
            terms_snapshot_sha256="sha256:" + "a" * 64,
        )
        self.assert_rejected(evidenced, "terms_effective_date")

        for invalid_hash in (
            "a" * 64,
            "sha256:" + "A" * 64,
            "sha256:" + "a" * 63,
            "sha512:" + "a" * 64,
        ):
            evidenced = anthropic_document()
            evidenced.update(
                terms_document="https://example.invalid/terms",
                terms_effective_date="2026-08-30",
                terms_snapshot_sha256=invalid_hash,
            )
            with self.subTest(invalid_hash=invalid_hash):
                self.assert_rejected(evidenced, "terms_snapshot_sha256")

    def test_free_form_generated_at_is_preserved(self):
        for provenance in (
            "2026-08-17/2026-08-18",
            "2026-08-19 onward (see data/raw batch files)",
        ):
            document = anthropic_document()
            document["generated_at"] = provenance
            self.assertEqual(self.load(document).generated_at, provenance)

    def test_policy_vocabularies_are_closed(self):
        mutations = {
            "channel": "web",
            "intended_use": "commercial",
            "project_training_policy": "maybe",
            "research_retention_status": "unknown",
            "research_evaluation_status": "unknown",
            "redistribution_status": "unknown",
            "provider_training_status": "unknown",
            "weight_publication_status": "unknown",
        }
        self._assert_field_values_rejected(mutations.items())

    def test_malformed_semantic_types_fail_through_rights_policy_error(self):
        fields = (
            "provider",
            "channel",
            "intended_use",
            "project_training_policy",
            "provider_training_status",
        )
        self._assert_field_values_rejected((field, []) for field in fields)

        document = anthropic_document()
        document["legacy_public_release"] = 1
        self.assert_rejected(document, "legacy_public_release")

    def test_research_only_is_blocked_even_if_provider_training_is_allowed(self):
        document = anthropic_document()
        document.update(
            terms_document="https://example.invalid/terms",
            terms_effective_date="2026-08-30",
            terms_snapshot_sha256="sha256:" + "a" * 64,
            provider_training_status="allowed",
            project_training_policy="allowed",
        )
        self.assert_rejected(document, "research_only.*blocked")

        document["project_training_policy"] = "blocked"
        result = self.load(document)
        self.assertEqual(result.provider_training_status, "allowed")
        self.assertEqual(result.project_training_policy, "blocked")

    def test_hosted_public_decision_must_match_the_sealed_authorization(self):
        promoted = anthropic_document()
        promoted.update(
            intended_use="training_candidate",
            project_training_policy="allowed",
        )

        self.assert_rejected(
            promoted,
            "received training_candidate/allowed; sealed decision is research_only/blocked",
        )

    def test_hosted_public_route_must_have_a_sealed_authorization(self):
        unauthorized_routes = (
            ("Anthropic", "api"),
            ("OpenAI", "api"),
            ("xAI (SpaceXAI)", "api"),
            ("Meta", "consumer"),
            ("Anthropic", "enterprise"),
            ("Anthropic", "local"),
        )
        for provider, channel in unauthorized_routes:
            document = anthropic_document()
            document.update(provider=provider, channel=channel)
            with self.subTest(provider=provider, channel=channel):
                self.assert_rejected(
                    document,
                    "no hosted-frontier authorization",
                )

        with self.assertRaisesRegex(
            rights_document.RightsPolicyError,
            "rights document must be an object",
        ):
            rights_document.load_rights_document_bytes(b"[]")

    def test_non_unresolved_status_requires_complete_real_evidence(self):
        for missing in (
            "terms_document",
            "terms_effective_date",
            "terms_snapshot_sha256",
            "status_basis",
        ):
            document = anthropic_document()
            document.update(
                terms_document="https://example.invalid/terms",
                terms_effective_date="2026-08-30",
                terms_snapshot_sha256="sha256:" + "a" * 64,
                redistribution_status="restricted",
            )
            document[missing] = None if missing != "status_basis" else "   "
            with self.subTest(missing=missing):
                pattern = "status_basis" if missing == "status_basis" else "evidence"
                self.assert_rejected(document, pattern)

    def test_unresolved_evidence_references_must_be_all_null_or_all_present(self):
        self.assertIsNone(self.load(anthropic_document()).terms_document)

        complete = anthropic_document()
        complete.update(
            terms_document="https://example.invalid/terms",
            terms_effective_date="2026-08-30",
            terms_snapshot_sha256="sha256:" + "a" * 64,
        )
        self.assertEqual(
            self.load(complete).terms_snapshot_sha256,
            "sha256:" + "a" * 64,
        )

        for lone_field, value in (
            ("terms_document", "https://example.invalid/terms"),
            ("terms_effective_date", "2026-08-30"),
            ("terms_snapshot_sha256", "sha256:" + "a" * 64),
        ):
            document = anthropic_document()
            document[lone_field] = value
            with self.subTest(lone_field=lone_field):
                self.assert_rejected(document, "evidence references")

    def test_legacy_provenance_is_exact_and_cannot_be_invented(self):
        for invalid_commit in (
            "a" * 39,
            "A" * 40,
            "sha1:" + "a" * 40,
            "not-a-commit",
        ):
            document = anthropic_document()
            document["original_release_commit"] = invalid_commit
            with self.subTest(invalid_commit=invalid_commit):
                self.assert_rejected(document, "original_release_commit")

        for field, invalid in (
            ("original_release_license", None),
            ("original_release_license", ""),
            ("original_release_commit", None),
        ):
            document = anthropic_document()
            document[field] = invalid
            with self.subTest(field=field, invalid=invalid):
                self.assert_rejected(document, "legacy_public_release")

        current = anthropic_document()
        current.update(
            legacy_public_release=False,
            original_release_license=None,
            original_release_commit=None,
        )
        self.assertFalse(self.load(current).legacy_public_release)

        for field in ("original_release_license", "original_release_commit"):
            invented = copy.deepcopy(current)
            invented[field] = (
                "apache-2.0" if field.endswith("license") else "a" * 40
            )
            with self.subTest(invented=field):
                self.assert_rejected(invented, "must be null")

    def test_required_text_fields_are_nonempty(self):
        for field in (
            "policy_source",
            "model",
            "subscription_plan",
            "generation_surface",
            "generated_at",
            "provider_output_attribution",
            "status_basis",
        ):
            document = anthropic_document()
            document[field] = "   "
            with self.subTest(field=field):
                self.assert_rejected(document, field)

    def test_strict_json_rejects_duplicate_keys_numbers_unicode_and_non_bytes(self):
        malformed = (
            b'{"schema_version":"0.1.0","schema_version":"0.1.0"}',
            b'{"number":NaN}',
            b'{"number":Infinity}',
            b'{"number":1e400}',
            b'{"provider":"\\ud800"}',
            b'{"\\ud800":"provider"}',
            b"\xff",
            b"{not json",
            b"[" * 2048,
        )
        for payload in malformed:
            with self.subTest(payload=payload):
                with self.assertRaises(rights_document.RightsPolicyError):
                    rights_document.load_rights_document_bytes(payload)

        with self.assertRaises(rights_document.RightsPolicyError):
            rights_document.load_rights_document_bytes("{}")

    def test_strict_json_rejects_payloads_over_the_explicit_byte_limit(self):
        payload = b" " * (rights_mapping.MAX_RIGHTS_JSON_BYTES + 1)

        with self.assertRaisesRegex(
            rights_document.RightsPolicyError,
            "exceeds the .*byte rights JSON limit",
        ):
            rights_document.load_rights_document_bytes(payload)

    def test_validate_object_and_byte_loader_return_the_same_value(self):
        document = anthropic_document()
        self.assertEqual(
            rights_document.validate_rights_document(copy.deepcopy(document)),
            rights_document.load_rights_document_bytes(encode(document)),
        )


if __name__ == "__main__":
    unittest.main()
