"""Authenticated simulator sessions retain bounded streams, never global authority."""

import unittest
from unittest.mock import patch

from pipelines import curate_identity as identity
from pipelines import curate_identity_registry_sources as sources
from pipelines import curate_identity_simulator_process as process
from pipelines import curate_identity_simulator_worker as worker
from pipelines import validate_run
from pipelines.curate_identity_json import IdentityCurationError
from pipelines.oracle_grounded import fault_oracle

STAMP = "2026-08-23T00:00:00.000Z"
FACTORY = "fault-recovery-simulator-factory"


class BatchReplayTests(unittest.TestCase):
    def test_worker_is_in_authenticated_snapshot(self):
        self.assertIn("pipelines/curate_identity_simulator_worker.py", sources.simulator_source_snapshot())

    def test_native_shared_validator_accepts_replayed_research_record(self):
        original = fault_oracle.build_records(42, 1, produced_at=STAMP)[0]
        self.assertEqual(validate_run.check_line(original, "native"), ([], "fault_recovery"))
        original["result"]["unreviewed"] = True
        self.assertTrue(validate_run.check_line(original, "native")[0])

    def test_batch_launches_one_worker_and_preserves_input_order(self):
        originals = fault_oracle.build_records(42, 6, produced_at=STAMP)
        records = [identity.SourceRecord(row, f"{FACTORY}/records.jsonl", i + 1)
                   for i, row in enumerate(originals)]
        with patch.object(process.subprocess, "Popen", wraps=process.subprocess.Popen) as launch:
            results = identity.curate_records(records)
        self.assertEqual([result.record for result in results], originals)
        self.assertEqual(launch.call_count, 1)

    def test_sequential_and_interleaved_streams_match_producer(self):
        expected = {seed: fault_oracle.build_records(seed, 10, produced_at=STAMP) for seed in (1, 2)}
        with process.replay_session():
            for index in range(10):
                for seed in expected:
                    self.assertEqual(process.replay_coordinate((seed, index, STAMP)), expected[seed][index])

    def test_draw_work_is_linear_and_reverse_requests_hit_budget(self):
        streams = worker.ProposalStreams(fault_oracle.scenario, max_draws=20)
        with patch.object(fault_oracle.scenario, "_system_draw", wraps=fault_oracle.scenario._system_draw) as draws:
            for index in range(10):
                streams.select(42, index, STAMP)
            self.assertEqual(draws.call_count, 10)
            streams.select(42, 8, STAMP)
            with self.assertRaisesRegex(ValueError, "work budget"):
                streams.select(42, 7, STAMP)
        self.assertLessEqual(draws.call_count, 20)

    def test_invalid_coordinates_never_launch_worker(self):
        with patch.object(process.subprocess, "Popen") as launch:
            for coordinates in ((-1, 0, STAMP), (1, 100000, STAMP), (True, 0, STAMP)):
                with self.assertRaises(IdentityCurationError):
                    process.replay_coordinate(coordinates)
        launch.assert_not_called()

    def test_evicted_streams_remain_bounded_and_restart_from_authenticated_seed(self):
        streams = worker.ProposalStreams(fault_oracle.scenario)
        expected = fault_oracle.scenario.propose_scenarios(0, 2)[1]
        for seed in range(worker.MAX_STREAMS + 1):
            streams.select(seed, 0, STAMP)
        self.assertEqual(len(streams.streams), worker.MAX_STREAMS)
        self.assertEqual(streams.select(0, 1, STAMP), expected)
        self.assertEqual(len(streams.streams), worker.MAX_STREAMS)

    def test_nested_batch_sessions_do_not_share_workers_or_authority(self):
        expected = fault_oracle.build_records(42, 1, produced_at=STAMP)[0]
        with patch.object(process.subprocess, "Popen", wraps=process.subprocess.Popen) as launch:
            with process.replay_session():
                self.assertEqual(process.replay_coordinate((42, 0, STAMP)), expected)
                with process.replay_session():
                    self.assertEqual(process.replay_coordinate((42, 0, STAMP)), expected)
                self.assertEqual(process.replay_coordinate((42, 0, STAMP)), expected)
        self.assertEqual(launch.call_count, 2)

    def test_identity_writer_and_manifest_replay_use_one_worker_per_phase(self):
        import json
        import tempfile
        from pathlib import Path
        originals = fault_oracle.build_records(42, 6, produced_at=STAMP)
        payload = "".join(json.dumps(row, separators=(",", ":")) + "\n" for row in originals).encode()
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            source = root / "source" / FACTORY
            source.mkdir(parents=True)
            (source / "records.jsonl").write_bytes(payload)
            with patch.object(process.subprocess, "Popen", wraps=process.subprocess.Popen) as launch:
                identity.write_run(root / "source", root / "output")
            self.assertEqual(launch.call_count, 2)
            self.assertEqual((root / "output" / FACTORY / "records.jsonl").read_bytes(), payload)
