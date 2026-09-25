#!/usr/bin/env python3
"""What every oracle adapter is: its identity, its targets, and its refusal.

`OracleUnavailable` carries a reason code rather than being a bare failure,
because "this oracle did not run" is evidence a record has to state.
"""

from __future__ import annotations

import sys

if __package__:
    # Import-twin helpers join the package import lock; import-order tests cover this edge.
    from . import _assert_direct_sibling, _expose_package_sibling  # pylint: disable=cyclic-import

    _assert_direct_sibling("neuro_oracle_adapter")
    from .neuro_oracle_digest import digest  # noqa: E402
else:
    getattr(sys.modules.get("pipelines"), "_join_package_sibling", lambda name: None)(
        "neuro_oracle_adapter"
    )
    from neuro_oracle_digest import digest  # noqa: E402

SCHEMA_VERSION = "1.0.0"


REFERENCE_DETERMINISM_MEANING = (
    "bit-determinism of this reference implementation; it is not "
    "evidence about run-to-run variability of physical hardware"
)

# Repeated values in an untrusted capture prove only their internal variation.
# No current capture adapter authenticates a physical execution receipt.
CAPTURE_DETERMINISM_MEANING = (
    "variability of retained capture traces; physical execution is unverified"
)


TARGET_SOFTWARE_FLOAT = "software_float"
TARGET_FIXED_POINT_MODEL = "fixed_point_reference_model"
TARGET_RECORDED_CAPTURE = "recorded_capture"
TARGET_FPGA_HARDWARE = "fpga_hardware"
EXECUTION_TARGETS = (
    TARGET_SOFTWARE_FLOAT,
    TARGET_FIXED_POINT_MODEL,
    TARGET_RECORDED_CAPTURE,
    TARGET_FPGA_HARDWARE,
)
# Target labels asserting physical silicon or a recording of it. Their
# board/bitstream metadata is checked, but the labels do not prove execution.
PHYSICAL_TARGETS = frozenset({TARGET_FPGA_HARDWARE, TARGET_RECORDED_CAPTURE})


class OracleUnavailable(Exception):
    """Raised when an oracle cannot execute. Carries a machine reason code."""

    def __init__(self, reason_code, detail):
        super().__init__(f"{reason_code}: {detail}")
        self.reason_code = reason_code
        self.detail = detail


def run_digest(outcome):
    """Fingerprint the complete retained behavioural observation."""
    return digest(
        {
            key: outcome[key]
            for key in ("spikes", "spike_events", "membrane", "action", "arithmetic")
        }
    )


class OracleAdapter:
    """Interface every parity oracle implements.

    ``availability()`` must be answerable without executing anything, and an
    adapter that reports ``available: False`` must raise
    :class:`OracleUnavailable` from ``run`` rather than returning a plausible
    substitute. That is the whole point of the boundary.
    """

    name = "abstract"
    execution_target = None
    runtime_class = "abstract"

    def availability(self):
        raise NotImplementedError

    def run(self, model, stimulus, repeats=1):
        raise NotImplementedError

    def _envelope(self, outcome, repeats, latency, extra=None):
        fingerprint = run_digest(outcome)
        payload = {
            "adapter": self.name,
            "execution_target": self.execution_target,
            "runtime_class": self.runtime_class,
            "repeats": repeats,
            "repeat_digests": [fingerprint] * repeats,
            "determinism": {
                "identical_repeats": True,
                "distinct_digests": 1,
                "meaning": REFERENCE_DETERMINISM_MEANING,
            },
            "latency": latency,
            "output_digest": fingerprint,
        }
        payload.update(outcome)
        if extra:
            payload.update(extra)
        return payload


if __package__:
    _expose_package_sibling(__name__)
