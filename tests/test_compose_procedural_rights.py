"""Reviewed, completed procedural sources must survive composition and export."""

import json
import tempfile
import unittest
from pathlib import Path

from tests.code_repair_admission_test_support import build_generated_admission_evidence
from tests.compose_curated_test_support import build_source_run
from code_repair import publication
from code_repair.publication_export import physical_completed_batch
import compose_curated
import export_hf
import training_audit
import training_audit_rights
from rights_record import ENVELOPE_FIELD, LANE_FIELD


class CompletedProceduralRights(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        _, cls.generated, _, _ = build_generated_admission_evidence(cls)

    def test_completed_source_remains_training_ready_after_compose_and_export(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            source = root / "outputs/raw/2099-01-01"
            factory = source / "python-function-repair-factory"
            factory.mkdir(parents=True)
            publication.publish_run(publication.PublishRequest(self.generated, factory, 1))
            before = training_audit.audit_run(source)
            self.assertTrue(before["training_ready"], before["blockers"])
            curated = root / "curated"
            summary = compose_curated.compose_run(source, curated)
            self.assertTrue(summary["audit"]["training_ready"], summary["audit"]["blockers"])
            self.assertTrue(summary["rights"]["training_exportable"])
            exported = export_hf.export_run(curated, root / "export")
            self.assertTrue(exported["training_ready"])

    def test_reviewed_procedural_source_passes_gate_and_promotion(self):
        from tests.procedural_gate_support import ProceduralGateFixture
        from tests.gate_fixture import _captured_main
        with tempfile.TemporaryDirectory() as temp:
            fixture = ProceduralGateFixture(temp, self.generated)
            code, report, errors = _captured_main([
                "integrate", "--plan", str(fixture.plan_path),
                "--cleaned-out", str(fixture.cleaned),
            ])
            self.assertEqual(code, 0, (report, errors))
            self.assertTrue(fixture.manifest()["gates"]["rights"]["passed"])
            code, report, errors = fixture.promote_report(fixture.accepted_review())
            self.assertEqual(code, 0, (report, errors))

    def test_gate_refuses_altered_procedural_authority(self):
        self._assert_gate_refuses_identity_change(
            "procedural_authority", "eligible_training_candidate", False,
        )

    def test_promotion_refuses_substituted_completion_source(self):
        from tests.procedural_gate_support import ProceduralGateFixture
        import round_txn
        with tempfile.TemporaryDirectory() as temp:
            fixture = ProceduralGateFixture(temp, self.generated)
            self.assertEqual(fixture.integrate(), 0)
            markers = round_txn.marker_paths(
                fixture.source_run / "python-function-repair-factory", 1,
            )
            markers["complete"].unlink()
            code, report, errors = fixture.promote_report(fixture.accepted_review())
            self.assertNotEqual(code, 0, (report, errors))
            self.assertFalse(fixture.curated.exists())

    def test_gate_refuses_substituted_identity_source(self):
        self._assert_gate_refuses_identity_change("source", "original", '{"id":"substituted"}')

    def _assert_gate_refuses_identity_change(self, section, field, value):
        from tests.procedural_gate_support import ProceduralGateFixture
        with tempfile.TemporaryDirectory() as temp:
            fixture = ProceduralGateFixture(temp, self.generated)
            manifest = fixture.manifest_paths[1]
            entries = json.loads(manifest.read_bytes())
            entry = next(item for item in entries if item["action"] == "retained")
            entry[section][field] = value
            manifest.write_text(json.dumps(entries))
            self.assertEqual(fixture.integrate(), 2)

    def test_outer_rights_verdict_rejects_integer_in_place_of_boolean(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            source = root / "outputs/raw/2099-01-01"
            factory = source / "python-function-repair-factory"
            factory.mkdir(parents=True)
            publication.publish_run(publication.PublishRequest(self.generated, factory, 1))
            curated = root / "curated"
            compose_curated.compose_run(source, curated)
            manifest = curated / "manifest/compose-manifest.jsonl"
            entries = [json.loads(line) for line in manifest.read_text().split("\n") if line]
            retained = next(entry for entry in entries if entry["action"] == "retained")
            retained["rights"]["eligible_training_candidate"] = 1
            manifest.write_text("".join(json.dumps(entry) + "\n" for entry in entries))
            blockers = training_audit_rights.collect_rights_blockers(curated / "records")
            self.assertTrue(any("tampered or stale" in item for item in blockers), blockers)

    def test_factory_root_compose_keeps_completed_procedural_records(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            factory = root / "outputs/raw/2099-01-01/python-function-repair-factory"
            factory.mkdir(parents=True)
            publication.publish_run(publication.PublishRequest(self.generated, factory, 1))
            curated = root / "curated"
            summary = compose_curated.compose_run(factory, curated)
            self.assertTrue(summary["audit"]["training_ready"], summary["audit"]["blockers"])
            report = training_audit.audit_run(curated / "records", completion_source=factory)
            self.assertTrue(report["training_ready"], report["blockers"])
            self.assertGreater(report["code_repair"]["records"], 0)
            self.assertEqual(
                report["code_repair"]["completed_records"],
                report["code_repair"]["records"],
            )
            exported = export_hf.export_run(curated, root / "export")
            self.assertTrue(exported["training_ready"])

    def test_transplanted_procedural_proof_cannot_authorize_hosted_output(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            hosted = root / "hosted"
            compose_curated.compose_run(build_source_run(root / "hosted-source"), hosted)
            factory = root / "outputs/raw/2099-01-01/python-function-repair-factory"
            factory.mkdir(parents=True)
            publication.publish_run(publication.PublishRequest(self.generated, factory, 1))
            procedural = root / "procedural"
            compose_curated.compose_run(factory.parent, procedural)
            hosted_path = hosted / "manifest/compose-manifest.jsonl"
            hosted_entries = [
                json.loads(line) for line in hosted_path.read_text().split("\n") if line
            ]
            procedural_entries = [
                json.loads(line)
                for line in (procedural / "manifest/compose-manifest.jsonl").read_text().split("\n")
                if line
            ]
            hosted_retained = next(entry for entry in hosted_entries if entry["action"] == "retained")
            procedural_retained = next(
                entry for entry in procedural_entries if entry["action"] == "retained"
            )
            hosted_retained["stages"] = procedural_retained["stages"]
            hosted_retained[ENVELOPE_FIELD] = procedural_retained[ENVELOPE_FIELD]
            hosted_retained[LANE_FIELD] = procedural_retained[LANE_FIELD]
            hosted_path.write_text("".join(json.dumps(entry) + "\n" for entry in hosted_entries))
            blockers = training_audit_rights.collect_rights_blockers(hosted / "records")
            self.assertTrue(any("tampered or stale" in item for item in blockers), blockers)
            report = training_audit.audit_run(hosted / "records")
            self.assertFalse(report["training_ready"])
            self.assertTrue(any(item.startswith("rights:") for item in report["blockers"]))

    def test_physical_completed_batch_strips_factory_prefix_only_when_rooted_there(self):
        factory = Path("/tmp/python-function-repair-factory")
        relative = Path("python-function-repair-factory/batch-r01.jsonl")
        self.assertEqual(physical_completed_batch(factory, relative), factory / "batch-r01.jsonl")
        run_root = Path("/tmp/2099-01-01")
        self.assertEqual(physical_completed_batch(run_root, relative), run_root / relative)
