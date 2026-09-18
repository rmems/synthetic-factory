#!/usr/bin/env python3
"""Is the deployment oracle actually available, and does the record agree?

Live adapter availability is re-probed. Historical recorded-capture absence
remains an inconclusive claim; its record-controlled path is never opened.
"""

from __future__ import annotations

import copy
import sys

if __package__:
    # Import-twin helpers join the package import lock; import-order tests cover this edge.
    from . import _assert_direct_sibling, _expose_package_sibling  # pylint: disable=cyclic-import

    _assert_direct_sibling("hardware_parity_validate_availability")
    from . import neuro_oracle  # noqa: E402
    from .neuro_oracle import (  # noqa: E402
        FpgaHardwareAdapter,
        RecordedCaptureAdapter,
    )
    from .hardware_parity_terms import (  # noqa: E402
        contract,
    )
else:
    getattr(sys.modules.get("pipelines"), "_join_package_sibling", lambda name: None)(
        "hardware_parity_validate_availability"
    )
    import neuro_oracle  # noqa: E402
    from neuro_oracle import (  # noqa: E402
        FpgaHardwareAdapter,
        RecordedCaptureAdapter,
    )
    from hardware_parity_terms import (  # noqa: E402
        contract,
    )

def availability_report(**kwargs):
    """The oracle's availability probe, resolved through its module each call."""
    return neuro_oracle.availability_report(**kwargs)


def _check_fpga_environment(record, where):
    """Shape-check the recorded FPGA probe; re-probe only live FPGA claims.

    Q8.8 and capture records store the generating-host probe as provenance.
    Requiring that sidecar to equal the current process environment would
    reject intact evidence after ``SPIKENAUT_FPGA_*`` or the bitstream path
    changes. Live ``fpga_hardware`` execution still requires the current
    adapter to be available. Unavailable FPGA diagnostics are authenticated
    by ``_check_unavailable_deployment`` against the selected adapter.
    """
    oracle = record.get("oracle")
    environment = oracle.get("environment") if isinstance(oracle, dict) else None
    if not isinstance(environment, dict):
        return [
            f"{where}: oracle.environment must be an object "
            "[ENVELOPE_MALFORMED]"
        ]
    recorded = environment.get("fpga_hardware")
    if not isinstance(recorded, dict):
        return [
            f"{where}: oracle.environment.fpga_hardware must be an object "
            "[ENVELOPE_MALFORMED]"
        ]
    errors = []
    if not isinstance(recorded.get("available"), bool):
        errors.append(
            f"{where}: oracle.environment.fpga_hardware.available must be a boolean "
            "[ENVELOPE_MALFORMED]"
        )
    if recorded.get("available") is False:
        reason = recorded.get("reason_code")
        if not isinstance(reason, str) or not reason.strip():
            errors.append(
                f"{where}: unavailable fpga_hardware probe must name a reason_code "
                "[ENVELOPE_MALFORMED]"
            )
    current = availability_report().get("spikenaut_fpga")
    current_available = isinstance(current, dict) and current.get("available") is True
    if recorded.get("available") is True and not current_available:
        # FpgaHardwareAdapter.run() always raises regardless of what
        # availability() reports, so no adapter code path in this repository
        # can produce a truthful ``available: true`` probe today. Unlike
        # reason_code/detail (which legitimately drift with the generating
        # host's environment and are intentionally not re-checked above),
        # a bare ``true`` is never intact evidence to preserve.
        errors.append(
            f"{where}: oracle.environment.fpga_hardware.available is true but no "
            "current adapter probe corroborates it [ORACLE_UNAVAILABLE]"
        )
    deployment = oracle.get("deployment")
    if (
        isinstance(deployment, dict)
        and deployment.get("adapter") == FpgaHardwareAdapter.name
        and deployment.get("runtime_class") == FpgaHardwareAdapter.runtime_class
        and not current_available
    ):
        errors.append(
            f"{where}: a live {FpgaHardwareAdapter.name!r} deployment requires the "
            "current adapter probe to report available [ORACLE_UNAVAILABLE]"
        )
    return errors


def _replayed_adapter_probe(_record, oracle, requested, where):
    """Probe live adapters; shape-check historical capture diagnostics as data.

    Returns ``(current, fatal)``: the probe result to authenticate against,
    or a fatal error list when the diagnostic cannot be replayed at all.
    """
    adapter_name = requested.get("adapter")
    if adapter_name != RecordedCaptureAdapter.name:
        return availability_report().get(adapter_name), []
    config = requested.get("adapter_config")
    capture_path = config.get("capture_path") if isinstance(config, dict) else None
    if not isinstance(capture_path, str) or not capture_path:
        return None, [
            f"{where}: recorded_capture unavailability must retain its capture "
            "path [ORACLE_UNAVAILABLE]"
        ]
    return _historical_capture_probe(oracle, requested, where)


_CAPTURE_REASON_CODES = frozenset({
    "CAPTURE_FILE_ABSENT", "CAPTURE_UNREADABLE", "CAPTURE_TARGET_UNKNOWN",
    "CAPTURE_DIGEST_MISMATCH", "CAPTURE_INPUT_FIXTURE_MISMATCH",
    "CAPTURE_QUANTIZATION_CONFLICT", "CAPTURE_QUANTIZATION_MISSING",
})


def _historical_capture_probe(oracle, requested, where):
    """Retain an inconclusive diagnostic without dereferencing its opaque path."""
    entry = oracle["unavailable"][0]
    config = requested["adapter_config"]
    reason = entry.get("reason_code")
    detail = entry.get("detail")
    target = requested.get("execution_target")
    if not _valid_capture_diagnostic(reason, detail, target) or set(config) != {"capture_path"}:
        return None, [f"{where}: unsupported historical capture diagnostic [ORACLE_UNAVAILABLE]"]
    return {
        "available": False,
        "execution_target": target,
        "reason_code": reason,
        "detail": detail,
    }, []


def _valid_capture_diagnostic(reason, detail, target):
    if not isinstance(reason, str) or reason not in _CAPTURE_REASON_CODES:
        return False
    if not isinstance(detail, str) or not detail.strip():
        return False
    if target is None:
        return True
    return isinstance(target, str) and target in neuro_oracle.EXECUTION_TARGETS


def _check_unavailable_deployment(record, where):
    """Authenticate the diagnostic used in place of a deployment run."""
    oracle = record.get("oracle") or {}
    unavailable = oracle.get("unavailable")
    if not isinstance(unavailable, list) or len(unavailable) != 1:
        return [
            f"{where}: oracle.unavailable must contain exactly one deployment "
            "diagnostic [ORACLE_UNAVAILABLE]"
        ]
    entry = unavailable[0]
    if not isinstance(entry, dict):
        return [
            f"{where}: oracle.unavailable[0] must be an object [ORACLE_UNAVAILABLE]"
        ]

    requested = oracle.get("requested_deployment")
    if not isinstance(requested, dict):
        return [
            f"{where}: oracle.requested_deployment must bind the selected adapter "
            "[ORACLE_UNAVAILABLE]"
        ]
    errors = []
    for key in ("adapter", "execution_target", "adapter_config"):
        if entry.get(key) != requested.get(key):
            errors.append(
                f"{where}: oracle.unavailable[0].{key} does not match the selected "
                f"adapter recorded in oracle.requested_deployment [ORACLE_UNAVAILABLE]"
            )

    adapter_name = requested.get("adapter")
    current, fatal = _replayed_adapter_probe(record, oracle, requested, where)
    if fatal:
        return fatal
    if not isinstance(current, dict) or current.get("available") is not False:
        return [
            f"{where}: unavailable deployment names adapter {adapter_name!r}, which "
            "does not currently report unavailable [ORACLE_UNAVAILABLE]"
        ]
    for key in ("execution_target", "reason_code", "detail"):
        if entry.get(key) != current.get(key):
            errors.append(
                f"{where}: oracle.unavailable[0].{key} is {entry.get(key)!r}, but "
                f"adapter {adapter_name!r} reports {current.get(key)!r} "
                "[ORACLE_UNAVAILABLE]"
            )
    expected_entry = {
        key: copy.deepcopy(requested[key])
        for key in ("adapter", "execution_target", "adapter_config")
        if key in requested
    }
    expected_entry.update(
        {
            "reason_code": current.get("reason_code"),
            "detail": current.get("detail"),
        }
    )
    if not contract.strict_json_equal(entry, expected_entry):
        errors.append(
            f"{where}: oracle.unavailable[0] must exactly match the "
            "selected-adapter diagnostic [ORACLE_UNAVAILABLE]"
        )
    return errors


if __package__:
    _expose_package_sibling(__name__)
