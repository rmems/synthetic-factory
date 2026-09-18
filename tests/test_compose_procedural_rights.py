"""Reviewed, completed procedural sources must survive composition and export."""

import json
import tempfile
import unittest
from pathlib import Path

from tests.code_repair_admission_test_support import build_generated_admission_evidence
from code_repair import publication
import compose_curated
import export_hf
import training_audit


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
        import training_audit_rights
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
