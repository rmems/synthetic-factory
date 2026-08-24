"""Tests for pipelines/oracle_contract.py — the shared parity record envelope."""

import copy
import sys
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
PIPELINES = REPO / "pipelines"
sys.path.insert(0, str(PIPELINES))

import oracle_contract as contract  # noqa: E402

WHERE = "unit:1"


def _record(**overrides):
    record = {
        "id": "rec-001",
        "record_kind": contract.KIND_HARDWARE_PARITY,
        "dataset": "hardware-parity-spike-trajectories",
        "schema_version": "1.0.0",
        "generator": {
            "name": "unit-generator",
            "model": "deterministic",
            "role": "proposes scenarios",
            "produced": ["scenario"],
            "may_certify_oracle_result": False,
        },
        "scenario": {"id": "sc-001"},
        "intervention": None,
        "candidate_prediction": {"source": "generator", "authoritative": False},
        "oracle": {"software": {}},
        "result": {
            "oracle_backed": True,
            "verdict": contract.VERDICT_MATCH,
            "reason_codes": [],
            "derived_from": ["sha256:aa"],
        },
        "provenance": {"kind": "simulated", "tool": "unit", "tool_version": "1"},
        "validation": {
            "validator": "unit",
            "validator_version": "1",
            "checks": ["envelope_contract"],
        },
        "meta": {"round": 1, "factory": "unit-factory"},
    }
    record.update(copy.deepcopy(overrides))
    return record


class Envelope(unittest.TestCase):
    def test_valid_record_passes(self):
        self.assertEqual(contract.check_envelope(_record(), WHERE), [])

    def test_non_object_rejected(self):
        errors = contract.check_envelope(["not", "an", "object"], WHERE)
        self.assertTrue(any("ENVELOPE_MALFORMED" in error for error in errors))

    def test_missing_envelope_keys_reported(self):
        record = _record()
        del record["provenance"]
        errors = contract.check_envelope(record, WHERE)
        self.assertTrue(any("envelope missing" in error for error in errors))

    def test_dataset_must_match_record_kind(self):
        errors = contract.check_envelope(
            _record(dataset="nir-cross-runtime-equivalence"), WHERE
        )
        self.assertTrue(any(".dataset must be" in error for error in errors))

    def test_unknown_record_kind_rejected(self):
        errors = contract.check_envelope(_record(record_kind="something_else"), WHERE)
        self.assertTrue(any("record_kind must be" in error for error in errors))

    def test_meta_round_must_be_an_integer(self):
        errors = contract.check_envelope(
            _record(meta={"round": "1", "factory": "unit-factory"}), WHERE
        )
        self.assertTrue(any("meta.round" in error for error in errors))

    def test_boolean_round_is_not_an_integer(self):
        errors = contract.check_envelope(
            _record(meta={"round": True, "factory": "unit-factory"}), WHERE
        )
        self.assertTrue(any("meta.round" in error for error in errors))

    def test_round_must_be_at_least_one(self):
        # Matches validate_run.check_meta_round, so a parity record is not the
        # one kind in the factory that can carry round 0.
        for value in (0, -1):
            with self.subTest(round=value):
                errors = contract.check_envelope(
                    _record(meta={"round": value, "factory": "unit-factory"}), WHERE
                )
                self.assertTrue(any("meta.round" in error for error in errors))


class GeneratorCannotSelfCertify(unittest.TestCase):
    def test_may_certify_must_be_exactly_false(self):
        record = _record()
        record["generator"]["may_certify_oracle_result"] = True
        errors = contract.check_envelope(record, WHERE)
        self.assertTrue(any("GENERATOR_SELF_CERTIFIED" in error for error in errors))

    def test_missing_flag_is_not_treated_as_false(self):
        record = _record()
        del record["generator"]["may_certify_oracle_result"]
        errors = contract.check_envelope(record, WHERE)
        self.assertTrue(any("GENERATOR_SELF_CERTIFIED" in error for error in errors))

    def test_generator_cannot_claim_authorship_of_the_result(self):
        record = _record()
        record["generator"]["produced"] = ["scenario", "result"]
        errors = contract.check_envelope(record, WHERE)
        self.assertTrue(
            any("GENERATOR_SUBSTITUTED_FOR_ORACLE" in error for error in errors)
        )

    def test_generator_must_declare_what_it_produced(self):
        record = _record()
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
        for key in ("spikes", "membrane", "latency", "parity", "bitstream", "capture"):
            with self.subTest(key=key):
                errors = contract.check_candidate_prediction(
                    {"source": "generator", "authoritative": False, key: "anything"},
                    WHERE,
                )
                self.assertTrue(
                    any("GENERATOR_SUBSTITUTED_FOR_ORACLE" in error for error in errors),
                    key,
                )

    def test_prediction_source_must_be_generator(self):
        errors = contract.check_candidate_prediction(
            {"source": "oracle", "authoritative": False}, WHERE
        )
        self.assertTrue(any("source must be" in error for error in errors))


class Result(unittest.TestCase):
    def test_result_must_be_oracle_backed(self):
        record = _record()
        record["result"]["oracle_backed"] = False
        errors = contract.check_envelope(record, WHERE)
        self.assertTrue(any("RESULT_NOT_ORACLE_BACKED" in error for error in errors))

    def test_unknown_verdict_rejected(self):
        record = _record()
        record["result"]["verdict"] = "probably_fine"
        errors = contract.check_envelope(record, WHERE)
        self.assertTrue(any("VERDICT_UNKNOWN" in error for error in errors))

    def test_unknown_reason_code_rejected(self):
        record = _record()
        record["result"]["reason_codes"] = ["SOMETHING_MADE_UP"]
        errors = contract.check_envelope(record, WHERE)
        self.assertTrue(any("unknown reason code" in error for error in errors))

    def test_derived_from_must_reference_real_oracle_digests(self):
        errors = contract.check_envelope(
            _record(), WHERE, oracle_digests=["sha256:bb"]
        )
        self.assertTrue(any("RESULT_DIGEST_UNLINKED" in error for error in errors))

    def test_derived_from_may_not_omit_an_executed_oracle(self):
        errors = contract.check_envelope(
            _record(), WHERE, oracle_digests=["sha256:aa", "sha256:bb"]
        )
        self.assertTrue(any("omits executed oracle digests" in error for error in errors))

    def test_empty_derived_from_rejected(self):
        record = _record()
        record["result"]["derived_from"] = []
        errors = contract.check_envelope(record, WHERE)
        self.assertTrue(any("RESULT_DIGEST_UNLINKED" in error for error in errors))


class Provenance(unittest.TestCase):
    def test_kind_vocabulary_is_enforced(self):
        record = _record()
        record["provenance"]["kind"] = "real"
        errors = contract.check_envelope(record, WHERE)
        self.assertTrue(any("PROVENANCE_KIND_INVALID" in error for error in errors))

    def test_real_world_claims_are_rejected(self):
        for claimed in ("real", "real-world", "REAL_WORLD", "real hardware"):
            with self.subTest(claimed=claimed):
                record = _record()
                record["provenance"]["claimed"] = claimed
                errors = contract.check_envelope(record, WHERE)
                self.assertTrue(
                    any("PROVENANCE_CLAIMS_REAL" in error for error in errors), claimed
                )

    def test_non_real_substring_is_not_a_real_claim(self):
        record = _record()
        record["provenance"]["claimed"] = "unrealistic"
        self.assertEqual(contract.check_envelope(record, WHERE), [])

    def test_tool_attribution_required(self):
        record = _record()
        del record["provenance"]["tool_version"]
        errors = contract.check_envelope(record, WHERE)
        self.assertTrue(any("provenance.tool_version" in error for error in errors))

    def test_hil_is_the_kind_for_real_hardware(self):
        record = _record()
        record["provenance"]["kind"] = "hil"
        self.assertEqual(contract.check_envelope(record, WHERE), [])


class TrainingViews(unittest.TestCase):
    def _view(self, record, **overrides):
        view = contract.build_training_view(
            record, "prompt", "completion", ["software_float"]
        )
        view.update(overrides)
        return view

    def test_built_view_passes_its_own_check(self):
        record = _record()
        self.assertEqual(
            contract.training_view_errors(record, self._view(record), WHERE), []
        )

    def test_mismatch_verdict_sets_parity_failed(self):
        record = _record()
        record["result"]["verdict"] = contract.VERDICT_MISMATCH
        record["result"]["reason_codes"] = ["ACTION_DISAGREEMENT"]
        view = self._view(record)
        self.assertTrue(view["parity_failed"])
        self.assertEqual(contract.training_view_errors(record, view, WHERE), [])

    def test_inconclusive_is_not_a_pass(self):
        record = _record()
        record["result"]["verdict"] = contract.VERDICT_INCONCLUSIVE
        self.assertTrue(self._view(record)["parity_failed"])

    def test_unsupported_is_not_a_pass(self):
        record = _record()
        record["result"]["verdict"] = contract.VERDICT_UNSUPPORTED
        self.assertTrue(self._view(record)["parity_failed"])

    def test_relabelled_verdict_is_rejected(self):
        record = _record()
        record["result"]["verdict"] = contract.VERDICT_MISMATCH
        view = self._view(record, verdict=contract.VERDICT_MATCH)
        errors = contract.training_view_errors(record, view, WHERE)
        self.assertTrue(any("TRAINING_VIEW_HIDES_FAILURE" in error for error in errors))

    def test_softened_failure_flag_is_rejected(self):
        record = _record()
        record["result"]["verdict"] = contract.VERDICT_MISMATCH
        view = self._view(record, parity_failed=False)
        errors = contract.training_view_errors(record, view, WHERE)
        self.assertTrue(any("parity_failed must be True" in error for error in errors))

    def test_dropped_reason_codes_are_rejected(self):
        record = _record()
        record["result"]["reason_codes"] = ["ACTION_DISAGREEMENT", "MEMBRANE_DIVERGENCE"]
        view = self._view(record, reason_codes=["ACTION_DISAGREEMENT"])
        errors = contract.training_view_errors(record, view, WHERE)
        self.assertTrue(any("drops reason codes" in error for error in errors))

    def test_view_must_name_its_execution_targets(self):
        record = _record()
        view = self._view(record, execution_targets=[])
        errors = contract.training_view_errors(record, view, WHERE)
        self.assertTrue(any("execution targets" in error for error in errors))

    def test_view_must_carry_evidence_digests(self):
        record = _record()
        view = self._view(record, evidence_digests=[])
        errors = contract.training_view_errors(record, view, WHERE)
        self.assertTrue(any("RESULT_DIGEST_UNLINKED" in error for error in errors))

    def test_view_must_stay_oracle_backed(self):
        record = _record()
        view = self._view(record, oracle_backed=False)
        errors = contract.training_view_errors(record, view, WHERE)
        self.assertTrue(any("RESULT_NOT_ORACLE_BACKED" in error for error in errors))

    def test_dropping_a_whole_record_from_the_view_set_is_rejected(self):
        passing = _record(id="rec-pass")
        failing = _record(id="rec-fail")
        failing["result"]["verdict"] = contract.VERDICT_MISMATCH
        views = [self._view(passing)]
        errors = contract.view_set_errors([passing, failing], views)
        self.assertTrue(any("rec-fail" in error for error in errors))

    def test_complete_view_set_passes(self):
        records = [_record(id="rec-a"), _record(id="rec-b")]
        views = [self._view(record) for record in records]
        self.assertEqual(contract.view_set_errors(records, views), [])

    def test_duplicating_a_view_reweights_the_corpus_and_is_rejected(self):
        # Repeating the agreeable half dilutes failures as effectively as
        # deleting them.
        passing = _record(id="rec-pass")
        failing = _record(id="rec-fail")
        failing["result"]["verdict"] = contract.VERDICT_MISMATCH
        records = [passing, failing]
        views = [self._view(passing), self._view(passing), self._view(failing)]
        errors = contract.view_set_errors(records, views)
        self.assertTrue(any("repeats" in error for error in errors))

    def test_a_view_with_no_record_behind_it_is_rejected(self):
        records = [_record(id="rec-a")]
        views = [self._view(records[0]), self._view(_record(id="rec-invented"))]
        errors = contract.view_set_errors(records, views)
        self.assertTrue(any("rec-invented" in error for error in errors))

    def test_unavailable_oracle_makes_the_view_incomplete(self):
        # `parity_failed: false` means the oracles that ran agreed. It does not
        # mean the intended oracles ran, and a consumer must be able to tell.
        record = _record()
        record["result"]["reason_codes"] = ["ORACLE_UNAVAILABLE"]
        view = self._view(record)
        self.assertFalse(view["parity_failed"])
        self.assertFalse(view["oracle_complete"])
        self.assertEqual(contract.training_view_errors(record, view, WHERE), [])

    def test_fully_executed_record_yields_a_complete_view(self):
        view = self._view(_record())
        self.assertTrue(view["oracle_complete"])

    def test_overstating_oracle_completeness_is_rejected(self):
        record = _record()
        record["result"]["reason_codes"] = ["ORACLE_UNAVAILABLE"]
        view = self._view(record, oracle_complete=True)
        errors = contract.training_view_errors(record, view, WHERE)
        self.assertTrue(any("oracle_complete" in error for error in errors))


class ReasonCodeVocabulary(unittest.TestCase):
    def test_reason_codes_are_screaming_snake_case(self):
        for code in contract.REASON_CODES:
            self.assertRegex(code, r"^[A-Z][A-Z0-9_]*$")

    def test_check_reason_codes_requires_a_list(self):
        errors = contract.check_reason_codes("ACTION_DISAGREEMENT", WHERE, "codes")
        self.assertTrue(any("must be an array" in error for error in errors))


if __name__ == "__main__":
    unittest.main()
