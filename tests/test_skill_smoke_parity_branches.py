"""Each failure the driver's parity smoke check can report, one at a time.

``smoke_parity_families`` guards three properties that would otherwise rot
silently: unavailable oracles say why, generated records validate and contain
a disagreement, and a relabelled mismatch is refused. The driver tests cover the
clean run; these break one property per case and pin the exact report line.
"""

import importlib
import importlib.util
import unittest
from pathlib import Path
from unittest import mock

REPO = Path(__file__).resolve().parents[1]
DRIVER_PATH = REPO / ".claude" / "skills" / "run-synthetic-factory" / "driver.py"
SPEC = importlib.util.spec_from_file_location("factory_driver", DRIVER_PATH)
if SPEC is None or SPEC.loader is None:
    raise ImportError(f"cannot load the operator driver from {DRIVER_PATH}")
factory_driver = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(factory_driver)

# The driver puts the skill directory and pipelines/ on sys.path; smoke_parity
# imports the parity families by these flat names, so they are the ones patched.
smoke_parity = importlib.import_module("smoke_parity")
hardware_parity = importlib.import_module("hardware_parity")
neuro_oracle = importlib.import_module("neuro_oracle")
nir_equivalence = importlib.import_module("nir_equivalence")
parity_contract = importlib.import_module("oracle_grounded.parity_contract")


FPGA_SILENT = (
    "FPGA adapter must report unavailability with a reason code unless a board transport exists"
)
FPGA_ENVELOPE_REFUSED = (
    "generated hardware-parity records do not validate: smoke-hw:1: "
    "unavailable fpga_hardware probe must name a reason_code [ENVELOPE_MALFORMED]"
)
NO_HARDWARE_MISMATCH = (
    "hardware-parity catalog produced no mismatch; a parity corpus in which "
    "nothing ever disagrees is not testing parity"
)
NO_NIR_DIVERGENCE = (
    "NIR catalog produced no divergence; without one the relabelling check "
    "below silently tests nothing"
)


def _without_mismatches(generate):
    """Wrap a generator so its catalog never disagrees."""

    def generate_matches(**kwargs):
        return [
            record
            for record in generate(**kwargs)
            if record["result"]["verdict"] != parity_contract.VERDICT_MISMATCH
        ]

    return generate_matches


def _silent_availability(module, key):
    """An availability report whose ``key`` entry is unavailable with no reason code."""

    report = module.availability_report()
    report[key] = {**report[key], "available": False, "reason_code": None}
    return mock.Mock(return_value=report)


class SmokeParityFailureReports(unittest.TestCase):
    def test_a_silent_fpga_adapter_is_reported_and_its_records_are_refused(self):
        silent = _silent_availability(neuro_oracle, "spikenaut_fpga")
        with mock.patch.object(neuro_oracle, "availability_report", silent):
            failures = smoke_parity.smoke_parity_families()

        # The generated hardware envelopes carry the same report, so the family
        # validator refuses them as well.
        self.assertEqual(failures, [FPGA_SILENT, FPGA_ENVELOPE_REFUSED])

    def test_each_other_broken_property_is_reported_with_its_exact_line(self):
        cases = (
            (
                "nir_rs unavailable without a reason",
                nir_equivalence, "availability_report",
                _silent_availability(nir_equivalence, "nir_rs"),
                "nir_rs must report unavailability with a reason code",
            ),
            (
                "hardware records do not validate",
                hardware_parity, "validate_records",
                mock.Mock(return_value=["HW_FIRST: forged", "HW_SECOND: forged"]),
                "generated hardware-parity records do not validate: HW_FIRST: forged",
            ),
            (
                "nir records do not validate",
                nir_equivalence, "validate_records",
                mock.Mock(return_value=["NIR_FIRST: forged"]),
                "generated NIR records do not validate: NIR_FIRST: forged",
            ),
            (
                "hardware catalog never disagrees",
                hardware_parity, "generate_records",
                _without_mismatches(hardware_parity.generate_records), NO_HARDWARE_MISMATCH,
            ),
            (
                "nir catalog never diverges",
                nir_equivalence, "generate_records",
                _without_mismatches(nir_equivalence.generate_records), NO_NIR_DIVERGENCE,
            ),
            (
                "hardware relabel accepted",
                hardware_parity, "validate_record", mock.Mock(return_value=[]),
                "a relabelled mismatch was not caught with PARITY_VERDICT_INCONSISTENT",
            ),
            (
                "nir relabel accepted",
                nir_equivalence, "validate_record", mock.Mock(return_value=[]),
                "a relabelled mismatch was not caught with DIVERGENCE_SUPPRESSED",
            ),
        )
        for label, module, name, replacement, expected in cases:
            with self.subTest(label), mock.patch.object(module, name, replacement):
                self.assertEqual(smoke_parity.smoke_parity_families(), [expected])


if __name__ == "__main__":
    unittest.main()
