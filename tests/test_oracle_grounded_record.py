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
import threading
import time
import unittest
from pathlib import Path
from unittest import mock

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "pipelines"))

from oracle_grounded import (  # noqa: E402
    canon,
    families,
    generators,
    oracles,
    record,
    schema_validation,
    sim,
)

DOUBLE = REPO / "tests" / "fixtures" / "oracle-grounded" / "protocol_double.py"
PINNED_COMMIT = oracles.resolve_commit(REPO)[0]


def build(family, index=0, **kwargs):
    kwargs.setdefault("commit", PINNED_COMMIT)
    kwargs.setdefault("dirty", False)
    kwargs.setdefault("environ", {})
    return record.build_record(family, index, seed=12345, **kwargs)


def double_env(mode="ok", runtimes=("axon-encoder",)):
    command = f"{sys.executable} {DOUBLE} {mode}"
    return {oracles.env_key(runtime): command for runtime in runtimes}


def result_findings(item):
    item["result_hash"] = canon.digest(item["result"])
    return record.validate_record(item, check_declared_status=False)


def proposal_findings(item):
    item["proposal_hash"] = canon.digest(record.proposal_of(item))
    return record.validate_record(item, check_declared_status=False)


def relabel_as_named_runtime(item):
    """Create a structurally valid synthetic named-runtime record for gate tests."""
    item = copy.deepcopy(item)
    oracle = item["oracle"]
    oracle["implementation"] = "named-runtime"
    oracle["authority"] = "measured-runtime"
    item["provenance"]["claimed"] = "measured-runtime"
    item["meta"]["tags"][-1] = "named-runtime"
    oracle["runtime_bound"] = True
    oracle["availability"]["all_bound"] = True
    oracle["availability"]["unbound"] = []
    for probe in oracle["availability"]["runtimes"]:
        probe["bound"] = True
    stage_ids = []
    for stage, runtime in zip(oracle["stages"], oracle["requested_runtime"], strict=True):
        stage["implementation"] = "named-runtime"
        stage["oracle_id"] = runtime
        stage["version"] = "0.0.0-double"
        stage["runtime_commit"] = "a" * 40
        stage["executable"] = runtime
        stage.pop("module_digest", None)
        stage_ids.append(runtime)
    oracle["id"] = "+".join(stage_ids)
    item["result"]["produced_by"] = oracle["id"]
    item["result_hash"] = canon.digest(item["result"])
    item["validation"] = record.assess(item)
    return item


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
        self.assertTrue(any("authoritative" in finding for finding in record.validate_record(item)))

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
        self.assertIn(item["validation"]["candidate_prediction_correct"], (True, False, None))
        self.assertNotIn("candidate_prediction", item["result"]["measured"])


class HashesCoverWhatTheyClaim(unittest.TestCase):
    def test_the_proposal_hash_covers_exactly_the_generator_sections(self):
        item = build(families.ENCODER_FAMILY)
        self.assertEqual(item["proposal_hash"], canon.digest(record.proposal_of(item)))
        self.assertEqual(sorted(record.proposal_of(item)), sorted(record.GENERATOR_SECTIONS))

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
        self.assertTrue(any("$.result" in f and "required" in f for f in findings), findings)

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

    def test_source_commit_requires_a_full_lowercase_object_id(self):
        for forged in ("main", "a" * 39, "a" * 41, "A" * 40, "0x" + "a" * 40):
            item = build(families.NEURON_FAMILY)
            item["oracle"]["commit"] = forged
            findings = record.validate_record(item, check_declared_status=False)
            with self.subTest(commit=forged):
                self.assertTrue(any("oracle.commit" in f for f in findings), findings)
        self.assertTrue(oracles.is_source_commit("a" * 40))
        self.assertTrue(oracles.is_source_commit("b" * 64))

    def test_a_syntactically_valid_but_absent_source_commit_is_rejected(self):
        absent = "f" * 40
        self.assertTrue(oracles.is_source_commit(absent))
        self.assertIsNone(oracles.resolve_source_commit(absent))
        item = build(families.NEURON_FAMILY)
        item["oracle"]["commit"] = absent
        findings = record.validate_record(item, check_declared_status=False)
        self.assertTrue(any("does not resolve" in finding for finding in findings), findings)

    def test_generator_seed_must_reproduce_the_stored_proposal(self):
        item = build(families.ENCODER_FAMILY)
        item["generator"]["seed"] += 1
        item["oracle"]["seed"] = item["generator"]["seed"]
        item["proposal_hash"] = canon.digest(record.proposal_of(item))
        findings = record.validate_record(item, check_declared_status=False)
        self.assertTrue(
            any("generator.seed does not reproduce" in finding for finding in findings),
            findings,
        )

    def test_a_missing_module_digest_is_an_error(self):
        item = build(families.NEURON_FAMILY)
        item["oracle"]["module_digest"] = "not-a-digest"
        findings = record.validate_record(item)
        self.assertTrue(any("module_digest" in f for f in findings), findings)

    def test_a_self_consistent_stale_reference_digest_is_rejected(self):
        item = build(families.NEURON_FAMILY)
        forged = canon.digest({"different": "reference implementation"})
        item["oracle"]["module_digest"] = forged
        item["oracle"]["stages"][0]["module_digest"] = forged
        findings = record.validate_record(item, check_declared_status=False)
        self.assertTrue(any("current reference implementation" in f for f in findings), findings)

    def test_named_runtime_records_still_bind_the_request_module_digest(self):
        item = relabel_as_named_runtime(build(families.ENCODER_FAMILY))
        item["oracle"]["module_digest"] = canon.digest({"forged": "named-runtime digest"})
        findings = record.validate_record(item, check_declared_status=False)
        self.assertTrue(any("current reference implementation" in f for f in findings), findings)

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
        self.assertTrue(any("provenance.kind" in f for f in findings), findings)

    def test_protocol_execution_cannot_self_attest_hil_or_designed_provenance(self):
        for item in (
            build(families.NEURON_FAMILY),
            relabel_as_named_runtime(build(families.ENCODER_FAMILY)),
        ):
            for forged in ("hil", "designed"):
                candidate = copy.deepcopy(item)
                candidate["provenance"]["kind"] = forged
                findings = record.validate_record(candidate, check_declared_status=False)
                with self.subTest(implementation=item["oracle"]["implementation"], kind=forged):
                    self.assertTrue(
                        any("does not attest physical hardware" in f for f in findings),
                        findings,
                    )


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

    def test_a_rejected_named_runtime_record_cannot_claim_publishability(self):
        item = next(
            relabel_as_named_runtime(build(families.MEMORY_FAMILY, index))
            for index in range(24)
            if build(families.MEMORY_FAMILY, index)["validation"]["status"] == "rejected"
        )
        self.assertEqual(item["validation"]["status"], "rejected")
        self.assertFalse(item["validation"]["publishable"])
        item["validation"]["publishable"] = True
        findings = record.validate_record(item)
        self.assertTrue(any("recomputed value" in f for f in findings), findings)

    def test_relabelling_a_reference_run_as_a_named_runtime_is_rejected(self):
        item = build(families.ENCODER_FAMILY)
        item["oracle"]["implementation"] = "named-runtime"
        item["oracle"]["authority"] = "measured-runtime"
        findings = record.validate_record(item)
        self.assertTrue(
            any("not every stage was run by a named runtime" in f for f in findings), findings
        )

    def test_coordinated_oracle_identity_and_version_rewrites_are_rejected(self):
        item = build(families.ENCODER_FAMILY)
        oracle = item["oracle"]
        oracle["id"] = "forged-reference-oracle"
        oracle["version"] = "999.0.0-forged"
        oracle["stages"][0]["oracle_id"] = "different-forged-stage-id"
        oracle["stages"][0]["version"] = "888.0.0-forged"
        item["result"]["produced_by"] = oracle["id"]
        findings = result_findings(item)
        self.assertTrue(any("canonical reference adapter" in f for f in findings), findings)
        self.assertTrue(any("oracle.id" in f for f in findings), findings)
        self.assertTrue(any("oracle.version" in f for f in findings), findings)

    def test_named_runtime_stage_requires_its_runtime_identity_and_executable(self):
        item = build(families.ENCODER_FAMILY)
        oracle = item["oracle"]
        oracle["implementation"] = "named-runtime"
        oracle["authority"] = "measured-runtime"
        oracle["runtime_bound"] = True
        oracle["availability"]["all_bound"] = True
        oracle["availability"]["unbound"] = []
        oracle["availability"]["runtimes"][0]["bound"] = True
        stage = oracle["stages"][0]
        stage["implementation"] = "named-runtime"
        stage["runtime_commit"] = "a" * 40
        item["provenance"]["claimed"] = "measured-runtime"
        item["meta"]["tags"][-1] = "named-runtime"
        item["validation"] = record.assess(item)
        findings = record.validate_record(item, check_declared_status=False)
        self.assertTrue(any("oracle_id" in f for f in findings), findings)
        self.assertTrue(any("executable" in f for f in findings), findings)

    def test_named_runtime_publication_does_not_claim_external_attestation(self):
        item = relabel_as_named_runtime(build(families.ENCODER_FAMILY))
        publishable, reason = record.publishability(item, ())
        self.assertTrue(publishable)
        self.assertIn("does not provide external attestation", reason)

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

    def test_each_stage_implementation_must_match_its_runtime_binding(self):
        item = build(families.CREDIT_FAMILY)
        availability = item["oracle"]["availability"]
        availability["runtimes"][0]["bound"] = True
        availability["unbound"] = ["plasticity-lab"]
        findings = record.validate_record(item)
        self.assertTrue(any("corresponding runtime binding" in f for f in findings), findings)

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
        probe = oracles.probe_runtime("axon-encoder", environ={})
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
        self.assertTrue(any("recomputed status" in f for f in findings), findings)

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
        self.assertTrue(any("recomputed status" in f for f in findings), findings)

    def test_an_unknown_status_is_rejected(self):
        item = build(families.ENCODER_FAMILY)
        item["validation"]["status"] = "probably fine"
        findings = record.validate_record(item)
        self.assertTrue(any("validation.status" in f for f in findings), findings)

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
            self.assertTrue(any("temporal dependence" in r for r in item["validation"]["reasons"]))

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

    def test_temporal_dependence_is_derived_from_the_ablation_responses(self):
        item = next(
            build(families.MEMORY_FAMILY, index)
            for index in range(24)
            if build(families.MEMORY_FAMILY, index)["validation"]["status"] == "accepted"
        )
        measured = item["result"]["measured"]
        for probe in measured["probes"].values():
            probe["response"] = measured["baseline"]["response"]
            probe["state_retained_at_probe"] = measured["baseline"][
                "state_retained_at_probe"
            ]
        measured["temporal_dependence"]["demonstrated"] = True
        measured["temporal_dependence"]["changed_by"] = ["cue_ablation"]
        item["result_hash"] = canon.digest(item["result"])
        findings = record.validate_record(item, check_declared_status=False)
        self.assertTrue(any("demonstrated" in f for f in findings), findings)
        self.assertTrue(any("changed_by" in f for f in findings), findings)

    def test_retained_latch_state_counts_as_temporal_dependence(self):
        baseline = {"response": "none", "state_retained_at_probe": True}
        same = {"response": "none", "state_retained_at_probe": True}
        latch_gone = {"response": "none", "state_retained_at_probe": False}
        self.assertFalse(families._memory_ablation_changed(baseline, same))
        self.assertTrue(families._memory_ablation_changed(baseline, latch_gone))
        self.assertTrue(
            families._memory_ablation_changed(
                {"response": "A", "state_retained_at_probe": True},
                {"response": "none", "state_retained_at_probe": True},
            )
        )

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
        self.assertTrue(any("configuration" in f for f in findings), findings)

    def test_an_inconsistent_neuron_delta_is_caught(self):
        item = build(families.NEURON_FAMILY)
        item["result"]["measured"]["delta"]["spike_count_delta"] += 3
        item["result_hash"] = canon.digest(item["result"])
        findings = record.validate_record(item, check_declared_status=False)
        self.assertTrue(any("spike_count_delta" in f for f in findings), findings)

    def test_every_redundant_neuron_delta_is_recomputed(self):
        for field in (
            "mean_rate_delta_hz",
            "first_spike_shift_ms",
            "mean_isi_delta_ms",
            "v_mean_delta",
        ):
            item = build(families.NEURON_FAMILY)
            item["result"]["measured"]["delta"][field] = 123.456
            item["result_hash"] = canon.digest(item["result"])
            findings = record.validate_record(item, check_declared_status=False)
            with self.subTest(field=field):
                self.assertTrue(any(field in f for f in findings), findings)

    def test_an_encoder_winner_outside_the_pair_is_caught(self):
        item = build(families.ENCODER_FAMILY)
        pair = item["scenario"]["encoding_pair"]
        outsider = next(e for e in ("rate", "latency", "delta", "temporal") if e not in pair)
        item["result"]["measured"]["winner"] = outsider
        item["result_hash"] = canon.digest(item["result"])
        findings = record.validate_record(item, check_declared_status=False)
        self.assertTrue(any("not one of the compared encodings" in f for f in findings))

    def test_encoder_tiebreak_and_tie_winners_are_recomputed(self):
        item = next(
            build(families.ENCODER_FAMILY, index)
            for index in range(200)
            if build(families.ENCODER_FAMILY, index)["result"]["measured"]["winner_basis"]
            == "spike_count_tiebreak"
        )
        measured = item["result"]["measured"]
        pair = item["scenario"]["encoding_pair"]
        measured["winner"] = pair[1] if measured["winner"] == pair[0] else pair[0]
        item["result_hash"] = canon.digest(item["result"])
        findings = record.validate_record(item, check_declared_status=False)
        self.assertTrue(any("spike_count_tiebreak" in f for f in findings), findings)

        item = build(families.ENCODER_FAMILY)
        measured = item["result"]["measured"]
        measured["encoding_b"]["information_retention"] = measured["encoding_a"][
            "information_retention"
        ]
        measured["encoding_b"]["spike_count"] = measured["encoding_a"]["spike_count"]
        measured["retention_margin"] = 0.0
        measured["winner_basis"] = "tie"
        measured["winner"] = item["scenario"]["encoding_pair"][0]
        item["result_hash"] = canon.digest(item["result"])
        findings = record.validate_record(item, check_declared_status=False)
        self.assertTrue(any("measured tie decision" in f for f in findings), findings)

    def test_an_unknown_encoder_winner_basis_is_rejected(self):
        item = build(families.ENCODER_FAMILY)
        item["result"]["measured"]["winner_basis"] = "trust-me"
        item["result_hash"] = canon.digest(item["result"])
        findings = record.validate_record(item, check_declared_status=False)
        self.assertTrue(any("winner_basis" in f for f in findings), findings)

    def test_a_broken_weight_identity_is_caught(self):
        item = build(families.CREDIT_FAMILY)
        item["result"]["measured"]["plasticity"]["weights_after"][0] += 0.5
        item["result_hash"] = canon.digest(item["result"])
        findings = record.validate_record(item, check_declared_status=False)
        self.assertTrue(any("after = before + delta" in f for f in findings), findings)

    def test_self_consistent_forged_weight_deltas_do_not_bypass_the_learning_rule(self):
        item = build(families.CREDIT_FAMILY)
        plasticity = item["result"]["measured"]["plasticity"]
        plasticity["weight_deltas"] = [0.0] * len(plasticity["weights_before"])
        plasticity["weights_after"] = list(plasticity["weights_before"])
        plasticity["update_applied"] = False
        item["result_hash"] = canon.digest(item["result"])
        findings = record.validate_record(item, check_declared_status=False)
        rule_findings = [finding for finding in findings if "retained learning rule" in finding]
        self.assertEqual(len(rule_findings), len(plasticity["weights_before"]), findings)

    def test_every_plasticity_behavior_delta_is_recomputed(self):
        for field in (
            "spike_count_delta",
            "output_rate_delta_hz",
            "first_spike_shift_ms",
        ):
            item = build(families.CREDIT_FAMILY)
            item["result"]["measured"]["plasticity"]["behavior_delta"][field] = 999
            item["result_hash"] = canon.digest(item["result"])
            findings = record.validate_record(item, check_declared_status=False)
            with self.subTest(field=field):
                self.assertTrue(any(field in f for f in findings), findings)

    def test_a_forged_update_applied_flag_is_caught(self):
        item = build(families.CREDIT_FAMILY)
        plasticity = item["result"]["measured"]["plasticity"]
        plasticity["update_applied"] = not plasticity["update_applied"]
        item["result_hash"] = canon.digest(item["result"])
        findings = record.validate_record(item, check_declared_status=False)
        self.assertTrue(any("update_applied" in f for f in findings), findings)

    def test_critic_modulators_are_recomputed_from_the_outcome(self):
        item = next(
            build(families.CREDIT_FAMILY, index)
            for index in range(24)
            if build(families.CREDIT_FAMILY, index)["validation"]["status"] == "accepted"
        )
        item["result"]["measured"]["critic"]["serotonin"] = 0.0
        findings = result_findings(item)
        self.assertTrue(any("critic.serotonin" in finding for finding in findings), findings)

    def test_eligibility_is_recomputed_before_the_weight_update(self):
        item = next(
            build(families.CREDIT_FAMILY, index)
            for index in range(24)
            if build(families.CREDIT_FAMILY, index)["validation"]["status"] == "accepted"
        )
        plasticity = item["result"]["measured"]["plasticity"]
        critic = item["result"]["measured"]["critic"]
        config = item["oracle"]["configuration"]["plasticity"]
        forged = [trace + 1.0 for trace in plasticity["eligibility"]]
        plasticity["eligibility"] = forged
        deltas = []
        updated = []
        for start, trace in zip(plasticity["weights_before"], forged, strict=True):
            raw_delta = (
                config["learning_rate"] * trace * critic["dopamine_phasic"] * plasticity["modulatory_gain"]
            )
            new_weight = sim.clamp(start + raw_delta, config["w_min"], config["w_max"])
            deltas.append(new_weight - start)
            updated.append(new_weight)
        plasticity["weight_deltas"] = deltas
        plasticity["weights_after"] = updated
        findings = result_findings(item)
        self.assertTrue(any("eligibility" in finding for finding in findings), findings)

    def test_post_update_behavior_is_re_run_from_the_updated_circuit(self):
        item = next(
            build(families.CREDIT_FAMILY, index)
            for index in range(24)
            if build(families.CREDIT_FAMILY, index)["validation"]["status"] == "accepted"
        )
        post = item["result"]["measured"]["plasticity"]["post_update_behavior"]
        post["spike_times_ms"] = []
        post["spike_count"] = 0
        post["first_spike_ms"] = None
        post["output_rate_hz"] = 0.0
        findings = result_findings(item)
        self.assertTrue(
            any("post_update_behavior" in finding and "re-run" in finding for finding in findings),
            findings,
        )

    def test_encoder_excerpt_is_bound_to_the_recomputed_spike_train(self):
        item = build(families.ENCODER_FAMILY)
        excerpt = item["result"]["measured"]["encoding_a"]["representation_excerpt"]
        self.assertTrue(excerpt)
        excerpt[0]["t_ms"] = excerpt[0]["t_ms"] + 1.0
        findings = result_findings(item)
        self.assertTrue(
            any("representation_excerpt is not the prefix" in finding for finding in findings),
            findings,
        )

    def test_impossible_neuron_voltage_summaries_are_rejected(self):
        item = build(families.NEURON_FAMILY)
        item["result"]["measured"]["before"]["v_min"] = 10.0
        item["result"]["measured"]["before"]["v_max"] = -10.0
        findings = result_findings(item)
        self.assertTrue(any("v_min is greater than v_max" in finding for finding in findings), findings)

    def test_the_credit_chain_reports_both_stages(self):
        item = build(families.CREDIT_FAMILY)
        self.assertEqual(
            [stage["oracle_id"] for stage in item["oracle"]["stages"]],
            ["critic-ref", "plasticity-ref"],
        )
        self.assertEqual(sorted(item["result"]["measured"]), ["critic", "plasticity"])
        self.assertEqual(item["oracle"]["requested_runtime"], ["limbic-critic", "plasticity-lab"])

    def test_memory_response_labels_are_derived_for_baseline_and_every_control(self):
        item = next(
            build(families.MEMORY_FAMILY, index)
            for index in range(24)
            if len(build(families.MEMORY_FAMILY, index)["result"]["measured"]["probes"]) > 1
        )
        measured = item["result"]["measured"]
        trials = [("baseline", measured["baseline"]), *sorted(measured["probes"].items())]
        for name, _trial in trials:
            candidate = copy.deepcopy(item)
            target = (
                candidate["result"]["measured"]["baseline"]
                if name == "baseline"
                else candidate["result"]["measured"]["probes"][name]
            )
            target["response"] = "B" if target["response"] != "B" else "A"
            target["response_latency_ms"] = 0.0
            findings = result_findings(candidate)
            with self.subTest(trial=name):
                self.assertTrue(
                    any(f"{name}.response does not match" in f for f in findings),
                    findings,
                )

    def test_memory_ambiguity_is_derived_from_both_output_counts(self):
        item = build(families.MEMORY_FAMILY)
        trial = item["result"]["measured"]["baseline"]
        trial["output_spike_counts"] = {"OA": 1, "OB": 1}
        trial["response"] = "none"
        trial["response_latency_ms"] = None
        trial["response_ambiguous"] = False
        findings = result_findings(item)
        self.assertTrue(
            any("baseline.response_ambiguous does not match" in f for f in findings),
            findings,
        )

    def test_a_mesh_sink_flag_that_contradicts_the_arrivals_is_caught(self):
        item = build(families.MESH_FAMILY)
        before = item["result"]["measured"]["before"]
        before["sink_reached"] = not before["sink_reached"]
        item["result_hash"] = canon.digest(item["result"])
        findings = record.validate_record(item, check_declared_status=False)
        self.assertTrue(any("sink_reached" in f for f in findings), findings)

    def test_mesh_propagation_delays_are_derived_from_arrival_times(self):
        item = build(families.MESH_FAMILY)
        measured = item["result"]["measured"]
        measured["before"]["propagation_delay_ms"] = 999.0
        measured["after"]["propagation_delay_ms"] = 998.0
        measured["delta"]["propagation_delay_delta_ms"] = -1.0
        item["result_hash"] = canon.digest(item["result"])
        findings = record.validate_record(item, check_declared_status=False)
        self.assertTrue(any("sink minus source arrival" in f for f in findings), findings)

        item = build(families.MESH_FAMILY)
        item["result"]["measured"]["delta"]["propagation_delay_delta_ms"] = 999.0
        item["result_hash"] = canon.digest(item["result"])
        findings = record.validate_record(item, check_declared_status=False)
        self.assertTrue(any("before/after delays" in f for f in findings), findings)

    def test_family_checks_survive_a_structurally_odd_record(self):
        item = build(families.MESH_FAMILY)
        item["result"]["measured"]["before"] = {}
        item["result_hash"] = canon.digest(item["result"])
        layers = record.classify(item)
        self.assertTrue(layers["envelope"] or layers["family"])

    def test_attribute_errors_from_malformed_family_shapes_become_findings(self):
        item = build(families.NEURON_FAMILY)
        item["oracle"]["configuration"]["after"] = []
        layers = record.classify(item)
        self.assertTrue(any("configuration" in f for f in layers["envelope"]))


class AuthoritativeRecordSemantics(unittest.TestCase):
    """Every retained label must be derivable from retained evidence."""

    def test_the_declared_candidate_score_and_layer_checks_are_authenticated(self):
        item = build(families.ENCODER_FAMILY)
        score = item["validation"]["candidate_prediction_correct"]
        item["validation"]["candidate_prediction_correct"] = not score
        findings = record.validate_record(item)
        self.assertTrue(any("candidate_prediction_correct" in f for f in findings), findings)

        item = build(families.ENCODER_FAMILY)
        item["validation"]["checks"]["envelope"] = False
        findings = record.validate_record(item)
        self.assertTrue(any("validation.checks" in f for f in findings), findings)

        item = build(families.ENCODER_FAMILY)
        item["validation"]["checks"]["invented"] = True
        findings = record.validate_record(item)
        self.assertTrue(any("invented" in f for f in findings), findings)

        item = build(families.ENCODER_FAMILY)
        item["validation"]["reasons"] = ["accepted because I said so"]
        findings = record.validate_record(item)
        self.assertTrue(any("validation.reasons" in f for f in findings), findings)

    def test_provenance_claims_and_authorship_lists_are_authenticated(self):
        mutations = {
            "claimed": "some-other-authority",
            "oracle_grounded": False,
            "generator_authored": ["scenario"],
            "oracle_authored": ["result"],
        }
        for field, forged in mutations.items():
            item = build(families.ENCODER_FAMILY)
            item["provenance"][field] = forged
            findings = record.validate_record(item, check_declared_status=False)
            with self.subTest(field=field):
                self.assertTrue(any(field in finding for finding in findings), findings)

    def test_units_must_be_nonempty_equal_and_family_exact(self):
        item = build(families.ENCODER_FAMILY)
        item["result"]["units"] = {}
        findings = result_findings(item)
        self.assertTrue(any("result.units" in f for f in findings), findings)

        item = build(families.ENCODER_FAMILY)
        item["result"]["units"]["rmse"] = "forged-unit"
        findings = result_findings(item)
        self.assertTrue(any("result.units" in f for f in findings), findings)

        item = build(families.ENCODER_FAMILY)
        item["result"]["units"]["rmse"] = "forged-unit"
        item["oracle"]["units"]["rmse"] = "forged-unit"
        findings = result_findings(item)
        self.assertTrue(any("family units contract" in f for f in findings), findings)

    def test_stdlib_schema_gate_enforces_nested_required_types_and_uniqueness(self):
        item = build(families.ENCODER_FAMILY)
        del item["scenario"]["sample_count"]
        findings = proposal_findings(item)
        self.assertTrue(any("sample_count" in f and "required" in f for f in findings), findings)

        item = build(families.ENCODER_FAMILY)
        item["scenario"]["sample_count"] = True
        findings = proposal_findings(item)
        self.assertTrue(any("sample_count" in f and "type" in f for f in findings), findings)

        item = build(families.ENCODER_FAMILY)
        item["scenario"]["encoding_pair"][1] = item["scenario"]["encoding_pair"][0]
        findings = proposal_findings(item)
        self.assertTrue(any("encoding_pair" in f and "unique" in f for f in findings), findings)

        item = build(families.MESH_FAMILY)
        item["scenario"]["nodes"][1] = item["scenario"]["nodes"][0]
        findings = proposal_findings(item)
        self.assertTrue(any("nodes" in f and "unique" in f for f in findings), findings)

        item = build(families.MESH_FAMILY)
        order = item["result"]["measured"]["before"]["firing_order"]
        order.append(order[0])
        findings = result_findings(item)
        self.assertTrue(any("firing_order" in f and "unique" in f for f in findings), findings)

    def test_draft_integer_semantics_accept_integral_floats_only(self):
        schema = {"type": "integer"}
        for value in (0, -4, 1.0, -12.0):
            with self.subTest(accepted=value):
                self.assertEqual(schema_validation._validate(value, schema, schema, "$"), [])
        for value in (True, False, 1.5, float("nan"), float("inf"), float("-inf")):
            with self.subTest(rejected=value):
                self.assertTrue(
                    schema_validation._validate(value, schema, schema, "$"),
                    f"{value!r} was accepted as an integer",
                )

        item = build(families.MEMORY_FAMILY)
        measured = item["result"]["measured"]
        for trial in (measured["baseline"], *measured["probes"].values()):
            trial["output_spike_counts"] = {
                key: float(value) for key, value in trial["output_spike_counts"].items()
            }
        item["result_hash"] = canon.digest(item["result"])
        item["validation"] = record.assess(item)
        layers = record.classify(item)
        self.assertEqual(layers["envelope"], [])
        self.assertEqual(layers["status"], [])

    def test_redundant_record_identity_labels_are_authenticated(self):
        item = build(families.ENCODER_FAMILY)
        item["generator"]["label"] = "another-family#99"
        findings = proposal_findings(item)
        self.assertTrue(any("generator.label" in f for f in findings), findings)

        item = build(families.ENCODER_FAMILY)
        item["meta"]["round"] += 1
        findings = record.validate_record(item, check_declared_status=False)
        self.assertTrue(any("meta.round" in f for f in findings), findings)

        item = build(families.ENCODER_FAMILY)
        item["meta"]["tags"][-1] = "named-runtime"
        findings = record.validate_record(item, check_declared_status=False)
        self.assertTrue(any("meta.tags" in f for f in findings), findings)

    def test_every_encoder_identity_and_summary_is_recomputed(self):
        item = build(families.ENCODER_FAMILY)
        item["result"]["measured"]["encoding_a"]["encoding"] = item["scenario"]["encoding_pair"][1]
        findings = result_findings(item)
        self.assertTrue(any("encoding_a.encoding" in f for f in findings), findings)

        scalar_fields = (
            "rmse",
            "mean_abs_error",
            "max_abs_error",
            "pearson_r",
            "information_retention",
            "mean_rate_hz",
            "energy_pJ",
            "retention_per_spike",
        )
        for field in scalar_fields:
            item = build(families.ENCODER_FAMILY)
            state = item["result"]["measured"]["encoding_a"]
            state[field] = 0.123456 if state[field] is None else state[field] + 0.123456
            findings = result_findings(item)
            with self.subTest(field=field):
                self.assertTrue(any(field in finding for finding in findings), findings)

        for field in ("retention_margin", "energy_margin_pJ"):
            item = build(families.ENCODER_FAMILY)
            item["result"]["measured"][field] += 0.25
            findings = result_findings(item)
            with self.subTest(field=field):
                self.assertTrue(any(field in finding for finding in findings), findings)

        item = build(families.ENCODER_FAMILY)
        state = item["result"]["measured"]["encoding_a"]
        state["representation_excerpt_truncated"] = not state["representation_excerpt_truncated"]
        findings = result_findings(item)
        self.assertTrue(any("representation_excerpt_truncated" in f for f in findings), findings)

    def test_every_neuron_spike_summary_is_recomputed(self):
        fields = (
            "spike_count",
            "first_spike_ms",
            "last_spike_ms",
            "mean_rate_hz",
            "mean_isi_ms",
            "cv_isi",
            "adaptation_index",
            "duration_ms",
            "v_trace_stride_ms",
        )
        for field in fields:
            item = build(families.NEURON_FAMILY)
            state = item["result"]["measured"]["before"]
            state[field] = 0.125 if state[field] is None else state[field] + 1
            findings = result_findings(item)
            with self.subTest(field=field):
                self.assertTrue(any(field in finding for finding in findings), findings)

        item = build(families.NEURON_FAMILY)
        item["result"]["measured"]["before"]["v_trace"].pop()
        findings = result_findings(item)
        self.assertTrue(any("v_trace length" in f for f in findings), findings)

    def test_neuron_spikes_cannot_be_shifted_outside_the_run(self):
        item = build(families.NEURON_FAMILY)
        duration = item["result"]["measured"]["before"]["duration_ms"]
        for side in ("before", "after"):
            state = item["result"]["measured"][side]
            state["spike_times_ms"] = [
                time_ms + duration * 4 for time_ms in state["spike_times_ms"]
            ]
            if state["spike_times_ms"]:
                state["first_spike_ms"] = state["spike_times_ms"][0]
                state["last_spike_ms"] = state["spike_times_ms"][-1]
        item["result"]["measured"]["delta"] = sim.compare_neuron_states(
            item["result"]["measured"]["before"],
            item["result"]["measured"]["after"],
        )
        findings = result_findings(item)
        self.assertTrue(any("outside the simulated duration" in f for f in findings), findings)

    def test_every_mesh_label_and_summary_is_recomputed(self):
        item = build(families.MESH_FAMILY)
        state = item["result"]["measured"]["before"]
        mutations = {
            "source": "forged-source",
            "sink": "forged-sink",
            "firing_order": list(reversed(state["firing_order"])),
            "downstream_activation": list(reversed(state["downstream_activation"])),
            "total_spikes": state["total_spikes"] + 1,
            "energy_pJ": state["energy_pJ"] + 1,
        }
        for field, forged in mutations.items():
            candidate = build(families.MESH_FAMILY)
            candidate["result"]["measured"]["before"][field] = forged
            findings = result_findings(candidate)
            with self.subTest(field=field):
                self.assertTrue(any(field in finding for finding in findings), findings)

    def test_mesh_arrivals_cannot_be_shifted_outside_the_run(self):
        item = build(families.MESH_FAMILY)
        duration = item["scenario"]["duration_ms"]
        for side in ("before", "after"):
            arrivals = item["result"]["measured"][side]["first_arrival_ms"]
            for node, time_ms in list(arrivals.items()):
                if time_ms is not None:
                    arrivals[node] = time_ms + duration * 4
        findings = result_findings(item)
        self.assertTrue(any("outside the simulated duration" in f for f in findings), findings)

        boundary = build(families.MESH_FAMILY)
        arrivals = boundary["result"]["measured"]["before"]["first_arrival_ms"]
        node = next(node for node, time_ms in arrivals.items() if time_ms is not None)
        arrivals[node] = duration
        findings = result_findings(boundary)
        self.assertTrue(any("outside the simulated duration" in f for f in findings), findings)

        expected_delta = item["result"]["measured"]["delta"]
        for field, value in expected_delta.items():
            candidate = build(families.MESH_FAMILY)
            delta = candidate["result"]["measured"]["delta"]
            if isinstance(value, bool):
                delta[field] = not value
            elif isinstance(value, list):
                delta[field] = value + ["forged-node"]
            else:
                delta[field] = 123.0 if value is None else value + 123.0
            findings = result_findings(candidate)
            with self.subTest(delta=field):
                self.assertTrue(any(field in finding for finding in findings), findings)

    def test_credit_labels_vectors_and_behavior_summaries_are_recomputed(self):
        item = build(families.CREDIT_FAMILY)
        plasticity = item["result"]["measured"]["plasticity"]
        plasticity["weights_before"][0] += 0.25
        findings = result_findings(item)
        self.assertTrue(any("weights_before" in f for f in findings), findings)

        item = build(families.CREDIT_FAMILY)
        item["result"]["measured"]["plasticity"]["eligibility"].pop()
        findings = result_findings(item)
        self.assertTrue(any("inconsistent lengths" in f for f in findings), findings)

        for field in ("spike_count", "first_spike_ms", "output_rate_hz"):
            item = build(families.CREDIT_FAMILY)
            behavior = item["result"]["measured"]["plasticity"]["pre_update_behavior"]
            behavior[field] = 0.25 if behavior[field] is None else behavior[field] + 1
            findings = result_findings(item)
            with self.subTest(behavior=field):
                self.assertTrue(any(field in finding for finding in findings), findings)

        item = build(families.CREDIT_FAMILY)
        item["result"]["measured"]["plasticity"]["modulatory_gain"] += 0.5
        findings = result_findings(item)
        self.assertTrue(any("modulatory_gain" in f for f in findings), findings)

        item = build(families.CREDIT_FAMILY)
        item["result"]["measured"]["plasticity"]["update_rule"] = "trust me"
        findings = result_findings(item)
        self.assertTrue(any("update_rule" in f for f in findings), findings)

        item = build(families.CREDIT_FAMILY)
        critic = item["result"]["measured"]["critic"]
        critic["valence"] = "negative" if critic["valence"] != "negative" else "positive"
        findings = result_findings(item)
        self.assertTrue(any("critic.valence" in f for f in findings), findings)

    def test_temporal_controls_and_all_derivable_summaries_are_recomputed(self):
        item = next(
            build(families.MEMORY_FAMILY, index)
            for index in range(24)
            if build(families.MEMORY_FAMILY, index)["scenario"]["distractor_ms"]
        )
        scenario_mutations = {
            "delay_ms": item["scenario"]["delay_ms"] + 1,
            "distractor_count": item["scenario"]["distractor_count"] + 1,
            "event_sparsity": item["scenario"]["event_sparsity"] + 1,
        }
        for field, forged in scenario_mutations.items():
            candidate = copy.deepcopy(item)
            candidate["scenario"][field] = forged
            findings = proposal_findings(candidate)
            with self.subTest(scenario=field):
                self.assertTrue(
                    any(
                        field in finding or "generator.seed does not reproduce" in finding
                        for finding in findings
                    ),
                    findings,
                )

        trial_mutations = {
            "state_retained_at_probe": not item["result"]["measured"]["baseline"][
                "state_retained_at_probe"
            ],
            "energy_pJ": item["result"]["measured"]["baseline"]["energy_pJ"] + 1,
            "duration_ms": item["result"]["measured"]["baseline"]["duration_ms"] + 1,
        }
        for field, forged in trial_mutations.items():
            candidate = copy.deepcopy(item)
            candidate["result"]["measured"]["baseline"][field] = forged
            findings = result_findings(candidate)
            with self.subTest(trial=field):
                self.assertTrue(any(field in finding for finding in findings), findings)

        candidate = copy.deepcopy(item)
        candidate["result"]["measured"]["delay_ms"] += 1
        findings = result_findings(candidate)
        self.assertTrue(any("measured.delay_ms" in f for f in findings), findings)

        candidate = copy.deepcopy(item)
        invariant = candidate["result"]["measured"]["distractor_invariant"]
        candidate["result"]["measured"]["distractor_invariant"] = not invariant
        findings = result_findings(candidate)
        self.assertTrue(any("distractor_invariant" in f for f in findings), findings)

        candidate = copy.deepcopy(item)
        del candidate["result"]["measured"]["probes"]["distractor_swap"]
        findings = result_findings(candidate)
        self.assertTrue(any("control probes" in f for f in findings), findings)


class Reproducibility(unittest.TestCase):
    def test_every_family_reproduces_from_its_stored_scenario(self):
        for family in families.FAMILY_NAMES:
            for index in range(3):
                item = build(family, index)
                with self.subTest(family=family, index=index):
                    status, detail = record.reproduce(item, environ={})
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
        status, detail = record.reproduce(item, environ={})
        self.assertEqual(status, "mismatch", detail)

    def test_reproduction_authenticates_reference_code_before_replaying(self):
        item = build(families.NEURON_FAMILY)
        forged = canon.digest({"forged": "implementation"})
        item["oracle"]["module_digest"] = forged
        item["oracle"]["stages"][0]["module_digest"] = forged
        status, detail = record.reproduce(item, environ={})
        self.assertEqual(status, "mismatch", detail)
        self.assertIn("module digest", detail)

    def test_reproduction_rejects_an_unresolved_source_commit_before_replaying(self):
        item = build(families.NEURON_FAMILY)
        item["oracle"]["commit"] = "main"
        status, detail = record.reproduce(item, environ={})
        self.assertEqual(status, "invalid", detail)
        self.assertIn("source commit", detail)

    def test_reproduce_reports_unavailable_rather_than_guessing(self):
        item = build(families.ENCODER_FAMILY)
        item["oracle"]["implementation"] = "named-runtime"
        status, detail = record.reproduce(item, environ={})
        self.assertEqual(status, "unavailable")
        self.assertIn("named-runtime", detail)

    def test_malformed_stored_data_is_bounded_as_invalid(self):
        malformed = {"family": families.ENCODER_FAMILY, "scenario": []}
        status, detail = record.reproduce(malformed, environ={})
        self.assertEqual(status, "invalid")
        self.assertIn("cannot rebuild", detail)


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
            "emptyunits",
            "unknowncommit",
            "badcommit",
            "nan",
            "infinity",
            "overflow",
            "stdout_flood",
            "stderr_flood",
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

    def test_stage_provenance_and_errors_never_copy_full_argv(self):
        secret = "TOP-SECRET-ARGUMENT"
        adapter = oracles.ExternalCommandOracle(
            oracle_id="axon-encoder",
            oracle_type="spike-encoder",
            description="double",
            runtime="axon-encoder",
            command=[sys.executable, str(DOUBLE), "ok", f"--token={secret}"],
        )
        run = adapter.run("f", {"configuration": {}, "data": {}})
        stage = run.stages[0]
        self.assertNotIn("command", stage)
        self.assertEqual(stage["executable"], Path(sys.executable).name)
        self.assertNotIn(secret, json.dumps(stage))

        missing = oracles.ExternalCommandOracle(
            oracle_id="axon-encoder",
            oracle_type="spike-encoder",
            description="missing",
            runtime="axon-encoder",
            command=[f"/definitely/not/{secret}", f"--token={secret}"],
        )
        with self.assertRaises(oracles.OracleError) as raised:
            missing.run("f", {})
        self.assertNotIn(secret, str(raised.exception))

    def test_malformed_shell_binding_is_bounded_and_names_only_the_env_key(self):
        key = oracles.env_key("axon-encoder")
        secret = "TOP-SECRET-UNTERMINATED"
        with self.assertRaises(oracles.OracleError) as raised:
            oracles.bind(
                runtime="axon-encoder",
                oracle_id="encoder-ref",
                oracle_type="spike-encoder",
                description="reference",
                reference_fn=lambda request: ({"ok": True}, {"ok": "unit"}),
                environ={key: f'{sys.executable} "{secret}'},
            )
        self.assertIn(key, str(raised.exception))
        self.assertNotIn(secret, str(raised.exception))

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
            any("family schema" in r for r in item["validation"]["reasons"]),
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

    def test_canonical_availability_is_independent_of_host_path(self):
        with mock.patch.object(oracles.shutil, "which", return_value="/host/a"):
            on_path = oracles.availability_report(("axon-encoder",), environ={})
        with mock.patch.object(oracles.shutil, "which", return_value=None):
            absent = oracles.availability_report(("axon-encoder",), environ={})
        self.assertEqual(on_path, absent)
        self.assertEqual(
            sorted(on_path["runtimes"][0]),
            ["binding_env", "bound", "runtime"],
        )

    def test_an_empty_measurement_from_any_oracle_is_refused(self):
        with self.assertRaises(oracles.OracleError):
            oracles.OracleRun({}, {}, [])
        with self.assertRaises(oracles.OracleError):
            oracles.OracleRun({"a": 1}, None, [])
        with self.assertRaises(oracles.OracleError):
            oracles.OracleRun({"a": 1}, {}, [{"stage": "f"}])

    def test_nonfinite_reference_output_is_also_an_oracle_error(self):
        with self.assertRaises(oracles.OracleError):
            oracles.OracleRun(
                {"value": float("inf")},
                {"value": "unit"},
                [{"stage": "f"}],
            )

    def test_nonfinite_external_request_is_bounded_as_an_oracle_error(self):
        with self.assertRaises(oracles.OracleError):
            self.adapter("ok").run(
                "f",
                {"configuration": {"overflow": float("inf")}, "data": {}},
            )

    def test_inherited_pipe_holders_are_bound_by_the_oracle_deadline(self):
        holder = (
            "import json, os, sys, time\n"
            "if os.fork() == 0:\n"
            "    os.setsid()\n"
            "    time.sleep(30)\n"
            "    os._exit(0)\n"
            "sys.stdout.write(json.dumps({\n"
            '    "protocol": "sf-oracle/1",\n'
            '    "runtime_version": "0.0.0-double",\n'
            '    "runtime_commit": "a" * 40,\n'
            '    "measured": {"ok": True},\n'
            '    "units": {"ok": "unit"},\n'
            "}))\n"
            "sys.stdout.flush()\n"
        )
        adapter = oracles.ExternalCommandOracle(
            oracle_id="axon-encoder",
            oracle_type="spike-encoder",
            description="pipe-holder",
            runtime="axon-encoder",
            command=[sys.executable, "-c", holder],
            timeout_s=0.2,
        )
        started = time.monotonic()
        with self.assertRaises(oracles.OracleError) as raised:
            adapter.run("f", {"configuration": {}, "data": {}})
        self.assertLess(time.monotonic() - started, 2.0)
        self.assertIn("timed out", str(raised.exception))
        hung = [
            thread.name
            for thread in threading.enumerate()
            if thread.name.startswith("sf-oracle-axon-encoder-") and thread.is_alive()
        ]
        self.assertEqual(hung, [])


class OracleProvenance(unittest.TestCase):
    def test_the_module_digest_pins_the_implementation_sources(self):
        here = REPO / "pipelines" / "oracle_grounded"
        expected = canon.digest_files(str(here / name) for name in oracles.IMPLEMENTATION_SOURCES)
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
        status, detail = record.reproduce(item, environ={})
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
