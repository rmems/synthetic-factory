#!/usr/bin/env python3
"""Tests for the record envelope, the generator/oracle split, and the boundary.

The point of these is adversarial: it should not be possible to make a record
that looks authoritative without an oracle having produced it. Each test below
mutates one thing and asserts the validator notices.
"""

import copy
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "pipelines"))

from oracle_grounded import canon, families, generators, oracles, record  # noqa: E402

DOUBLE = REPO / "tests" / "fixtures" / "oracle-grounded" / "protocol_double.py"
PINNED_COMMIT = "0" * 40


def build(family, index=0, **kwargs):
    kwargs.setdefault("commit", PINNED_COMMIT)
    kwargs.setdefault("dirty", False)
    return record.build_record(family, index, seed=12345, **kwargs)


def double_env(mode="ok", runtimes=("axon-encoder",)):
    command = f"{sys.executable} {DOUBLE} {mode}"
    return {oracles.env_key(runtime): command for runtime in runtimes}


class EnvelopeShape(unittest.TestCase):
    def test_every_family_builds_a_record_that_validates(self):
        for family in families.FAMILY_NAMES:
            with self.subTest(family=family):
                item = build(family)
                layers = record.classify(item)
                self.assertEqual(layers["envelope"], [])
                self.assertEqual(layers["status"], [])
                self.assertEqual(item["family"], family)
                self.assertEqual(item["schema"], record.SCHEMA_ID)

    def test_the_envelope_carries_every_declared_key(self):
        item = build(families.ENCODER_FAMILY)
        for key in record.ENVELOPE_KEYS:
            self.assertIn(key, item)
        for key in record.ORACLE_KEYS:
            self.assertIn(key, item["oracle"])

    def test_the_schema_file_and_the_code_agree_on_the_required_keys(self):
        schema = json.loads((REPO / "schemas" / "oracle-grounded-v1.schema.json").read_text())
        self.assertEqual(sorted(schema["required"]), sorted(record.ENVELOPE_KEYS))
        oracle_required = schema["$defs"]["oracle"]["required"]
        self.assertEqual(sorted(oracle_required), sorted(record.ORACLE_KEYS))
        self.assertEqual(schema["properties"]["schema"]["const"], record.SCHEMA_ID)
        self.assertEqual(
            sorted(schema["properties"]["family"]["enum"]), sorted(families.FAMILY_NAMES)
        )

    def test_every_family_has_a_published_schema_file(self):
        for family in families.FAMILY_NAMES:
            path = REPO / "schemas" / "oracle-grounded" / f"{family}.schema.json"
            with self.subTest(family=family):
                self.assertTrue(path.is_file(), f"missing schema: {path}")
                json.loads(path.read_text())

    def test_an_unknown_family_is_refused(self):
        with self.assertRaises(KeyError):
            families.spec_for("not-a-family")
        with self.assertRaises(KeyError):
            build("not-a-family")


class GeneratorNeverMeasures(unittest.TestCase):
    def test_the_generator_block_declares_itself_non_authoritative(self):
        item = build(families.MESH_FAMILY)
        self.assertIs(item["generator"]["authoritative"], False)

    def test_a_generator_claiming_authority_is_rejected(self):
        item = build(families.MESH_FAMILY)
        item["generator"]["authoritative"] = True
        self.assertTrue(
            any("authoritative" in finding for finding in record.validate_record(item))
        )

    def test_a_measurement_key_in_a_generator_section_is_rejected(self):
        for section in ("scenario", "candidate_prediction"):
            item = build(families.NEURON_FAMILY)
            item[section]["measured"] = {"spike_count": 99}
            with self.subTest(section=section):
                findings = record.validate_record(item)
                self.assertTrue(any("oracle-reserved keys" in f for f in findings), findings)

    def test_a_nested_measurement_key_is_found(self):
        item = build(families.NEURON_FAMILY)
        item["scenario"]["stimulus"]["parameters"]["ground_truth"] = 1
        findings = record.validate_record(item)
        self.assertTrue(any("oracle-reserved keys" in f for f in findings), findings)

    def test_build_refuses_a_generator_that_authors_a_measurement(self):
        original = generators.propose_mesh_scenario

        def poisoned(rng, *args, **kwargs):
            scenario = original(rng, *args, **kwargs)
            scenario["measured"] = {"propagation_delay_ms": 0.0}
            return scenario

        generators.propose_mesh_scenario = poisoned
        try:
            with self.assertRaises(record.GenerationError):
                build(families.MESH_FAMILY)
        finally:
            generators.propose_mesh_scenario = original

    def test_a_candidate_prediction_cannot_pose_as_ground_truth(self):
        item = build(families.ENCODER_FAMILY)
        item["candidate_prediction"]["kind"] = "ground_truth"
        findings = record.validate_record(item)
        self.assertTrue(any("non_authoritative_guess" in f for f in findings), findings)

    def test_the_candidate_prediction_is_scored_but_not_believed(self):
        item = build(families.ENCODER_FAMILY)
        self.assertIn(
            item["validation"]["candidate_prediction_correct"], (True, False, None)
        )
        self.assertNotIn("candidate_prediction", item["result"]["measured"])


class HashesCoverWhatTheyClaim(unittest.TestCase):
    def test_the_proposal_hash_covers_exactly_the_generator_sections(self):
        item = build(families.ENCODER_FAMILY)
        self.assertEqual(
            item["proposal_hash"], canon.digest(record.proposal_of(item))
        )
        self.assertEqual(
            sorted(record.proposal_of(item)), sorted(record.GENERATOR_SECTIONS)
        )

    def test_editing_a_scenario_after_the_fact_is_detected(self):
        item = build(families.ENCODER_FAMILY)
        item["scenario"]["sample_count"] += 1
        findings = record.validate_record(item)
        self.assertTrue(any("proposal_hash" in f for f in findings), findings)

    def test_editing_the_oracle_block_does_not_disturb_the_proposal_hash(self):
        item = build(families.ENCODER_FAMILY)
        item["oracle"]["description"] = "annotated later"
        self.assertNotIn(
            "proposal_hash",
            " ".join(record.classify(item)["envelope"]),
        )

    def test_the_result_hash_covers_the_result(self):
        item = build(families.MESH_FAMILY)
        self.assertEqual(item["result_hash"], canon.digest(item["result"]))
        item["result"]["measured"]["before"]["sink_reached"] = not item["result"]["measured"][
            "before"
        ]["sink_reached"]
        findings = record.validate_record(item)
        self.assertTrue(any("result_hash" in f for f in findings), findings)

    def test_hashes_survive_a_json_round_trip(self):
        item = build(families.CREDIT_FAMILY)
        reloaded = json.loads(canon.dumps_record(item))
        self.assertEqual(reloaded["proposal_hash"], canon.digest(record.proposal_of(reloaded)))
        self.assertEqual(reloaded["result_hash"], canon.digest(reloaded["result"]))
        self.assertEqual(record.validate_record(reloaded), [])


class CurationFailsClosed(unittest.TestCase):
    def test_a_missing_result_is_an_error(self):
        item = build(families.NEURON_FAMILY)
        item["result"] = {}
        findings = record.validate_record(item)
        self.assertTrue(any("fails closed" in f for f in findings), findings)

    def test_an_empty_measurement_is_an_error(self):
        item = build(families.NEURON_FAMILY)
        item["result"]["measured"] = {}
        item["result_hash"] = canon.digest(item["result"])
        findings = record.validate_record(item)
        self.assertTrue(any("measured" in f for f in findings), findings)

    def test_a_misattributed_result_is_an_error(self):
        item = build(families.NEURON_FAMILY)
        item["result"]["produced_by"] = "somebody-else"
        item["result_hash"] = canon.digest(item["result"])
        findings = record.validate_record(item)
        self.assertTrue(any("produced_by" in f for f in findings), findings)

    def test_an_unresolved_commit_is_an_error(self):
        item = build(families.NEURON_FAMILY)
        item["oracle"]["commit"] = "unknown"
        findings = record.validate_record(item)
        self.assertTrue(any("commit" in f for f in findings), findings)

    def test_a_missing_module_digest_is_an_error(self):
        item = build(families.NEURON_FAMILY)
        item["oracle"]["module_digest"] = "not-a-digest"
        findings = record.validate_record(item)
        self.assertTrue(any("module_digest" in f for f in findings), findings)

    def test_a_missing_dirty_state_is_an_error(self):
        item = build(families.NEURON_FAMILY)
        del item["oracle"]["dirty"]
        findings = record.validate_record(item)
        self.assertTrue(any("dirty" in f for f in findings), findings)

    def test_a_record_with_no_executed_stages_is_an_error(self):
        item = build(families.NEURON_FAMILY)
        item["oracle"]["stages"] = []
        findings = record.validate_record(item)
        self.assertTrue(any("stages" in f for f in findings), findings)

    def test_provenance_never_claims_a_real_measurement(self):
        for family in families.FAMILY_NAMES:
            with self.subTest(family=family):
                self.assertEqual(build(family)["provenance"]["kind"], "simulated")

    def test_an_out_of_vocabulary_provenance_kind_is_rejected(self):
        item = build(families.NEURON_FAMILY)
        item["provenance"]["kind"] = "real"
        findings = record.validate_record(item)
        self.assertTrue(any("provenance.kind" in f for f in findings), findings)

    def test_unknown_provenance_is_not_allowed_on_a_new_record(self):
        item = build(families.NEURON_FAMILY)
        item["provenance"]["kind"] = "unknown"
        findings = record.validate_record(item)
        self.assertTrue(any("unknown" in f for f in findings), findings)


class AuthorityCannotBeSelfDeclared(unittest.TestCase):
    def test_reference_records_are_never_publishable(self):
        for family in families.FAMILY_NAMES:
            with self.subTest(family=family):
                item = build(family)
                self.assertEqual(item["oracle"]["implementation"], "reference")
                self.assertEqual(item["oracle"]["authority"], "reference-simulator")
                self.assertFalse(item["validation"]["publishable"])
                self.assertIn(
                    "measured by a reference implementation",
                    item["validation"]["publishable_reason"],
                )

    def test_claiming_publishable_on_a_reference_record_is_rejected(self):
        item = build(families.ENCODER_FAMILY)
        item["validation"]["publishable"] = True
        findings = record.validate_record(item)
        self.assertTrue(any("publishable" in f for f in findings), findings)

    def test_relabelling_a_reference_run_as_a_named_runtime_is_rejected(self):
        item = build(families.ENCODER_FAMILY)
        item["oracle"]["implementation"] = "named-runtime"
        item["oracle"]["authority"] = "measured-runtime"
        findings = record.validate_record(item)
        self.assertTrue(
            any("not every stage was run by a named runtime" in f for f in findings), findings
        )

    def test_a_stage_digest_that_does_not_match_the_oracle_is_rejected(self):
        item = build(families.ENCODER_FAMILY)
        item["oracle"]["stages"][0]["module_digest"] = canon.digest({"tampered": True})
        findings = record.validate_record(item)
        self.assertTrue(any("module_digest" in f for f in findings), findings)

    def test_runtime_bound_must_agree_with_the_availability_report(self):
        item = build(families.ENCODER_FAMILY)
        item["oracle"]["runtime_bound"] = True
        findings = record.validate_record(item)
        self.assertTrue(any("runtime_bound" in f for f in findings), findings)

    def test_require_named_runtime_rejects_a_reference_record(self):
        item = build(families.ENCODER_FAMILY)
        self.assertEqual(record.validate_record(item), [])
        findings = record.validate_record(item, require_named_runtime=True)
        self.assertTrue(any("named-runtime" in f for f in findings), findings)

    def test_the_availability_report_names_the_missing_runtime(self):
        item = build(families.ENCODER_FAMILY)
        availability = item["oracle"]["availability"]
        self.assertEqual(availability["unbound"], ["axon-encoder"])
        self.assertFalse(availability["all_bound"])
        probe = availability["runtimes"][0]
        self.assertEqual(probe["binding_env"], "SF_ORACLE_AXON_ENCODER_CMD")
        self.assertIn("axon-encoder", probe["note"])

    def test_the_availability_report_carries_no_host_details(self):
        # This block is compared byte for byte by the golden fixture, so it must
        # describe the oracle binding and nothing about the machine.
        report = oracles.availability_report(("axon-encoder",), environ={})
        self.assertEqual(sorted(report), ["all_bound", "protocol", "runtimes", "unbound"])


class DeclaredStatus(unittest.TestCase):
    def test_a_failing_record_relabelled_as_accepted_is_rejected(self):
        item = self.rejected_memory_record()
        item["validation"]["status"] = "accepted"
        item["validation"]["reasons"] = []
        findings = record.validate_record(item)
        self.assertTrue(any("fails its own checks" in f for f in findings), findings)

    def test_a_rewritten_rejection_reason_is_rejected(self):
        item = self.rejected_memory_record()
        item["validation"]["reasons"] = ["nothing to see here"]
        findings = record.validate_record(item)
        self.assertTrue(any("do not match the recomputed findings" in f for f in findings))

    def test_a_rejected_record_with_no_reason_is_rejected(self):
        item = build(families.ENCODER_FAMILY)
        item["validation"]["status"] = "rejected"
        item["validation"]["reasons"] = []
        findings = record.validate_record(item)
        self.assertTrue(any("no reason is recorded" in f for f in findings), findings)

    def test_an_unknown_status_is_rejected(self):
        item = build(families.ENCODER_FAMILY)
        item["validation"]["status"] = "probably fine"
        findings = record.validate_record(item)
        self.assertTrue(any("accepted or rejected" in f for f in findings), findings)

    def test_a_rejected_record_keeps_a_clean_envelope(self):
        item = self.rejected_memory_record()
        layers = record.classify(item)
        self.assertEqual(layers["envelope"], [])
        self.assertEqual(layers["status"], [])
        self.assertTrue(layers["family"])

    def rejected_memory_record(self):
        for index in range(24):
            item = build(families.MEMORY_FAMILY, index)
            if item["validation"]["status"] == "rejected":
                return item
        self.skipTest("no rejected temporal-memory record in the first 24 proposals")
        return None


class FamilyInvariants(unittest.TestCase):
    def test_temporal_dependence_is_required(self):
        item = build(families.MEMORY_FAMILY)
        measured = item["result"]["measured"]
        if measured["temporal_dependence"]["demonstrated"]:
            self.assertEqual(item["validation"]["status"], "accepted")
        else:
            self.assertEqual(item["validation"]["status"], "rejected")
            self.assertTrue(
                any("temporal dependence" in r for r in item["validation"]["reasons"])
            )

    def test_a_forged_temporal_dependence_flag_is_caught(self):
        item = build(families.MEMORY_FAMILY)
        measured = item["result"]["measured"]
        measured["temporal_dependence"]["demonstrated"] = not measured["temporal_dependence"][
            "demonstrated"
        ]
        findings = record.validate_record(item)
        # Either the hash no longer covers the result, or the gate now disagrees
        # with the declared status. Both are fatal.
        self.assertTrue(findings)

    def test_the_cue_ablation_control_is_always_present(self):
        for index in range(6):
            item = build(families.MEMORY_FAMILY, index)
            with self.subTest(index=index):
                self.assertIn("cue_ablation", item["result"]["measured"]["probes"])

    def test_an_ambiguous_response_is_rejected(self):
        item = build(families.MEMORY_FAMILY)
        item["result"]["measured"]["baseline"]["response_ambiguous"] = True
        item["result_hash"] = canon.digest(item["result"])
        findings = record.validate_record(item, check_declared_status=False)
        self.assertTrue(any("ambiguous" in f for f in findings), findings)

    def test_the_neuron_intervention_changes_exactly_one_parameter(self):
        for index in range(6):
            item = build(families.NEURON_FAMILY, index)
            configuration = item["oracle"]["configuration"]
            changed = [
                key
                for key in configuration["before"]
                if configuration["before"][key] != configuration["after"][key]
            ]
            with self.subTest(index=index):
                self.assertEqual(changed, [configuration["intervened_parameter"]])

    def test_a_second_changed_neuron_parameter_is_caught(self):
        item = build(families.NEURON_FAMILY)
        item["oracle"]["configuration"]["after"]["v_rest"] = 0.25
        findings = record.validate_record(item, check_declared_status=False)
        self.assertTrue(any("exactly" in f for f in findings), findings)

    def test_an_inconsistent_neuron_delta_is_caught(self):
        item = build(families.NEURON_FAMILY)
        item["result"]["measured"]["delta"]["spike_count_delta"] += 3
        item["result_hash"] = canon.digest(item["result"])
        findings = record.validate_record(item, check_declared_status=False)
        self.assertTrue(any("spike_count_delta" in f for f in findings), findings)

    def test_an_encoder_winner_outside_the_pair_is_caught(self):
        item = build(families.ENCODER_FAMILY)
        pair = item["scenario"]["encoding_pair"]
        outsider = next(e for e in ("rate", "latency", "delta", "temporal") if e not in pair)
        item["result"]["measured"]["winner"] = outsider
        item["result_hash"] = canon.digest(item["result"])
        findings = record.validate_record(item, check_declared_status=False)
        self.assertTrue(any("not one of the compared encodings" in f for f in findings))

    def test_a_broken_weight_identity_is_caught(self):
        item = build(families.CREDIT_FAMILY)
        item["result"]["measured"]["plasticity"]["weights_after"][0] += 0.5
        item["result_hash"] = canon.digest(item["result"])
        findings = record.validate_record(item, check_declared_status=False)
        self.assertTrue(any("after = before + delta" in f for f in findings), findings)

    def test_a_forged_update_applied_flag_is_caught(self):
        item = build(families.CREDIT_FAMILY)
        plasticity = item["result"]["measured"]["plasticity"]
        plasticity["update_applied"] = not plasticity["update_applied"]
        item["result_hash"] = canon.digest(item["result"])
        findings = record.validate_record(item, check_declared_status=False)
        self.assertTrue(any("update_applied" in f for f in findings), findings)

    def test_the_credit_chain_reports_both_stages(self):
        item = build(families.CREDIT_FAMILY)
        self.assertEqual(
            [stage["oracle_id"] for stage in item["oracle"]["stages"]],
            ["critic-ref", "plasticity-ref"],
        )
        self.assertEqual(sorted(item["result"]["measured"]), ["critic", "plasticity"])
        self.assertEqual(item["oracle"]["requested_runtime"], ["limbic-critic", "plasticity-lab"])

    def test_a_mesh_sink_flag_that_contradicts_the_arrivals_is_caught(self):
        item = build(families.MESH_FAMILY)
        before = item["result"]["measured"]["before"]
        before["sink_reached"] = not before["sink_reached"]
        item["result_hash"] = canon.digest(item["result"])
        findings = record.validate_record(item, check_declared_status=False)
        self.assertTrue(any("sink_reached" in f for f in findings), findings)

    def test_family_checks_survive_a_structurally_odd_record(self):
        item = build(families.MESH_FAMILY)
        item["result"]["measured"]["before"] = {}
        item["result_hash"] = canon.digest(item["result"])
        layers = record.classify(item)
        self.assertTrue(layers["envelope"] or layers["family"])


class Reproducibility(unittest.TestCase):
    def test_every_family_reproduces_from_its_stored_scenario(self):
        for family in families.FAMILY_NAMES:
            for index in range(3):
                item = build(family, index)
                with self.subTest(family=family, index=index):
                    status, detail = record.reproduce(item)
                    self.assertEqual(status, "reproduced", detail)
                    self.assertEqual(detail, item["result_hash"])

    def test_the_same_seed_produces_the_same_record(self):
        for family in families.FAMILY_NAMES:
            with self.subTest(family=family):
                self.assertEqual(
                    canon.dumps_record(build(family, 2)),
                    canon.dumps_record(build(family, 2)),
                )

    def test_a_different_index_produces_a_different_record(self):
        left = build(families.NEURON_FAMILY, 0)
        right = build(families.NEURON_FAMILY, 1)
        self.assertNotEqual(left["proposal_hash"], right["proposal_hash"])

    def test_a_tampered_measurement_does_not_reproduce(self):
        item = build(families.NEURON_FAMILY)
        item["result"]["measured"]["after"]["spike_count"] += 1
        item["result_hash"] = canon.digest(item["result"])
        status, detail = record.reproduce(item)
        self.assertEqual(status, "mismatch", detail)

    def test_reproduce_reports_unavailable_rather_than_guessing(self):
        item = build(families.ENCODER_FAMILY)
        item["oracle"]["implementation"] = "named-runtime"
        status, detail = record.reproduce(item)
        self.assertEqual(status, "unavailable")
        self.assertIn("named-runtime", detail)


class ExternalOracleProtocol(unittest.TestCase):
    """The boundary itself, exercised with a protocol double.

    The double is not a simulator and its numbers are not measurements; these
    tests check that the pipeline talks the protocol correctly and refuses
    every malformed answer.
    """

    def adapter(self, mode="ok"):
        return oracles.bind(
            runtime="axon-encoder",
            oracle_id="encoder-ref",
            oracle_type="spike-encoder",
            description="reference",
            reference_fn=lambda request: ({"unused": True}, {}),
            environ=double_env(mode),
        )

    def test_an_unbound_runtime_falls_back_to_the_reference_adapter(self):
        reference = oracles.bind(
            runtime="axon-encoder",
            oracle_id="encoder-ref",
            oracle_type="spike-encoder",
            description="reference",
            reference_fn=lambda request: ({"ok": True}, {}),
            environ={},
        )
        self.assertIsInstance(reference, oracles.ReferenceOracle)
        self.assertEqual(reference.implementation, "reference")

    def test_a_bound_runtime_is_used_and_attributed(self):
        adapter = self.adapter("ok")
        self.assertIsInstance(adapter, oracles.ExternalCommandOracle)
        self.assertEqual(adapter.implementation, "named-runtime")
        self.assertEqual(adapter.authority, "measured-runtime")
        run = adapter.run("spike-encoder-equivalence-pairs", {"configuration": {}, "data": {}})
        self.assertTrue(run.measured["protocol_double"])
        stage = run.stages[0]
        self.assertEqual(stage["implementation"], "named-runtime")
        self.assertEqual(stage["version"], "0.0.0-double")
        self.assertTrue(stage["runtime_commit"])

    def test_the_request_reaches_the_runtime_in_protocol_form(self):
        run = self.adapter("ok").run("a-family", {"configuration": {"x": 1}, "data": {"y": 2}})
        self.assertEqual(run.measured["echoed_family"], "a-family")
        self.assertEqual(run.measured["echoed_request_keys"], ["configuration", "data"])

    def test_every_malformed_answer_raises_rather_than_falling_back(self):
        for mode in (
            "fail",
            "badjson",
            "wrongproto",
            "noversion",
            "empty",
            "unknowncommit",
            "badcommit",
        ):
            with self.subTest(mode=mode):
                with self.assertRaises(oracles.OracleError):
                    self.adapter(mode).run("f", {"configuration": {}, "data": {}})

    def test_a_missing_command_raises(self):
        adapter = oracles.ExternalCommandOracle(
            oracle_id="axon-encoder",
            oracle_type="spike-encoder",
            description="missing",
            runtime="axon-encoder",
            command=[str(REPO / "definitely" / "not" / "here")],
        )
        with self.assertRaises(oracles.OracleError):
            adapter.run("f", {})

    def test_a_bound_record_declares_the_runtime(self):
        item = build(families.ENCODER_FAMILY, environ=double_env("ok"))
        self.assertEqual(item["oracle"]["implementation"], "named-runtime")
        self.assertEqual(item["oracle"]["id"], "axon-encoder")
        self.assertTrue(item["oracle"]["runtime_bound"])
        self.assertEqual(item["oracle"]["availability"]["unbound"], [])
        self.assertEqual(item["result"]["produced_by"], "axon-encoder")
        # Only a bound runtime can clear the publication bar at all; this
        # particular record still cannot, because the double answers in a shape
        # the family does not recognise.
        self.assertTrue(record.publishability(item, ())[0])
        self.assertEqual(item["validation"]["status"], "rejected")
        self.assertFalse(item["validation"]["publishable"])

    def test_a_named_runtime_stage_requires_a_resolved_hex_commit(self):
        item = build(families.ENCODER_FAMILY, environ=double_env("ok"))
        item["oracle"]["stages"][0]["runtime_commit"] = "unknown"
        findings = record.validate_record(item)
        self.assertTrue(any("runtime_commit" in f for f in findings), findings)

    def test_a_runtime_answering_in_the_wrong_shape_is_rejected_not_crashed(self):
        item = build(families.ENCODER_FAMILY, environ=double_env("ok"))
        self.assertEqual(item["validation"]["status"], "rejected")
        self.assertTrue(
            any("family checks could not run" in r for r in item["validation"]["reasons"]),
            item["validation"]["reasons"],
        )
        self.assertIsNone(item["validation"]["candidate_prediction_correct"])

    def test_a_half_bound_chain_is_labelled_mixed(self):
        adapter = families.spec_for(families.CREDIT_FAMILY).oracle(
            double_env("ok", runtimes=("limbic-critic",))
        )
        self.assertEqual(adapter.implementation, "mixed")
        self.assertEqual(adapter.authority, "mixed-reference-and-runtime")
        self.assertEqual(adapter.oracle_id, "limbic-critic+plasticity-ref")

    def test_a_chain_stage_that_cannot_consume_its_input_fails_closed(self):
        # The double answers stage one in a shape the plasticity stage cannot
        # use. That must surface as an OracleError, not a traceback.
        with self.assertRaises(oracles.OracleError):
            build(
                families.CREDIT_FAMILY,
                environ=double_env("ok", runtimes=("limbic-critic",)),
            )

    def test_a_failing_bound_oracle_drops_the_record(self):
        with self.assertRaises(oracles.OracleError):
            build(families.ENCODER_FAMILY, environ=double_env("fail"))

    def test_the_environment_key_is_derived_mechanically(self):
        self.assertEqual(oracles.env_key("axon-encoder"), "SF_ORACLE_AXON_ENCODER_CMD")
        self.assertEqual(oracles.env_key("plasticity-lab"), "SF_ORACLE_PLASTICITY_LAB_CMD")

    def test_a_runtime_on_path_without_a_binding_is_not_claimed(self):
        probe = oracles.probe_runtime("python3", environ={})
        self.assertTrue(probe["on_path"])
        self.assertFalse(probe["bound"])
        self.assertIn("no sf-oracle/1 binding", probe["note"])

    def test_an_empty_measurement_from_any_oracle_is_refused(self):
        with self.assertRaises(oracles.OracleError):
            oracles.OracleRun({}, {}, [])
        with self.assertRaises(oracles.OracleError):
            oracles.OracleRun({"a": 1}, None, [])


class OracleProvenance(unittest.TestCase):
    def test_the_module_digest_pins_the_implementation_sources(self):
        here = REPO / "pipelines" / "oracle_grounded"
        expected = canon.digest_files(
            str(here / name) for name in oracles.IMPLEMENTATION_SOURCES
        )
        self.assertEqual(oracles.module_digest(), expected)
        self.assertTrue(canon.is_digest(oracles.module_digest()))

    def test_file_digests_are_independent_of_checkout_path(self):
        here = REPO / "pipelines" / "oracle_grounded"
        original = [here / name for name in oracles.IMPLEMENTATION_SOURCES]
        with tempfile.TemporaryDirectory(prefix="oracle-digest-") as temp:
            copied = []
            for source in original:
                destination = Path(temp) / source.name
                shutil.copy2(source, destination)
                copied.append(destination)
            self.assertEqual(canon.digest_files(original), canon.digest_files(copied))

    def test_resolve_commit_returns_a_pair(self):
        commit, dirty = oracles.resolve_commit()
        self.assertIsInstance(commit, str)
        self.assertTrue(commit)
        self.assertIn(type(dirty), (bool, type(None)))

    def test_resolve_commit_reports_unknown_outside_a_repository(self):
        commit, dirty = oracles.resolve_commit(repo_root=Path("/"))
        self.assertEqual((commit, dirty), ("unknown", None))

    def test_the_oracle_block_retains_the_configuration_and_seed(self):
        for family in families.FAMILY_NAMES:
            item = build(family)
            with self.subTest(family=family):
                self.assertTrue(item["oracle"]["configuration"])
                self.assertIsInstance(item["oracle"]["seed"], int)
                self.assertTrue(item["oracle"]["units"])
                self.assertEqual(item["oracle"]["repo"], oracles.REPO_SLUG)
                self.assertEqual(item["oracle"]["commit"], PINNED_COMMIT)

    def test_the_stored_configuration_is_what_the_oracle_was_handed(self):
        for family in families.FAMILY_NAMES:
            item = build(family)
            spec = families.spec_for(family)
            request = spec.build_request(item["scenario"], item["intervention"])
            with self.subTest(family=family):
                self.assertEqual(
                    canon.normalize(request["configuration"]),
                    canon.normalize(item["oracle"]["configuration"]),
                )

    def test_reproduction_rejects_a_tampered_stored_configuration(self):
        item = build(families.ENCODER_FAMILY)
        item["oracle"]["configuration"]["max_rate_hz"] = 1
        status, detail = record.reproduce(item)
        self.assertEqual(status, "mismatch")
        self.assertIn("configuration", detail)

    def test_the_double_is_a_runnable_script(self):
        completed = subprocess.run(
            [sys.executable, str(DOUBLE), "ok"],
            input=json.dumps({"family": "f", "request": {}}),
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertTrue(json.loads(completed.stdout)["measured"]["protocol_double"])


class RecordIsSelfContained(unittest.TestCase):
    def test_a_record_survives_deep_copy_and_still_validates(self):
        item = build(families.MESH_FAMILY)
        self.assertEqual(record.validate_record(copy.deepcopy(item)), [])

    def test_a_non_object_record_is_refused(self):
        for value in ("a string", 5, None, []):
            with self.subTest(value=value):
                layers = record.classify(value)
                self.assertTrue(layers["envelope"])

    def test_a_missing_envelope_key_is_refused(self):
        item = build(families.MESH_FAMILY)
        del item["oracle"]
        findings = record.validate_record(item)
        self.assertTrue(any("missing envelope keys" in f for f in findings), findings)

    def test_a_wrong_schema_id_is_refused(self):
        item = build(families.MESH_FAMILY)
        item["schema"] = "something-else/v9"
        findings = record.validate_record(item)
        self.assertTrue(any("schema must be" in f for f in findings), findings)

    def test_meta_identifies_the_family_and_round(self):
        item = build(families.MESH_FAMILY, round_number=4)
        self.assertEqual(item["meta"]["round"], 4)
        self.assertIn(families.MESH_FAMILY, item["meta"]["tags"])
        self.assertTrue(item["id"].startswith(families.MESH_FAMILY))
        self.assertIn("r04", item["id"])


if __name__ == "__main__":
    unittest.main()
