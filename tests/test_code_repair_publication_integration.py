"""Real procedural publication and admission, with no validator doubles."""
from __future__ import annotations

import json
import contextlib
import hashlib
import io
import shlex
import shutil
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from tests.test_round_txn import round_txn as rt
from tests.code_repair_test_support import REPO, generate
from code_repair import cli, export, publication
import training_audit


def _change_seed(run):
    run["seed"] += 1


def _change_harness_digest(run):
    run["harness_sha256"] = "0" * 64


def _change_count(run):
    run["count"] += 1


def _change_generator(run):
    run["generator"]["version"] = "unknown"


def _change_candidate_evidence(record):
    record["result"]["evidence_sha256"] = "0" * 64


def _change_candidate_source(record):
    record["scenario"]["source"]["upstream"]["repository"] = "foreign/source"


def _change_candidate_generator(record):
    record["generator"]["name"] = "foreign-generator"


_RUN_CORRUPTIONS = {
    "seed": _change_seed,
    "harness_sha256": _change_harness_digest,
    "count": _change_count,
    "generator": _change_generator,
}
_CANDIDATE_CORRUPTIONS = {
    "candidate_evidence": _change_candidate_evidence,
    "candidate_source": _change_candidate_source,
    "candidate_generator": _change_candidate_generator,
}


def _corrupt_run_input(run_dir, field):
    run = json.loads((run_dir / "RUN.json").read_text())
    if field in _CANDIDATE_CORRUPTIONS:
        from code_repair._contract import oc

        records = [json.loads(line) for line in
                   (run_dir / "candidates.jsonl").read_bytes().splitlines()]
        record = records[-1]  # Corrupt the final candidate, not just a chosen positive.
        _CANDIDATE_CORRUPTIONS[field](record)
        record["provenance"]["record_sha256"] = oc.record_digest(record)
        candidates = b"".join(oc.canonical_json(row).encode() + b"\n" for row in records)
        (run_dir / "candidates.jsonl").write_bytes(candidates)
        run["candidates_sha256"] = hashlib.sha256(candidates).hexdigest()
    else:
        _RUN_CORRUPTIONS[field](run)
    (run_dir / "RUN.json").write_text(json.dumps(run))


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
                audit = training_audit.audit_run(factory.parent)
                self.assertTrue(audit["training_ready"], audit["blockers"])
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

    def test_cli_publish_and_admitted_export_bind_actual_marker_and_exact_membership(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            factory = root / "outputs/raw/2099-01-01/python-function-repair-factory"
            factory.mkdir(parents=True)
            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                status = cli.run(["publish", "--run", str(self.run_dir),
                                  "--factory-dir", str(factory), "--round", "1",
                                  "--lineage-cap", "1", "--json"])
            self.assertEqual(status, 0)
            marker = factory / "ROUND-r01.complete.json"
            published = json.loads(marker.read_text())
            exported = root / "admitted"
            with contextlib.redirect_stdout(io.StringIO()):
                status = cli.run(["export", "--run", str(self.run_dir), "--catalog",
                                  str(REPO / "catalogs/python-repair-v1"),
                                  "--out", str(exported), "--lineage-cap", "1",
                                  "--admit", "--round-marker", str(marker), "--json"])
            self.assertEqual(status, 0)
            manifest = json.loads((exported / "MANIFEST.json").read_text())
            self.assertEqual(manifest["admission"]["training_export"], "training_candidate")
            self.assertEqual(manifest["admission"]["blockers"], [])
            self.assertEqual(manifest["rights"]["project_training_policy"], "allowed")
            completion = manifest["admission"]["round_completion"]
            self.assertEqual(completion["path"], str(marker.resolve()))
            self.assertEqual(completion["sha256"], hashlib.sha256(marker.read_bytes()).hexdigest())
            selected = published["execution_verification"]["procedural"]["selected"]
            agoge = [json.loads(line) for line in (exported / export.AGOGE_PATH).read_bytes().splitlines()]
            self.assertEqual({r["canonical_id"] for r in agoge}, {r["id"] for r in selected})
            self.assertTrue(all(type(r["completion_start_char"]) is int for r in agoge))
            self.assertEqual((exported / export.EVIDENCE_PATH).read_bytes(),
                             (self.run_dir / "candidates.jsonl").read_bytes())
            freeze = json.loads((exported / export.FREEZE_PATH).read_text())
            self.assertEqual(freeze["sft_sha256"], hashlib.sha256(
                (exported / "sft/held_out.jsonl").read_bytes()).hexdigest())
            self.assertEqual((exported / "LICENSE.upstream").read_bytes(),
                             (REPO / "catalogs/python-repair-v1/LICENSE.upstream").read_bytes())

    def test_snapshot_audit_requires_exact_completed_batch_bytes(self):
        with tempfile.TemporaryDirectory() as directory:
            factory = Path(directory) / "outputs/raw/2099-01-01/python-function-repair-factory"
            factory.mkdir(parents=True)
            publication.publish_run(publication.PublishRequest(self.run_dir, factory, 1))
            payload = (factory / "batch-r01.jsonl").read_bytes()
            for name, contents in (("batch-r01.jsonl", b" " + payload),
                                   ("unpublished.jsonl", payload)):
                report = training_audit.audit_run(factory.parent, snapshot={
                    f"{factory.name}/{name}": contents,
                })
                self.assertFalse(report["training_ready"])
                self.assertEqual(report["code_repair"]["completed_records"], 0)

    def test_admitted_export_freshly_executes_even_with_a_valid_completed_marker(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            factory = root / "outputs/raw/2099-01-01/python-function-repair-factory"
            factory.mkdir(parents=True)
            publication.publish_run(publication.PublishRequest(self.run_dir, factory, 1))
            sentinel, trap = root / "fresh-execution", root / "failing-interpreter"
            trap.write_text("#!/bin/sh\nprintf executed > " + shlex.quote(str(sentinel)) + "\nexit 1\n")
            trap.chmod(0o700)
            out = root / "must-refuse"
            with mock.patch.object(sys, "executable", str(trap)), self.assertRaises(ValueError):
                export.run(export.ExportRequest(self.run_dir, out,
                    catalog_dir=REPO / "catalogs/python-repair-v1", admit=True,
                    round_marker=factory / "ROUND-r01.complete.json"))
            self.assertTrue(sentinel.exists(), "admitted export did not perform fresh execution")
            self.assertFalse(out.exists())

    def test_admitted_export_detects_artifact_swap_during_capture(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            factory = root / "outputs/raw/2099-01-01/python-function-repair-factory"
            factory.mkdir(parents=True)
            publication.publish_run(publication.PublishRequest(self.run_dir, factory, 1))
            real_capture = rt.capture_regular_file
            swapped = []

            def race(source, destination):
                result = real_capture(source, destination)
                if source == factory / publication.input_name(1):
                    source.write_bytes(source.read_bytes() + b"\n")
                    swapped.append(source)
                return result

            out = root / "must-refuse"
            with mock.patch.object(rt, "capture_regular_file", side_effect=race):
                with self.assertRaises(ValueError):
                    export.run(export.ExportRequest(self.run_dir, out,
                        catalog_dir=REPO / "catalogs/python-repair-v1", admit=True,
                        round_marker=factory / "ROUND-r01.complete.json"))
            self.assertTrue(swapped)
            self.assertFalse(out.exists())

    def test_changed_candidate_input_during_publish_capture_refuses_before_reservation(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            run_dir = root / "run"
            shutil.copytree(self.run_dir, run_dir)
            factory = root / "outputs/raw/2099-01-01/python-function-repair-factory"
            factory.mkdir(parents=True)
            real_capture = rt.capture_regular_file

            def race(source, destination):
                result = real_capture(source, destination)
                if source == run_dir / "RUN.json":
                    (run_dir / "candidates.jsonl").write_bytes(
                        (run_dir / "candidates.jsonl").read_bytes() + b"\n")
                return result

            with mock.patch.object(rt, "capture_regular_file", side_effect=race):
                with self.assertRaises(rt.TransactionError):
                    publication.publish_run(publication.PublishRequest(run_dir, factory, 1))
            self.assertEqual(list(factory.iterdir()), [])

    def test_admitted_export_refuses_marker_mode_changes_during_fresh_replay(self):
        for change in ("missing", "replaced", "corrupt"):
            with self.subTest(change=change), tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                factory = root / "outputs/raw/2099-01-01/python-function-repair-factory"
                factory.mkdir(parents=True)
                publication.publish_run(publication.PublishRequest(self.run_dir, factory, 1))
                mode = factory / rt.MODE_FILE
                original_mode = mode.read_bytes()
                real_gate = publication.fresh_gate

                def change_mode_after_replay(
                    *args, replay_state=(real_gate, mode, change, original_mode)
                ):
                    real_gate, mode, change, original_mode = replay_state
                    result = real_gate(*args)
                    mode.unlink()
                    if change == "replaced":
                        mode.write_bytes(original_mode + b"\n")
                    elif change == "corrupt":
                        mode.write_bytes(b"{corrupt\n")
                    return result

                out = root / "must-refuse"
                with mock.patch.object(publication, "fresh_gate", side_effect=change_mode_after_replay):
                    with self.assertRaises(ValueError):
                        export.run(export.ExportRequest(self.run_dir, out,
                            catalog_dir=REPO / "catalogs/python-repair-v1", admit=True,
                            round_marker=factory / "ROUND-r01.complete.json"))
                self.assertFalse(out.exists())

    def test_admitted_export_refuses_missing_fake_foreign_and_partial_membership(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            factory = root / "outputs/raw/2099-01-01/python-function-repair-factory"
            factory.mkdir(parents=True)
            publication.publish_run(publication.PublishRequest(self.run_dir, factory, 1))
            marker = factory / "ROUND-r01.complete.json"
            fake = root / "fake.json"
            fake.write_bytes(marker.read_bytes())
            foreign_run = root / "foreign-run"
            shutil.copytree(self.run_dir, foreign_run)
            with (foreign_run / "RUN.json").open("ab") as handle:
                handle.write(b"\n")
            unregistered = root / "unregistered-factory"
            shutil.copytree(factory, unregistered)
            alias = root / "alias" / factory.name
            alias.parent.mkdir()
            alias.symlink_to(unregistered, target_is_directory=True)
            cases = ((None, self.run_dir, 6), (fake, self.run_dir, 6),
                     (root / "missing", self.run_dir, 6), (marker, foreign_run, 6),
                     (marker, self.run_dir, 1),
                     (alias / marker.name, self.run_dir, 6))
            for index, (marker_path, source_run, cap) in enumerate(cases):
                out = root / f"refused-{index}"
                with self.subTest(index=index), self.assertRaises(ValueError):
                    export.run(export.ExportRequest(source_run, out, lineage_cap=cap,
                        catalog_dir=REPO / "catalogs/python-repair-v1",
                        admit=True, round_marker=marker_path))
                self.assertFalse(out.exists())

    def test_corrupt_original_run_and_any_candidate_refuse_before_reservation(self):
        cases = ("seed", "harness_sha256", "count", "generator", "candidate_evidence",
                 "candidate_source", "candidate_generator")
        for field in cases:
            with self.subTest(field=field), tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                run_dir = root / "run"
                shutil.copytree(self.run_dir, run_dir)
                _corrupt_run_input(run_dir, field)
                factory = root / "outputs/raw/2099-01-01/python-function-repair-factory"
                factory.mkdir(parents=True)
                with self.assertRaises(rt.TransactionError):
                    publication.publish_run(publication.PublishRequest(run_dir, factory, 1))
                self.assertEqual(list(factory.iterdir()), [])

    def test_forged_replay_report_cannot_replace_actual_publication_execution(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            run_dir = root / "run"
            shutil.copytree(self.run_dir, run_dir)
            (run_dir / "REPLAY.json").write_text(json.dumps({"status": "passed", "failed": 0}))
            factory = root / "outputs/raw/2099-01-01/python-function-repair-factory"
            factory.mkdir(parents=True)
            sentinel, trap = root / "fresh-publication", root / "failing-interpreter"
            trap.write_text("#!/bin/sh\nprintf executed > " + shlex.quote(str(sentinel)) + "\nexit 1\n")
            trap.chmod(0o700)
            with mock.patch.object(sys, "executable", str(trap)), self.assertRaises(rt.TransactionError):
                publication.publish_run(publication.PublishRequest(run_dir, factory, 1))
            self.assertTrue(sentinel.exists())
            self.assertFalse((factory / "ROUND-r01.complete.json").exists())

    def test_publish_cli_returns_one_coded_refusal_for_missing_inputs(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                status = cli.run(["publish", "--run", str(root / "absent"),
                                  "--factory-dir", str(root / "python-function-repair-factory"),
                                  "--round", "1", "--json"])
            self.assertEqual(status, 2)
            self.assertEqual(json.loads(output.getvalue())["status"], "refused")

    def test_admitted_export_refuses_self_consistent_substituted_catalog_license(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            factory = root / "outputs/raw/2099-01-01/python-function-repair-factory"
            factory.mkdir(parents=True)
            publication.publish_run(publication.PublishRequest(self.run_dir, factory, 1))
            catalog = root / "catalog"
            shutil.copytree(REPO / "catalogs/python-repair-v1", catalog)
            changed = b"An arbitrary replacement with the same SPDX label.\n"
            (catalog / "LICENSE.upstream").write_bytes(changed)
            meta = json.loads((catalog / "CATALOG.json").read_text())
            meta["upstream"]["license_sha256"] = hashlib.sha256(changed).hexdigest()
            (catalog / "CATALOG.json").write_text(json.dumps(meta))
            out = root / "must-refuse"
            with self.assertRaises(ValueError):
                export.run(export.ExportRequest(self.run_dir, out, catalog_dir=catalog,
                    admit=True, round_marker=factory / "ROUND-r01.complete.json"))
            self.assertFalse(out.exists())
