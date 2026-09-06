#!/usr/bin/env python3
"""Direct tests of the validator-owned stamp and the fail-closed curation gate
(``distill_curation``)."""

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))  # the shared test support, by bare name

from distill_contract_test_support import (  # noqa: E402
    minimal_record,
    oc,
    uncanonicalisable_records,
)


class ValidationIsNotSelfCertified(unittest.TestCase):
    def test_a_passed_status_with_no_validator_is_rejected(self):
        record = minimal_record()
        record["validation"] = {"status": "passed", "validator": None, "findings": []}
        errors = oc.check_envelope(record, "x")
        self.assertTrue(any("validator must be an object" in error for error in errors))

    def test_a_self_named_validator_is_structurally_valid_but_not_trusted(self):
        # check_envelope cannot tell who wrote a validation block — nothing on
        # disk can. The defence is that curation_eligible ignores it entirely,
        # which CurationFailsClosed asserts.
        record = minimal_record()
        record["validation"] = {
            "status": "passed",
            "validator": {
                "name": "the-producer-itself",
                "version": "1.0.0",
                "checked_at": oc.utc_now_iso(),
            },
            "findings": [],
        }
        self.assertEqual(oc.check_envelope(record, "x"), [])
        self.assertFalse(oc.stamp_is_bound_to_content(record))
        eligible, _ = oc.curation_eligible(record, ["found a problem"])
        self.assertFalse(eligible)

    def test_unvalidated_record_may_not_name_a_validator(self):
        record = minimal_record()
        record["validation"] = {
            "status": "unvalidated",
            "validator": {"name": "me", "version": "1"},
            "findings": [],
        }
        errors = oc.check_envelope(record, "x")
        self.assertTrue(
            any("must not name a validator" in error for error in errors)
        )

    def test_stamp_records_findings_as_failed(self):
        record = minimal_record()
        stamped = oc.stamp_validation(
            record, validator="validate_distill", version="1.0.0", findings=["boom"]
        )
        self.assertEqual(stamped["validation"]["status"], "failed")
        self.assertEqual(stamped["validation"]["findings"], ["boom"])
        self.assertEqual(oc.check_envelope(stamped, "x"), [])

    def test_stamp_does_not_mutate_the_input(self):
        record = minimal_record()
        oc.stamp_validation(record, validator="v", version="1", findings=[])
        self.assertEqual(record["validation"]["status"], "unvalidated")


class CurationFailsClosed(unittest.TestCase):
    def test_a_record_with_findings_is_not_eligible(self):
        eligible, reasons = oc.curation_eligible(minimal_record(), ["something wrong"])
        self.assertFalse(eligible)
        self.assertIn("VALIDATION_FINDINGS:1", reasons)

    def test_a_self_stamped_passed_verdict_does_not_make_a_record_eligible(self):
        # The whole point of the gate: a producer can write any validation
        # block it likes, so eligibility must come from the caller's own run.
        record = minimal_record()
        record["validation"] = {
            "status": oc.VALIDATION_PASSED,
            "validator": {
                "name": "the-producer-itself",
                "version": "1.0.0",
                "checked_at": oc.utc_now_iso(),
            },
            "findings": [],
        }
        eligible, reasons = oc.curation_eligible(record, ["a real finding"])
        self.assertFalse(eligible)
        self.assertIn("VALIDATION_FINDINGS:1", reasons)

    def test_reference_only_oracle_is_never_eligible(self):
        record = minimal_record()
        record["oracle"]["authority"] = oc.AUTHORITY_REFERENCE_ONLY
        record["provenance"]["record_sha256"] = oc.record_digest(record)
        eligible, reasons = oc.curation_eligible(record, [])
        self.assertFalse(eligible)
        self.assertIn("ORACLE_NOT_AUTHORITATIVE:'reference_only'", reasons)

    def test_abstained_result_is_never_eligible(self):
        record = minimal_record()
        record["result"] = oc.new_result(
            status=oc.RESULT_ABSTAINED,
            measurements=[],
            abstention_reason="no meter",
        )
        record["provenance"]["record_sha256"] = oc.record_digest(record)
        eligible, reasons = oc.curation_eligible(record, [])
        self.assertFalse(eligible)
        self.assertTrue(
            any(reason.startswith("ORACLE_RESULT_NOT_MEASURED") for reason in reasons)
        )

    def test_a_tampered_record_is_never_eligible(self):
        record = minimal_record()
        record["result"]["outcome"] = "continue"
        eligible, reasons = oc.curation_eligible(record, [])
        self.assertFalse(eligible)
        self.assertIn("RECORD_DIGEST_MISMATCH", reasons)

    def test_a_result_of_only_unmeasured_readings_is_not_eligible(self):
        # `measured: false` throughout is a modelled result wearing a measured
        # status. A non-empty measurements array is not enough.
        record = minimal_record()
        for item in record["result"]["measurements"]:
            item["measured"] = False
        record["provenance"]["record_sha256"] = oc.record_digest(record)
        eligible, reasons = oc.curation_eligible(record, [])
        self.assertFalse(eligible)
        self.assertIn("NO_MEASURED_READING", reasons)

    def test_a_record_with_no_digest_at_all_is_not_eligible(self):
        record = minimal_record()
        del record["provenance"]["record_sha256"]
        eligible, reasons = oc.curation_eligible(record, [])
        self.assertFalse(eligible)
        self.assertIn("RECORD_DIGEST_MISSING", reasons)

    def test_an_authoritative_measured_record_that_validated_clean_is_eligible(self):
        self.assertEqual(oc.curation_eligible(minimal_record(), []), (True, []))


class StampBinding(unittest.TestCase):
    def test_a_stamp_is_bound_to_the_content_it_was_formed_over(self):
        stamped = oc.stamp_validation(
            minimal_record(), validator="v", version="1", findings=[]
        )
        self.assertTrue(oc.stamp_is_bound_to_content(stamped))

    def test_a_stamp_lifted_onto_other_content_is_detected(self):
        stamped = oc.stamp_validation(
            minimal_record(), validator="v", version="1", findings=[]
        )
        other = minimal_record(id="rec-2")
        other["provenance"]["record_sha256"] = oc.record_digest(other)
        other["validation"] = stamped["validation"]
        self.assertFalse(oc.stamp_is_bound_to_content(other))

    def test_an_unstamped_record_is_not_bound(self):
        self.assertFalse(oc.stamp_is_bound_to_content(minimal_record()))



class CurationReasons(unittest.TestCase):
    """The remaining fail-closed reasons of ``curation_eligible`` and the stamp binding."""

    def reasons(self, mutate):
        record = minimal_record()
        mutate(record)
        record["provenance"]["record_sha256"] = oc.record_digest(record)
        eligible, reasons = oc.curation_eligible(record, [])
        self.assertFalse(eligible)
        return reasons

    def test_a_missing_oracle_block_is_a_reason(self):
        self.assertIn("ORACLE_BLOCK_MISSING", self.reasons(lambda r: r.__delitem__("oracle")))

    def test_a_result_that_is_not_an_object_is_a_reason(self):
        self.assertIn("ORACLE_RESULT_MISSING", self.reasons(lambda r: r.update(result="done")))

    def test_a_measured_result_with_no_readings_is_a_reason(self):
        self.assertIn(
            "ORACLE_RESULT_MISSING", self.reasons(lambda r: r["result"].update(measurements=[]))
        )

    def test_a_stamp_without_a_validator_object_is_not_bound(self):
        record = minimal_record()
        record["validation"] = {"status": "passed", "validator": "me"}
        self.assertFalse(oc.stamp_is_bound_to_content(record))
        record["validation"] = "passed"
        self.assertFalse(oc.stamp_is_bound_to_content(record))



class DigestBoundaryInCuration(unittest.TestCase):
    """RoR-190-B1: curation fails closed with its own reason, stamps refuse, binding is False."""

    def test_uncomputable_digests_are_their_own_curation_reason(self):
        for name, record in uncanonicalisable_records().items():
            with self.subTest(case=name):
                eligible, reasons = oc.curation_eligible(record, [])
                self.assertFalse(eligible)
                self.assertIn("RECORD_DIGEST_UNCOMPUTABLE", reasons)
                self.assertNotIn("RECORD_DIGEST_MISMATCH", reasons)
                self.assertNotIn("RECORD_DIGEST_MISSING", reasons)

    def test_the_three_digest_reasons_stay_distinct(self):
        missing = minimal_record()
        del missing["provenance"]["record_sha256"]
        self.assertIn("RECORD_DIGEST_MISSING", oc.curation_eligible(missing, [])[1])
        stale = minimal_record()
        stale["result"]["outcome"] = "fail_closed"
        self.assertIn("RECORD_DIGEST_MISMATCH", oc.curation_eligible(stale, [])[1])

    def test_stamping_uncomputable_content_is_a_contract_error(self):
        for name, record in uncanonicalisable_records().items():
            with self.subTest(case=name):
                with self.assertRaises(oc.ContractError) as caught:
                    oc.stamp_validation(record, validator="v", version="1", findings=[])
                self.assertIsNotNone(caught.exception.__cause__)

    def test_the_binding_predicate_is_false_for_uncomputable_content(self):
        for name, record in uncanonicalisable_records().items():
            with self.subTest(case=name):
                record["validation"] = {
                    "status": "passed",
                    "validator": {"name": "v", "version": "1", "validated_digest": "0" * 64},
                }
                self.assertFalse(oc.stamp_is_bound_to_content(record))


if __name__ == "__main__":
    unittest.main()
