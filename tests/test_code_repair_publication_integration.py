"""Real procedural transactions; pending shared S1/S2/S3 integration, no validator doubles."""
from __future__ import annotations

import json
import shlex
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from tests.test_round_txn import round_txn as rt
from tests.code_repair_test_support import REPO, generate
from code_repair import publication


class PublicationIntegrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.scratch = tempfile.TemporaryDirectory(prefix="procedural-publication-")
        cls.addClassCleanup(cls.scratch.cleanup)
        cls.root = Path(cls.scratch.name)
        cls.run_dir = cls.root / "original-run"
        generate.run(generate.RunRequest(REPO / "catalogs/python-repair-v1", cls.run_dir,
                                         20260908, 12, "2026-09-09T00:00:00.000Z"))

    def test_real_publish_preserves_selected_bytes_and_read_traversal_never_executes(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            factory = root / "outputs/raw/2099-01-01/python-function-repair-factory"
            factory.mkdir(parents=True)
            manifest = publication.publish_run(publication.PublishRequest(self.run_dir, factory, 1))
            original_bytes = (self.run_dir / "candidates.jsonl").read_bytes()
            by_id = {json.loads(line)["id"]: line for line in original_bytes.splitlines()}
            selected = manifest["execution_verification"]["procedural"]["selected"]
            expected = b"".join(by_id[row["id"]] + b"\n" for row in selected)
            self.assertEqual((factory / "batch-r01.jsonl").read_bytes(), expected)
            artifact = json.loads((factory / publication.input_name(1)).read_text())
            self.assertEqual(artifact["candidates_jsonl"].encode(), original_bytes)
            self.assertEqual(manifest["records"], len(selected))

            # Actual process side effect trap: if a read spawns the family executor,
            # this executable leaves an observable file. No validator is mocked.
            sentinel = root / "executed-on-read"
            trap = root / "interpreter-trap"
            trap.write_text("#!/bin/sh\nprintf executed > " + shlex.quote(str(sentinel)) + "\nexit 1\n")
            trap.chmod(0o700)
            with mock.patch.object(sys, "executable", str(trap)):
                self.assertEqual(rt.committed_jsonl_paths(factory), [factory / "batch-r01.jsonl"])
                self.assertEqual(len(rt.completed_manifests(factory)), 1)
                rt.frontier_status(factory)
            self.assertFalse(sentinel.exists(), "read-only marker traversal executed candidate code")

    def test_edited_round_artifact_cannot_be_rebound_by_restamping_marker_hash(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            factory = root / "outputs/raw/2099-01-01/python-function-repair-factory"
            factory.mkdir(parents=True)
            publication.publish_run(publication.PublishRequest(self.run_dir, factory, 1))
            artifact_path = factory / publication.input_name(1)
            value = json.loads(artifact_path.read_text())
            run = json.loads(value["run_json"])
            run["seed"] += 1
            value["run_json"] = json.dumps(run)
            artifact_path.write_text(json.dumps(value))
            marker = factory / "ROUND-r01.complete.json"
            manifest = json.loads(marker.read_text())
            entry = next(item for item in manifest["files"] if item["name"] == artifact_path.name)
            entry.update(sha256=rt.file_sha256(artifact_path), bytes=artifact_path.stat().st_size)
            marker.write_text(json.dumps(manifest))
            with self.assertRaises(rt.TransactionError):
                rt.committed_jsonl_paths(factory)
