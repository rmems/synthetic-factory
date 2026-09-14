#!/usr/bin/env python3
"""What the deployment leg is allowed to claim, and the probe that checks it.

Unavailability is re-probed rather than taken from the record, and a physical
claim must carry board revision, bitstream hash, capture manifest digest and a
measured latency -- values only a real run produces.
"""

from __future__ import annotations

import math
import sys

if __package__:
    # Import-twin helpers join the package import lock; import-order tests cover this edge.
    from . import _assert_direct_sibling, _expose_package_sibling  # pylint: disable=cyclic-import

    _assert_direct_sibling("hardware_parity_validate_deployment")
    from .hardware_parity_validate_availability import (  # noqa: E402,F401
        _check_fpga_environment,
        _check_unavailable_deployment,
        _replayed_adapter_probe,
        availability_report,
    )
    from .neuro_oracle import (  # noqa: E402
        FpgaHardwareAdapter,
        PHYSICAL_TARGETS,
        RecordedCaptureAdapter,
        TARGET_FIXED_POINT_MODEL,
        TARGET_FPGA_HARDWARE,
    )
    from .hardware_parity_terms import (  # noqa: E402
        REQUIRED_HARDWARE_FIELDS,
    )
    from .hardware_parity_validate_capture import _check_capture_chain  # noqa: E402
    from .hardware_parity_validate_observation import _physical_observation_errors  # noqa: E402
else:
    getattr(sys.modules.get("pipelines"), "_join_package_sibling", lambda name: None)(
        "hardware_parity_validate_deployment"
    )
    from hardware_parity_validate_availability import (  # noqa: E402,F401
        _check_fpga_environment,
        _check_unavailable_deployment,
        _replayed_adapter_probe,
        availability_report,
    )
    from neuro_oracle import (  # noqa: E402
        FpgaHardwareAdapter,
        PHYSICAL_TARGETS,
        RecordedCaptureAdapter,
        TARGET_FIXED_POINT_MODEL,
        TARGET_FPGA_HARDWARE,
    )
    from hardware_parity_terms import (  # noqa: E402
        REQUIRED_HARDWARE_FIELDS,
    )
    from hardware_parity_validate_capture import _check_capture_chain  # noqa: E402
    from hardware_parity_validate_observation import _physical_observation_errors  # noqa: E402

def _is_canonical_sha256(value):
    """True only for the canonical lowercase ``sha256:<64hex>`` spelling."""
    return (
        isinstance(value, str)
        and len(value) == 71
        and value.startswith("sha256:")
        and all(character in "0123456789abcdef" for character in value[7:])
    )


def _reference_latency_claim_errors(deployment, target, where):
    """A non-physical target must not report measured hardware latency."""
    latency = deployment.get("latency")
    if target == TARGET_FIXED_POINT_MODEL and (
        not isinstance(latency, dict)
        or latency.get("measured") is not False
        or latency.get("value_ms") is not None
        or latency.get("reason_code") != "LATENCY_NOT_MEASURED_REFERENCE_MODEL"
    ):
        return [
            f"{where}: the fixed-point reference model cannot report measured "
            "hardware latency [LATENCY_NOT_MEASURED]"
        ]
    return []


def _physical_adapter_identity_errors(deployment, target, where):
    """Only the adapters that can substantiate the target may be named."""
    adapter_identity = (
        deployment.get("adapter"),
        deployment.get("runtime_class"),
    )
    allowed_identities = {
        (RecordedCaptureAdapter.name, RecordedCaptureAdapter.runtime_class)
    }
    if target == TARGET_FPGA_HARDWARE:
        allowed_identities.add(
            (FpgaHardwareAdapter.name, FpgaHardwareAdapter.runtime_class)
        )
    if adapter_identity not in allowed_identities:
        return [
            f"{where}: retained physical evidence uses unsupported adapter identity "
            f"{adapter_identity!r}; allowed for target {target!r}: "
            f"{sorted(allowed_identities)!r} "
            "[HW_PROVENANCE_MISSING]"
        ]
    return []


def _physical_provenance_field_errors(deployment, target, where):
    """Board, bitstream, latency, and repeat-count evidence for the claim."""
    errors = []
    for section, key in REQUIRED_HARDWARE_FIELDS:
        block = deployment.get(section)
        value = block.get(key) if isinstance(block, dict) else None
        if not isinstance(value, str) or not value.strip():
            errors.append(
                f"{where}: {target} claim needs oracle.deployment.{section}.{key} "
                "[HW_PROVENANCE_MISSING]"
            )
    bitstream = deployment.get("bitstream")
    bitstream_sha256 = bitstream.get("sha256") if isinstance(bitstream, dict) else None
    if bitstream_sha256 and not _is_canonical_sha256(bitstream_sha256):
        errors.append(
            f"{where}: {target} claim needs canonical lowercase "
            "oracle.deployment.bitstream.sha256 in sha256:<64hex> form "
            "[HW_PROVENANCE_MISSING]"
        )
    latency = deployment.get("latency") or {}
    value_ms = latency.get("value_ms")
    if (
        latency.get("measured") is not True
        or not isinstance(value_ms, (int, float))
        or isinstance(value_ms, bool)
        or not math.isfinite(value_ms)
        or value_ms < 0
    ):
        errors.append(
            f"{where}: {target} claim needs a measured latency in ms "
            "[HW_PROVENANCE_MISSING]"
        )
    repeats = deployment.get("repeats")
    if not isinstance(repeats, int) or isinstance(repeats, bool) or repeats < 2:
        errors.append(
            f"{where}: {target} claim needs at least 2 repeated runs to say anything "
            "about determinism [REPEATABILITY_UNPROVEN]"
        )
    return errors


def _check_physical_claim(record, where):
    """A physical-target record needs board, bitstream, and capture metadata."""
    deployment = (record.get("oracle") or {}).get("deployment")
    if not isinstance(deployment, dict):
        return []
    target = deployment.get("execution_target")
    # A missing target is treated as unknown rather than waved through: it is
    # exactly what deleting an inconvenient label would look like.
    if target not in (TARGET_FIXED_POINT_MODEL, *PHYSICAL_TARGETS):
        return [
            f"{where}: unknown deployment execution_target {target!r} [HW_TARGET_UNKNOWN]"
        ]
    if target not in PHYSICAL_TARGETS:
        return _reference_latency_claim_errors(deployment, target, where)
    errors = _physical_adapter_identity_errors(deployment, target, where)
    errors += _physical_provenance_field_errors(deployment, target, where)
    # A run on physical silicon is hardware-in-the-loop by definition. A record
    # that claims a board while still declaring itself `simulated` is not
    # describing one execution consistently, and the mismatch is exactly what a
    # relabelled reference-model run looks like.
    kind = (record.get("provenance") or {}).get("kind")
    if kind != "hil":
        errors.append(
            f"{where}: a {target} claim requires provenance.kind 'hil', got {kind!r} "
            "[HW_PROVENANCE_MISSING]"
        )
    errors += _physical_observation_errors(
        deployment, record.get("scenario"), "oracle.deployment", where
    )
    errors += _check_capture_chain(record, deployment, where)
    return errors


if __package__:
    _expose_package_sibling(__name__)
