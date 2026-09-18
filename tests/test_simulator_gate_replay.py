"""Native simulator identity evidence replays exactly and cannot authorize training."""

import copy
import json
import tempfile
from pathlib import Path
import unittest

from pipelines import curate_gate_identity_gate as claims
from pipelines import curate_gate_identity_mapping as mappings
from pipelines import curate_gate_manifests as manifests
from pipelines import curate_identity as identity
from pipelines import training_audit
from pipelines import check_records
from pipelines.oracle_grounded import fault_oracle


class SimulatorGateReplay(unittest.TestCase):
    def _entry(self):
        record = fault_oracle.build_records(42, 1, produced_at="2026-08-23T00:00:00.000Z")[0]
        source = identity.SourceRecord(record, "fault-recovery-simulator-factory/records.jsonl", 1)
        result = identity.curate_record(source)
        entry = manifests._normalize_entry(result.mapping, {"order": 1, "transform": "curate_identity", "version": "identity-provenance-v1"})
        return record, entry

    def test_authentic_preserved_mapping_passes_source_and_final_identity_gates(self):
        record, entry = self._entry()
        entry["source_originals_sha256"] = claims._authenticate_identity_source_claims(entry, record, "native")
        result = mappings._identity_mapping_gate([entry], {(entry["source_path"], 1): record})
        self.assertTrue(result["passed"], result)
        row = identity.default_registry().by_path_id["fault-recovery-simulator-factory"]
        self.assertEqual(row.training_ready_policy, "never")

    def test_authority_and_outer_envelope_mutations_are_refused(self):
        record, original = self._entry()
        for field, value in (("source_line", True), ("output_id", "forged"), ("record_kind", "thalamic")):
            with self.subTest(field=field):
                changed = copy.deepcopy(original)
                changed[field] = value
                with self.assertRaises(claims.GateError):
                    claims._authenticate_identity_source_claims(changed, record, "native")
        changed = copy.deepcopy(original)
        changed["identity_detail"]["simulator_authority"]["basis"] = "self-assertion"
        with self.assertRaises(claims.GateError):
            claims._authenticate_identity_source_claims(changed, record, "native")

    def test_native_research_records_are_never_training_eligible(self):
        record, _entry = self._entry()
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            target = root / "fault-recovery-simulator-factory" / "records.jsonl"
            target.parent.mkdir()
            target.write_text(json.dumps(record) + "\n")
            report = training_audit.audit_run(root)
        self.assertEqual(report["totals"]["eligible_records"], 0)
        self.assertEqual(report["identity"]["coverage_pct"], 100.0)
        self.assertFalse(report["training_ready"])

    def test_shared_record_validation_retains_native_replay_errors(self):
        record, _entry = self._entry()
        self.assertEqual(check_records.check_record(record, "native")[0], [])
        record["result"]["unreviewed"] = True
        self.assertTrue(check_records.check_record(record, "native")[0])

    def test_native_research_record_survives_real_integration_without_reencoding(self):
        from tests.gate_fixture import GateFixture
        record, _entry = self._entry()
        payload = (json.dumps(record, separators=(",", ":")) + "\r\n").encode()
        relative = "fault-recovery-simulator-factory/records.jsonl"
        with tempfile.TemporaryDirectory() as temp:
            fixture = GateFixture(Path(temp))
            for root in (fixture.source_run, fixture.lane_core):
                target = root / relative
                target.parent.mkdir()
                target.write_bytes(payload)
            source = identity.SourceRecord(record, relative, 1,
                identity.sha256_bytes(payload[:-2]), payload[:-2].decode())
            manifest_path = fixture.manifest_paths[1]
            entries = json.loads(manifest_path.read_text())
            for entry in entries:
                entry["transform_version"] = identity.TRANSFORM_VERSION
            plan = json.loads(fixture.plan_path.read_text())
            plan["lanes"][1]["version"] = identity.TRANSFORM_VERSION
            fixture.plan_path.write_text(json.dumps(plan))
            entries.append(identity.curate_record(source).mapping)
            manifest_path.write_text(json.dumps(entries))
            from tests.gate_fixture import _captured_main
            code, _report, errors = _captured_main([
                "integrate", "--plan", str(fixture.plan_path), "--cleaned-out", str(fixture.cleaned)])
            self.assertTrue(fixture.cleaned.exists(), (code, errors))
            manifest = fixture.manifest()
            self.assertTrue(manifest["gates"]["identity_mappings"]["passed"], manifest["gates"]["identity_mappings"])
            self.assertEqual((fixture.cleaned / relative).read_bytes(), payload)
            report = training_audit.audit_run(fixture.cleaned)
            self.assertFalse(report["training_ready"])
            self.assertEqual(report["factories"]["fault-recovery-simulator-factory"]["eligible_records"], 0)

    def test_mixed_ready_corpus_cannot_export_research_only_simulator(self):
        from tests.gate_fixture import GateFixture
        from pipelines import export_hf
        record, _entry = self._entry()
        with tempfile.TemporaryDirectory() as temp:
            fixture = GateFixture(Path(temp))
            self.assertEqual(fixture.integrate(), 0)
            payload = (json.dumps(record, separators=(",", ":")) + "\n").encode()
            target = fixture.cleaned / "fault-recovery-simulator-factory" / "records.jsonl"
            target.parent.mkdir()
            target.write_bytes(payload)
            report = training_audit.audit_run(fixture.cleaned)
            self.assertGreater(report["totals"]["eligible_records"], 0)
            self.assertEqual(report["identity"]["coverage_pct"], 100.0)
            self.assertFalse(report["training_ready"])
            self.assertTrue(any("research-only" in reason for reason in report["blockers"]))
            files, _rows, snapshot = export_hf._curated_snapshot(fixture.cleaned)
            self.assertIn(payload, [item.payload for item in files])
            with self.assertRaisesRegex(export_hf.ExportError, "research-only"):
                export_hf._training_ready_audit(fixture.cleaned, snapshot)
            export_root = Path(temp) / "export-source"
            native = export_root / "records" / "fault-recovery-simulator-factory" / "records.jsonl"
            native.parent.mkdir(parents=True)
            native.write_bytes(payload)
            destination = Path(temp) / "export-destination"
            with self.assertRaisesRegex(export_hf.ExportError, "research-only"):
                export_hf.export_run(export_root, destination)
            self.assertFalse(destination.exists())
