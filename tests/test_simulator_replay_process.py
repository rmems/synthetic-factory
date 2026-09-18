"""Simulator execution consumes one sealed snapshot with bounded process output."""

from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from pipelines import curate_identity_registry_sources as sources
from pipelines import curate_identity_simulator_process as replay
from pipelines.curate_identity_json import IdentityCurationError
from pipelines.oracle_grounded import fault_oracle

COORDINATE = (42, 0, "2026-08-23T00:00:00.000Z")


class ReplaySnapshot(unittest.TestCase):
    def test_source_changed_after_capture_cannot_change_executed_bytes(self):
        captured = sources.simulator_source_snapshot()
        expected = fault_oracle.build_records(42, 1, produced_at=COORDINATE[2])[0]
        materialize = replay._materialize
        with tempfile.TemporaryDirectory() as temp:
            source_root = Path(temp)
            materialize(source_root, captured)

            def replace_after_capture(root, snapshot):
                target = source_root / "pipelines/oracle_grounded/fault_oracle.py"
                target.write_text("raise RuntimeError('unreviewed replacement')\n")
                materialize(root, snapshot)

            with patch.object(sources, "_REPO_ROOT", source_root):
                with patch.object(replay, "_materialize", replace_after_capture):
                    self.assertEqual(replay.replay_coordinate(COORDINATE), expected)
                with self.assertRaises(IdentityCurationError):
                    replay.replay_coordinate(COORDINATE)

    def test_worker_timeout_is_a_coded_identity_refusal(self):
        with patch.object(replay.subprocess, "run", side_effect=replay.subprocess.TimeoutExpired("worker", 60)):
            with self.assertRaises(IdentityCurationError):
                replay.replay_coordinate(COORDINATE)

    def test_worker_result_parsing_is_bounded(self):
        def oversized(command, **options):
            options["stdout"].write(b"x" * (replay._MAX_RESULT_BYTES + 1))
            return SimpleNamespace(returncode=0)

        with patch.object(replay.subprocess, "run", oversized):
            with self.assertRaisesRegex(IdentityCurationError, "exceeds its bound"):
                replay.replay_coordinate(COORDINATE)
