"""Student labels and requested severity must agree with their source fields."""

import copy
import unittest

from test_fault_recovery import fr, oc


class FaultLabelConsistency(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.records = fr.build_records(7, 30)

    def test_prediction_prose_cannot_disagree_or_disappear(self):
        for label in ("fabricated outcome", None):
            record = copy.deepcopy(self.records[0])
            record["candidate_prediction"]["predicted_outcome_label"] = label
            record["provenance"]["record_sha256"] = oc.record_digest(record)
            with self.subTest(label=label):
                errors = fr.check_family(record, "test")
                self.assertTrue(any("predicted_outcome_label" in e for e in errors), errors)

    def test_requested_corruption_detail_must_match_intervention(self):
        original = next(r for r in self.records if r["intervention"]["kind"] == "burst_corruption")
        for requested in (0.999, None, True):
            record = copy.deepcopy(original)
            measurement = next(m for m in record["result"]["measurements"] if m["quantity"] == "corrupt_ratio")
            measurement["detail"]["requested"] = requested
            record["provenance"]["record_sha256"] = oc.record_digest(record)
            with self.subTest(requested=requested):
                errors = fr.check_family(record, "test")
                self.assertTrue(any("requested" in e for e in errors), errors)
