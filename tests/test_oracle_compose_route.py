"""Standalone oracle runs retain physical evidence through logical routing."""

import hashlib
import json
from pathlib import Path
import shutil
import sys
import tempfile
import unittest
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "pipelines"))
import compose_curated as compose
import export_replay

GOLDEN = Path(__file__).resolve().parent / "fixtures/oracle-grounded/golden-r01"


class OracleComposeRoute(unittest.TestCase):
    def test_golden_run_retains_all_records_and_replays_physical_coordinates(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "composed"
            summary = compose.compose_run(GOLDEN, out)
            self.assertEqual(summary["counts"]["retained"], 20)
            self.assertEqual(summary["counts"]["excluded"], 0)
            self.assertFalse(summary["audit"]["training_ready"])
            entries = (out / "manifest/compose-manifest.jsonl").read_text().splitlines()
            self.assertEqual(len(entries), 20)
            replay = export_replay._replay_source_lines(GOLDEN, {})
            self.assertEqual(replay.expected_manifest, [json.loads(raw) for raw in entries])
            for raw in entries:
                entry = json.loads(raw)
                source = GOLDEN / entry["physical_source_path"]
                body = source.read_bytes().split(b"\n")[entry["source_line"] - 1]
                self.assertEqual(hashlib.sha256(body).hexdigest(), entry["source_sha256"])
                self.assertEqual(entry["source_original"], body.decode())
                self.assertEqual(entry["source_path"], "oracle-grounded/" + entry["physical_source_path"])
                identity = next(stage["detail"] for stage in entry["stages"] if stage["lane"] == "identity")
                self.assertEqual(identity["source"]["path"], entry["source_path"])
                self.assertEqual(identity["source"]["original"], body.decode())
                emitted = (out / entry["output_path"]).read_text().splitlines()[entry["output_line"] - 1]
                self.assertEqual(json.loads(emitted), json.loads(body))

    def test_malformed_oracle_manifest_refuses_before_destination_creation(self):
        with tempfile.TemporaryDirectory() as tmp:
            source, out = Path(tmp) / "source", Path(tmp) / "out"
            shutil.copytree(GOLDEN, source)
            path = source / "manifest.json"
            manifest = json.loads(path.read_text())
            member = next(iter(manifest["files"]))
            manifest["files"][member]["sha256"] = "0" * 64
            path.write_text(json.dumps(manifest))
            with self.assertRaises(compose.ComposeError):
                compose.compose_run(source, out)
            self.assertFalse(out.exists())

    def test_manifest_must_authenticate_the_exact_compose_snapshot(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "out"
            capture = compose._capture_source_snapshot

            def changed(*args):
                members, payloads, identities = capture(*args)
                payloads = dict(payloads)
                payloads[next(iter(payloads))] += b"\n"
                return members, payloads, identities

            with mock.patch.object(compose, "_capture_source_snapshot", side_effect=changed):
                with self.assertRaises(compose.ComposeError):
                    compose.compose_run(GOLDEN, out)
            self.assertFalse(out.exists())


    def test_manifest_header_is_validated_before_routing(self):
        with tempfile.TemporaryDirectory() as tmp:
            source, out = Path(tmp) / "source", Path(tmp) / "out"
            shutil.copytree(GOLDEN, source)
            path = source / "manifest.json"
            manifest = json.loads(path.read_text())
            manifest["count_per_family"] += 1
            path.write_text(json.dumps(manifest))
            with self.assertRaisesRegex(compose.ComposeError, "failed validation"):
                compose.compose_run(source, out)
            self.assertFalse(out.exists())

    def test_corrupt_schema_and_unreadable_manifests_refuse_routing(self):
        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp) / "source"
            shutil.copytree(GOLDEN, source)
            path = source / "manifest.json"
            manifest = json.loads(path.read_text())
            manifest["schema"] = "oracle-grounded/forged"
            for body in (json.dumps(manifest), "not json"):
                with self.subTest(body=body[:40]):
                    path.write_text(body)
                    out = Path(tmp) / "out"
                    with self.assertRaises(compose.ComposeError):
                        compose.compose_run(source, out)
                    self.assertFalse(out.exists())

    def test_family_folders_and_payloads_do_not_authorize_a_route(self):
        with tempfile.TemporaryDirectory() as tmp:
            source, out = Path(tmp) / "source", Path(tmp) / "out"
            shutil.copytree(GOLDEN, source)
            (source / "manifest.json").unlink()
            summary = compose.compose_run(source, out)
            self.assertEqual(summary["counts"]["retained"], 0)
            self.assertEqual(summary["exclusions"]["identity.unknown_factory"], 20)

    def test_export_reauthenticates_manifest_and_physical_route_evidence(self):
        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp) / "source"
            shutil.copytree(GOLDEN, source)
            snapshot = export_replay._replay_source_lines(source, {})
            entries = [dict(entry) for entry in snapshot.expected_manifest]
            entries[0]["physical_source_path"] = "forged/accepted-r01.jsonl"
            with self.assertRaisesRegex(export_replay.ExportError, "does not reproduce"):
                export_replay._require_replayed_documents(snapshot, entries, [])
            manifest = source / "manifest.json"
            data = json.loads(manifest.read_text())
            data["count_per_family"] += 1
            manifest.write_text(json.dumps(data))
            with self.assertRaisesRegex(export_replay.ExportError, "failed validation"):
                export_replay._replay_source_lines(source, {})


if __name__ == "__main__":
    unittest.main()
