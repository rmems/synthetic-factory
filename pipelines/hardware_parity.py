#!/usr/bin/env python3
"""`hardware-parity-spike-trajectories` generator, oracle driver, and validator.

The question this family answers is behavioural, not procedural:

    does a known software Spikenaut execution still do the same thing after
    Q8.8 export and execution on the deployment target?

A successful export, a successful build, and a successful board load are not
evidence of that. Only paired spike trains are.

What actually runs here
-----------------------
The software side is the float64 LIF reference in ``neuro_oracle``. The
deployment side is whichever adapter the caller names. In this repository the
only deployment-side adapter that can execute is the **Q8.8 fixed-point
reference model** -- a model of an FPGA datapath, not an FPGA. Records emitted
against it say ``fixed_point_reference_model`` and their reason codes say
``ORACLE_UNAVAILABLE`` for the hardware leg. The validator refuses to accept a
record claiming ``fpga_hardware`` or ``recorded_capture`` unless it carries
board revision, bitstream hash, capture manifest digest, and a measured
latency -- values only a real run can produce.

Every number in ``result.parity`` is recomputed from the recorded spike and
membrane traces during validation, so a record cannot assert an agreement its
own traces do not support.

Usage:
  python3 pipelines/hardware_parity.py availability
  python3 pipelines/hardware_parity.py generate <out_dir> [--round N] [--steps N]
                                       [--repeats N] [--target NAME] [--capture PATH]
  python3 pipelines/hardware_parity.py validate <path>
  python3 pipelines/hardware_parity.py training-view <path>
"""

from __future__ import annotations

import sys

if __package__:
    # Import-twin helpers join the package import lock; import-order tests cover this edge.
    from . import _assert_direct_sibling, _expose_package_sibling  # pylint: disable=cyclic-import

    _assert_direct_sibling("hardware_parity")
    from .hardware_parity_terms import (  # noqa: E402,F401  # pylint: disable=unused-import
        CATALOG_AUTHORSHIP,
        FACTORY_SLUG,
        GENERATOR_BLOCK,
        MEMBRANE_TOLERANCE,
        METRIC_TOL,
        ORACLE_PAIRING,
        RECORD_KIND,
        REQUIRED_HARDWARE_FIELDS,
        SCHEMA_VERSION,
        VALIDATION_DATA_ERRORS,
        VALIDATOR,
        contract,
    )
    from .hardware_parity_catalog import (  # noqa: E402,F401
        SCENARIO_SPECS,
        build_scenario,
        build_scenarios,
    )
    from .hardware_parity_metrics import (  # noqa: E402,F401
        MEMBRANE_UNITS,
        compute_parity,
        membrane_metrics,
        quantization_metrics,
        repeatability_metrics,
        spike_bitmap_metrics,
        timing_metrics,
    )
    from .hardware_parity_provenance import (  # noqa: E402,F401  # pylint: disable=unused-import
        _FAMILY,
        _catalog_digest,
        _catalog_provenance_stamps,
        _family_sources,
        _module_source_digest,
    )
    from .hardware_parity_record import (  # noqa: E402,F401  # pylint: disable=unused-import
        _capture_evidence_digest,
        _expected_summary,
        _summarize,
        _unavailable_evidence_digest,
        build_record,
        generate_records,
        run_pair,
    )
    from .hardware_parity_validate_result import (  # noqa: E402,F401
        validate_record,
        validate_records,
    )
    from .hardware_parity_views import (  # noqa: E402,F401
        build_training_views,
        training_view,
        training_view_errors,
    )
    from .hardware_parity_cli import (  # noqa: E402,F401  # pylint: disable=unused-import
        availability_report,
        main,
        parse_args,
        read_jsonl,
        write_jsonl,
    )
else:
    getattr(sys.modules.get("pipelines"), "_join_package_sibling", lambda name: None)(
        "hardware_parity"
    )
    from hardware_parity_terms import (  # noqa: E402,F401
        CATALOG_AUTHORSHIP,
        FACTORY_SLUG,
        GENERATOR_BLOCK,
        MEMBRANE_TOLERANCE,
        METRIC_TOL,
        ORACLE_PAIRING,
        RECORD_KIND,
        REQUIRED_HARDWARE_FIELDS,
        SCHEMA_VERSION,
        VALIDATION_DATA_ERRORS,
        VALIDATOR,
        contract,
    )
    from hardware_parity_catalog import (  # noqa: E402,F401
        SCENARIO_SPECS,
        build_scenario,
        build_scenarios,
    )
    from hardware_parity_metrics import (  # noqa: E402,F401
        MEMBRANE_UNITS,
        compute_parity,
        membrane_metrics,
        quantization_metrics,
        repeatability_metrics,
        spike_bitmap_metrics,
        timing_metrics,
    )
    from hardware_parity_provenance import (  # noqa: E402,F401
        _FAMILY,
        _catalog_digest,
        _catalog_provenance_stamps,
        _family_sources,
        _module_source_digest,
    )
    from hardware_parity_record import (  # noqa: E402,F401
        _capture_evidence_digest,
        _expected_summary,
        _summarize,
        _unavailable_evidence_digest,
        build_record,
        generate_records,
        run_pair,
    )
    from hardware_parity_validate_result import (  # noqa: E402,F401
        validate_record,
        validate_records,
    )
    from hardware_parity_views import (  # noqa: E402,F401
        build_training_views,
        training_view,
        training_view_errors,
    )
    from hardware_parity_cli import (  # noqa: E402,F401
        availability_report,
        main,
        parse_args,
        read_jsonl,
        write_jsonl,
    )

__all__ = [
    "FACTORY_SLUG",
    "availability_report",
    "MEMBRANE_UNITS",
    "RECORD_KIND",
    "REQUIRED_HARDWARE_FIELDS",
    "SCENARIO_SPECS",
    "SCHEMA_VERSION",
    "VALIDATOR",
    "build_record",
    "build_scenario",
    "build_scenarios",
    "build_training_views",
    "compute_parity",
    "generate_records",
    "main",
    "membrane_metrics",
    "quantization_metrics",
    "read_jsonl",
    "repeatability_metrics",
    "run_pair",
    "spike_bitmap_metrics",
    "timing_metrics",
    "training_view",
    "training_view_errors",
    "validate_record",
    "validate_records",
    "write_jsonl",
]

if __package__:
    _expose_package_sibling(__name__)


if __name__ == "__main__":
    sys.exit(main())
