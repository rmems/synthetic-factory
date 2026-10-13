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
    required_item,
    smoke_run,
    views,
    views_chat,
)
from code_repair_test_support import vocabulary as cv

DATASET = "rmems/python-function-repair-test"


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def repin(export_dir, relative):
    """Point one manifest file digest at the bytes on disk, leaving every other pin."""

    manifest_path = Path(export_dir) / export.MANIFEST_FILENAME
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["files"][relative] = sha(Path(export_dir) / relative)
    manifest_path.write_text(json.dumps(manifest) + "\n", encoding="utf-8")


def manifest_matches_bytes(export_dir):
    """True when every manifest digest equals the sha256 of the file it names."""

    root = Path(export_dir)
    manifest = json.loads((root / export.MANIFEST_FILENAME).read_text(encoding="utf-8"))
    return all(digest == sha(root / relative) for relative, digest in manifest["files"].items())


def write_json(path, payload):
    Path(path).write_text(json.dumps(payload) + "\n", encoding="utf-8")


def false_freezes(freeze):
    """Copies of a freeze with one rendering digest lied about, removed, or blank."""

    lied = {**freeze, "sft_sha256": "0" * 64}
    missing = {key: value for key, value in freeze.items() if key != "chat_sha256"}
    blank = {**freeze, "edit_sha256": ""}
    return (
        ("lie", export.SFT_DIR, lied),
        ("missing", export.CHAT_DIR, missing),
        ("blank", export.EDIT_DIR, blank),
    )


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


class BuiltBundle(unittest.TestCase):
    """One replayed export bundled once; each test reads one aspect of the result."""

    @classmethod
    def setUpClass(cls):
        cls.root = Path(tempfile.mkdtemp(prefix="code-repair-hub-bundle-built-"))
        cls.manifest, cls.out, cls.records, _run_dir = exported(cls.root)
        cls.bundle = cls.root / "bundle"
        cls.summary = hub_bundle.run(hub_bundle.BundleRequest(cls.out, cls.bundle, DATASET))
        card = (cls.bundle / hub_bundle.CARD_FILENAME).read_text(encoding="utf-8")
        cls.card = card
        cls.head, cls.body = card.split("\n---\n", 1)

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.root, True)

    def read_json(self, relative):
        return json.loads((self.bundle / relative).read_text())

    def test_summary_lists_typed_configs_and_pins_every_file(self):
        self.assertEqual(self.summary["configs"], ["sft", "chat", "edit", "viewer"])
        self.assertFalse(self.summary["training_ready"])
        self.assertEqual(self.read_json(hub_bundle.BUNDLE_FILENAME), self.summary)
        for relative, digest in self.summary["files"].items():
            self.assertEqual(sha(self.bundle / relative), digest, relative)

    def test_export_bytes_are_copied_unchanged(self):
        pairs = [(f"data/{directory}/{split}.jsonl", f"{directory}/{split}.jsonl")
                 for _name, directory in hub_bundle.TEXT_CONFIGS for split in lineage.SPLITS]
        pairs += [("evidence/candidates.jsonl", export.EVIDENCE_PATH),
                  ("evidence/MANIFEST.json", export.MANIFEST_FILENAME),
                  ("evidence/FREEZE.json", export.FREEZE_PATH)]
        for bundled, exported_path in pairs:
            self.assertEqual((self.bundle / bundled).read_bytes(),
                             (self.out / exported_path).read_bytes(), bundled)
        self.assertIn(b"Apache License", (self.bundle / hub_bundle.LICENSE_FILENAME).read_bytes())

    def test_front_matter_declares_exactly_the_nonempty_splits(self):
        self.assertTrue(self.card.startswith("---\n"))
        for fragment in ("license: apache-2.0", "- research-snapshot", "- config_name: viewer",
                         f"num_examples: {len(self.records)}"):
            self.assertIn(fragment, self.head)
        for name, directory in hub_bundle.TEXT_CONFIGS:
            self.assertIn(f"- config_name: {name}", self.head)
            for split in lineage.SPLITS:
                declared = f"path: data/{directory}/{split}.jsonl" in self.head
                self.assertEqual(declared, self.summary["rows"][name][split] > 0, (name, split))

    def test_card_body_states_the_blockers_and_no_unreal_catalog_path(self):
        self.assertIn("**not training-ready.**", self.body)
        for code in self.manifest["admission"]["blockers"]:
            self.assertIn(f"`{code}`", self.body)
        self.assertNotIn("catalogs/code-repair-fixture-v1", self.body)

    def test_viewer_is_a_lossless_projection_of_the_evidence(self):
        rows = hub_bundle.read_viewer_parquet((self.bundle / hub_bundle.VIEWER_PATH).read_bytes())
        lines = (self.out / export.EVIDENCE_PATH).read_text(encoding="utf-8").split("\n")[:-1]
        self.assertEqual([row.record_json for row in rows], lines)
        self.assertEqual([(row.source_file, row.source_line) for row in rows],
                         [("candidates.jsonl", number) for number in range(1, len(lines) + 1)])
        self.assertEqual(json.loads(lines[0])["id"], self.records[0]["id"])

    def test_companions_follow_the_manifest(self):
        status = self.read_json(hub_bundle.RELEASE_STATUS_FILENAME)
        observed = (status["training_ready"], status["release_stage"], status["payload_published"])
        self.assertEqual(observed, (False, hub_bundle.STAGE_BLOCKED, False))
        self.assertEqual(status["admission"], self.manifest["admission"])
        provenance = self.read_json(hub_bundle.PROVENANCE_FILENAME)
        self.assertEqual(provenance["export_manifest_sha256"],
                         sha(self.out / export.MANIFEST_FILENAME))
        self.assertFalse(provenance["training_ready"])
        companions = {hub_bundle.PROVENANCE_FILENAME, hub_bundle.RELEASE_STATUS_FILENAME,
                      hub_bundle.CARD_FILENAME}
        self.assertEqual({entry["path"] for entry in provenance["files"]},
                         set(self.summary["files"]) - companions)


class Bundle(unittest.TestCase):
    def setUp(self):
        self.root = Path(tempfile.mkdtemp(prefix="code-repair-hub-bundle-"))
        self.addCleanup(shutil.rmtree, self.root, True)

    def request(self, export_dir, name="bundle", dataset=DATASET):
        return hub_bundle.BundleRequest(export_dir, self.root / name, dataset)

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
            hub_bundle.run(hub_bundle.BundleRequest(out, self.root / "b2", DATASET, "two\nlines"))
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

    def test_a_malformed_split_policy_refuses_before_the_card_renders(self):
        _manifest, out, _records, _run_dir = exported(self.root)
        for name, policy in (("p1", {"weights": {}}), ("p2", "train-only"), ("p3", [])):
            with self.subTest(policy=policy):
                tampered = self.root / f"tampered-{name}"
                shutil.copytree(out, tampered)
                manifest_path = tampered / export.MANIFEST_FILENAME
                manifest = json.loads(manifest_path.read_text())
                manifest["run"]["split_policy"] = policy
                manifest_path.write_text(json.dumps(manifest))
                with refusal(self, cv.FINDING_BUNDLE_MANIFEST_INVALID):
                    hub_bundle.run(self.request(tampered, name))
                self.assertFalse((self.root / name).exists())

    def test_tampered_held_out_bytes_are_refused_after_the_manifest_digest_is_updated(self):
        _manifest, out, _records, _run_dir = exported(self.root)
        for directory in (export.SFT_DIR, export.CHAT_DIR, export.EDIT_DIR):
            with self.subTest(directory=directory):
                tampered = self.root / f"bytes-{directory}"
                shutil.copytree(out, tampered)
                relative = f"{directory}/held_out.jsonl"
                path = tampered / relative
                path.write_bytes(path.read_bytes() + b'{"tampered": true}\n')
                repin(tampered, relative)
                self.assertTrue(manifest_matches_bytes(tampered))
                freeze = json.loads((tampered / export.FREEZE_PATH).read_text(encoding="utf-8"))
                self.assertNotEqual(freeze[f"{directory}_sha256"], sha(path))
                name = f"refused-bytes-{directory}"
                with refusal(self, cv.FINDING_EXPORT_INTEGRITY,
                             "held-out freeze digest", directory):
                    hub_bundle.run(self.request(tampered, name))
                self.assertFalse((self.root / name).exists())

    def test_a_lying_or_missing_freeze_digest_is_refused_when_the_manifest_matches(self):
        _manifest, out, _records, _run_dir = exported(self.root)
        original = json.loads((out / export.FREEZE_PATH).read_text(encoding="utf-8"))
        for name, directory, freeze in false_freezes(original):
            with self.subTest(name=name):
                tampered = self.root / f"freeze-{name}"
                shutil.copytree(out, tampered)
                write_json(tampered / export.FREEZE_PATH, freeze)
                repin(tampered, export.FREEZE_PATH)
                self.assertTrue(manifest_matches_bytes(tampered))
                bundle = f"refused-freeze-{name}"
                with refusal(self, cv.FINDING_EXPORT_INTEGRITY,
                             "held-out freeze digest", directory):
                    hub_bundle.run(self.request(tampered, bundle))
                self.assertFalse((self.root / bundle).exists())


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
        positive = required_item(r for r in records if views.is_positive(r))
        code, text, _err = invoke(["render", str(run_dir), positive["id"], "--json"])
        self.assertEqual(code, 0)
        payload = json.loads(text)
        self.assertEqual(views_chat.chat_pair(payload["chat"]),
                         (payload["sft"]["prompt"], payload["sft"]["completion"]))
        self.assertEqual(set(payload["edit"]), {"prompt", "completion"})
        self.assertTrue(payload["edit"]["completion"].startswith(cv.EDIT_SEARCH_MARKER))


if __name__ == "__main__":
    unittest.main()
