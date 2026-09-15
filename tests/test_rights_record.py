#!/usr/bin/env python3
"""Rights envelopes on retained records: lanes, bindings, and independence."""

from __future__ import annotations

import hashlib
import sys
import unittest
from pathlib import Path

PIPELINES = Path(__file__).resolve().parents[1] / "pipelines"
if str(PIPELINES) not in sys.path:
    sys.path.insert(0, str(PIPELINES))

from curate_identity_registry import default_registry
from rights_mapping import RightsPolicyError
from rights_record import (
    LANE_RESEARCH,
    LANE_TRAINING,
    envelope_for_row,
    envelope_lane,
    training_export_blockers,
    verify_bound_envelope,
)


class RightsRecordTests(unittest.TestCase):
    SOURCE_BYTES = b'{"id":"rights-record-1"}\n'

    def setUp(self):
        self.registry = default_registry()
        self.hosted_row = self.registry.by_path_id["thalamic-trajectory-factory"]
        self.procedural_row = self.registry.by_path_id["python-function-repair-factory"]
        self.source_digest = hashlib.sha256(self.SOURCE_BYTES).hexdigest()

    def _hosted(self):
        return envelope_for_row(
            self.hosted_row,
            source_sha256=self.source_digest,
            factory_registry_sha256=self.registry.sha256,
        )

    def _procedural(self, *, eligible, reasons=()):
        return envelope_for_row(
            self.procedural_row,
            source_sha256=self.source_digest,
            factory_registry_sha256=self.registry.sha256,
            eligible=eligible,
            ineligibility_reasons=reasons,
        )

    def test_hosted_envelope_is_research_only_and_not_exportable(self):
        envelope = self._hosted()
        exportable, blockers = training_export_blockers(envelope)
        self.assertFalse(exportable)
        self.assertEqual(envelope_lane(envelope), LANE_RESEARCH)
        joined = " ".join(blockers)
        self.assertIn("intended_use is not training_candidate", joined)
        self.assertIn("project_training_policy is not allowed", joined)
        self.assertIn("provider_training_status is not allowed", joined)

    def test_project_and_provider_decisions_are_independent(self):
        envelope = self._hosted()
        project_cleared = dict(envelope)
        project_cleared["intended_use"] = "training_candidate"
        project_cleared["project_training_policy"] = "allowed"
        project_cleared["provider_training_status"] = "blocked"
        exportable, blockers = training_export_blockers(project_cleared)
        self.assertFalse(exportable)
        self.assertTrue(any("provider_training_status" in item for item in blockers))
        self.assertFalse(any("project_training_policy is not allowed" in item for item in blockers))

        provider_cleared = dict(envelope)
        provider_cleared["intended_use"] = "training_candidate"
        provider_cleared["project_training_policy"] = "blocked"
        provider_cleared["provider_training_status"] = "allowed"
        exportable, blockers = training_export_blockers(provider_cleared)
        self.assertFalse(exportable)
        self.assertTrue(any("project_training_policy" in item for item in blockers))

    def test_eligible_procedural_envelope_is_training_exportable(self):
        envelope = self._procedural(eligible=True)
        exportable, blockers = training_export_blockers(envelope)
        self.assertTrue(exportable, blockers)
        self.assertEqual(envelope_lane(envelope), LANE_TRAINING)
        self.assertEqual(envelope["project_training_policy"], "allowed")
        self.assertEqual(envelope["provider_training_status"], "allowed")
        self.assertEqual(envelope["intended_use"], "training_candidate")

    def test_ineligible_procedural_envelope_is_research_only(self):
        envelope = self._procedural(eligible=False, reasons=("COPYLEFT_UPSTREAM",))
        exportable, blockers = training_export_blockers(envelope)
        self.assertFalse(exportable)
        self.assertEqual(envelope_lane(envelope), LANE_RESEARCH)
        self.assertTrue(any("eligible training candidate" in item for item in blockers))

    def test_tampered_source_binding_fails_closed(self):
        envelope = self._hosted()
        with self.assertRaises(RightsPolicyError):
            verify_bound_envelope(
                envelope,
                source_bytes=b'{"id":"forged"}\n',
                factory_registry_bytes=self.registry.raw_bytes,
                expected_row=self.hosted_row,
            )

    def test_stale_policy_digest_fails_closed(self):
        envelope = self._procedural(eligible=True)
        envelope["rights_policy_sha256"] = "sha256:" + ("0" * 64)
        with self.assertRaises(RightsPolicyError):
            verify_bound_envelope(
                envelope,
                source_bytes=self.SOURCE_BYTES,
                factory_registry_bytes=self.registry.raw_bytes,
                expected_row=self.procedural_row,
                eligible=True,
            )

    def test_matching_hosted_bytes_still_cannot_export(self):
        envelope = self._hosted()
        verified = verify_bound_envelope(
            envelope,
            source_bytes=self.SOURCE_BYTES,
            factory_registry_bytes=self.registry.raw_bytes,
            expected_row=self.hosted_row,
        )
        exportable, _blockers = training_export_blockers(verified)
        self.assertFalse(exportable)
        self.assertEqual(envelope_lane(verified), LANE_RESEARCH)


if __name__ == "__main__":
    unittest.main()
