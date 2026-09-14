#!/usr/bin/env python3
"""Which oracles can run here, and why the others cannot.

The FPGA adapter reports unavailability with a reason code and raises rather
than substituting a simulator, so an absent board can never read as a quiet
pass.
"""

from __future__ import annotations

from pathlib import Path
import json
import os
import sys

if __package__:
    # Import-twin helpers join the package import lock; import-order tests cover this edge.
    from . import _assert_direct_sibling, _expose_package_sibling  # pylint: disable=cyclic-import

    _assert_direct_sibling("neuro_oracle_availability")
    from .neuro_oracle_adapter import (  # noqa: E402
        OracleAdapter,
        OracleUnavailable,
        TARGET_FPGA_HARDWARE,
    )
    from .neuro_oracle_capture import RecordedCaptureAdapter  # noqa: E402
    from .neuro_oracle_reference import (  # noqa: E402
        FixedPointReferenceAdapter,
        SoftwareFloatAdapter,
    )
else:
    getattr(sys.modules.get("pipelines"), "_join_package_sibling", lambda name: None)(
        "neuro_oracle_availability"
    )
    from neuro_oracle_adapter import (  # noqa: E402
        OracleAdapter,
        OracleUnavailable,
        TARGET_FPGA_HARDWARE,
    )
    from neuro_oracle_capture import RecordedCaptureAdapter  # noqa: E402
    from neuro_oracle_reference import (  # noqa: E402
        FixedPointReferenceAdapter,
        SoftwareFloatAdapter,
    )

FPGA_DEVICE_ENV = "SPIKENAUT_FPGA_DEVICE"
FPGA_BITSTREAM_ENV = "SPIKENAUT_FPGA_BITSTREAM"


class FpgaHardwareAdapter(OracleAdapter):
    """Real FPGA execution target.

    This adapter has no fallback. If no board is declared and reachable it
    reports unavailability with a reason code and ``run`` raises. There is no
    code path in this module by which an ``fpga_hardware`` result can be
    produced without a board.
    """

    name = "spikenaut_fpga"
    execution_target = TARGET_FPGA_HARDWARE
    runtime_class = "physical_hardware"

    def __init__(self, env=None):
        self.env = os.environ if env is None else env

    def availability(self):
        device = self.env.get(FPGA_DEVICE_ENV)
        if not device:
            return {
                "available": False,
                "reason_code": "FPGA_DEVICE_NOT_DECLARED",
                "detail": (
                    f"{FPGA_DEVICE_ENV} is unset; no board is claimed and none is assumed"
                ),
            }
        if not Path(device).exists():
            return {
                "available": False,
                "reason_code": "FPGA_DEVICE_ABSENT",
                "detail": f"declared device {device} does not exist",
            }
        if not self.env.get(FPGA_BITSTREAM_ENV):
            return {
                "available": False,
                "reason_code": "FPGA_BITSTREAM_NOT_DECLARED",
                "detail": (
                    f"{FPGA_BITSTREAM_ENV} is unset; a parity run without a pinned "
                    "bitstream hash is not attributable"
                ),
            }
        return {
            "available": False,
            "reason_code": "FPGA_DRIVER_NOT_IMPLEMENTED",
            "detail": (
                "device and bitstream are declared but this repository ships no board "
                "transport; implement one before claiming fpga_hardware"
            ),
        }

    def run(self, model, stimulus, repeats=1):
        status = self.availability()
        raise OracleUnavailable(status["reason_code"], status["detail"])


ADAPTERS = {
    SoftwareFloatAdapter.name: SoftwareFloatAdapter,
    FixedPointReferenceAdapter.name: FixedPointReferenceAdapter,
    FpgaHardwareAdapter.name: FpgaHardwareAdapter,
}


def get_adapter(name, **kwargs):
    """Construct an adapter by name. Captures are addressed by path."""
    if name == RecordedCaptureAdapter.name:
        return RecordedCaptureAdapter(**kwargs)
    if name not in ADAPTERS:
        raise KeyError(f"unknown oracle adapter {name!r}")
    return ADAPTERS[name](**kwargs)


def availability_report(env=None):
    """What can actually run here, and the reason code for what cannot."""
    report = {}
    for name, factory in ADAPTERS.items():
        adapter = factory(env=env) if factory is FpgaHardwareAdapter else factory()
        status = dict(adapter.availability())
        status["execution_target"] = adapter.execution_target
        status["runtime_class"] = adapter.runtime_class
        report[name] = status
    return report


def main():
    """``python3 pipelines/neuro_oracle.py`` prints the availability report."""
    print(json.dumps(availability_report(), indent=2, sort_keys=True))
    return 0


if __package__:
    _expose_package_sibling(__name__)
