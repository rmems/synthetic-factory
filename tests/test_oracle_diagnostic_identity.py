"""Caller-selected identities are diagnostics outside the reviewed policy."""

from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "pipelines"))
import curate_identity
from oracle_grounded import admission, families, record
from test_oracle_grounded_record import build


class DiagnosticIdentity(unittest.TestCase):
    def test_custom_identities_remain_valid_but_cannot_claim_publishability(self):
        row = curate_identity.default_registry().by_path_id["oracle-grounded"]
        for options in ({"model": "unreviewed-hosted-model"}, {"factory": "foreign-factory"}):
            with self.subTest(options=options):
                item = build(families.ENCODER_FAMILY, **options)
                self.assertEqual(record.validate_record(item), [])
                self.assertEqual(item["validation"]["status"], "accepted")
                self.assertFalse(item["validation"]["publishable"])
                self.assertIn("reviewed", item["validation"]["publishable_reason"])
                with self.assertRaises(admission.OracleAdmissionError):
                    admission.natural_eligibility(item, row)

    def test_generator_version_cannot_claim_reviewed_publishability(self):
        item = build(families.ENCODER_FAMILY)
        item["generator"]["version"] = "unreviewed-version"
        publishable, reason = record.publishability(item)
        self.assertFalse(publishable)
        self.assertIn("reviewed", reason)

    def test_default_identity_remains_publishable_and_training_eligible(self):
        item = build(families.ENCODER_FAMILY)
        self.assertTrue(item["validation"]["publishable"])
        row = curate_identity.default_registry().by_path_id["oracle-grounded"]
        self.assertEqual(admission.natural_eligibility(item, row), (True, ()))


if __name__ == "__main__":
    unittest.main()
