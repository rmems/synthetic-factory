"""Fresh simulator generation reaches exact research assembly, never training export."""

import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from pipelines import compose_curated, export_hf, training_audit, validate_run
from pipelines import curate_identity_simulator_process as process
from pipelines.oracle_grounded import fault_oracle

FACTORY = "fault-recovery-simulator-factory"


class SimulatorAssembly(unittest.TestCase):
    def _generated(self, root):
        records = fault_oracle.build_records(97531, 6, produced_at="2026-09-18T12:00:00.000Z")
        payload = "".join(json.dumps(row, separators=(",", ":")) + "\n" for row in records).encode()
        source = root / "source" / FACTORY / "fresh.jsonl"
        source.parent.mkdir(parents=True)
        source.write_bytes(payload)
        return records, payload, source.parent.parent

    def test_fresh_generation_validation_composition_replay_and_export_boundary(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            records, payload, source = self._generated(root)
            with process.replay_session():
                self.assertTrue(all(validate_run.check_line(row, "fresh") == ([], "fault_recovery") for row in records))
            with patch.object(process.subprocess, "Popen", wraps=process.subprocess.Popen) as launches:
                summary = compose_curated.compose_run(source, root / "composed")
            self.assertEqual(summary["counts"]["retained"], 6)
            self.assertEqual(launches.call_count, 2)
            target = root / "composed" / "records" / FACTORY / "fresh.jsonl"
            self.assertEqual(target.read_bytes(), payload)
            files, _rows, _snapshot = export_hf._curated_snapshot(target.parents[1])
            report = training_audit.audit_run(target.parents[1])
            self.assertEqual(report["totals"]["eligible_records"], 0)
            with patch.object(process.subprocess, "Popen", wraps=process.subprocess.Popen) as replay_launches:
                evidence = export_hf._compose_metadata(root / "composed", files, report)
            self.assertTrue(evidence)
            self.assertEqual(replay_launches.call_count, 1)
            with self.assertRaisesRegex(export_hf.ExportError, "research-only"):
                export_hf.export_run(root / "composed", root / "export")
            self.assertFalse((root / "export").exists())

    def test_crlf_and_unterminated_native_source_bytes_are_preserved(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            records = fault_oracle.build_records(97531, 2, produced_at="2026-09-18T12:00:00.000Z")
            first = json.dumps(records[0], separators=(",", ":")).encode()
            second = json.dumps(records[1], separators=(",", ":")).encode()
            payload = first + b"\r\n" + second
            source = root / "source" / FACTORY / "fresh.jsonl"
            source.parent.mkdir(parents=True)
            source.write_bytes(payload)
            summary = compose_curated.compose_run(source.parent.parent, root / "composed")
            self.assertEqual(summary["counts"]["retained"], 2)
            target = root / "composed" / "records" / FACTORY / "fresh.jsonl"
            self.assertEqual(target.read_bytes(), payload)
            with self.assertRaisesRegex(export_hf.ExportError, "research-only"):
                export_hf.export_run(root / "composed", root / "export")

    def test_malformed_family_claim_cannot_escape_to_thalamic_shape(self):
        from pipelines import record_kind

        claimant = {
            "family": "neuromorphic-fault-recovery",
            "state": {},
            "proposed_action": {},
            "safety_decision": {},
            "executed_action": {},
            "future_outcome": {},
            "reward_components": {},
        }
        self.assertEqual(record_kind.classify_kind(claimant), "fault_recovery")
        errors, kind = validate_run.check_line(claimant, "claim")
        self.assertEqual(kind, "fault_recovery")
        self.assertTrue(errors)

    def test_changed_native_source_precision_is_excluded(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            _records, payload, source = self._generated(root)
            target = source / FACTORY / "fresh.jsonl"
            changed = payload.replace(b'"confidence":0.5', b'"confidence":0.50000000000000000001', 1)
            self.assertNotEqual(changed, payload)
            target.write_bytes(changed)
            summary = compose_curated.compose_run(source, root / "composed")
            self.assertEqual(summary["counts"]["excluded"], 1)
