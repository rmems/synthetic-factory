"""Standalone oracle runs retain physical evidence through logical routing."""

import copy
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
from compose_contract import retained_json_line
import export_replay

GOLDEN = Path(__file__).resolve().parent / "fixtures/oracle-grounded/golden-r01"


def copy_golden(tmp):
    source = Path(tmp) / "source"
    shutil.copytree(GOLDEN, source)
    return source, Path(tmp) / "out"


def load_manifest(source):
    path = source / "manifest.json"
    return path, json.loads(path.read_text())


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

    def test_noncanonical_native_records_keep_exact_bytes_through_export_replay(self):
        with tempfile.TemporaryDirectory() as tmp:
            source, out = copy_golden(tmp)
            manifest_path, manifest = load_manifest(source)
            for relative, metadata in manifest["files"].items():
                path = source / relative
                records = [json.loads(line) for line in path.read_bytes().split(b"\n") if line]
                body = "".join("  " + json.dumps(dict(reversed(list(record.items()))),
                                                 ensure_ascii=False, separators=(", ", ": "))
                               + "  \n" for record in records).encode()
                path.write_bytes(body)
                metadata["sha256"] = hashlib.sha256(body).hexdigest()
            manifest_path.write_text(json.dumps(manifest))
            summary = compose.compose_run(source, out)
            self.assertEqual(summary["counts"]["retained"], 20)
            entries = [json.loads(line) for line in (out / "manifest/compose-manifest.jsonl").read_text().splitlines()]
            for entry in entries:
                original = (source / entry["physical_source_path"]).read_bytes().split(b"\n")[entry["source_line"] - 1]
                emitted = (out / entry["output_path"]).read_bytes().split(b"\n")[entry["output_line"] - 1]
                self.assertEqual(emitted, original)
                identity = next(stage["detail"] for stage in entry["stages"] if stage["lane"] == "identity")
                self.assertEqual(identity["source"]["original"].encode(), original)
                self.assertEqual(entry["output_sha256"], hashlib.sha256(original).hexdigest())
            replay = export_replay._replay_source_lines(source, {})
            self.assertEqual(replay.expected_manifest, entries)
            for relative, payload in replay.expected_payloads.items():
                self.assertEqual((out / relative).read_bytes(), payload)

    def test_preserved_output_refuses_tampered_text_hash_and_json(self):
        path = next(GOLDEN.glob("*/accepted-r01.jsonl"))
        raw = path.read_bytes()
        body = raw.split(b"\n")[0]
        coordinate = compose.SourceLineCoordinate(
            "oracle-grounded/" + path.relative_to(GOLDEN).as_posix(), 1,
            hashlib.sha256(raw).hexdigest(),
        )
        decision = compose.compose_source_line(body, coordinate)
        original = body.decode()
        self.assertEqual(retained_json_line(decision), original)
        cases = (
            (original + " ", hashlib.sha256(body).hexdigest()),
            (original, "0" * 64),
            (original, None),
            (original + "\n", "rehash"),
            ('{"duplicate":1,"duplicate":2}', "rehash"),
            ('{"unbounded":NaN}', "rehash"),
            ('{"different":"record"}', "rehash"),
        )
        for text, digest in cases:
            with self.subTest(text=text[:30], digest=digest):
                changed = copy.deepcopy(decision)
                identity = next(stage["detail"] for stage in changed.stages if stage["lane"] == "identity")
                identity["source"]["original"] = text
                identity["source"]["sha256"] = (hashlib.sha256(text.encode()).hexdigest()
                                                  if digest == "rehash" else digest)
                with self.assertRaises(compose.ComposeError):
                    retained_json_line(changed)

    def test_malformed_oracle_manifest_refuses_before_destination_creation(self):
        with tempfile.TemporaryDirectory() as tmp:
            source, out = copy_golden(tmp)
            path, manifest = load_manifest(source)
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
            source, out = copy_golden(tmp)
            path, manifest = load_manifest(source)
            manifest["count_per_family"] += 1
            path.write_text(json.dumps(manifest))
            with self.assertRaisesRegex(compose.ComposeError, "failed validation"):
                compose.compose_run(source, out)
            self.assertFalse(out.exists())

    def test_corrupt_schema_and_unreadable_manifests_refuse_routing(self):
        with tempfile.TemporaryDirectory() as tmp:
            source, out = copy_golden(tmp)
            path, manifest = load_manifest(source)
            manifest["schema"] = "oracle-grounded/forged"
            for body in (json.dumps(manifest), "not json"):
                with self.subTest(body=body[:40]):
                    path.write_text(body)
                    with self.assertRaises(compose.ComposeError):
                        compose.compose_run(source, out)
                    self.assertFalse(out.exists())

    def test_family_folders_and_payloads_do_not_authorize_a_route(self):
        with tempfile.TemporaryDirectory() as tmp:
            source, out = copy_golden(tmp)
            (source / "manifest.json").unlink()
            summary = compose.compose_run(source, out)
            self.assertEqual(summary["counts"]["retained"], 0)
            self.assertEqual(summary["exclusions"]["identity.unknown_factory"], 20)

    def test_export_reauthenticates_manifest_and_physical_route_evidence(self):
        with tempfile.TemporaryDirectory() as tmp:
            source, _out = copy_golden(tmp)
            snapshot = export_replay._replay_source_lines(source, {})
            entries = [dict(entry) for entry in snapshot.expected_manifest]
            entries[0]["physical_source_path"] = "forged/accepted-r01.jsonl"
            with self.assertRaisesRegex(export_replay.ExportError, "does not reproduce"):
                export_replay._require_replayed_documents(snapshot, entries, [])
            manifest, data = load_manifest(source)
            data["count_per_family"] += 1
            manifest.write_text(json.dumps(data))
            with self.assertRaisesRegex(export_replay.ExportError, "failed validation"):
                export_replay._replay_source_lines(source, {})


if __name__ == "__main__":
    unittest.main()
