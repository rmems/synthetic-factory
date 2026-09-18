"""Rejected family measurements still need authentic reference execution."""

import json
from pathlib import Path
import unittest
from unittest import mock

import curate_identity
import validate_run
from oracle_grounded import canon, families, record
from test_oracle_grounded_record import accepted_reference


class ReferenceReplayAuthority(unittest.TestCase):
    def test_resealed_fabricated_measurements_are_corrupt_not_honest_rejections(self):
        for family in (families.ENCODER_FAMILY, families.NEURON_FAMILY):
            with self.subTest(family=family):
                item = accepted_reference(family)
                measured = item["result"]["measured"]
                if family == families.ENCODER_FAMILY:
                    measured["encoding_b"] = dict(measured["encoding_a"])
                else:
                    measured["delta"]["external_attestation"] = "invented"
                item["result_hash"] = canon.digest(item["result"])
                item["validation"] = record.assess(item)
                layers = record.classify(item)
                self.assertTrue(any("reference replay" in error for error in layers["envelope"]), layers)
                self.assertFalse(item["validation"]["checks"]["envelope"])
                source = curate_identity.SourceRecord(item, f"oracle-grounded/{family}/rejected-r01.jsonl", 1)
                result = curate_identity.curate_record(source)
                self.assertEqual(result.action, "exclude")
                self.assertIn("identity.oracle_invalid", result.mapping["reason_codes"])
                errors, kind = validate_run.check_line(item, "rejected-r01.jsonl:1")
                self.assertEqual(kind, "oracle")
                self.assertTrue(errors)

    def test_genuine_reproduced_family_rejection_remains_retained(self):
        path = (Path(__file__).parent / "fixtures/oracle-grounded/golden-r01"
                / families.MEMORY_FAMILY / "rejected-r01.jsonl")
        item = json.loads(path.read_bytes().split(b"\n")[0])
        with mock.patch.object(record, "reproduce", wraps=record.reproduce) as replay:
            layers = record.classify(item)
        replay.assert_called_once_with(item, environ={})
        self.assertEqual(layers["envelope"], [])
        self.assertEqual(layers["status"], [])
        self.assertTrue(layers["family"])
        source = curate_identity.SourceRecord(item, f"oracle-grounded/{families.MEMORY_FAMILY}/rejected-r01.jsonl", 1)
        result = curate_identity.curate_record(source)
        self.assertEqual(result.action, "retained")
        self.assertFalse(result.mapping["procedural_authority"]["eligible_training_candidate"])

    def test_incomplete_reference_replay_cannot_be_restamped_as_valid_rejection(self):
        item = accepted_reference(families.ENCODER_FAMILY)
        for status in ("invalid", "unavailable", "mismatch"):
            with self.subTest(status=status):
                with mock.patch.object(record, "reproduce", return_value=(status, "diagnostic")):
                    item["validation"] = record.assess(item)
                    layers = record.classify(item)
                self.assertTrue(layers["envelope"])
                self.assertFalse(item["validation"]["checks"]["envelope"])


if __name__ == "__main__":
    unittest.main()
