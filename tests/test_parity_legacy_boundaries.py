"""Legacy marker adoption and deep audit preserve parity evidence boundaries."""

from pathlib import Path
import tempfile
import unittest

from pipelines import check_records, hardware_parity as hp, nir_equivalence as nir, round_txn
from pipelines.exact_json import dumps_exact_json


class LegacyParityBoundaries(unittest.TestCase):
    def test_partial_catalog_cannot_become_a_committed_legacy_baseline(self):
        for module in (hp, nir):
            with self.subTest(module=module.__name__), tempfile.TemporaryDirectory() as tmp:
                records = module.generate_records()
                factory = Path(tmp) / records[0]["meta"]["factory"]
                module.write_jsonl(factory / "batch-r01.jsonl", records[:1])
                with self.assertRaises(round_txn.TransactionError):
                    round_txn.ensure_marker_mode(factory)
                self.assertFalse((factory / round_txn.MODE_FILE).exists())

    def test_complete_catalog_can_become_a_legacy_baseline(self):
        for module in (hp, nir):
            with self.subTest(module=module.__name__), tempfile.TemporaryDirectory() as tmp:
                records = module.generate_records()
                factory = Path(tmp) / records[0]["meta"]["factory"]
                module.write_jsonl(factory / "batch-r01.jsonl", records)
                marker = round_txn.ensure_marker_mode(factory)
                self.assertEqual(marker["legacy_baseline"], 1)

    def test_deep_audit_rejects_duplicate_fields_in_original_parity_bytes(self):
        for module in (hp, nir):
            record = module.generate_records()[0]
            payload = dumps_exact_json(record, ensure_ascii=False, sort_keys=True)
            duplicate = '{"record_kind":' + dumps_exact_json(record["record_kind"]) + ',' + payload[1:]
            with self.subTest(module=module.__name__), tempfile.TemporaryDirectory() as tmp:
                path = Path(tmp) / "batch-r01.jsonl"
                path.write_text(duplicate + "\n", encoding="utf-8")
                errors, _, _, count = check_records.check_jsonl(path, path.name)
                self.assertTrue(any("duplicate" in error.lower() for error in errors), errors)
                self.assertEqual(count, 0)
