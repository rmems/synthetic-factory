"""Tests for pipelines/oracle_grounded/parity_envelope.py -- the shared envelope check."""

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from parity_contract_support import WHERE, contract, make_record  # noqa: E402


class Envelope(unittest.TestCase):
    def test_valid_record_passes(self):
        self.assertEqual(contract.check_envelope(make_record(), WHERE), [])

    def test_non_object_rejected(self):
        errors = contract.check_envelope(["not", "an", "object"], WHERE)
        self.assertTrue(any("ENVELOPE_MALFORMED" in error for error in errors))

    def test_missing_envelope_keys_reported(self):
        record = make_record()
        del record["provenance"]
        errors = contract.check_envelope(record, WHERE)
        self.assertTrue(any("envelope missing" in error for error in errors))

    def test_dataset_must_match_record_kind(self):
        errors = contract.check_envelope(
            make_record(dataset="nir-cross-runtime-equivalence"), WHERE
        )
        self.assertTrue(any(".dataset must be" in error for error in errors))

    def test_unknown_record_kind_rejected(self):
        errors = contract.check_envelope(make_record(record_kind="something_else"), WHERE)
        self.assertTrue(any("record_kind must be" in error for error in errors))

    def test_unsupported_schema_version_rejected(self):
        errors = contract.check_envelope(make_record(schema_version="2.0.0"), WHERE)
        self.assertTrue(any("schema_version must be '1.0.0'" in error for error in errors))

    def test_meta_round_must_be_an_integer(self):
        errors = contract.check_envelope(
            make_record(meta={"round": "1", "factory": "unit-factory"}), WHERE
        )
        self.assertTrue(any("meta.round" in error for error in errors))

    def test_boolean_round_is_not_an_integer(self):
        errors = contract.check_envelope(
            make_record(meta={"round": True, "factory": "unit-factory"}), WHERE
        )
        self.assertTrue(any("meta.round" in error for error in errors))

    def test_round_must_be_at_least_one(self):
        # Matches validate_run.check_meta_round, so a parity record is not the
        # one kind in the factory that can carry round 0.
        for value in (0, -1):
            with self.subTest(round=value):
                errors = contract.check_envelope(
                    make_record(meta={"round": value, "factory": "unit-factory"}), WHERE
                )
                self.assertTrue(any("meta.round" in error for error in errors))


if __name__ == "__main__":
    unittest.main()
