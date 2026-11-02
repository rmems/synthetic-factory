"""Strict public ``rights.json`` 0.2.0 procedural-route contract tests."""

from __future__ import annotations

import copy
import json
import sys
import unittest
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
PIPELINES = ROOT / "pipelines"
for _path in (Path(__file__).resolve().parent, PIPELINES):
    if str(_path) not in sys.path:
        sys.path.insert(0, str(_path))

import rights_document
import rights_document_procedural
from rights_test_support import SpoofedString
from test_rights_document import anthropic_document, encode

REGISTRY_PATH = ROOT / "config" / "FACTORY-REGISTRY.json"
REPAIR_PATH_ID = "python-function-repair-factory"
ORACLE_PATH_ID = "oracle-grounded"


def raw_registry_rows() -> dict[str, dict[str, object]]:
    """The committed registry rows, read as plain JSON independently of the validator."""

    payload = json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))
    return {row["path_id"]: row for row in payload["factories"]}


def repair_document() -> dict[str, Any]:
    """A hand-authored procedural sidecar for the python-function-repair registry row."""

    return {
        "schema_version": "0.2.0",
        "dataset_id": "rmems/python-function-repair-20261006",
        "policy_source": "https://github.com/rmems/synthetic-factory/issues/175",
        "source_type": "procedural",
        "path_id": REPAIR_PATH_ID,
        "payload_factory": REPAIR_PATH_ID,
        "generator": "python-repair-mutator",
        "generator_version": "2.1.0",
        "intended_use": "training_candidate",
        "project_training_policy": "allowed",
        "source_license_evidence": {
            "repository": "TheAlgorithms/Python",
            "commit": "2067ce6dfb3b0426a88c7a40531e355a5c703cff",
            "license": "MIT",
            "license_sha256": (
                "4395a1dc4bda1d6054c45b4d1230c709c7398e6d66f1d0aff4b22d95973bea56"
            ),
        },
        "catalog_id": "python-repair-v1",
        "catalog_sha256": "2402fe1d85a9a4a978ef4cc5e4491859cdf302b9c4b33415a66a4c00a5311f98",
        "programs_sha256": "fbd012638c92cbad072553405c545e5f8dc26bc677100a11e693d61b7bf9d904",
        "procedural_policy_sha256": (
            "c517874c7fe74bbaaefd13f938be162fac328c9704e378a937f1c080eb8b6cd4"
        ),
        "release_license": "apache-2.0",
        "training_ready": False,
        "reviewed_at": "2026-10-12",
        "notes": "Upstream programs remain MIT; generated content is Apache-2.0.",
    }


def registry_document(path_id: str, dataset_id: str) -> dict[str, Any]:
    """A procedural sidecar whose bound fields are copied from the raw registry row."""

    row = raw_registry_rows()[path_id]
    document = repair_document()
    document.update({field: copy.deepcopy(row[field]) for field in BOUND_FIELDS})
    document["dataset_id"] = dataset_id
    return document


BOUND_FIELDS = (
    "path_id",
    "payload_factory",
    "generator",
    "generator_version",
    "intended_use",
    "project_training_policy",
    "source_license_evidence",
    "catalog_id",
    "catalog_sha256",
    "programs_sha256",
    "procedural_policy_sha256",
)


def load(document: object):
    return rights_document.load_rights_document_bytes(encode(document))


class ProceduralRightsDocumentTests(unittest.TestCase):
    def assert_rejected(self, document: object, pattern: str):
        # Direct validation, so SpoofedString values reach the validator unserialized.
        with self.assertRaisesRegex(rights_document.RightsPolicyError, pattern):
            rights_document.validate_rights_document(document)

    def assert_field_values_rejected(self, field: str, values, pattern: str):
        for invalid in values:
            document = repair_document()
            document[field] = invalid
            with self.subTest(field=field, invalid=invalid):
                self.assert_rejected(document, pattern)

    def test_hand_authored_document_equals_the_committed_registry_row(self):
        self.assertEqual(
            repair_document(),
            registry_document(REPAIR_PATH_ID, "rmems/python-function-repair-20261006"),
        )

    def test_both_procedural_registry_rows_normalize_immutably(self):
        cases = (
            (repair_document(), REPAIR_PATH_ID),
            (
                registry_document(ORACLE_PATH_ID, "rmems/oracle-grounded-neuromorphic-20261006"),
                ORACLE_PATH_ID,
            ),
        )
        for document, path_id in cases:
            with self.subTest(path_id=path_id):
                result = load(document)
                self.assertIsInstance(result, rights_document.ProceduralRightsDocument)
                self.assertEqual(result.path_id, path_id)
                self.assertEqual(result.source_type, "procedural")
                self.assertEqual(result.dataset_id, document["dataset_id"])
                self.assertEqual(
                    dict(result.source_license_evidence), document["source_license_evidence"]
                )
                self.assertEqual(result.release_license, "apache-2.0")
                self.assertIs(result.training_ready, False)
                with self.assertRaises((AttributeError, TypeError)):
                    result.project_training_policy = "blocked"
                with self.assertRaises(TypeError):
                    result.source_license_evidence["license"] = "Apache-2.0"

    def test_sections_have_no_writable_state(self):
        result = load(repair_document())
        sections = (
            result,
            result.identity,
            result.route,
            result.decision,
            result.evidence,
            result.release,
        )
        for section in sections:
            with self.subTest(section=type(section).__name__):
                with self.assertRaises(TypeError):
                    vars(section)
                field = section._fields[0]
                with self.assertRaises((AttributeError, TypeError)):
                    object.__setattr__(section, field, "tampered")
        for missing in ("identity_", "provider", "__wrapped__"):
            with self.subTest(missing=missing), self.assertRaises(AttributeError):
                getattr(result, missing)

    def test_registry_rows_are_exactly_the_procedural_rows(self):
        procedural = {
            path_id
            for path_id, row in raw_registry_rows().items()
            if row.get("source_type") == "procedural"
        }
        rows = rights_document_procedural.PROCEDURAL_REGISTRY_ROWS
        self.assertEqual(set(rows), procedural)
        self.assertEqual(procedural, {REPAIR_PATH_ID, ORACLE_PATH_ID})
        with self.assertRaises(TypeError):
            rows["hosted"] = rows[REPAIR_PATH_ID]

    def test_validate_object_and_byte_loader_return_the_same_value(self):
        document = repair_document()
        self.assertEqual(
            rights_document.validate_rights_document(copy.deepcopy(document)),
            load(document),
        )

    def test_required_fields_are_exactly_the_documented_set(self):
        self.assertEqual(
            rights_document.PROCEDURAL_REQUIRED_FIELDS, set(repair_document()) - {"notes"}
        )
        self.assertEqual(rights_document.PROCEDURAL_OPTIONAL_FIELDS, {"notes"})

    def test_dataset_id_must_be_an_exact_string_on_both_routes(self):
        cases = (
            (repair_document(), "rmems/python-function-repair-20261006"),
            (anthropic_document(), "rmems/thalamic-relay-trajectories"),
        )
        for document, dataset_id in cases:
            # Well-formed emitted text, so only the exact-string check can refuse it.
            document["dataset_id"] = SpoofedString("rmems/other", dataset_id)
            with self.subTest(dataset_id=dataset_id):
                self.assert_rejected(document, "dataset_id must be an exact owner/name")

    def test_missing_and_unknown_fields_fail(self):
        for field in rights_document.PROCEDURAL_REQUIRED_FIELDS:
            document = repair_document()
            document.pop(field)
            with self.subTest(missing=field):
                pattern = "source_type" if field == "source_type" else "fields must be exactly"
                self.assert_rejected(document, pattern)
        for extra, value in (
            ("provider", "Anthropic"),
            ("legacy_public_release", False),
            ("training_eligible", True),
        ):
            document = repair_document()
            document[extra] = value
            with self.subTest(extra=extra):
                self.assert_rejected(document, "fields must be exactly")

    def test_notes_is_optional_nonempty_text(self):
        document = repair_document()
        document.pop("notes")
        self.assertIsNone(load(document).notes)
        self.assert_field_values_rejected("notes", (None, "", "  ", 1), "notes must be")

    def test_route_fields_must_repeat_the_registry_row(self):
        oracle_row = raw_registry_rows()[ORACLE_PATH_ID]
        for field in ("payload_factory", "generator", "generator_version", "catalog_id"):
            committed = repair_document()[field]
            invalid = (
                oracle_row[field],
                committed + "-tampered",
                SpoofedString("tampered", committed),
                None,
            )
            self.assert_field_values_rejected(
                field, invalid, f"{field} differs from the registry row {REPAIR_PATH_ID}"
            )

    def test_path_id_must_name_a_procedural_registry_row(self):
        hosted = sorted(
            path_id
            for path_id, row in raw_registry_rows().items()
            if row.get("source_type") != "procedural"
        )
        self.assertTrue(hosted)
        invalid = (
            hosted[0],
            "unregistered-factory",
            REPAIR_PATH_ID.upper(),
            SpoofedString("unregistered", REPAIR_PATH_ID),
            [],
            None,
        )
        self.assert_field_values_rejected(
            "path_id", invalid, "path_id does not name a procedural registry row"
        )

    def test_a_document_cannot_mix_two_procedural_rows(self):
        document = registry_document(ORACLE_PATH_ID, "rmems/oracle-grounded-neuromorphic-20261006")
        document["path_id"] = REPAIR_PATH_ID
        self.assert_rejected(document, f"differs from the registry row {REPAIR_PATH_ID}")

    def test_registry_digests_are_bare_lowercase_hex_and_bound(self):
        document = repair_document()
        for field in ("catalog_sha256", "programs_sha256", "procedural_policy_sha256"):
            value = document[field]
            self.assert_field_values_rejected(
                field,
                (value.upper(), value[:-1], "sha256:" + value, 1, None),
                f"{field} must be lowercase 64 hex",
            )
            self.assert_field_values_rejected(
                field, ("0" * 64,), f"{field} differs from the registry row"
            )
        swapped = repair_document()
        swapped["catalog_sha256"], swapped["programs_sha256"] = (
            swapped["programs_sha256"],
            swapped["catalog_sha256"],
        )
        self.assert_rejected(swapped, "catalog_sha256 differs from the registry row")

    def test_source_license_evidence_must_equal_the_registry_row(self):
        def evidence(**changes):
            value = dict(repair_document()["source_license_evidence"])
            value.update(changes)
            return {key: item for key, item in value.items() if item is not None}

        differs = (
            evidence(commit=None),
            evidence(path="pipelines/code_repair"),
            evidence(license="Apache-2.0"),
            evidence(license_sha256="0" * 64),
            evidence(repository="rmems/synthetic-factory"),
        )
        self.assert_field_values_rejected(
            "source_license_evidence",
            differs,
            f"source_license_evidence differs from the registry row {REPAIR_PATH_ID}",
        )
        spoofed_key = evidence()
        spoofed_key[SpoofedString("license_name", "license")] = spoofed_key.pop("license")
        malformed = (
            {},
            [],
            "MIT",
            None,
            evidence(license="  "),
            evidence(license=1),
            evidence(license=SpoofedString("Apache-2.0", "MIT")),
            spoofed_key,
        )
        self.assert_field_values_rejected(
            "source_license_evidence",
            malformed,
            "source_license_evidence must be an object of nonempty string fields",
        )

    def test_public_decision_must_equal_the_registry_row(self):
        for intended_use, policy in (
            ("research_only", "blocked"),
            ("training_candidate", "blocked"),
            ("research_only", "allowed"),
        ):
            document = repair_document()
            document.update(intended_use=intended_use, project_training_policy=policy)
            with self.subTest(decision=(intended_use, policy)):
                self.assert_rejected(
                    document,
                    f"received {intended_use}/{policy}; registry row states "
                    "training_candidate/allowed",
                )
        self.assert_field_values_rejected(
            "intended_use",
            ("commercial", [], SpoofedString("research_only", "training_candidate")),
            "intended_use has an unknown value",
        )
        self.assert_field_values_rejected(
            "project_training_policy",
            ("maybe", None, SpoofedString("blocked", "allowed")),
            "project_training_policy has an unknown value",
        )

    def test_release_license_is_a_closed_vocabulary(self):
        self.assertEqual(rights_document_procedural.PROCEDURAL_RELEASE_LICENSES, {"apache-2.0"})
        self.assert_field_values_rejected(
            "release_license",
            ("Apache-2.0", "mit", "apache-2.0 ", "", None, SpoofedString("mit", "apache-2.0")),
            "release_license has an unknown value",
        )

    def test_training_ready_is_only_the_json_boolean_false(self):
        self.assert_field_values_rejected(
            "training_ready",
            (True, "false", 0, None, []),
            "training_ready must be the JSON boolean false",
        )

    def test_identity_and_review_fields_are_exact(self):
        self.assert_field_values_rejected(
            "dataset_id",
            ("rmems", "rmems/a/b", "https://huggingface.co/rmems/a", None),
            "dataset_id must be an exact owner/name identifier",
        )
        self.assert_field_values_rejected(
            "policy_source", ("", "   ", None), "policy_source must be a nonempty string"
        )
        self.assert_field_values_rejected(
            "reviewed_at", ("2026-02-30", "20261012", None), "reviewed_at must be an ISO"
        )

    def test_schema_version_selects_exactly_one_route(self):
        self.assertEqual(rights_document.HOSTED_DOCUMENT_SCHEMA_VERSION, "0.1.0")
        self.assertEqual(rights_document.PROCEDURAL_DOCUMENT_SCHEMA_VERSION, "0.2.0")
        self.assertEqual(rights_document.RIGHTS_DOCUMENT_SCHEMA_VERSION, "0.2.0")
        self.assertEqual(rights_document.RIGHTS_DOCUMENT_SCHEMA_VERSIONS, {"0.1.0", "0.2.0"})
        self.assertIsInstance(load(anthropic_document()), rights_document.RightsDocument)

        procedural_at_hosted_version = repair_document()
        procedural_at_hosted_version["schema_version"] = "0.1.0"
        self.assert_rejected(procedural_at_hosted_version, "fields must be exactly")

        for source_type in (None, "hosted", "Procedural", SpoofedString("hosted", "procedural")):
            document = repair_document()
            if source_type is None:
                document.pop("source_type")
            else:
                document["source_type"] = source_type
            with self.subTest(source_type=source_type):
                self.assert_rejected(document, "documents must declare source_type procedural")

        hosted_at_procedural_version = anthropic_document()
        hosted_at_procedural_version["schema_version"] = "0.2.0"
        self.assert_rejected(hosted_at_procedural_version, "source_type procedural")

        spoofed = repair_document()
        spoofed["schema_version"] = SpoofedString("0.3.0", "0.2.0")
        with self.assertRaises(rights_document.RightsPolicyError):
            rights_document.validate_rights_document(spoofed)

    def test_strict_json_and_unicode_still_apply(self):
        document = repair_document()
        document["notes"] = "\ud800 unpaired"
        self.assert_rejected(document, "invalid rights document Unicode")
        payload = encode(repair_document()).replace(
            b'"notes": "Upstream', b'"notes": "\\ud800 Upstream'
        )
        self.assertIn(b"\\ud800", payload)
        with self.assertRaises(rights_document.RightsPolicyError):
            rights_document.load_rights_document_bytes(payload)
        duplicated = b'{"schema_version":"0.2.0","schema_version":"0.2.0"}'
        with self.assertRaises(rights_document.RightsPolicyError):
            rights_document.load_rights_document_bytes(duplicated)
        with self.assertRaisesRegex(rights_document.RightsPolicyError, "must be an object"):
            rights_document_procedural.validate_procedural_document([])


if __name__ == "__main__":
    unittest.main()
