#!/usr/bin/env python3
"""The two in-repo adapters: float64 software and the Q8.8 deployment model.

The Q8.8 side is a model of an FPGA datapath, not an FPGA, and the records it
produces say so.
"""

from __future__ import annotations

from pathlib import Path
import sys

_PIPELINES = Path(__file__).resolve().parent

if __package__:
    # Import-twin helpers join the package import lock; import-order tests cover this edge.
    from . import _assert_direct_sibling, _expose_package_sibling  # pylint: disable=cyclic-import

    _assert_direct_sibling("neuro_oracle_reference")
    from .neuro_oracle_adapter import (  # noqa: E402
        OracleAdapter,
        TARGET_FIXED_POINT_MODEL,
        TARGET_SOFTWARE_FLOAT,
    )
    from .neuro_oracle_quantize import quantize_model  # noqa: E402
    from .neuro_oracle_simulate import (  # noqa: E402
        simulate_fixed_point,
        simulate_float,
    )
else:
    getattr(sys.modules.get("pipelines"), "_join_package_sibling", lambda name: None)(
        "neuro_oracle_reference"
    )
    if str(_PIPELINES) not in sys.path:
        sys.path.insert(0, str(_PIPELINES))
    from neuro_oracle_adapter import (  # noqa: E402
        OracleAdapter,
        TARGET_FIXED_POINT_MODEL,
        TARGET_SOFTWARE_FLOAT,
    )
    from neuro_oracle_quantize import quantize_model  # noqa: E402
    from neuro_oracle_simulate import (  # noqa: E402
        simulate_fixed_point,
        simulate_float,
    )

class SoftwareFloatAdapter(OracleAdapter):
    """The software side of the parity pair."""

    name = "spikenaut_software_float"
    execution_target = TARGET_SOFTWARE_FLOAT
    runtime_class = "in_repo_reference"

    def availability(self):
        return {"available": True, "reason_code": None, "detail": "stdlib float64 simulator"}

    def run(self, model, stimulus, repeats=1):
        outcome = simulate_float(model, stimulus)
        latency = {
            "measured": False,
            "value_ms": None,
            "reason_code": "LATENCY_NOT_MEASURED_SOFTWARE",
            "detail": "wall-clock time of a Python simulator is not a hardware latency",
            "modeled_steps": len(outcome["spikes"]),
        }
        return self._envelope(outcome, repeats, latency)


class FixedPointReferenceAdapter(OracleAdapter):
    """Q8.8 model of an FPGA datapath. Explicitly *not* an FPGA."""

    name = "spikenaut_q88_reference_model"
    execution_target = TARGET_FIXED_POINT_MODEL
    runtime_class = "in_repo_reference"

    def availability(self):
        return {
            "available": True,
            "reason_code": None,
            "detail": "stdlib Q8.8 integer datapath model; no hardware involved",
        }

    def run(self, model, stimulus, repeats=1):
        q_model, provenance = quantize_model(model)
        outcome = simulate_fixed_point(q_model, stimulus)
        latency = {
            "measured": False,
            "value_ms": None,
            "reason_code": "LATENCY_NOT_MEASURED_REFERENCE_MODEL",
            "detail": "a datapath model has no physical latency to report",
            "modeled_steps": len(outcome["spikes"]),
        }
        return self._envelope(
            outcome, repeats, latency, {"quantization": provenance, "q_model": q_model}
        )


if __package__:
    _expose_package_sibling(__name__)
