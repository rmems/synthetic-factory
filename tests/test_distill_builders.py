#!/usr/bin/env python3
"""Direct tests of the distillation contract's block builders (``distill_builders``):
what they refuse, and the copy boundary every caller-supplied value crosses."""

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))  # the shared test support, by bare name

from distill_contract_test_support import (  # noqa: E402
    minimal_record,
    oc,
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

    def test_measured_option_is_a_boolean_or_none(self):
        for claimed in ("false", 0, "yes"):
            with self.subTest(claimed=claimed):
                with self.assertRaises(oc.ContractError):
                    oc.new_measurement(
                        "recovery_latency_ms", 4.0, "simulator_clock", measured=claimed
                    )
        lowered = oc.new_measurement("recovery_latency_ms", 4.0, "simulator_clock", measured=False)
        self.assertIs(lowered["measured"], False)

    def test_integer_values_stay_integers(self):
        big = 2**53 + 1
        exact = oc.new_measurement("dropped_event_count", big, "hardware_counter")
        self.assertEqual(exact["value"], big)
        self.assertIsInstance(exact["value"], int)
        real = oc.new_measurement("recovery_latency_ms", 4.0, "simulator_clock")
        self.assertIsInstance(real["value"], float)

    def test_oracle_identity_fields_are_refused_by_the_builder(self):
        for changes in ({"name": ""}, {"implementation": ""}, {"version": ""}):
            with self.subTest(changes=changes):
                fields = {
                    "name": "o", "oracle_type": "deterministic_simulator",
                    "implementation": "x", "version": "1",
                }
                fields.update(changes)
                with self.assertRaises(oc.ContractError):
                    oc.new_oracle(oc.OracleIdentity(**fields))

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



class EveryBuilderCopiesInsideTheBoundary(unittest.TestCase):
    """Caller-supplied extra fields and run setup cross the same copy boundary as sections."""

    class Uncopiable:
        def __deepcopy__(self, memo):
            raise TypeError("cannot copy")

    def test_extra_fields_run_setup_and_detail_are_refused_not_raised_raw(self):
        bad = self.Uncopiable()
        identity = oc.OracleIdentity(
            "o", oracle_type="deterministic_simulator", implementation="x", version="1"
        )
        reading = oc.new_measurement("recovery_latency_ms", 4.0, "simulator_clock")
        for name, build in (
            ("result", lambda: oc.new_result(measurements=[reading], extra=bad)),
            ("provenance", lambda: oc.new_provenance("p", host=bad)),
            ("oracle", lambda: oc.new_oracle(identity, oc.OracleRun(configuration={"n": bad}))),
            ("detail", lambda: oc.new_measurement(
                "recovery_latency_ms", 4.0, "simulator_clock", detail={"k": bad}
            )),
        ):
            with self.subTest(section=name):
                with self.assertRaises(oc.ContractError):
                    build()


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
