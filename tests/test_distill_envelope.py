#!/usr/bin/env python3
"""Direct tests of the distillation contract's record blocks, builders and the
generator/oracle separation rule (``distill_blocks``, ``distill_builders``)."""

import copy
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))  # the shared test support, by bare name

from distill_contract_test_support import (  # noqa: E402
    envelope,
    minimal_record,
    oc,
    uncanonicalisable_records,
)


class EnvelopeShape(unittest.TestCase):
    def test_minimal_record_is_valid_and_digest_matches(self):
        record = minimal_record()
        self.assertEqual(oc.check_envelope(record, "x"), [])
        self.assertEqual(oc.check_digest(record, "x"), [])

    def test_unknown_family_is_rejected(self):
        record = minimal_record(family="not-a-family")
        self.assertTrue(
            any("family must be one of" in error for error in oc.check_envelope(record, "x"))
        )

    def test_schema_version_is_pinned(self):
        record = minimal_record(schema_version="oracle-grounded/0.9.0")
        self.assertTrue(
            any("schema_version must be" in error for error in oc.check_envelope(record, "x"))
        )

    def test_digest_detects_hand_editing(self):
        record = minimal_record()
        record["result"]["outcome"] = "continue"
        self.assertTrue(oc.check_digest(record, "x"))

    def test_digest_survives_a_validation_stamp(self):
        record = minimal_record()
        stamped = oc.stamp_validation(record, validator="v", version="1", findings=[])
        self.assertEqual(oc.check_digest(stamped, "x"), [])
        self.assertEqual(oc.record_digest(record), oc.record_digest(stamped))


class GeneratorNeverCertifies(unittest.TestCase):
    def test_generator_authority_is_pinned(self):
        record = minimal_record()
        record["generator"]["authority"] = "authoritative"
        errors = oc.check_envelope(record, "x")
        self.assertTrue(any("propose_only" in error for error in errors))

    def test_new_generator_refuses_an_unnamed_llm(self):
        with self.assertRaises(oc.ContractError):
            oc.new_generator(oc.GeneratorIdentity("g", version="1", kind="llm"))

    def test_oracle_key_inside_scenario_is_a_violation(self):
        record = minimal_record()
        record["scenario"]["measurements"] = [{"quantity": "energy_j"}]
        errors = oc.check_generator_oracle_separation(record, "x")
        self.assertTrue(
            any("ORACLE_FIELD_IN_GENERATOR_NAMESPACE" in error for error in errors)
        )

    def test_oracle_key_nested_deep_in_intervention_is_a_violation(self):
        record = minimal_record()
        record["intervention"]["parameters"]["expected"] = {"outcome": "quarantine"}
        errors = oc.check_generator_oracle_separation(record, "x")
        self.assertTrue(
            any("intervention.parameters.expected.outcome" in error for error in errors)
        )

    def test_prediction_keys_must_be_namespaced(self):
        record = minimal_record()
        record["candidate_prediction"]["expected_latency_ms"] = 3.0
        errors = oc.check_generator_oracle_separation(record, "x")
        self.assertTrue(any("predicted_*" in error for error in errors))

    def test_prediction_free_keys_are_allowed(self):
        record = minimal_record()
        record["candidate_prediction"]["rationale"] = "kind lookup"
        record["candidate_prediction"]["method"] = "lookup"
        self.assertEqual(oc.check_generator_oracle_separation(record, "x"), [])

    def test_every_energy_quantity_name_is_oracle_owned(self):
        for key in ("energy_j", "energy_per_op_j", "power_w"):
            with self.subTest(key=key):
                record = minimal_record()
                record["scenario"][key] = 1.5
                errors = oc.check_generator_oracle_separation(record, "x")
                self.assertTrue(any(f"scenario.{key}" in e for e in errors), errors)


class ResultFailsClosed(unittest.TestCase):
    def test_measured_result_needs_a_measurement(self):
        with self.assertRaises(oc.ContractError):
            oc.new_result(measurements=[])

    def test_abstained_result_needs_a_reason(self):
        with self.assertRaises(oc.ContractError):
            oc.new_result(status=oc.RESULT_ABSTAINED, measurements=[])

    def test_empty_measured_result_is_reported_as_missing(self):
        record = minimal_record()
        record["result"]["measurements"] = []
        errors = oc.check_envelope(record, "x")
        self.assertTrue(any("ORACLE_RESULT_MISSING" in error for error in errors))

    def test_abstained_result_is_structurally_valid(self):
        record = minimal_record()
        record["result"] = oc.new_result(
            status=oc.RESULT_ABSTAINED,
            measurements=[],
            abstention_reason="meter unavailable",
        )
        record["provenance"]["record_sha256"] = oc.record_digest(record)
        self.assertEqual(oc.check_envelope(record, "x"), [])



class MalformedBlocksAreFindings(unittest.TestCase):
    """Every advertised malformed-type finding of ``check_envelope``, by message.

    The families and the validator in #138 exercised these branches only
    indirectly; here each one is pinned through the public facade on the
    minimal record with exactly one thing wrong.
    """

    def check(self, cases):
        for name, (mutate, fragment) in cases.items():
            with self.subTest(case=name):
                record = minimal_record()
                mutate(record)
                errors = oc.check_envelope(record, "x")
                self.assertTrue(any(fragment in e for e in errors), (fragment, errors))

    @staticmethod
    def block(section, **changes):
        def mutate(record):
            record[section].update(changes)
        return mutate

    @staticmethod
    def drop(section, key):
        def mutate(record):
            del record[section][key]
        return mutate

    def test_validation_findings_have_a_shape(self):
        def unvalidated(findings):
            def mutate(record):
                record["validation"] = {"status": oc.VALIDATION_UNVALIDATED, "validator": None,
                                        "findings": findings}
            return mutate

        def passed_with_findings(record):
            stamped = oc.stamp_validation(record, findings=[], validator="v", version="1")
            record["validation"] = stamped["validation"]
            record["validation"]["findings"] = ["a finding beside a passed verdict"]

        shape = "x.validation.findings must be a list of non-empty strings"
        self.check({
            "findings object": (unvalidated({"a": 1}), shape),
            "findings number": (unvalidated(5), shape),
            "findings null": (unvalidated(None), shape),
            "findings with a non-string": (unvalidated(["ok", 3]), shape),
            "findings with an empty string": (unvalidated([""]), shape),
            "passed verdict carrying findings": (
                passed_with_findings, "x.validation: a passed verdict cannot carry findings"
            ),
        })

    def test_header_findings(self):
        self.check({
            "empty id": (lambda r: r.update(id=""), "x.id must be a non-empty string"),
            "unknown family": (lambda r: r.update(family="no-such-family"), "x.family must be one of"),
            "wrong schema version": (lambda r: r.update(schema_version="v0"), "x.schema_version must be"),
            "empty scenario": (lambda r: r.update(scenario={}), "x.scenario must be a non-empty object"),
            "scenario is a list": (lambda r: r.update(scenario=["x"]), "x.scenario must be a non-empty object"),
            "intervention is a list": (lambda r: r.update(intervention=[]), "x.intervention must be an object"),
            "prediction is a list": (
                lambda r: r.update(candidate_prediction=[]), "x.candidate_prediction must be an object"
            ),
        })

    def test_generator_block_findings(self):
        self.check({
            "not an object": (lambda r: r.update(generator=[]), "x.generator must be an object"),
            "empty name": (self.block("generator", name=""), "x.generator.name must be a non-empty string"),
            "unknown kind": (self.block("generator", kind="alien"), "x.generator.kind must be one of"),
            "empty version": (
                self.block("generator", version=""), "x.generator.version must be a non-empty string"
            ),
            "self-certifying authority": (
                self.block("generator", authority="certify"),
                "x.generator.authority must be 'propose_only'",
            ),
            "llm without a model": (
                self.block("generator", kind="llm"), "x.generator.model is required for an llm generator"
            ),
            "seed absent": (self.drop("generator", "seed"), "x.generator.seed must be present"),
            "seed is a string": (
                self.block("generator", seed="3"), "x.generator.seed must be an integer or null"
            ),
            "seed is a boolean": (
                self.block("generator", seed=True), "x.generator.seed must be an integer or null"
            ),
        })

    def test_oracle_block_findings(self):
        self.check({
            "not an object": (lambda r: r.update(oracle="sim"), "x.oracle must be an object"),
            "empty name": (self.block("oracle", name=""), "x.oracle.name must be a non-empty string"),
            "unknown type": (self.block("oracle", type="astrology"), "x.oracle.type must be one of"),
            "empty implementation": (
                self.block("oracle", implementation=""), "x.oracle.implementation must be a non-empty string"
            ),
            "empty version": (self.block("oracle", version=""), "x.oracle.version must be a non-empty string"),
            "unknown authority": (self.block("oracle", authority="guess"), "x.oracle.authority must be one of"),
            "configuration is a list": (
                self.block("oracle", configuration=[]), "x.oracle.configuration must be an object"
            ),
            "seed absent": (self.drop("oracle", "seed"), "x.oracle.seed must be present"),
            "seed is an object": (self.block("oracle", seed={}), "x.oracle.seed must be an integer or null"),
            "commit absent": (self.drop("oracle", "commit"), "x.oracle.commit must be present"),
            "commit is a number": (self.block("oracle", commit=7), "x.oracle.commit must be a string or null"),
        })

    def test_result_block_findings(self):
        self.check({
            "not an object": (lambda r: r.update(result="done"), "x.result must be an object"),
            "unknown status": (self.block("result", status="done"), "x.result.status must be one of"),
            "measurements not an array": (
                self.block("result", measurements={}), "x.result.measurements must be an array"
            ),
            "measured but empty": (self.block("result", measurements=[]), "ORACLE_RESULT_MISSING"),
            "abstained without a reason": (
                self.block("result", status="abstained", measurements=[]),
                "x.result.abstention_reason must explain",
            ),
        })

    def test_provenance_block_findings(self):
        self.check({
            "not an object": (lambda r: r.update(provenance="me"), "x.provenance must be an object"),
            "empty producer": (
                self.block("provenance", producer=""), "x.provenance.producer must be a non-empty string"
            ),
            "produced_at not a timestamp": (
                self.block("provenance", produced_at="yesterday"),
                "x.provenance.produced_at must be an ISO-8601 UTC timestamp",
            ),
            "digest not sha256": (
                self.block("provenance", record_sha256="abc"),
                "x.provenance.record_sha256 must be a sha256 hex digest",
            ),
            "digest absent": (
                self.drop("provenance", "record_sha256"),
                "x.provenance.record_sha256 must be a sha256 hex digest",
            ),
        })

    def test_validation_block_findings(self):
        stamped = {"name": "v", "version": "1", "checked_at": oc.utc_now_iso(), "validated_digest": "0" * 64}
        self.check({
            "not an object": (lambda r: r.update(validation="ok"), "x.validation must be an object"),
            "unknown status": (self.block("validation", status="maybe"), "x.validation.status must be one of"),
            "passed without a validator object": (
                self.block("validation", status="passed", validator="me"),
                "x.validation.validator must be an object naming the validator",
            ),
            "validator without a name": (
                self.block("validation", status="passed", validator={**stamped, "name": ""}),
                "x.validation.validator.name must be a non-empty string",
            ),
            "validator without a version": (
                self.block("validation", status="failed", validator={**stamped, "version": ""}),
                "x.validation.validator.version must be a non-empty string",
            ),
            "checked_at not a timestamp": (
                self.block("validation", status="passed", validator={**stamped, "checked_at": "now"}),
                "x.validation.validator.checked_at must be an ISO-8601 UTC timestamp",
            ),
            "validated_digest not sha256": (
                self.block("validation", status="passed", validator={**stamped, "validated_digest": "zz"}),
                "x.validation.validator.validated_digest must be a sha256 digest",
            ),
            "unvalidated names a validator": (
                self.block("validation", validator={"name": "v"}),
                "x.validation: unvalidated records must not name a validator",
            ),
        })

    def test_a_non_object_record_is_one_finding(self):
        for record in ("nope", None, ["x"], 7):
            with self.subTest(record=record):
                self.assertEqual(oc.check_envelope(record, "x"), ["x: record must be a JSON object"])

    def test_a_missing_digest_is_a_shape_finding_not_a_mismatch(self):
        record = minimal_record()
        del record["provenance"]["record_sha256"]
        self.assertEqual(oc.check_digest(record, "x"), [])
        record["provenance"] = "gone"
        self.assertEqual(oc.check_digest(record, "x"), [])

    def test_the_prediction_naming_rule_skips_a_non_object_prediction(self):
        record = minimal_record()
        record["candidate_prediction"] = ["outcome"]
        self.assertEqual(oc.check_generator_oracle_separation(record, "x"), [])
        self.assertIn(
            "x.candidate_prediction must be an object", oc.check_envelope(record, "x")
        )


class BuildersRefuseOutsideTheVocabulary(unittest.TestCase):
    """The block builders raise ContractError instead of writing an illegal value."""

    def test_generator_kind_model_and_notes(self):
        with self.assertRaises(oc.ContractError):
            oc.new_generator(oc.GeneratorIdentity("g", version="1", kind="alien"))
        with self.assertRaises(oc.ContractError):
            oc.new_generator(oc.GeneratorIdentity("g", version="1", kind="llm"))
        llm = oc.new_generator(
            oc.GeneratorIdentity("g", version="1", kind="llm", model="teacher-x"), seed=7, notes="why"
        )
        self.assertEqual(
            (llm["model"], llm["notes"], llm["seed"], llm["authority"]),
            ("teacher-x", "why", 7, oc.GENERATOR_AUTHORITY),
        )
        plain = oc.new_generator(oc.GeneratorIdentity("g", version="1"))
        self.assertNotIn("model", plain)
        self.assertNotIn("notes", plain)
        self.assertIsNone(plain["seed"])

    def test_generator_identity_and_seed_are_refused_by_the_builder(self):
        for identity, seed in (
            (oc.GeneratorIdentity("", version="1"), None),
            (oc.GeneratorIdentity("g", version=""), None),
            (oc.GeneratorIdentity("g", version="1"), True),
            (oc.GeneratorIdentity("g", version="1"), 2.0),
        ):
            with self.subTest(name=identity.name, version=identity.version, seed=seed):
                with self.assertRaises(oc.ContractError):
                    oc.new_generator(identity, seed=seed)

    def test_oracle_type_authority_and_run(self):
        def identity(**changes):
            fields = {"oracle_type": "deterministic_simulator", "implementation": "x", "version": "1"}
            fields.update(changes)
            return oc.OracleIdentity("o", **fields)

        with self.assertRaises(oc.ContractError):
            oc.new_oracle(identity(oracle_type="astrology"))
        with self.assertRaises(oc.ContractError):
            oc.new_oracle(identity(authority="guess"))
        fingerprint = {"model": "m", "layers": [1, 2]}
        block = oc.new_oracle(
            identity(),
            oc.OracleRun(configuration={"n": 4}, seed=3, commit="abc", fingerprint=fingerprint),
        )
        fingerprint["layers"].append(3)  # the block took a copy, not a reference
        self.assertEqual(block["fingerprint"], {"model": "m", "layers": [1, 2]})
        self.assertEqual((block["configuration"], block["seed"], block["commit"]), ({"n": 4}, 3, "abc"))
        bare = oc.new_oracle(identity())
        self.assertNotIn("fingerprint", bare)
        self.assertEqual((bare["configuration"], bare["seed"], bare["commit"]), ({}, None, None))

    def test_result_status_and_record_family(self):
        with self.assertRaises(oc.ContractError):
            oc.new_result(status="done")
        base = minimal_record()
        with self.assertRaises(oc.ContractError):
            oc.build_record(
                identity=oc.RecordIdentity("rec-2", "no-such-family"),
                proposal=oc.Proposal(generator=base["generator"], scenario=base["scenario"]),
                verdict=oc.Verdict(oracle=base["oracle"], result=base["result"]),
                provenance=oc.new_provenance("unit-test"),
            )
        record = oc.build_record(
            identity=oc.RecordIdentity("rec-2", base["family"]),
            proposal=oc.Proposal(generator=base["generator"], scenario=base["scenario"]),
            verdict=oc.Verdict(oracle=base["oracle"], result=base["result"]),
            provenance=oc.new_provenance("unit-test"),
        )
        self.assertNotIn("intervention", record)
        self.assertNotIn("candidate_prediction", record)
        self.assertEqual(record["provenance"]["record_sha256"], oc.record_digest(record))
        self.assertEqual(oc.check_envelope(record, "x"), [])



class DigestBoundary(unittest.TestCase):
    """RoR-190-B1: content that cannot be canonicalised is a finding, never an exception."""

    def test_uncanonicalisable_content_is_a_digest_finding(self):
        for name, record in uncanonicalisable_records().items():
            with self.subTest(case=name):
                errors = oc.check_digest(record, "x")
                self.assertEqual(len(errors), 1, errors)
                self.assertIn("RECORD_DIGEST_UNCOMPUTABLE", errors[0])
                self.assertIn("x.provenance.record_sha256", errors[0])

    def test_a_stale_digest_is_still_a_mismatch_and_a_missing_one_still_missing(self):
        stale = minimal_record()
        stale["result"]["outcome"] = "fail_closed"
        errors = oc.check_digest(stale, "x")
        self.assertEqual(len(errors), 1, errors)
        self.assertIn("record_sha256 mismatch", errors[0])
        self.assertNotIn("RECORD_DIGEST_UNCOMPUTABLE", errors[0])
        missing = minimal_record()
        del missing["provenance"]["record_sha256"]
        self.assertEqual(oc.check_digest(missing, "x"), [])
        self.assertIn("x.provenance.record_sha256 must be a sha256 hex digest", oc.check_envelope(missing, "x"))

    def test_the_digest_dialect_is_unchanged_for_canonicalisable_content(self):
        import hashlib

        record = minimal_record()
        payload = copy.deepcopy(record)
        payload.pop("validation")
        payload["provenance"].pop("record_sha256")
        expected = hashlib.sha256(envelope.canonical_json(payload).encode("utf-8")).hexdigest()
        self.assertEqual(record["provenance"]["record_sha256"], expected)
        self.assertEqual(oc.check_digest(record, "x"), [])

    def test_the_builder_refuses_uncanonicalisable_caller_content(self):
        base = minimal_record()
        for name, scenario in {
            "lone surrogate": {"mission": "bounded \ud800 fixture"},
            "set": {"tags": {"a"}},
            "NaN": {"threshold": float("nan")},
        }.items():
            with self.subTest(case=name):
                with self.assertRaises(oc.ContractError) as caught:
                    oc.build_record(
                        identity=oc.RecordIdentity("rec-3", base["family"]),
                        proposal=oc.Proposal(generator=base["generator"], scenario=scenario),
                        verdict=oc.Verdict(oracle=base["oracle"], result=base["result"]),
                        provenance=oc.new_provenance("unit-test"),
                    )
                self.assertIsNotNone(caught.exception.__cause__)


class BuilderCopyBoundary(unittest.TestCase):
    """RoR-190-B1 follow-through: the builder copies every section before it
    digests, so a copy failure is translated at that boundary too."""

    GOLDEN_DIGEST = "445ee6a8087064685802b04a7215df74480225fdf2a45abb6e909381f9b39dab"

    @staticmethod
    def build(scenario, result=None):
        base = minimal_record()
        return oc.build_record(
            identity=oc.RecordIdentity("rec-copy", base["family"]),
            proposal=oc.Proposal(generator=base["generator"], scenario=scenario),
            verdict=oc.Verdict(oracle=base["oracle"], result=result or base["result"]),
            provenance=oc.new_provenance("unit-test"),
        )

    def test_a_genuinely_nested_section_is_a_contract_error(self):
        deep: dict = {}
        cursor = deep
        for _ in range(50_000):
            cursor["k"] = {}
            cursor = cursor["k"]
        with self.assertRaises(oc.ContractError) as caught:
            self.build(deep)
        self.assertIsInstance(caught.exception.__cause__, RecursionError)
        self.assertIn("scenario", str(caught.exception))

    def test_an_injected_copy_failure_is_translated_whatever_the_recursion_limit(self):
        class Uncopyable:
            def __init__(self, error):
                self.error = error

            def __deepcopy__(self, memo):
                raise self.error

        for name, error, section in (
            ("recursion in scenario", RecursionError("injected"), "scenario"),
            ("uncopyable value in result", TypeError("cannot copy"), "result"),
        ):
            with self.subTest(case=name):
                payload = {"payload": Uncopyable(error)}
                with self.assertRaises(oc.ContractError) as caught:
                    if section == "scenario":
                        self.build(payload)
                    else:
                        base = minimal_record()
                        self.build({"mission": "x"}, result={**base["result"], **payload})
                self.assertIs(caught.exception.__cause__, error)
                self.assertIn(section, str(caught.exception))

    def test_ordinary_builder_output_and_digest_are_unchanged(self):
        generator = oc.new_generator(oc.GeneratorIdentity("golden-gen", version="1.0.0"), seed=7)
        oracle = oc.new_oracle(
            oc.OracleIdentity(
                "golden-sim", oracle_type="deterministic_simulator", implementation="x:Y", version="1.0.0"
            ),
            oc.OracleRun(configuration={"n": 4}, seed=3, commit="abc"),
        )
        result = oc.new_result(
            measurements=[oc.new_measurement("recovery_latency_ms", 4.0, "simulator_clock")],
            outcome="fallback",
            reason_codes=["FALLBACK_SOURCE_ENGAGED"],
        )
        scenario = {"mission": "golden", "nested": {"a": [1, {"b": 2}]}}
        record = oc.build_record(
            identity=oc.RecordIdentity("golden-1", "neuromorphic-fault-recovery"),
            proposal=oc.Proposal(
                generator=generator,
                scenario=scenario,
                intervention={"kind": "sensor_loss", "parameters": {"channels": ["c0"]}},
                candidate_prediction={"predicted_outcome": "fallback", "confidence": 0.5},
            ),
            verdict=oc.Verdict(oracle=oracle, result=result),
            provenance=oc.new_provenance("golden-producer", produced_at="2026-09-05T00:00:00Z"),
        )
        self.assertEqual(record["provenance"]["produced_at"], "2026-09-05T00:00:00Z")
        self.assertEqual(record["provenance"]["record_sha256"], self.GOLDEN_DIGEST)
        self.assertEqual(oc.check_envelope(record, "x") + oc.check_digest(record, "x"), [])
        # The record holds copies: the caller's objects stay theirs.
        scenario["nested"]["a"].append(3)
        self.assertEqual(record["scenario"]["nested"]["a"], [1, {"b": 2}])


if __name__ == "__main__":
    unittest.main()
