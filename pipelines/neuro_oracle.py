#!/usr/bin/env python3
"""Deterministic neuromorphic oracle boundary for the parity dataset families.

This module owns the *oracle interface* used by the hardware-parity and
NIR-equivalence families. It deliberately separates three things that are easy
to conflate:

1. A **software float reference simulator** (float64 LIF) — available here.
2. A **Q8.8 fixed-point reference model** of the same datapath — available
   here. It is a *model of* an FPGA datapath, not an FPGA.
3. A **real FPGA execution target** — an adapter that probes for a board and
   reports unavailability with a reason code when there is none. It never
   fabricates spikes, latency, or board metadata.

The distinction is load-bearing: a record produced against the fixed-point
reference model must say ``fixed_point_reference_model``, and the validators in
``hardware_parity`` refuse ``fpga_hardware`` provenance without the board,
bitstream, and capture metadata that only a real run can supply.

Stdlib only. Every simulator here is bit-deterministic for a given model and
stimulus: no RNG is consulted during execution, and repeat runs exist to
measure *hardware* variability, not to add noise.
"""

from __future__ import annotations

import sys

if __package__:
    # Import-twin helpers join the package import lock; import-order tests cover this edge.
    from . import _assert_direct_sibling, _expose_package_sibling  # pylint: disable=cyclic-import

    _assert_direct_sibling("neuro_oracle")
    from .neuro_oracle_digest import (  # noqa: E402,F401
        canonical_json,
        digest,
    )
    from .neuro_oracle_q88 import (  # noqa: E402,F401
        Q88_FRACTIONAL_BITS,
        Q88_MAX_RAW,
        Q88_MAX_VALUE,
        Q88_MIN_RAW,
        Q88_MIN_VALUE,
        Q88_ROUNDING,
        Q88_SATURATION_POLICY,
        Q88_SCALE,
        Q88_STEP,
        q88_mul,
        q88_quantize,
        q88_saturate,
        q88_to_float,
    )
    from .neuro_oracle_model import (  # noqa: E402,F401
        DEFAULT_ACTION_LABELS,
        RESET_MODES,
        normalize_model,
        normalize_stimulus,
        stimulus_fixture,
    )
    from .neuro_oracle_quantize import (  # noqa: E402,F401
        quantize_model,
    )
    from .neuro_oracle_observation import (  # noqa: E402,F401  # pylint: disable=unused-import
        _decode_action,
        _spike_events,
    )
    from .neuro_oracle_simulate import (  # noqa: E402,F401
        simulate_fixed_point,
        simulate_float,
    )
    from .neuro_oracle_adapter import (  # noqa: E402,F401
        CAPTURE_DETERMINISM_MEANING,
        EXECUTION_TARGETS,
        OracleAdapter,
        OracleUnavailable,
        PHYSICAL_TARGETS,
        REFERENCE_DETERMINISM_MEANING,
        SCHEMA_VERSION,
        TARGET_FIXED_POINT_MODEL,
        TARGET_FPGA_HARDWARE,
        TARGET_RECORDED_CAPTURE,
        TARGET_SOFTWARE_FLOAT,
        run_digest,
    )
    from .neuro_oracle_reference import (  # noqa: E402,F401
        FixedPointReferenceAdapter,
        SoftwareFloatAdapter,
    )
    from .neuro_oracle_capture import (  # noqa: E402,F401
        MAX_CAPTURE_BYTES,
        RecordedCaptureAdapter,
    )
    from .neuro_oracle_availability import (  # noqa: E402,F401
        ADAPTERS,
        FPGA_BITSTREAM_ENV,
        FPGA_BITSTREAM_TOOLCHAIN_ENV,
        FPGA_BOARD_REVISION_ENV,
        FPGA_BOARD_SERIAL_ENV,
        FPGA_DEVICE_ENV,
        FPGA_TRANSPORT_ENV,
        FPGA_TRANSPORT_EXECUTABLE,
        FpgaHardwareAdapter,
        availability_report,
        get_adapter,
        main,
    )
else:
    getattr(sys.modules.get("pipelines"), "_join_package_sibling", lambda name: None)(
        "neuro_oracle"
    )
    from neuro_oracle_digest import (  # noqa: E402,F401
        canonical_json,
        digest,
    )
    from neuro_oracle_q88 import (  # noqa: E402,F401
        Q88_FRACTIONAL_BITS,
        Q88_MAX_RAW,
        Q88_MAX_VALUE,
        Q88_MIN_RAW,
        Q88_MIN_VALUE,
        Q88_ROUNDING,
        Q88_SATURATION_POLICY,
        Q88_SCALE,
        Q88_STEP,
        q88_mul,
        q88_quantize,
        q88_saturate,
        q88_to_float,
    )
    from neuro_oracle_model import (  # noqa: E402,F401
        DEFAULT_ACTION_LABELS,
        RESET_MODES,
        normalize_model,
        normalize_stimulus,
        stimulus_fixture,
    )
    from neuro_oracle_quantize import (  # noqa: E402,F401
        quantize_model,
    )
    from neuro_oracle_observation import (  # noqa: E402,F401
        _decode_action,
        _spike_events,
    )
    from neuro_oracle_simulate import (  # noqa: E402,F401
        simulate_fixed_point,
        simulate_float,
    )
    from neuro_oracle_adapter import (  # noqa: E402,F401
        CAPTURE_DETERMINISM_MEANING,
        EXECUTION_TARGETS,
        OracleAdapter,
        OracleUnavailable,
        PHYSICAL_TARGETS,
        REFERENCE_DETERMINISM_MEANING,
        SCHEMA_VERSION,
        TARGET_FIXED_POINT_MODEL,
        TARGET_FPGA_HARDWARE,
        TARGET_RECORDED_CAPTURE,
        TARGET_SOFTWARE_FLOAT,
        run_digest,
    )
    from neuro_oracle_reference import (  # noqa: E402,F401
        FixedPointReferenceAdapter,
        SoftwareFloatAdapter,
    )
    from neuro_oracle_capture import (  # noqa: E402,F401
        MAX_CAPTURE_BYTES,
        RecordedCaptureAdapter,
    )
    from neuro_oracle_availability import (  # noqa: E402,F401
        ADAPTERS,
        FPGA_BITSTREAM_ENV,
        FPGA_BITSTREAM_TOOLCHAIN_ENV,
        FPGA_BOARD_REVISION_ENV,
        FPGA_BOARD_SERIAL_ENV,
        FPGA_DEVICE_ENV,
        FPGA_TRANSPORT_ENV,
        FPGA_TRANSPORT_EXECUTABLE,
        FpgaHardwareAdapter,
        availability_report,
        get_adapter,
        main,
    )

__all__ = [
    "ADAPTERS",
    "CAPTURE_DETERMINISM_MEANING",
    "DEFAULT_ACTION_LABELS",
    "EXECUTION_TARGETS",
    "FPGA_BITSTREAM_ENV",
    "FPGA_BITSTREAM_TOOLCHAIN_ENV",
    "FPGA_BOARD_REVISION_ENV",
    "FPGA_BOARD_SERIAL_ENV",
    "FPGA_DEVICE_ENV",
    "FPGA_TRANSPORT_ENV",
    "FPGA_TRANSPORT_EXECUTABLE",
    "FixedPointReferenceAdapter",
    "FpgaHardwareAdapter",
    "MAX_CAPTURE_BYTES",
    "OracleAdapter",
    "OracleUnavailable",
    "PHYSICAL_TARGETS",
    "Q88_FRACTIONAL_BITS",
    "Q88_MAX_RAW",
    "Q88_MAX_VALUE",
    "Q88_MIN_RAW",
    "Q88_MIN_VALUE",
    "Q88_ROUNDING",
    "Q88_SATURATION_POLICY",
    "Q88_SCALE",
    "Q88_STEP",
    "REFERENCE_DETERMINISM_MEANING",
    "RESET_MODES",
    "RecordedCaptureAdapter",
    "SCHEMA_VERSION",
    "SoftwareFloatAdapter",
    "TARGET_FIXED_POINT_MODEL",
    "TARGET_FPGA_HARDWARE",
    "TARGET_RECORDED_CAPTURE",
    "TARGET_SOFTWARE_FLOAT",
    "availability_report",
    "canonical_json",
    "digest",
    "get_adapter",
    "main",
    "normalize_model",
    "normalize_stimulus",
    "q88_mul",
    "q88_quantize",
    "q88_saturate",
    "q88_to_float",
    "quantize_model",
    "run_digest",
    "simulate_fixed_point",
    "simulate_float",
    "stimulus_fixture",
]

if __package__:
    _expose_package_sibling(__name__)


if __name__ == "__main__":
    sys.exit(main())
