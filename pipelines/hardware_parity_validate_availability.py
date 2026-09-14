#!/usr/bin/env python3
"""Is the deployment oracle actually available, and does the record agree?

Availability is re-probed here rather than read off the record, so a stale
or forged absence claim cannot survive on a host where the runtime exists.
"""

from __future__ import annotations

import copy
import sys
from pathlib import Path

_PIPELINES = Path(__file__).resolve().parent
if str(_PIPELINES) not in sys.path:
    sys.path.insert(0, str(_PIPELINES))

import neuro_oracle  # noqa: E402
from neuro_oracle import (  # noqa: E402
    FpgaHardwareAdapter,
    OracleUnavailable,
    RecordedCaptureAdapter,
)
from hardware_parity_terms import (  # noqa: E402
    contract,
)

# `availability_report` is read off the `neuro_oracle` module at call time, not
# bound at import, because it is a live probe of this host: tests fake an
# available FPGA by patching `neuro_oracle.availability_report`, and a bound
# copy here would keep answering the real one. The same reason the validator
# re-probes rather than trusting a record's snapshot.
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


def _replayed_adapter_probe(record, oracle, requested, where):
    """Re-derive the selected adapter's current diagnostic.

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
    adapter = RecordedCaptureAdapter(capture_path)
    scenario = record.get("scenario") or {}
    software = oracle.get("software") or {}
    try:
        adapter.run(
            scenario.get("model_float"),
            scenario.get("stimulus"),
            repeats=software.get("repeats", 1),
        )
    except OracleUnavailable as exc:
        return {
            "available": False,
            "execution_target": adapter.execution_target,
            "reason_code": exc.reason_code,
            "detail": exc.detail,
        }, []
    except (
        ValueError,
        TypeError,
        KeyError,
        IndexError,
        AttributeError,
        OverflowError,
    ) as exc:
        return None, [
            f"{where}: recorded_capture diagnostic is not reproducible: {exc} "
            "[ORACLE_UNAVAILABLE]"
        ]
    return {
        "available": True,
        "execution_target": adapter.execution_target,
        "reason_code": None,
        "detail": "capture executes for the recorded scenario",
    }, []


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
            f"{where}: oracle.unavailable[0] must exactly match the current "
            "selected-adapter diagnostic [ORACLE_UNAVAILABLE]"
        )
    return errors
