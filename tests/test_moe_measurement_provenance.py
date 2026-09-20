"""Compact router measurements must identify the oracle that produced them."""

import copy
import unittest

from test_moe_router import mr, oc


class RouterMeasurementProvenance(unittest.TestCase):
    def test_rehashed_meter_substitution_is_refused(self):
        original = mr.build_records(11, 1, oracle=mr.ReferenceMoERouter())[0]
        self.assertEqual(mr.check_family(original, "test"), [])
        for index in range(3):
            record = copy.deepcopy(original)
            record["result"]["measurements"][index]["meter"] = "unrelated_meter"
            record["provenance"]["record_sha256"] = oc.record_digest(record)
            with self.subTest(index=index):
                errors = mr.check_family(record, "test")
                self.assertTrue(any("MEASUREMENT_ORACLE_MISMATCH" in e for e in errors), errors)
