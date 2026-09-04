#!/usr/bin/env python3
"""Tests for the shared oracle-grounded record envelope (#172).

Ported from the three implementations the foundation replaces -- #138's
``tests/test_oracle_contract.py`` (digests, separation, exceptions, parse
hooks), #135's ``tests/test_oracle_contract.py`` (oracle-only keys in a
prediction, provenance vocabulary) and #134's
``tests/test_oracle_grounded_record.py`` (bounded reserved-key scan,
``proposal_of``) -- and adapted to the foundation API. The reserved-key sets
below stand in for the domain contracts' own: the walker takes the set as a
parameter, so the same record passes or fails depending on whose keys apply.
"""

import copy
import hashlib
import importlib
import json
import math
import sys
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "pipelines"))

import validate_run_provenance  # noqa: E402
from oracle_grounded import envelope  # noqa: E402

WHERE = "unit:1"

# A few of #138's ORACLE_ONLY_KEYS, #135's ORACLE_ONLY_KEYS and #134's
# RESERVED_GENERATOR_KEYS respectively.
DISTILL_KEYS = frozenset({"measurements", "outcome", "energy_j", "result"})
PARITY_KEYS = frozenset({"spikes", "membrane", "output_digest"})
RESERVED_KEYS = frozenset({"ground_truth", "measured", "result", "produced_by"})


def minimal_record(**overrides):
    record = {
        "id": "rec-1",
        "generator": {"name": "gen", "version": "1.0.0", "seed": 3},
        "scenario": {"mission": "bounded fixture", "stimulus": {"parameters": {"amplitude": 1.5}}},
        "intervention": {"kind": "sensor_loss", "parameters": {"channels": ["c0"]}},
        "candidate_prediction": {"predicted_outcome": "fallback", "confidence": 0.5},
        "oracle": {"id": "sim", "type": "deterministic_simulator"},
        "result": {"outcome": "fallback", "measured": {"recovery_latency_ms": 4.0}},
        "provenance": {"kind": "simulated", "producer": "unit-test"},
        "validation": {"status": "unvalidated"},
    }
    record.update(copy.deepcopy(overrides))
    return record


class Sections(unittest.TestCase):
    def test_the_eight_contract_sections_extend_the_generator_sections(self):
        self.assertEqual(envelope.CONTRACT_SECTIONS[:4], envelope.GENERATOR_SECTIONS)
        self.assertEqual(
            envelope.CONTRACT_SECTIONS[4:], ("oracle", "result", "provenance", "validation")
        )

    def test_a_minimal_record_passes(self):
        self.assertEqual(envelope.check_sections(minimal_record(), WHERE), [])

    def test_a_non_dict_section_is_rejected(self):
        errors = envelope.check_sections(minimal_record(oracle="sim"), WHERE)
        self.assertEqual(errors, [f"{WHERE}.oracle must be an object"])

    def test_a_missing_required_section_is_rejected(self):
        record = minimal_record()
        del record["result"]
        self.assertEqual(envelope.check_sections(record, WHERE), [f"{WHERE}.result is required"])

    def test_intervention_and_prediction_may_be_absent_or_null(self):
        record = minimal_record(candidate_prediction=None)
        del record["intervention"]
        self.assertEqual(envelope.check_sections(record, WHERE), [])

    def test_an_optional_section_must_still_be_an_object(self):
        errors = envelope.check_sections(minimal_record(intervention=["x"]), WHERE)
        self.assertEqual(errors, [f"{WHERE}.intervention must be an object or null"])

    def test_a_non_object_record_is_one_error(self):
        self.assertEqual(envelope.check_sections([], WHERE), [f"{WHERE}: record must be a JSON object"])


class GeneratorOracleSeparation(unittest.TestCase):
    def test_oracle_key_inside_scenario_is_a_violation(self):
        record = minimal_record()
        record["scenario"]["measurements"] = [{"quantity": "energy_j"}]
        errors = envelope.check_generator_oracle_separation(record, DISTILL_KEYS, WHERE)
        self.assertTrue(any("ORACLE_FIELD_IN_GENERATOR_NAMESPACE" in e for e in errors), errors)

    def test_oracle_key_nested_deep_in_intervention_is_a_violation(self):
        record = minimal_record()
        record["intervention"]["parameters"]["expected"] = {"outcome": "quarantine"}
        errors = envelope.check_generator_oracle_separation(record, DISTILL_KEYS, WHERE)
        self.assertTrue(any("intervention.parameters.expected.outcome" in e for e in errors), errors)

    def test_the_separation_check_stops_before_any_prediction_naming_rule(self):
        record = minimal_record()
        record["candidate_prediction"]["expected_latency_ms"] = 3.0
        record["candidate_prediction"]["rationale"] = "kind lookup"
        self.assertEqual(envelope.check_generator_oracle_separation(record, DISTILL_KEYS, WHERE), [])

    def test_prediction_may_not_carry_oracle_only_fields(self):
        for key in sorted(PARITY_KEYS):
            with self.subTest(key=key):
                record = minimal_record(candidate_prediction={"source": "generator", key: "x"})
                errors = envelope.check_generator_oracle_separation(record, PARITY_KEYS, WHERE)
                self.assertTrue(any(f"candidate_prediction.{key}" in e for e in errors), errors)

    def test_nested_oracle_only_fields_are_rejected(self):
        prediction = {"source": "generator", "nested": {"spikes": [1], "output_digest": "x"}}
        record = minimal_record(candidate_prediction=prediction)
        errors = envelope.check_generator_oracle_separation(record, PARITY_KEYS, WHERE)
        self.assertEqual(len(errors), 1, errors)
        self.assertIn("candidate_prediction.nested.spikes", errors[0])
        self.assertIn("candidate_prediction.nested.output_digest", errors[0])

    def test_a_measurement_key_in_a_generator_section_is_rejected(self):
        for section in ("scenario", "candidate_prediction"):
            with self.subTest(section=section):
                record = minimal_record()
                record[section]["measured"] = {"spike_count": 99}
                errors = envelope.check_generator_oracle_separation(record, RESERVED_KEYS, WHERE)
                self.assertTrue(any("oracle-reserved keys" in e for e in errors), errors)

    def test_a_nested_measurement_key_is_found(self):
        record = minimal_record()
        record["scenario"]["stimulus"]["parameters"]["ground_truth"] = 1
        hits = envelope.reserved_key_hits(record, RESERVED_KEYS)
        self.assertEqual(hits, ["scenario.stimulus.parameters.ground_truth"])

    def test_reserved_key_scanning_is_bounded_against_adversarial_payloads(self):
        # A schema-open scenario section can legally carry large extra arrays,
        # so the reserved-key scan must not turn one reserved key per element
        # into a multi-megabyte list of paths before the record is rejected.
        payload = {"scenario": {"junk": [{"measured": index} for index in range(10_000)]}}
        hits = envelope.reserved_key_hits(payload, RESERVED_KEYS)
        self.assertEqual(len(hits), envelope.MAX_RESERVED_KEY_HITS)

        record = minimal_record()
        record["scenario"]["junk"] = [{"measured": index} for index in range(10_000)]
        findings = envelope.check_generator_oracle_separation(record, RESERVED_KEYS, WHERE)
        reserved = [f for f in findings if "oracle-reserved keys" in f]
        self.assertEqual(len(reserved), 1, findings)
        self.assertLess(len(reserved[0]), 4_000, len(reserved[0]))
        self.assertIn("scan capped", reserved[0])

    def test_oracle_sections_are_never_scanned(self):
        record = minimal_record()
        record["result"]["ground_truth"] = 1
        self.assertEqual(envelope.reserved_key_hits(record, RESERVED_KEYS), [])

    def test_the_reserved_set_is_the_callers(self):
        # #134's golden credit-assignment scenarios carry ``outcome``, which is
        # oracle-only for #138 and generator-authored for #134.
        record = minimal_record()
        record["scenario"]["outcome"] = "reward"
        self.assertTrue(envelope.check_generator_oracle_separation(record, DISTILL_KEYS, WHERE))
        self.assertEqual(envelope.check_generator_oracle_separation(record, RESERVED_KEYS, WHERE), [])

    def test_a_scalar_generator_section_is_reported(self):
        errors = envelope.check_generator_oracle_separation(
            minimal_record(scenario="oops"), RESERVED_KEYS, WHERE
        )
        self.assertEqual(errors, [f"{WHERE}.scenario must be an object"])


class Digests(unittest.TestCase):
    def test_record_digest_ignores_validation_and_its_own_stamp(self):
        record = minimal_record()
        digest = envelope.record_digest(record)
        stamped = copy.deepcopy(record)
        stamped["provenance"]["record_sha256"] = digest
        stamped["validation"] = {"status": "passed", "validator": "v", "version": "1"}
        self.assertEqual(envelope.record_digest(stamped), digest)

    def test_record_digest_detects_hand_editing(self):
        record = minimal_record()
        digest = envelope.record_digest(record)
        record["result"]["outcome"] = "continue"
        self.assertNotEqual(envelope.record_digest(record), digest)

    def test_record_digest_is_the_bare_hex_of_canonical_json(self):
        record = minimal_record()
        digest = envelope.record_digest(record)
        self.assertRegex(digest, envelope.SHA256_RE)
        payload = {key: value for key, value in record.items() if key != "validation"}
        expected = hashlib.sha256(envelope.canonical_json(payload).encode("utf-8")).hexdigest()
        self.assertEqual(digest, expected)

    def test_canonical_json_dialect(self):
        self.assertEqual(envelope.canonical_json({"b": [1, "é"], "a": 0.5}), '{"a":0.5,"b":[1,"é"]}')
        with self.assertRaises(ValueError):
            envelope.canonical_json({"v": math.nan})

    def test_the_proposal_covers_exactly_the_generator_sections(self):
        record = minimal_record()
        del record["intervention"]
        proposal = envelope.proposal_of(record)
        self.assertEqual(tuple(proposal), envelope.GENERATOR_SECTIONS)
        self.assertIsNone(proposal["intervention"])
        self.assertIs(proposal["scenario"], record["scenario"])

    def test_editing_a_scenario_after_the_fact_changes_the_proposal_digest(self):
        record = minimal_record()
        digest = envelope.proposal_digest(record)
        self.assertEqual(digest, envelope.record_digest(envelope.proposal_of(record)))
        record["scenario"]["stimulus"]["parameters"]["amplitude"] += 1
        self.assertNotEqual(envelope.proposal_digest(record), digest)

    def test_editing_the_oracle_block_does_not_disturb_the_proposal_digest(self):
        record = minimal_record()
        digest = envelope.proposal_digest(record)
        record["oracle"]["description"] = "annotated later"
        record["result"]["outcome"] = "continue"
        self.assertEqual(envelope.proposal_digest(record), digest)

    def test_the_proposal_digest_survives_a_json_round_trip(self):
        record = minimal_record()
        reloaded = json.loads(envelope.canonical_json(record))
        self.assertEqual(envelope.proposal_digest(reloaded), envelope.proposal_digest(record))

    def test_the_proposal_digest_takes_the_contracts_digest_dialect(self):
        seen = []

        def prefixed(value):
            seen.append(value)
            return "sha256:" + hashlib.sha256(envelope.canonical_json(value).encode()).hexdigest()

        record = minimal_record()
        digest = envelope.proposal_digest(record, prefixed)
        self.assertEqual(seen, [envelope.proposal_of(record)])
        self.assertEqual(digest, "sha256:" + envelope.proposal_digest(record))


class ParseHooks(unittest.TestCase):
    def test_a_non_finite_constant_is_a_parse_failure_not_a_value(self):
        # json.loads accepts bare NaN. Letting one through means the first
        # canonical re-serialisation raises and takes down the whole run.
        for constant in ("NaN", "Infinity", "-Infinity"):
            with self.subTest(constant=constant):
                with self.assertRaises(ValueError):
                    json.loads(f'{{"v": {constant}}}', parse_constant=envelope.reject_json_constant)

    def test_an_overflowing_float_literal_is_a_parse_failure(self):
        with self.assertRaises(ValueError):
            json.loads('{"v": 1e999}', parse_float=envelope.reject_nonfinite_float)
        self.assertEqual(envelope.reject_nonfinite_float("0.5"), 0.5)

    def test_a_finite_record_round_trips_through_both_hooks(self):
        record = minimal_record()
        reloaded = json.loads(
            envelope.canonical_json(record),
            parse_constant=envelope.reject_json_constant,
            parse_float=envelope.reject_nonfinite_float,
        )
        self.assertTrue(envelope.strict_json_equal(reloaded, record))


class StrictJsonEqual(unittest.TestCase):
    def test_bool_and_int_do_not_coerce(self):
        self.assertFalse(envelope.strict_json_equal(True, 1))
        self.assertFalse(envelope.strict_json_equal(1, 1.0))
        self.assertTrue(envelope.strict_json_equal(1.0, 1.0))

    def test_nested_shapes_compare_by_key_and_order(self):
        self.assertTrue(envelope.strict_json_equal({"a": [1, {"b": 2.5}]}, {"a": [1, {"b": 2.5}]}))
        self.assertFalse(envelope.strict_json_equal({"a": 1}, {"a": 1, "b": 2}))
        self.assertFalse(envelope.strict_json_equal([1, 2], [2, 1]))

    def test_non_finite_floats_never_compare_equal(self):
        self.assertFalse(envelope.strict_json_equal(math.nan, math.nan))
        self.assertFalse(envelope.strict_json_equal(math.inf, math.inf))


class Exceptions(unittest.TestCase):
    def test_contract_error_is_a_value_error(self):
        self.assertTrue(issubclass(envelope.ContractError, ValueError))

    def test_oracle_unavailable_names_the_oracle_and_the_reason(self):
        error = envelope.OracleUnavailable("fpga", "no board attached")
        self.assertIsInstance(error, RuntimeError)
        self.assertEqual((error.oracle, error.detail), ("fpga", "no board attached"))
        self.assertEqual(str(error), "fpga unavailable: no board attached")


class Vocabularies(unittest.TestCase):
    def test_provenance_kinds_are_mains_thalamic_schema_vocabulary(self):
        self.assertEqual(envelope.PROVENANCE_KINDS, validate_run_provenance.ALLOWED_PROVENANCE_KIND)
        self.assertEqual(envelope.PROVENANCE_KINDS, {"designed", "simulated", "hil", "unknown"})

    def test_training_kinds_are_a_proper_subset(self):
        self.assertLess(envelope.TRAINING_PROVENANCE_KINDS, envelope.PROVENANCE_KINDS)
        self.assertEqual(envelope.PROVENANCE_KINDS - envelope.TRAINING_PROVENANCE_KINDS, {"unknown"})

    def test_real_world_provenance_is_not_in_the_vocabulary(self):
        self.assertFalse(envelope.is_enum_value("real", envelope.PROVENANCE_KINDS))
        self.assertFalse(envelope.is_enum_value(["simulated"], envelope.PROVENANCE_KINDS))
        self.assertTrue(envelope.is_enum_value("hil", envelope.PROVENANCE_KINDS))


class Helpers(unittest.TestCase):
    def test_is_number_excludes_bools_and_non_finite_values(self):
        for value in (1, 1.5, -2):
            self.assertTrue(envelope.is_number(value), value)
        for value in (True, math.nan, math.inf, "1", None):
            self.assertFalse(envelope.is_number(value), value)

    def test_is_number_fails_closed_for_integers_beyond_float_range(self):
        # A 400-digit integer is valid JSON, but converting it to float raises
        # OverflowError, which would abort validation of the whole run instead
        # of answering; main's validate_run_spikes.is_number answers False.
        self.assertFalse(envelope.is_number(json.loads("9" * 400)))
        self.assertFalse(envelope.is_number(2**1024))
        self.assertTrue(envelope.is_number(2**1023))

    def test_utc_now_iso_matches_the_timestamp_shape(self):
        stamp = envelope.utc_now_iso()
        self.assertRegex(stamp, envelope.ISO_8601_RE)
        self.assertTrue(stamp.endswith("Z"))

    def test_sha256_re_is_bare_lowercase_hex(self):
        bare = "0123456789abcdef" * 4
        self.assertRegex(bare, envelope.SHA256_RE)
        self.assertIsNone(envelope.SHA256_RE.match("sha256:" + bare))
        self.assertIsNone(envelope.SHA256_RE.match(bare.upper()))


class ImportModes(unittest.TestCase):
    def test_the_package_form_loads_from_the_repository_root(self):
        if str(REPO) not in sys.path:
            sys.path.append(str(REPO))
        module = importlib.import_module("pipelines.oracle_grounded.envelope")
        self.assertEqual(module.GENERATOR_SECTIONS, envelope.GENERATOR_SECTIONS)
        self.assertEqual(module.PROVENANCE_KINDS, envelope.PROVENANCE_KINDS)
        self.assertEqual(module.record_digest(minimal_record()), envelope.record_digest(minimal_record()))

    def test_both_import_forms_are_one_module_object(self):
        # Whichever form loads first serves both names, as pipelines/__init__.py
        # arranges for its flat siblings: an exception raised through one form
        # must be caught through the other.
        if str(REPO) not in sys.path:
            sys.path.append(str(REPO))
        module = importlib.import_module("pipelines.oracle_grounded.envelope")
        self.assertIs(module, envelope)
        self.assertIs(module.ContractError, envelope.ContractError)
        self.assertIs(sys.modules["oracle_grounded.envelope"], sys.modules["pipelines.oracle_grounded.envelope"])


if __name__ == "__main__":
    unittest.main()
