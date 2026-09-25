"""Only the reviewed simulator's replayable native records receive its identity."""

import copy
import unittest
import tempfile
import json
from pathlib import Path
from unittest.mock import patch
from pipelines import curate_identity_simulator as simulator_identity

from pipelines import curate_identity as identity
from pipelines.oracle_grounded import fault_oracle
from tests.test_curate_identity import factory_thalamic

FACTORY = "fault-recovery-simulator-factory"


def _curate(record):
    return identity.curate_record(identity.SourceRecord(record, f"{FACTORY}/records.jsonl", 1))


def _record():
    return fault_oracle.build_records(42, 1, produced_at="2026-08-23T00:00:00.000Z")[0]


class SimulatorIdentityReplay(unittest.TestCase):
    def test_native_record_is_retained_without_changing_oracle_evidence(self):
        original = _record()
        result = _curate(original)
        self.assertEqual(result.action, "retained")
        self.assertEqual(result.record, original)
        self.assertEqual(result.mapping["output_id"], original["id"])

    def test_thalamic_self_claim_is_not_simulator_evidence(self):
        result = _curate(factory_thalamic(FACTORY, claim="simulated"))
        self.assertEqual(result.action, "exclude")

    def test_altered_native_result_and_scenario_are_refused(self):
        original = _record()
        for field in ("result", "scenario", "generator", "oracle", "provenance"):
            with self.subTest(field=field):
                changed = copy.deepcopy(original)
                changed[field]["unreviewed"] = True
                self.assertEqual(_curate(changed).action, "exclude")

    def test_written_native_identity_tree_replays_complete_mapping(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            source = root / "source" / FACTORY
            source.mkdir(parents=True)
            original = _record()
            (source / "records.jsonl").write_text(identity.canonical_json(original) + "\n")
            destination = root / "curated"
            identity.write_run(root / "source", destination)
            identity.validate_identity_tree(destination)
            manifest_path = destination / identity.IDENTITY_MANIFEST_SIDECAR
            manifest = json.loads(manifest_path.read_bytes())
            manifest[0]["simulator_authority"]["basis"] = "unreviewed"
            manifest_path.write_text(json.dumps(manifest))
            with self.assertRaises(identity.IdentityTreeError):
                identity.validate_identity_tree(destination)

    def test_seeded_later_record_preserves_its_original_coordinate(self):
        original = fault_oracle.build_records(42, 3, produced_at="2026-08-23T00:00:00.000Z")[2]
        result = _curate(original)
        self.assertEqual(result.action, "retained")
        self.assertEqual(result.record, original)

    def test_malformed_replay_coordinates_are_excluded(self):
        for key, value in (("id", "fr-42-100000"), ("id", "fr-42-" + "9" * 5000),
                           ("schema_version", "unreviewed-envelope")):
            with self.subTest(key=key, value=str(value)[:30]):
                record = _record()
                record[key] = value
                self.assertEqual(_curate(record).action, "exclude")

    def test_invalid_coordinates_do_not_execute_the_producer(self):
        for record_id in ("fr-1-999999999", "fr-01-0000", "fr-1-00000", "fr-18446744073709551616-0000"):
            with self.subTest(record_id=record_id):
                record = _record()
                record["id"] = record_id
                with patch.object(simulator_identity, "replay_coordinate") as producer:
                    self.assertEqual(_curate(record).action, "exclude")
                producer.assert_not_called()

    def test_replay_coordinate_bounds_match_reviewed_producer(self):
        self.assertEqual(simulator_identity.MAX_SEED, fault_oracle.fv.MAX_SEED)
        self.assertEqual(simulator_identity.MAX_INDEX + 1, fault_oracle.fv.MAX_COUNT)

    def test_cached_parent_producer_cannot_authorize_forged_evidence(self):
        original = _record()
        forged = copy.deepcopy(original)
        forged["result"]["unreviewed"] = True
        with patch.object(fault_oracle, "build_records", return_value=[forged]):
            self.assertEqual(_curate(original).record, original)
            self.assertEqual(_curate(forged).action, "exclude")

    def test_isolated_replay_matches_producer_at_seed_and_cycle_boundaries(self):
        from pipelines.curate_identity_simulator_process import replay_coordinate
        stamp = "2026-08-23T00:00:00.000Z"
        for seed in (0, fault_oracle.fv.MAX_SEED):
            originals = fault_oracle.build_records(seed, 19, produced_at=stamp)
            for index in (0, 8, 9, 18):
                with self.subTest(seed=seed, index=index):
                    self.assertEqual(replay_coordinate((seed, index, stamp)), originals[index])

    def test_maximum_coordinate_uses_original_proposal_without_prior_oracle_runs(self):
        from pipelines.curate_identity_simulator_process import replay_coordinate
        seed, index, stamp = 0, simulator_identity.MAX_INDEX, "2026-08-23T00:00:00.000Z"
        proposal = fault_oracle.scenario.propose_scenarios(seed, index + 1)[-1]
        with patch.object(fault_oracle.scenario, "propose_scenarios", return_value=[proposal]):
            expected = fault_oracle.build_records(seed, index + 1, produced_at=stamp)[0]
        self.assertEqual(replay_coordinate((seed, index, stamp)), expected)
