"""Rights manifests must cover retained records and cannot erase refusals."""

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from tests.test_curate_identity import episode, FABLE_ACT, identity
from pipelines import training_audit_rights, training_audit
from tests.compose_curated_test_support import build_source_run
from pipelines import compose_curated


class RightsManifestRefusal(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        root = Path(self.temp.name)
        source = root / "source" / FABLE_ACT
        source.mkdir(parents=True)
        (source / "batch.jsonl").write_text(identity.canonical_json(episode()) + "\n")
        self.destination = root / "cleaned"
        identity.write_run(root / "source", self.destination)
        self.manifest = self.destination / "IDENTITY-MANIFEST.json"

    def test_malformed_manifest_cannot_erase_rights_blockers(self):
        for document in ([], {}, None, [None], ["ignored"], [{"action": "excluded"}]):
            with self.subTest(document=document):
                self.manifest.write_text(json.dumps(document))
                blockers = training_audit_rights.collect_rights_blockers(self.destination)
                self.assertTrue(blockers, "present invalid manifest must fail closed")

    def test_removed_manifest_cannot_reclassify_identity_tree_as_raw(self):
        self.manifest.unlink()
        self.assertTrue(training_audit_rights.collect_rights_blockers(self.destination))

    def test_identity_rights_cover_the_captured_records_not_a_later_tree(self):
        files = {path.relative_to(self.destination).as_posix(): path.read_bytes()
                 for path in self.destination.rglob("*.jsonl")}
        relative = next(iter(files))
        record = json.loads(files[relative])
        record["id"] = "substituted-snapshot"
        files[relative] = (json.dumps(record) + "\n").encode()
        audit = training_audit_rights.capture_rights_audit(self.destination, files)
        self.assertTrue(any("tampered or stale" in item for item in audit.blockers), audit.blockers)

    def test_identity_coordinate_gaps_preserve_valid_research_verdict(self):
        root = self.destination.parent
        source = root / "gapped-source" / FABLE_ACT
        source.mkdir(parents=True)
        (source / "batch.jsonl").write_text("{}\n" + identity.canonical_json(episode()) + "\n")
        dest = root / "gapped-cleaned"
        identity.write_run(source.parent, dest)
        blockers = training_audit_rights.collect_rights_blockers(dest)
        self.assertTrue(any("research-only" in item for item in blockers), blockers)
        self.assertFalse(any("tampered or stale" in item for item in blockers), blockers)

    def test_original_identity_tree_retains_research_blocker(self):
        blockers = training_audit_rights.collect_rights_blockers(self.destination)
        self.assertTrue(any("research-only" in item for item in blockers), blockers)

    def test_boolean_identity_source_line_cannot_impersonate_a_coordinate(self):
        entries = json.loads(self.manifest.read_text())
        retained = next(entry for entry in entries if entry.get("action") == "retained")
        retained["source"]["line"] = True
        self.manifest.write_text(json.dumps(entries))
        blockers = training_audit_rights.collect_rights_blockers(self.destination)
        self.assertTrue(any("tampered or stale" in item for item in blockers), blockers)


class RightsAuditSnapshot(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        root = Path(temp.name)
        source = build_source_run(root / "source")
        self.dest = root / "curated"
        compose_curated.compose_run(compose_curated.ComposeRunContext(source, self.dest))
        self.manifest = self.dest / "manifest/compose-manifest.jsonl"
        self.entries = [json.loads(line) for line in self.manifest.read_text().split("\n") if line]

    def _write_entries(self, entries):
        self.manifest.write_text("".join(json.dumps(entry) + "\n" for entry in entries))

    def _blockers(self):
        return training_audit_rights.collect_rights_blockers(self.dest / "records")

    def test_compose_manifest_requires_complete_record_coverage(self):
        mutations = ([], [None], [entry for entry in self.entries if entry["action"] != "retained"])
        for entries in mutations:
            with self.subTest(entries=entries):
                self._write_entries(entries)
                blockers = self._blockers()
                self.assertTrue(any("tampered or stale" in item for item in blockers), blockers)

    def test_removed_compose_manifest_cannot_reclassify_records_as_raw(self):
        self.manifest.unlink()
        self.assertTrue(self._blockers())

    def test_boolean_output_line_cannot_impersonate_a_coordinate(self):
        retained = next(entry for entry in self.entries if entry["action"] == "retained")
        retained["output_line"] = True
        self._write_entries(self.entries)
        blockers = self._blockers()
        self.assertTrue(any("tampered or stale" in item for item in blockers), blockers)

    def test_malformed_identity_stage_fails_closed(self):
        retained = next(entry for entry in self.entries if entry["action"] == "retained")
        retained["stages"] = [{"lane": "identity", "detail": ["not-an-object"]}]
        self._write_entries(self.entries)
        self.assertTrue(any("tampered or stale" in item for item in self._blockers()))

    def test_manifest_swap_during_record_scan_cannot_remove_refusal(self):
        observe = training_audit._CorpusAudit.observe_file

        def swap(audit, *args):
            self.manifest.write_bytes(b"")
            return observe(audit, *args)

        with patch.object(training_audit._CorpusAudit, "observe_file", swap):
            report = training_audit.audit_run(self.dest / "records")
        self.assertTrue(any(item.startswith("rights:") for item in report["blockers"]))


class MalformedManifestPresence(unittest.TestCase):
    def test_empty_manifest_is_invalid_even_without_record_files(self):
        for relative, payload in (("IDENTITY-MANIFEST.json", b"[]"), ("manifest/compose-manifest.jsonl", b"")):
            with self.subTest(relative=relative), tempfile.TemporaryDirectory() as temp:
                root = Path(temp)
                path = root / relative
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(payload)
                self.assertTrue(training_audit_rights.capture_rights_audit(root).blockers)

    def test_directory_manifest_is_not_absence(self):
        for relative in ("IDENTITY-MANIFEST.json", "manifest/compose-manifest.jsonl"):
            with self.subTest(relative=relative), tempfile.TemporaryDirectory() as temp:
                root = Path(temp)
                (root / relative).mkdir(parents=True)
                self.assertTrue(training_audit_rights.capture_rights_audit(root).blockers)

    def test_dangling_manifest_symlink_is_not_absence(self):
        for relative in ("IDENTITY-MANIFEST.json", "manifest/compose-manifest.jsonl"):
            with self.subTest(relative=relative), tempfile.TemporaryDirectory() as temp:
                root = Path(temp)
                path = root / relative
                path.parent.mkdir(parents=True, exist_ok=True)
                path.symlink_to(root / "missing")
                self.assertTrue(training_audit_rights.capture_rights_audit(root).blockers)
