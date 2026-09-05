"""Tests for pipelines/oracle_grounded/parity_blocks.py -- the per-block rules."""

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from parity_contract_support import WHERE, contract, make_record  # noqa: E402


class GeneratorCannotSelfCertify(unittest.TestCase):
    def test_may_certify_must_be_exactly_false(self):
        record = make_record()
        record["generator"]["may_certify_oracle_result"] = True
        errors = contract.check_envelope(record, WHERE)
        self.assertTrue(any("GENERATOR_SELF_CERTIFIED" in error for error in errors))

    def test_missing_flag_is_not_treated_as_false(self):
        record = make_record()
        del record["generator"]["may_certify_oracle_result"]
        errors = contract.check_envelope(record, WHERE)
        self.assertTrue(any("GENERATOR_SELF_CERTIFIED" in error for error in errors))

    def test_generator_cannot_claim_authorship_of_the_result(self):
        record = make_record()
        record["generator"]["produced"] = ["scenario", "result"]
        errors = contract.check_envelope(record, WHERE)
        self.assertTrue(
            any("GENERATOR_SUBSTITUTED_FOR_ORACLE" in error for error in errors)
        )

    def test_generator_must_declare_what_it_produced(self):
        record = make_record()
        record["generator"]["produced"] = []
        errors = contract.check_envelope(record, WHERE)
        self.assertTrue(any("generator.produced" in error for error in errors))


class CandidatePrediction(unittest.TestCase):
    def test_null_prediction_is_allowed(self):
        self.assertEqual(
            contract.check_candidate_prediction(None, WHERE), []
        )

    def test_prediction_must_disclaim_authority(self):
        errors = contract.check_candidate_prediction(
            {"source": "generator", "authoritative": True}, WHERE
        )
        self.assertTrue(
            any("GENERATOR_SUBSTITUTED_FOR_ORACLE" in error for error in errors)
        )

    def test_prediction_may_not_carry_oracle_only_fields(self):
        for key in (
            "spikes",
            "membrane",
            "latency",
            "parity",
            "bitstream",
            "capture",
            "output_trace",
            "spike_count",
            "final_membrane",
            "roundtrip",
            "comparison",
        ):
            with self.subTest(key=key):
                errors = contract.check_candidate_prediction(
                    {"source": "generator", "authoritative": False, key: "anything"},
                    WHERE,
                )
                self.assertTrue(
                    any("GENERATOR_SUBSTITUTED_FOR_ORACLE" in error for error in errors),
                    key,
                )

    def test_nested_oracle_only_fields_are_rejected(self):
        errors = contract.check_candidate_prediction(
            {
                "source": "generator",
                "authoritative": False,
                "nested": {"spikes": [1], "output_digest": "x"},
            },
            WHERE,
        )
        self.assertTrue(
            any("GENERATOR_SUBSTITUTED_FOR_ORACLE" in error for error in errors),
            errors,
        )
        self.assertTrue(any("spikes" in error for error in errors), errors)

    def test_prediction_source_must_be_generator(self):
        errors = contract.check_candidate_prediction(
            {"source": "oracle", "authoritative": False}, WHERE
        )
        self.assertTrue(any("source must be" in error for error in errors))


class Result(unittest.TestCase):
    def test_result_must_be_oracle_backed(self):
        record = make_record()
        record["result"]["oracle_backed"] = False
        errors = contract.check_envelope(record, WHERE)
        self.assertTrue(any("RESULT_NOT_ORACLE_BACKED" in error for error in errors))

    def test_unknown_verdict_rejected(self):
        record = make_record()
        record["result"]["verdict"] = "probably_fine"
        errors = contract.check_envelope(record, WHERE)
        self.assertTrue(any("VERDICT_UNKNOWN" in error for error in errors))

    def test_unknown_reason_code_rejected(self):
        record = make_record()
        record["result"]["reason_codes"] = ["SOMETHING_MADE_UP"]
        errors = contract.check_envelope(record, WHERE)
        self.assertTrue(any("unknown reason code" in error for error in errors))

    def test_derived_from_must_reference_real_oracle_digests(self):
        errors = contract.check_envelope(
            make_record(), WHERE, oracle_digests=["sha256:bb"]
        )
        self.assertTrue(any("RESULT_DIGEST_UNLINKED" in error for error in errors))

    def test_derived_from_may_not_omit_an_executed_oracle(self):
        errors = contract.check_envelope(
            make_record(), WHERE, oracle_digests=["sha256:aa", "sha256:bb"]
        )
        self.assertTrue(any("omits executed oracle digests" in error for error in errors))

    def test_derived_from_must_preserve_oracle_order(self):
        record = make_record()
        record["result"]["derived_from"] = ["sha256:bb", "sha256:aa"]
        errors = contract.check_envelope(
            record, WHERE, oracle_digests=["sha256:aa", "sha256:bb"]
        )
        self.assertTrue(any("ordered oracle evidence" in error for error in errors), errors)

    def test_derived_from_must_preserve_duplicate_occurrences(self):
        record = make_record()
        record["result"]["derived_from"] = ["sha256:aa"]
        errors = contract.check_envelope(
            record, WHERE, oracle_digests=["sha256:aa", "sha256:aa"]
        )
        self.assertTrue(any("duplicate occurrences" in error for error in errors), errors)

    def test_empty_derived_from_rejected(self):
        record = make_record()
        record["result"]["derived_from"] = []
        errors = contract.check_envelope(record, WHERE)
        self.assertTrue(any("RESULT_DIGEST_UNLINKED" in error for error in errors))


class Provenance(unittest.TestCase):
    def test_kind_vocabulary_is_enforced(self):
        record = make_record()
        record["provenance"]["kind"] = "real"
        errors = contract.check_envelope(record, WHERE)
        self.assertTrue(any("PROVENANCE_KIND_INVALID" in error for error in errors))

    def test_real_world_claims_are_rejected(self):
        for claimed in ("real", "real-world", "REAL_WORLD", "real hardware"):
            with self.subTest(claimed=claimed):
                record = make_record()
                record["provenance"]["claimed"] = claimed
                errors = contract.check_envelope(record, WHERE)
                self.assertTrue(
                    any("PROVENANCE_CLAIMS_REAL" in error for error in errors), claimed
                )

    def test_non_real_substring_is_not_a_real_claim(self):
        record = make_record()
        record["provenance"]["claimed"] = "unrealistic"
        self.assertEqual(contract.check_envelope(record, WHERE), [])

    def test_tool_attribution_required(self):
        record = make_record()
        del record["provenance"]["tool_version"]
        errors = contract.check_envelope(record, WHERE)
        self.assertTrue(any("provenance.tool_version" in error for error in errors))

    def test_hil_is_the_kind_for_real_hardware(self):
        record = make_record()
        record["provenance"]["kind"] = "hil"
        self.assertEqual(contract.check_envelope(record, WHERE), [])


class ReasonCodeVocabulary(unittest.TestCase):
    def test_reason_codes_are_screaming_snake_case(self):
        for code in contract.REASON_CODES:
            self.assertRegex(code, r"^[A-Z][A-Z0-9_]*$")

    def test_check_reason_codes_requires_a_list(self):
        errors = contract.check_reason_codes("ACTION_DISAGREEMENT", WHERE, "codes")
        self.assertTrue(any("must be an array" in error for error in errors))

    def test_check_reason_codes_rejects_non_string_entries_without_crashing(self):
        errors = contract.check_reason_codes([None, 3, {}], WHERE, "codes")
        self.assertEqual(len(errors), 3)
        self.assertTrue(all("must be strings" in error for error in errors), errors)


if __name__ == "__main__":
    unittest.main()
