"""Raw reference validation authenticates the entire measured object."""

from pathlib import Path
import sys
import unittest
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "pipelines"))
from oracle_grounded import canon, families, record
from test_oracle_grounded_record import accepted_reference, relabel_as_named_runtime


class ReferenceMeasurementValidation(unittest.TestCase):
    def test_injected_nested_labels_are_rejected_even_with_recomputed_hash(self):
        for family, section in (
            (families.NEURON_FAMILY, "delta"),
            (families.MESH_FAMILY, "delta"),
            (families.CREDIT_FAMILY, "critic"),
        ):
            with self.subTest(family=family):
                item = accepted_reference(family)
                item["result"]["measured"][section]["external_attestation"] = "invented"
                item["result_hash"] = canon.digest(item["result"])
                self.assertTrue(record.validate_record(item, check_declared_status=False))
                verdict = record.assess(item)
                self.assertEqual(verdict["status"], "rejected")
                self.assertFalse(verdict["publishable"])
                self.assertTrue(any("reference replay" in reason for reason in verdict["reasons"]))

    def test_unresolved_dirty_diagnostic_stays_accepted_but_unpublishable(self):
        item = accepted_reference(families.ENCODER_FAMILY)
        item["oracle"]["dirty"] = None
        item["validation"] = record.assess(item)
        self.assertEqual(item["validation"]["status"], "accepted")
        self.assertFalse(item["validation"]["publishable"])
        self.assertEqual(record.validate_record(item), [])

    def test_invalid_proposal_does_not_reach_replay(self):
        item = accepted_reference(families.NEURON_FAMILY)
        item["scenario"]["duration_ms"] = 10**12
        item["proposal_hash"] = canon.digest(record.proposal_of(item))
        with mock.patch.object(record, "reproduce") as replay:
            self.assertTrue(record.validate_record(item, check_declared_status=False))
        replay.assert_not_called()

    def test_named_runtime_metadata_validation_does_not_execute_replay(self):
        item = relabel_as_named_runtime(accepted_reference(families.ENCODER_FAMILY))
        with mock.patch.object(record, "reproduce") as replay:
            self.assertEqual(record.validate_record(item), [])
        replay.assert_not_called()


if __name__ == "__main__":
    unittest.main()
