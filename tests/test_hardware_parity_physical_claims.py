"""Physical-target claims in hardware-parity records.

A record may only claim an execution target it can substantiate; these
tests pin the rejection of unsupported or unproven physical claims.
"""

import copy
import unittest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from hardware_parity_support import (  # noqa: E402
    WHERE,
)

import hardware_parity as hp  # noqa: E402
import neuro_oracle as oracle  # noqa: E402

class PhysicalTargetClaims(unittest.TestCase):
    def _promoted(self, hil=True, **deployment_overrides):
        """A reference-model record relabelled as if it came from a board."""
        record = copy.deepcopy(hp.generate_records(round_number=1, steps=4, repeats=2)[0])
        deployment = record["oracle"]["deployment"]
        deployment["execution_target"] = oracle.TARGET_FPGA_HARDWARE
        deployment.update(copy.deepcopy(deployment_overrides))
        if hil:
            record["provenance"]["kind"] = "hil"
        return record

    def test_bare_fpga_claim_is_rejected(self):
        errors = hp.validate_record(self._promoted(), WHERE)
        self.assertTrue(any("HW_PROVENANCE_MISSING" in error for error in errors))

    def test_hardware_claim_must_declare_hil_provenance(self):
        # A record claiming a board while still calling itself `simulated` is
        # not describing one execution consistently.
        errors = hp.validate_record(self._promoted(hil=False), WHERE)
        self.assertTrue(any("provenance.kind 'hil'" in error for error in errors))

    def _fully_attributed(self):
        """Everything the physical-target gate demands, and nothing more."""
        return {
            "hardware": {"revision": "rev-b", "board_serial": "SN-1"},
            "bitstream": {"sha256": "sha256:aa", "toolchain": "vendor 1.2"},
            "capture": {"manifest_sha256": "sha256:bb"},
            "latency": {"measured": True, "value_ms": 0.4},
            "repeats": 3,
            "repeat_digests": ["sha256:cc"] * 3,
            "determinism": {"distinct_digests": 1, "identical_repeats": True},
            "output_digest": "sha256:cc",
        }

    def test_each_required_field_is_individually_load_bearing(self):
        # Drop exactly one field from an otherwise complete claim, so the test
        # cannot pass merely because everything is missing at once.
        for section, key in hp.REQUIRED_HARDWARE_FIELDS:
            with self.subTest(field=f"{section}.{key}"):
                attributed = self._fully_attributed()
                del attributed[section][key]
                errors = hp.validate_record(self._promoted(**attributed), WHERE)
                self.assertTrue(
                    any(f"{section}.{key}" in error for error in errors),
                    f"{section}.{key} was not demanded",
                )

    def test_labels_alone_cannot_turn_a_reference_run_into_hardware(self):
        # Even a fully decorated reference-model record lacks the capture
        # source bytes and adapter binding needed for a physical claim.
        errors = hp.validate_record(self._promoted(**self._fully_attributed()), WHERE)
        self.assertTrue(
            any("capture.source" in error or "cannot come from adapter" in error
                for error in errors),
            errors,
        )

    def test_unmeasured_latency_blocks_a_hardware_claim(self):
        record = self._promoted(
            hardware={"revision": "rev-b", "board_serial": "SN-1"},
            bitstream={"sha256": "sha256:aa", "toolchain": "vendor 1.2"},
            capture={"manifest_sha256": "sha256:bb"},
        )
        errors = hp.validate_record(record, WHERE)
        self.assertTrue(any("measured latency" in error for error in errors))

    def test_physical_latency_must_be_finite_nonnegative_and_not_boolean(self):
        for value in (True, -0.1, float("nan"), float("inf")):
            with self.subTest(value=value):
                attributed = self._fully_attributed()
                attributed["latency"]["value_ms"] = value
                errors = hp.validate_record(self._promoted(**attributed), WHERE)
                self.assertTrue(
                    any("measured latency" in error for error in errors), errors
                )

    def test_single_run_cannot_prove_determinism(self):
        record = self._promoted(
            hardware={"revision": "rev-b", "board_serial": "SN-1"},
            bitstream={"sha256": "sha256:aa", "toolchain": "vendor 1.2"},
            capture={"manifest_sha256": "sha256:bb"},
            latency={"measured": True, "value_ms": 0.4},
            repeats=1,
        )
        errors = hp.validate_record(record, WHERE)
        self.assertTrue(any("REPEATABILITY_UNPROVEN" in error for error in errors))

    def test_unknown_execution_target_is_rejected(self):
        record = self._promoted()
        record["oracle"]["deployment"]["execution_target"] = "some_accelerator"
        errors = hp.validate_record(record, WHERE)
        self.assertTrue(any("HW_TARGET_UNKNOWN" in error for error in errors))

    def test_non_boolean_fpga_available_is_rejected(self):
        record = copy.deepcopy(hp.generate_records(round_number=1, steps=4, repeats=2)[0])
        record["oracle"]["environment"]["fpga_hardware"]["available"] = "false"
        errors = hp.validate_record(record, WHERE)
        self.assertTrue(
            any(
                "fpga_hardware.available must be a boolean" in error for error in errors
            ),
            errors,
        )

    def test_unavailable_fpga_probe_needs_a_nonblank_reason_code(self):
        record = copy.deepcopy(hp.generate_records(round_number=1, steps=4, repeats=2)[0])
        record["oracle"]["environment"]["fpga_hardware"]["reason_code"] = "   "
        errors = hp.validate_record(record, WHERE)
        self.assertTrue(
            any("must name a reason_code" in error for error in errors), errors
        )

    def test_fpga_available_true_is_not_corroborated(self):
        # No adapter code path in this repository can produce a truthful
        # `available: true` probe; a fixed-point record claiming one must
        # still be rejected even though it does not claim a live FPGA
        # deployment.
        record = copy.deepcopy(hp.generate_records(round_number=1, steps=4, repeats=2)[0])
        record["oracle"]["environment"]["fpga_hardware"] = {
            "available": True,
            "reason_code": None,
            "detail": "board online",
        }
        errors = hp.validate_record(record, WHERE)
        self.assertTrue(
            any("fpga_hardware.available is true" in error for error in errors), errors
        )

    def test_deleting_the_execution_target_is_not_a_way_out(self):
        # Removing an inconvenient label must not be quieter than declaring it.
        record = copy.deepcopy(hp.generate_records(round_number=1, steps=4, repeats=2)[0])
        del record["oracle"]["deployment"]["execution_target"]
        errors = hp.validate_record(record, WHERE)
        self.assertTrue(any("HW_TARGET_UNKNOWN" in error for error in errors))

    def test_reference_model_target_needs_no_board_metadata(self):
        records = hp.generate_records(round_number=1, steps=4, repeats=2)
        self.assertEqual(hp.validate_records(records), [])

    def test_reference_model_cannot_claim_measured_latency(self):
        record = copy.deepcopy(hp.generate_records(round_number=1, steps=4, repeats=2)[0])
        record["oracle"]["deployment"]["latency"] = {
            "measured": True,
            "value_ms": 0.001,
        }
        parity, verdict, codes = hp.compute_parity(
            record["scenario"],
            record["oracle"]["software"],
            record["oracle"]["deployment"],
        )
        record["result"]["parity"] = parity
        record["result"]["verdict"] = verdict
        record["result"]["reason_codes"] = codes
        record["result"]["summary"] = hp._summarize(
            record["scenario"], parity, verdict, record["oracle"]["deployment"]
        )
        errors = hp.validate_record(record, WHERE)
        self.assertTrue(any("LATENCY_NOT_MEASURED" in error for error in errors), errors)


if __name__ == "__main__":
    unittest.main()
