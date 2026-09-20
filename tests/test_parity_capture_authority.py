"""Self-contained capture checksums cannot establish physical execution."""

import tempfile
import copy
import unittest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import hardware_parity_support as capture_support  # noqa: E402
import test_hardware_parity_capture as capture_tests  # noqa: E402

import hardware_parity as hp  # noqa: E402
import neuro_oracle as oracle  # noqa: E402


class CaptureAuthority(unittest.TestCase):
    def _record(self):
        with tempfile.TemporaryDirectory() as temporary:
            return capture_tests.RecordedCapturePath()._record(temporary)

    def test_fabricated_capture_retains_only_unverified_research_evidence(self):
        record = self._record()
        self.assertEqual(hp.validate_record(record, "capture"), [])
        self.assertEqual(record["provenance"]["kind"], "unknown")
        self.assertEqual(record["result"]["verdict"], "inconclusive")
        self.assertEqual(record["result"]["evidence_basis"], "reference_execution_and_unverified_capture")
        self.assertIn("PHYSICAL_EXECUTION_UNATTESTED", record["result"]["reason_codes"])
        self.assertFalse(record["result"]["parity"]["repeatability"]["hardware_repeatability_measured"])
        self.assertEqual(record["oracle"]["deployment"]["capture"]["attestation"],
                         {"status": "unverified", "basis": "self_contained_checksums"})
        view = hp.training_view(record)
        self.assertFalse(view["oracle_complete"])
        self.assertIn("unverified", view["prompt"])
        self.assertIn("unverified", view["completion"])
        self.assertEqual(view["provenance"]["catalog_authorship"]["project_training_policy"], "blocked")

    def test_capture_cannot_be_promoted_to_hil_by_relabeling(self):
        record = self._record()
        record["provenance"]["kind"] = "hil"
        self.assertTrue(hp.validate_record(record, "capture"))

    def test_capture_cannot_supply_its_own_verified_attestation(self):
        record = self._record()
        record["oracle"]["deployment"]["capture"]["attestation"] = {
            "status": "verified", "basis": "self_contained_checksums"}
        self.assertTrue(hp.validate_record(record, "capture"))

    def test_projection_cannot_hide_missing_physical_authority(self):
        record = self._record()
        view = hp.training_view(record)
        view["oracle_complete"] = True
        self.assertTrue(hp.training_view_errors(record, view, "view"))

    def test_resealed_capture_cannot_upgrade_physical_verdict(self):
        record = self._record()
        record["result"]["verdict"] = "match"
        record["result"]["reason_codes"] = [code for code in record["result"]["reason_codes"]
                                             if code != "PHYSICAL_EXECUTION_UNATTESTED"]
        self.assertTrue(hp.validate_record(record, "capture"))

    def test_numeric_mismatch_survives_inconclusive_physical_verdict(self):
        scenario = hp.build_scenarios(steps=6)[0]
        with tempfile.TemporaryDirectory() as temporary:
            adapter = capture_tests.RecordedCapturePath()._capture_adapter(temporary, scenario)
            captured = adapter._capture
            spikes = copy.deepcopy(captured["payload"]["spikes"])
            spikes[0][0] ^= 1
            payload = capture_support._capture_payload(scenario, spikes, captured["payload"]["membrane"])
            captured["payload"] = payload
            captured["manifest"]["payload_sha256"] = oracle.digest(payload)
            record = hp.generate_records(steps=6, deployment=(adapter, None))[0]
        self.assertEqual(hp.validate_record(record, "mismatched capture"), [])
        self.assertEqual(record["result"]["verdict"], "inconclusive")
        self.assertIn("SPIKE_BITMAP_DISAGREEMENT", record["result"]["reason_codes"])
        self.assertGreater(record["result"]["parity"]["spike_bitmap"]["hamming_distance"], 0)

    def test_result_cannot_claim_authenticated_physical_evidence(self):
        record = self._record()
        record["result"]["evidence_basis"] = "authenticated_physical_execution"
        self.assertTrue(hp.validate_record(record, "capture"))
