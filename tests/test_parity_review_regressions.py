"""Historical runtime evidence and physical capture quantization boundaries."""

import copy
from pathlib import Path
import tempfile
import unittest
from unittest import mock

from hardware_parity_support import WHERE
import hardware_parity as hp
import nir_equivalence as nir
import nir_equivalence_runtimes as runtimes
import test_hardware_parity_capture as capture_support
import census
import check_records
import round_txn


class HistoricalAvailability(unittest.TestCase):
    def test_installing_unimplemented_packages_preserves_recorded_diagnostics(self):
        record = nir.generate_records()[0]
        before = copy.deepcopy(record)
        with mock.patch.object(runtimes.importlib.util, "find_spec", return_value=object()):
            self.assertEqual(nir.validate_record(record, WHERE), [])
        self.assertEqual(record, before)

    def test_a_now_available_runtime_still_refuses_an_unavailable_claim(self):
        record = nir.generate_records()[0]
        runtime = runtimes.UPSTREAM_RUNTIMES[0]
        with mock.patch.object(runtime, "availability", return_value={"available": True}):
            errors = nir.validate_record(record, WHERE)
        self.assertTrue(any("probe reports available" in error for error in errors), errors)


class CapturePresence(unittest.TestCase):
    def test_falsy_top_level_quantization_cannot_hide_a_conflict(self):
        fixture = capture_support.RecordedCapturePath()
        for value in ({}, None, False, 0, ""):
            with self.subTest(value=value), tempfile.TemporaryDirectory() as tmp:
                record = copy.deepcopy(fixture._record(tmp))
                source = record["oracle"]["deployment"]["capture"]["source"]
                source["payload"]["quantization"] = source["quantization"]
                source["quantization"] = value
                fixture._reseal_capture(record)
                errors = hp.validate_record(record, WHERE)
                self.assertTrue(any("Q88_PROVENANCE_MISMATCH" in error for error in errors), errors)

    def test_payload_only_quantization_remains_valid(self):
        fixture = capture_support.RecordedCapturePath()
        with tempfile.TemporaryDirectory() as tmp:
            record = copy.deepcopy(fixture._record(tmp))
            source = record["oracle"]["deployment"]["capture"]["source"]
            source["payload"]["quantization"] = source.pop("quantization")
            fixture._reseal_capture(record)
            self.assertEqual(hp.validate_record(record, WHERE), [])


class FactoryBinding(unittest.TestCase):
    def test_swapped_batch_is_foreign_in_census_and_deep_validation(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            factory = root / "hardware-parity-spike-trajectories"
            factory.mkdir()
            batch = factory / "batch-r01.jsonl"
            nir.write_jsonl(batch, nir.generate_records())
            self.assertTrue(check_records.check_jsonl(batch, batch.name)[0])
            self.assertTrue(census.census_dir(root)["mill_mix"]["quarantined_records"])

    def test_transaction_checks_factory_even_for_an_external_staging_path(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            batch = root / "candidate.jsonl"
            records = nir.generate_records()
            nir.write_jsonl(batch, records)
            with mock.patch.object(round_txn, "committed_ids", side_effect=lambda _path: {}):
                with self.assertRaises(round_txn.TransactionError):
                    round_txn._validate_staged_batch(
                        batch, root / "hardware-parity-spike-trajectories", len(records), 1
                    )
                kinds, count = round_txn._validate_staged_batch(
                    batch, root / "nir-cross-runtime-equivalence", len(records), 1
                )
            self.assertEqual((kinds, count), ({"nir_equivalence": len(records)}, len(records)))
