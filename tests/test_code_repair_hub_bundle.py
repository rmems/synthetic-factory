#!/usr/bin/env python3
"""The Hub bundle: typed configs with real splits over verified export bytes; refusals are coded."""

import contextlib
import hashlib
import io
import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from code_repair_test_support import (
    FIXTURE_CATALOG,
    cli,
    export,
    hub_bundle,
    lineage,
    refusal,
    replay,
    smoke_run,
    views,
)
from code_repair_test_support import vocabulary as cv

DATASET = "rmems/python-function-repair-test"


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def exported(root, *, replayed=True):
    """A smoke run exported into ``root``; replayed exports carry consumer rows."""

    _summary, records, run_dir = smoke_run()
    replay_dir = None
    if replayed:
        replay_dir = root / "replay"
        replay.run(replay.ReplayRequest(run_dir, FIXTURE_CATALOG, replay_dir, 5.0))
    out = root / "export"
    manifest = export.run(export.ExportRequest(
        run_dir, out, replay_dir, export.DEFAULT_LINEAGE_CAP, catalog_dir=FIXTURE_CATALOG,
    ))
    return manifest, out, records, run_dir


def invoke(argv):
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        code = cli.run(argv)
    return code, out.getvalue(), err.getvalue()


class Bundle(unittest.TestCase):
    def setUp(self):
        self.root = Path(tempfile.mkdtemp(prefix="code-repair-hub-bundle-"))
        self.addCleanup(shutil.rmtree, self.root, True)

    def request(self, export_dir, name="bundle", dataset=DATASET, pretty=None):
        return hub_bundle.BundleRequest(export_dir, self.root / name, dataset, pretty)

    def test_typed_configs_real_splits_and_verified_bytes(self):
        manifest, out, records, _run_dir = exported(self.root)
        summary = hub_bundle.run(self.request(out))
        bundle = self.root / "bundle"
        self.assertEqual(summary["configs"], ["sft", "chat", "edit", "viewer"])
        self.assertFalse(summary["training_ready"])
        self.assertEqual(json.loads((bundle / hub_bundle.BUNDLE_FILENAME).read_text()), summary)
        for relative, digest in summary["files"].items():
            self.assertEqual(sha(bundle / relative), digest, relative)
        for _name, directory in hub_bundle.TEXT_CONFIGS:
            for split in lineage.SPLITS:
                self.assertEqual((bundle / f"data/{directory}/{split}.jsonl").read_bytes(),
                                 (out / f"{directory}/{split}.jsonl").read_bytes())
        self.assertEqual((bundle / "evidence/candidates.jsonl").read_bytes(),
                         (out / export.EVIDENCE_PATH).read_bytes())
        self.assertEqual((bundle / "evidence/MANIFEST.json").read_bytes(),
                         (out / export.MANIFEST_FILENAME).read_bytes())
        self.assertEqual((bundle / "evidence/FREEZE.json").read_bytes(),
                         (out / export.FREEZE_PATH).read_bytes())
        self.assertIn(b"Apache License", (bundle / hub_bundle.LICENSE_FILENAME).read_bytes())
        card = (bundle / hub_bundle.CARD_FILENAME).read_text(encoding="utf-8")
        self.assertTrue(card.startswith("---\n"))
        head, body = card.split("\n---\n", 1)
        self.assertIn("license: apache-2.0", head)
        self.assertIn("- research-snapshot", head)
        self.assertIn("- config_name: viewer", head)
        self.assertIn(f"num_examples: {len(records)}", head)
        for name, directory in hub_bundle.TEXT_CONFIGS:
            self.assertIn(f"- config_name: {name}", head)
            for split in lineage.SPLITS:
                declared = f"path: data/{directory}/{split}.jsonl" in head
                self.assertEqual(declared, summary["rows"][name][split] > 0, (name, split))
        self.assertIn("**not training-ready.**", body)
        for code in manifest["admission"]["blockers"]:
            self.assertIn(f"`{code}`", body)
        self.assertNotIn("catalogs/code-repair-fixture-v1", body)
        rows = hub_bundle.read_viewer_parquet((bundle / hub_bundle.VIEWER_PATH).read_bytes())
        lines = (out / export.EVIDENCE_PATH).read_text(encoding="utf-8").split("\n")[:-1]
        self.assertEqual([row.record_json for row in rows], lines)
        self.assertEqual([(row.source_file, row.source_line) for row in rows],
                         [("candidates.jsonl", number) for number in range(1, len(lines) + 1)])
        self.assertEqual(json.loads(lines[0])["id"], records[0]["id"])
        status = json.loads((bundle / hub_bundle.RELEASE_STATUS_FILENAME).read_text())
        observed = (status["training_ready"], status["release_stage"], status["payload_published"])
        self.assertEqual(observed, (False, hub_bundle.STAGE_BLOCKED, False))
        self.assertEqual(status["admission"], manifest["admission"])
        provenance = json.loads((bundle / hub_bundle.PROVENANCE_FILENAME).read_text())
        self.assertEqual(provenance["export_manifest_sha256"], sha(out / export.MANIFEST_FILENAME))
        self.assertFalse(provenance["training_ready"])
        companions = {hub_bundle.PROVENANCE_FILENAME, hub_bundle.RELEASE_STATUS_FILENAME,
                      hub_bundle.CARD_FILENAME}
        self.assertEqual({entry["path"] for entry in provenance["files"]},
                         set(summary["files"]) - companions)

    def test_a_blocked_export_without_replay_declares_only_the_viewer(self):
        _manifest, out, _records, _run_dir = exported(self.root, replayed=False)
        summary = hub_bundle.run(self.request(out))
        self.assertEqual(summary["configs"], ["viewer"])
        self.assertEqual(summary["rows"]["sft"], {split: 0 for split in lineage.SPLITS})
        card = (self.root / "bundle" / hub_bundle.CARD_FILENAME).read_text(encoding="utf-8")
        self.assertIn("(no rows; not declared as a config)", card)
        self.assertNotIn("config_name: sft", card)

    def test_two_bundles_of_one_export_are_byte_identical(self):
        _manifest, out, _records, _run_dir = exported(self.root)
        first = hub_bundle.run(self.request(out, "a"))
        second = hub_bundle.run(self.request(out, "b"))
        self.assertEqual(first, second)
        for relative in [*first["files"], hub_bundle.BUNDLE_FILENAME]:
            self.assertEqual((self.root / "a" / relative).read_bytes(),
                             (self.root / "b" / relative).read_bytes(), relative)

    def test_training_ready_follows_the_manifest(self):
        manifest = {"admission": {"training_export": "training_candidate", "blockers": []},
                    "replay": "passed"}
        self.assertTrue(hub_bundle.training_ready(manifest))
        for edit in (
            {"replay": "not run"},
            {"admission": {"training_export": "blocked", "blockers": []}},
            {"admission": {"training_export": "training_candidate", "blockers": ["X"]}},
        ):
            self.assertFalse(hub_bundle.training_ready({**manifest, **edit}))

    def test_request_refusals_write_nothing(self):
        _manifest, out, _records, _run_dir = exported(self.root)
        (self.root / "taken").mkdir()
        with refusal(self, cv.FINDING_DESTINATION_EXISTS):
            hub_bundle.run(self.request(out, "taken"))
        with refusal(self, cv.FINDING_DESTINATION_UNDER_RAW):
            raw = self.root / "outputs" / "raw" / "x"
            hub_bundle.run(hub_bundle.BundleRequest(out, raw, DATASET))
        with refusal(self, cv.FINDING_BUNDLE_REQUEST_INVALID):
            hub_bundle.run(self.request(out, "b1", dataset="no-owner"))
        with refusal(self, cv.FINDING_BUNDLE_REQUEST_INVALID):
            hub_bundle.run(self.request(out, "b2", pretty="two\nlines"))
        empty = self.root / "empty"
        empty.mkdir()
        with refusal(self, cv.FINDING_RUN_FILE_MISSING):
            hub_bundle.run(self.request(empty, "b3"))
        for name in ("b1", "b2", "b3"):
            self.assertFalse((self.root / name).exists())

    def test_drifted_or_malformed_exports_refuse_before_anything_is_written(self):
        _manifest, out, _records, _run_dir = exported(self.root)
        drifted = self.root / "drifted"
        shutil.copytree(out, drifted)
        path = drifted / f"{export.SFT_DIR}/train.jsonl"
        path.write_bytes(path.read_bytes() + b"\n")
        with refusal(self, cv.FINDING_EXPORT_INTEGRITY):
            hub_bundle.run(self.request(drifted, "d1"))
        missing = self.root / "missing"
        shutil.copytree(out, missing)
        (missing / export.AGOGE_PATH).unlink()
        with refusal(self, cv.FINDING_EXPORT_INTEGRITY):
            hub_bundle.run(self.request(missing, "d2"))
        malformed = self.root / "malformed"
        shutil.copytree(out, malformed)
        (malformed / export.MANIFEST_FILENAME).write_text("{not json")
        with refusal(self, cv.FINDING_BUNDLE_MANIFEST_INVALID):
            hub_bundle.run(self.request(malformed, "d3"))
        incomplete = self.root / "incomplete"
        shutil.copytree(out, incomplete)
        manifest_path = incomplete / export.MANIFEST_FILENAME
        manifest = json.loads(manifest_path.read_text())
        manifest["pipeline_status"] = "partial"
        manifest_path.write_text(json.dumps(manifest))
        with refusal(self, cv.FINDING_BUNDLE_MANIFEST_INVALID):
            hub_bundle.run(self.request(incomplete, "d4"))
        for name in ("d1", "d2", "d3", "d4"):
            self.assertFalse((self.root / name).exists())


class Cli(unittest.TestCase):
    def setUp(self):
        self.root = Path(tempfile.mkdtemp(prefix="code-repair-hub-bundle-cli-"))
        self.addCleanup(shutil.rmtree, self.root, True)

    def test_hub_bundle_and_render_report_every_rendering(self):
        _manifest, out, records, run_dir = exported(self.root)
        bundle = self.root / "bundle"
        code, text, _err = invoke([
            "hub-bundle", "--export", str(out), "--out", str(bundle),
            "--dataset-id", DATASET, "--json",
        ])
        self.assertEqual(code, 0, text)
        payload = json.loads(text)
        self.assertEqual((payload["status"], payload["summary"]["configs"]),
                         ("ok", ["sft", "chat", "edit", "viewer"]))
        self.assertTrue((bundle / hub_bundle.CARD_FILENAME).is_file())
        code, text, err = invoke([
            "hub-bundle", "--export", str(out), "--out", str(bundle), "--dataset-id", DATASET,
        ])
        self.assertEqual((code, text), (2, ""))
        self.assertTrue(err.startswith(cv.FINDING_DESTINATION_EXISTS), err)
        positive = next(r for r in records if views.is_positive(r))
        code, text, _err = invoke(["render", str(run_dir), positive["id"], "--json"])
        self.assertEqual(code, 0)
        payload = json.loads(text)
        self.assertEqual(views.chat_pair(payload["chat"]),
                         (payload["sft"]["prompt"], payload["sft"]["completion"]))
        self.assertEqual(set(payload["edit"]), {"prompt", "completion"})
        self.assertTrue(payload["edit"]["completion"].startswith(cv.EDIT_SEARCH_MARKER))


if __name__ == "__main__":
    unittest.main()
