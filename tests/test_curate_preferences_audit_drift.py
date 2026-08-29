#!/usr/bin/env python3
"""``audit --expect`` must fail closed on a structurally altered audit.

The drift check is the only thing standing between a published audit and a
quiet rewrite of the evidence behind it. Every test here edits an expected
document in a way that a value-only comparison would wave through, and
asserts that the check reports it.
"""

import copy
import json
import unittest

from preference_test_support import PURITY_FIXTURES  # noqa: E402
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
