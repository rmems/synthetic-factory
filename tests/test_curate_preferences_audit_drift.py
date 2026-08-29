#!/usr/bin/env python3
"""``audit --expect`` must fail closed on a structurally altered audit.

The drift check is the only thing standing between a published audit and a
quiet rewrite of the evidence behind it. Every test here edits an expected
document in a way that a value-only comparison would wave through, and
asserts that the check reports it.
"""

import copy
import json
import tempfile
import unittest
from pathlib import Path

from preference_test_support import PURITY_FIXTURES, run_cli  # noqa: E402
import curate_preferences  # noqa: E402


def audit_document(*pairs, source_files=None):
    """A minimal audit whose header and summary already agree."""

    return {
        "schema_version": curate_preferences.AUDIT_SCHEMA_VERSION,
        "audit": curate_preferences.AUDIT_NAME,
        "transform": {"name": "same-context-preference-curation", "version": "1.2.0"},
        "summary": {"impure_pairs": len(pairs)},
        "source_files": list(source_files or []),
        "impure_pairs": [dict(entry) for entry in pairs],
    }


def impure_pair(**overrides):
    """One fully populated audit row, so no field is missing by accident."""

    row = {
        "source_path": "batch-r05.jsonl",
        "source_line": 1,
        "source_sha256": "0" * 64,
        "record_id": "ffpc-0001",
        "action": "excluded",
        "classification": "unsupported_context_divergence",
        "reason_codes": ["STATE_CONTEXT_DIVERGES"],
        "same_state": False,
        "same_proposed_action": True,
        "divergent_context_fields": ["state"],
        "context_diff_paths": ["state.step"],
    }
    row.update(overrides)
    return row


def source_file(**overrides):
    """One fully populated source-file inventory row."""

    row = {"source_path": "batch-r05.jsonl", "source_file_sha256": "a" * 64}
    row.update(overrides)
    return row


class AuditDriftCase(unittest.TestCase):
    """One shape for every case: alter the audit, then expect it reported."""

    def drift_after(self, actual, alter):
        """Differences reported once ``alter`` has edited the expected copy."""

        expected = copy.deepcopy(actual)
        alter(expected)
        return curate_preferences.audit_differences(expected, actual)

    def assert_reports(self, differences, named):
        self.assertTrue(
            any(named in item for item in differences),
            f"expected {named!r} to be reported, got: {differences}",
        )


class MissingAuditFieldsAreDrift(AuditDriftCase):
    """A dropped key must not read as a present ``null``."""

    def test_a_dropped_record_id_is_drift_against_an_anonymous_pair(self):
        # The six published anonymous pairs carry ``record_id: null``, so a
        # deleted key and a present null are exactly the case that collided.
        differences = self.drift_after(
            audit_document(impure_pair(record_id=None)),
            lambda doc: doc["impure_pairs"][0].pop("record_id"),
        )

        self.assert_reports(differences, "record_id")

    def test_a_dropped_agreement_field_is_drift_on_an_undetermined_pair(self):
        differences = self.drift_after(
            audit_document(impure_pair(same_state=None, same_proposed_action=None)),
            lambda doc: doc["impure_pairs"][0].pop("same_state"),
        )

        self.assert_reports(differences, "same_state")

    def test_a_dropped_source_file_hash_is_drift(self):
        differences = self.drift_after(
            audit_document(source_files=[source_file(source_file_sha256=None)]),
            lambda doc: doc["source_files"][0].pop("source_file_sha256"),
        )

        self.assert_reports(differences, "source_file_sha256")

    def test_a_matching_document_still_reports_no_drift(self):
        actual = audit_document(
            impure_pair(), impure_pair(source_line=2, record_id=None)
        )

        self.assertEqual(self.drift_after(actual, lambda doc: None), [])


class DuplicateLocationsAreRejected(AuditDriftCase):
    """An inventory that lists one location twice no longer reconciles."""

    def test_two_expected_pairs_at_one_location_are_reported(self):
        # The summary agrees with the row count on both sides, so only the
        # duplicate itself can reveal that the expected list is inconsistent.
        differences = self.drift_after(
            audit_document(impure_pair()),
            lambda doc: doc["impure_pairs"].append(
                impure_pair(action="repaired", record_id="forged")
            ),
        )

        self.assert_reports(differences, "more than once")

    def test_two_expected_source_files_at_one_path_are_reported(self):
        differences = self.drift_after(
            audit_document(source_files=[source_file()]),
            lambda doc: doc["source_files"].append(
                source_file(source_file_sha256="b" * 64)
            ),
        )

        self.assert_reports(differences, "more than once")


class CollectionsThemselvesAreValidated(AuditDriftCase):
    """An absent collection reads as "no rows"; on a pure corpus that matches."""

    def test_a_deleted_impure_pairs_collection_is_drift(self):
        differences = self.drift_after(
            audit_document(), lambda doc: doc.pop("impure_pairs")
        )

        self.assert_reports(differences, "impure_pairs")

    def test_a_scalar_impure_pairs_collection_is_drift(self):
        differences = self.drift_after(
            audit_document(), lambda doc: doc.__setitem__("impure_pairs", "none")
        )

        self.assert_reports(differences, "impure_pairs")

    def test_a_deleted_source_files_collection_is_drift(self):
        differences = self.drift_after(
            audit_document(), lambda doc: doc.pop("source_files")
        )

        self.assert_reports(differences, "source_files")

    def test_an_empty_but_present_collection_still_reconciles(self):
        # The point is presence and type, not contents: a genuinely pure
        # corpus publishes an empty list and must keep verifying.
        self.assertEqual(self.drift_after(audit_document(), lambda doc: None), [])


class MalformedRowsAreRejected(AuditDriftCase):
    """A row the comparison cannot read is drift, not a row to skip."""

    def test_a_non_object_pair_row_is_reported(self):
        differences = self.drift_after(
            audit_document(impure_pair()),
            lambda doc: doc["impure_pairs"].append("forged"),
        )

        self.assert_reports(differences, "not an object")

    def test_a_non_object_source_file_row_is_reported(self):
        differences = self.drift_after(
            audit_document(source_files=[source_file()]),
            lambda doc: doc["source_files"].append("forged"),
        )

        self.assert_reports(differences, "not an object")

    def test_a_source_file_row_without_a_usable_path_is_reported(self):
        differences = self.drift_after(
            audit_document(source_files=[source_file()]),
            lambda doc: doc["source_files"].append({"source_file_sha256": "c" * 64}),
        )

        self.assert_reports(differences, "source_path")

    def test_impure_pairs_that_are_not_a_list_are_reported(self):
        differences = self.drift_after(
            audit_document(impure_pair()),
            lambda doc: doc.__setitem__("impure_pairs", {"forged": True}),
        )

        self.assertTrue(differences, "a non-list impure_pairs reconciled cleanly")


class JsonTypesAreComparedNotJustValues(AuditDriftCase):
    """``False`` is not ``0`` and ``True`` is not line ``1``."""

    def rewrite_pair_field(self, field_name, published, rewritten):
        """Publish ``published`` for one field, then expect ``rewritten``."""

        return self.drift_after(
            audit_document(impure_pair(**{field_name: published})),
            lambda doc: doc["impure_pairs"][0].__setitem__(field_name, rewritten),
        )

    def test_a_false_agreement_rewritten_as_zero_is_drift(self):
        self.assert_reports(
            self.rewrite_pair_field("same_state", False, 0), "same_state"
        )

    def test_a_true_agreement_rewritten_as_one_is_drift(self):
        self.assert_reports(
            self.rewrite_pair_field("same_proposed_action", True, 1),
            "same_proposed_action",
        )

    def test_a_nested_boolean_inside_a_list_is_compared_by_type(self):
        self.assert_reports(
            self.rewrite_pair_field("divergent_context_fields", [False], [0]),
            "divergent_context_fields",
        )

    def test_a_source_line_of_true_does_not_key_as_line_one(self):
        self.assertTrue(
            self.rewrite_pair_field("source_line", 1, True),
            "an expected pair at line `true` reconciled against line 1",
        )

    def test_a_summary_counter_rewritten_as_a_boolean_is_drift(self):
        actual = audit_document(impure_pair())
        actual["summary"]["state_divergent_pairs"] = 1

        differences = self.drift_after(
            actual,
            lambda doc: doc["summary"].__setitem__("state_divergent_pairs", True),
        )

        self.assert_reports(differences, "state_divergent_pairs")


class DuplicateJsonMembersAreRejected(unittest.TestCase):
    """``json.loads`` keeps the last of a repeated member; the audit must not."""

    def expect_file(self, directory, mutate):
        """A published audit of the fixtures, with ``mutate`` applied to its text."""

        audit = curate_preferences.build_audit(
            curate_preferences.curate_source(PURITY_FIXTURES)
        )
        text = json.dumps(audit, indent=2, sort_keys=True, ensure_ascii=False)
        path = Path(directory) / "expected.json"
        path.write_text(mutate(text), encoding="utf-8")
        return path

    def run_expect(self, path):
        return run_cli("audit", str(PURITY_FIXTURES), "--expect", str(path))

    def test_an_unmodified_published_audit_still_verifies(self):
        with tempfile.TemporaryDirectory() as td:
            status, _, stderr = self.run_expect(self.expect_file(td, lambda text: text))

        self.assertEqual(status, 0, stderr)

    def test_a_repeated_member_shadowing_a_forged_value_is_rejected(self):
        # The forged value is overwritten by the real one during parsing, so
        # the comparison itself can never see it.
        with tempfile.TemporaryDirectory() as td:
            path = self.expect_file(
                td, lambda text: text.replace("{", '{\n  "audit": "forged",', 1)
            )
            status, _, stderr = self.run_expect(path)

        self.assertEqual(status, 1, "a duplicated member reconciled cleanly")
        self.assertIn("duplicate", stderr.lower())

    def test_a_repeated_member_nested_in_a_pair_row_is_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            path = self.expect_file(
                td,
                lambda text: text.replace(
                    '"action":', '"record_id": "forged",\n        "action":', 1
                ),
            )
            status, _, stderr = self.run_expect(path)

        self.assertEqual(status, 1, "a duplicated nested member reconciled cleanly")
        self.assertIn("duplicate", stderr.lower())


class RealAuditsStillVerify(AuditDriftCase):
    """The stricter check must not invent drift in a genuine audit."""

    def test_a_json_round_trip_of_a_real_scan_reports_no_drift(self):
        scan = curate_preferences.build_audit(
            curate_preferences.curate_source(PURITY_FIXTURES)
        )
        # An expected audit always reaches the check as parsed JSON, so the
        # comparison has to survive serialization of every field it reads.
        expected = json.loads(json.dumps(scan))

        self.assertEqual(curate_preferences.audit_differences(expected, scan), [])


if __name__ == "__main__":
    unittest.main()
