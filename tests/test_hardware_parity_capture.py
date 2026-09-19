"""Captured-evidence provenance for pipelines/hardware_parity.py.

Covers the recorded-capture replay path, physical-target claims, and the
training views derived from them.
"""

import copy
import json
import os
# Required only for the fixed-argv interpreter subprocess below.
import subprocess  # nosec B404
import tempfile
import unittest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from hardware_parity_support import PIPELINES, WHERE, CaptureCase  # noqa: E402

import hardware_parity as hp  # noqa: E402
import neuro_oracle as oracle  # noqa: E402


class RecordedCapturePath(CaptureCase):
    """The `--capture` route must actually produce validatable records.

    It is also the one place where the deployment traces are *not*
    re-derivable, so these tests pin how that limitation is surfaced.
    """

    def test_capture_derived_records_validate(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.assertEqual(hp.validate_record(self._record(tmp), WHERE), [])

    def test_capture_derived_record_declares_unknown_provenance(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.assertEqual(self._record(tmp)["provenance"]["kind"], "unknown")

    def test_capture_evidence_cannot_be_relabelled_as_an_unknown_adapter(self):
        self._assert_relabelled_adapter_rejected(
            "plausible_vendor_driver", "physical_hardware", "unsupported adapter identity"
        )

    def test_capture_digest_chain_is_rechecked_from_stored_source(self):
        with tempfile.TemporaryDirectory() as tmp:
            record = self._record(tmp)
            record["oracle"]["deployment"]["capture"]["source"]["payload"][
                "spikes"
            ][0][0] ^= 1
            errors = hp.validate_record(record, WHERE)
            self.assertTrue(any("capture" in error.lower() for error in errors), errors)

    def test_capture_recorded_at_is_bound_to_the_manifest(self):
        def mutate(record):
            record["oracle"]["deployment"]["capture"]["recorded_at"] = "1999-01-01T00:00:00Z"

        self._assert_capture_rejected(("recorded_at", "HW_PROVENANCE_MISSING"), mutate)

    def test_missing_capture_recorded_at_is_rejected(self):
        self._assert_capture_rejected(
            ("recorded_at", "HW_PROVENANCE_MISSING"),
            lambda record: record["oracle"]["deployment"]["capture"].pop("recorded_at", None),
        )

    def test_whitespace_only_recorded_at_does_not_bind(self):
        # A whitespace-only value matched on both sides must not validate as
        # bound provenance; `not recorded_at` alone only rejects "".
        with tempfile.TemporaryDirectory() as tmp:
            record = self._record(tmp)
            record["oracle"]["deployment"]["capture"]["recorded_at"] = "   "
            record["oracle"]["deployment"]["capture"]["source"]["manifest"][
                "recorded_at"
            ] = "   "
            errors = hp.validate_record(record, WHERE)
            self.assertTrue(
                any(
                    "recorded_at" in error and "HW_PROVENANCE_MISSING" in error
                    for error in errors
                ),
                errors,
            )

    def test_capture_lineage_includes_physical_provenance_digest(self):
        # Two captures with identical behavioural output but different
        # physical provenance must not collapse to the same result lineage.
        with tempfile.TemporaryDirectory() as tmp:
            record = self._record(tmp)
            derived = record["result"]["derived_from"]
            self.assertEqual(len(derived), 3, derived)
            record["result"]["derived_from"] = derived[:2]
            errors = hp.validate_record(record, WHERE)
            self.assertTrue(
                any("RESULT_DIGEST_UNLINKED" in error for error in errors), errors
            )

    def test_physical_bitstream_requires_canonical_sha256(self):
        with tempfile.TemporaryDirectory() as tmp:
            record = self._record(tmp, bitstream_sha256="sha256:" + "A" * 64)
            errors = hp.validate_record(record, WHERE)
            self.assertTrue(
                any("canonical lowercase" in error for error in errors), errors
            )

    def test_truncated_capture_window_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            record = self._record(tmp, truncate_spikes=True)
            self.assertFalse(record["result"]["parity"]["timing"]["comparable"])
            errors = hp.validate_record(record, WHERE)
            self.assertTrue(
                any(
                    "spikes must have exactly 6 rows" in error
                    and "ENVELOPE_MALFORMED" in error
                    for error in errors
                ),
                errors,
            )

    def test_capture_spike_width_is_bound_to_neuron_count(self):
        self._assert_capture_rejected(("spikes[0]", "exactly 4 cells"), narrow_spikes=True)

    def test_capture_spike_cells_are_exact_binary_integers(self):
        for cell in (True, 2, 0.5):
            with self.subTest(cell=cell), tempfile.TemporaryDirectory() as tmp:
                record = self._record(tmp, invalid_spike_cell=cell)
                errors = hp.validate_record(record, WHERE)
                self.assertTrue(
                    any("exact integer 0 or 1" in error for error in errors), errors
                )

    def test_capture_membrane_width_is_bound_to_neuron_count(self):
        self._assert_capture_rejected(("membrane.trace[0]", "exactly 4 cells"), narrow_membrane=True)

    def test_capture_action_and_events_must_encode_the_spike_grid(self):
        with tempfile.TemporaryDirectory() as tmp:
            record = self._record(tmp)
            deployment = record["oracle"]["deployment"]
            deployment["action"]["counts"][0] += 1
            deployment["spike_events"][0]["neuron_id"] += 1
            errors = hp.validate_record(record, WHERE)
            self.assertTrue(any(".action does not decode" in error for error in errors), errors)
            self.assertTrue(
                any(".spike_events does not exactly" in error for error in errors),
                errors,
            )

    def test_capture_arithmetic_attestation_is_strict_and_nonnegative(self):
        malformed_values = (
            None,
            {"format": "Q7.9", "saturation_events": 0},
            {"format": "Q8.8", "saturation_events": -1},
            {"format": "Q8.8", "saturation_events": False},
            {"format": "Q8.8", "saturation_events": 0.0},
        )
        for malformed in malformed_values:
            with self.subTest(
                arithmetic=malformed
            ), tempfile.TemporaryDirectory() as tmp:
                record = self._record(tmp)
                deployment = record["oracle"]["deployment"]
                capture = deployment["capture"]
                source = capture["source"]
                payload = source["payload"]
                deployment["arithmetic"] = copy.deepcopy(malformed)
                payload["arithmetic"] = copy.deepcopy(malformed)
                for repeat in payload["repeat_outputs"]:
                    repeat["arithmetic"] = copy.deepcopy(malformed)
                payload_sha = oracle.digest(payload)
                source["manifest"]["payload_sha256"] = payload_sha
                capture["payload_sha256"] = payload_sha
                capture["manifest_sha256"] = oracle.digest(source["manifest"])
                capture["source_sha256"] = oracle.digest(source)

                errors = hp.validate_record(record, WHERE)
                self.assertTrue(
                    any(
                        "arithmetic must declare Q8.8" in error
                        and "ENVELOPE_MALFORMED" in error
                        for error in errors
                    ),
                    errors,
                )

    def test_physical_provenance_values_must_be_nonempty_strings(self):
        mutations = (
            ("hardware", "revision", True),
            ("hardware", "board_serial", 9),
            ("bitstream", "sha256", False),
            ("bitstream", "toolchain", "   "),
            ("capture", "manifest_sha256", ["sha256:bb"]),
        )
        for section, key, value in mutations:
            with self.subTest(
                path=f"{section}.{key}"
            ), tempfile.TemporaryDirectory() as tmp:
                record = self._record(tmp)
                record["oracle"]["deployment"][section][key] = value
                errors = hp.validate_record(record, WHERE)
                self.assertTrue(
                    any(
                        f"oracle.deployment.{section}.{key}" in error
                        and "HW_PROVENANCE_MISSING" in error
                        for error in errors
                    ),
                    errors,
                )

    def test_live_fpga_identity_requires_an_available_transport(self):
        with tempfile.TemporaryDirectory() as tmp:
            record = self._record(tmp)
            deployment = record["oracle"]["deployment"]
            deployment["adapter"] = oracle.FpgaHardwareAdapter.name
            deployment["runtime_class"] = oracle.FpgaHardwareAdapter.runtime_class
            source = deployment["capture"]["source"]
            source["adapter"] = oracle.FpgaHardwareAdapter.name
            source["runtime_class"] = oracle.FpgaHardwareAdapter.runtime_class
            deployment["capture"]["source_sha256"] = oracle.digest(source)
            errors = hp.validate_record(record, WHERE)
            self.assertTrue(
                any(
                    "current adapter probe to report available" in error
                    for error in errors
                ),
                errors,
            )

    def test_recorded_capture_cannot_be_relabelled_as_a_live_board(self):
        self._assert_relabelled_adapter_rejected(
            oracle.FpgaHardwareAdapter.name,
            oracle.FpgaHardwareAdapter.runtime_class,
            "live FPGA evidence must bind",
        )


if __name__ == "__main__":
    unittest.main()
