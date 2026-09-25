"""Publication must preserve the complete scenario inventory and reserved round."""

from pathlib import Path
import tempfile
import unittest
from unittest import mock

from pipelines import hardware_parity as hp, nir_equivalence as nir, round_txn
from pipelines.oracle_grounded.parity_jsonl import read_jsonl


class PublicationBoundaries(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.addCleanup(mock.patch.stopall)
        mock.patch.object(round_txn, "committed_ids", side_effect=lambda _path: {}).start()

    def _check(self, module, records, round_number=1):
        batch = self.root / "candidate.jsonl"
        batch.unlink(missing_ok=True)
        module.write_jsonl(batch, records)
        return round_txn._validate_staged_batch(
            batch, self.root / records[0]["meta"]["factory"], len(records), round_number,
        )

    def test_complete_catalog_rounds_are_accepted(self):
        for module in (hp, nir):
            with self.subTest(module=module.__name__):
                records = module.generate_records(round_number=2)
                self.assertEqual(self._check(module, records, 2)[1], len(records))

    def test_filtered_valid_records_cannot_publish_a_partial_catalog(self):
        for module in (hp, nir):
            with self.subTest(module=module.__name__), self.assertRaises(round_txn.TransactionError):
                self._check(module, module.generate_records()[:1])

    def test_complete_catalog_cannot_claim_another_reserved_round(self):
        for module in (hp, nir):
            with self.subTest(module=module.__name__), self.assertRaises(round_txn.TransactionError):
                self._check(module, module.generate_records(round_number=2), 1)

    def test_ambiguous_json_keys_are_refused_before_publication(self):
        path = self.root / "ambiguous.jsonl"
        path.write_text('{"record_kind":"hardware_parity","record_kind":"nir_equivalence"}\n')
        records, errors = read_jsonl(path)
        self.assertEqual(records, [])
        self.assertTrue(errors)
