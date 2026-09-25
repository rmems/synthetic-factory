"""Simulator execution consumes one sealed snapshot with bounded process output."""

import os
from pathlib import Path
import tempfile
import threading
import unittest
from unittest.mock import patch

from pipelines import curate_identity_registry_sources as sources
from pipelines import curate_identity_simulator_process as replay
from pipelines.curate_identity_json import IdentityCurationError
from pipelines.oracle_grounded import fault_oracle

COORDINATE = (42, 0, "2026-08-23T00:00:00.000Z")


class ReplaySnapshot(unittest.TestCase):
    def _capture_then_replace(self, relative):
        captured = sources.simulator_source_snapshot()
        expected = fault_oracle.build_records(42, 1, produced_at=COORDINATE[2])[0]
        materialize = replay._materialize
        with tempfile.TemporaryDirectory() as temp:
            source_root = Path(temp)
            materialize(source_root, captured)

            def replace_after_capture(root, snapshot):
                (source_root / relative).write_text("raise RuntimeError('unreviewed replacement')\n")
                materialize(root, snapshot)

            with patch.object(sources, "_REPO_ROOT", source_root):
                with patch.object(replay, "_materialize", replace_after_capture):
                    self.assertEqual(replay.replay_coordinate(COORDINATE), expected)
                with self.assertRaises(IdentityCurationError):
                    replay.replay_coordinate(COORDINATE)

    def test_source_changed_after_capture_cannot_change_executed_bytes(self):
        self._capture_then_replace("pipelines/oracle_grounded/fault_oracle.py")

    def test_worker_changed_after_capture_cannot_change_executed_bytes(self):
        self._capture_then_replace("pipelines/curate_identity_simulator_worker.py")

    def test_worker_timeout_is_a_coded_identity_refusal(self):
        reader, writer = os.pipe()
        with os.fdopen(reader, "rb", buffering=0) as incoming, os.fdopen(writer, "wb"):
            with patch.object(replay, "_REPLAY_TIMEOUT", 0.01):
                with self.assertRaisesRegex(IdentityCurationError, "timed out"):
                    replay._read_frame(incoming)

    def test_worker_result_parsing_is_bounded(self):
        reader, writer = os.pipe()
        payload = b"x" * (replay._MAX_RESULT_BYTES + 1)
        def write():
            with os.fdopen(writer, "wb") as outgoing:
                outgoing.write(payload)
        sender = threading.Thread(target=write)
        sender.start()
        with os.fdopen(reader, "rb", buffering=0) as incoming:
            with self.assertRaisesRegex(IdentityCurationError, "exceeds its bound"):
                replay._read_frame(incoming)
        sender.join(timeout=2)
        self.assertFalse(sender.is_alive())

    def test_protocol_failure_kills_worker_and_prevents_authority_reuse(self):
        processes = []
        popen = replay.subprocess.Popen
        def launch(*args, **kwargs):
            process = popen(*args, **kwargs)
            processes.append(process)
            return process
        with patch.object(replay.subprocess, "Popen", launch), replay.replay_session():
            with patch.object(replay, "_read_frame", side_effect=ValueError("bad JSON")):
                with self.assertRaises(IdentityCurationError):
                    replay.replay_coordinate(COORDINATE)
            self.assertIsNotNone(processes[0].poll())
            with self.assertRaisesRegex(IdentityCurationError, "session has failed"):
                replay.replay_coordinate(COORDINATE)
        self.assertEqual(len(processes), 1)

    def test_ready_stream_cannot_extend_elapsed_deadline(self):
        reader, writer = os.pipe()
        with os.fdopen(reader, "rb", buffering=0) as incoming, os.fdopen(writer, "wb", buffering=0) as outgoing:
            outgoing.write(b"{}\n")
            with patch.object(replay.time, "monotonic", side_effect=[0, 61]):
                with self.assertRaisesRegex(IdentityCurationError, "timed out"):
                    replay._read_frame(incoming)
