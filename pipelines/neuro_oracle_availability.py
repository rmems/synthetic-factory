#!/usr/bin/env python3
"""Which oracles can run here, and why the others cannot.

The FPGA adapter reports unavailability with a reason code and raises rather
than substituting a simulator, so an absent board can never read as a quiet
pass.
"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
import json
import os
import shutil
import subprocess
import sys

if __package__:
    # Import-twin helpers join the package import lock; import-order tests cover this edge.
    from . import _assert_direct_sibling, _expose_package_sibling  # pylint: disable=cyclic-import

    _assert_direct_sibling("neuro_oracle_availability")
    from .neuro_oracle_adapter import (  # noqa: E402
        CAPTURE_DETERMINISM_MEANING,
        OracleAdapter,
        OracleUnavailable,
        TARGET_FPGA_HARDWARE,
        run_digest,
    )
    from .neuro_oracle_capture import RecordedCaptureAdapter  # noqa: E402
    from .neuro_oracle_digest import digest  # noqa: E402
    from .neuro_oracle_model import (  # noqa: E402
        normalize_model,
        normalize_stimulus,
        stimulus_fixture,
    )
    from .neuro_oracle_observation import (  # noqa: E402
        _decode_action,
        _spike_events,
    )
    from .neuro_oracle_quantize import quantize_model  # noqa: E402
    from .neuro_oracle_reference import (  # noqa: E402
        FixedPointReferenceAdapter,
        SoftwareFloatAdapter,
    )
else:
    getattr(sys.modules.get("pipelines"), "_join_package_sibling", lambda name: None)(
        "neuro_oracle_availability"
    )
    from neuro_oracle_adapter import (  # noqa: E402
        CAPTURE_DETERMINISM_MEANING,
        OracleAdapter,
        OracleUnavailable,
        TARGET_FPGA_HARDWARE,
        run_digest,
    )
    from neuro_oracle_capture import RecordedCaptureAdapter  # noqa: E402
    from neuro_oracle_digest import digest  # noqa: E402
    from neuro_oracle_model import (  # noqa: E402
        normalize_model,
        normalize_stimulus,
        stimulus_fixture,
    )
    from neuro_oracle_observation import (  # noqa: E402
        _decode_action,
        _spike_events,
    )
    from neuro_oracle_quantize import quantize_model  # noqa: E402
    from neuro_oracle_reference import (  # noqa: E402
        FixedPointReferenceAdapter,
        SoftwareFloatAdapter,
    )

FPGA_DEVICE_ENV = "SPIKENAUT_FPGA_DEVICE"
FPGA_BITSTREAM_ENV = "SPIKENAUT_FPGA_BITSTREAM"
FPGA_BITSTREAM_TOOLCHAIN_ENV = "SPIKENAUT_FPGA_BITSTREAM_TOOLCHAIN"
FPGA_BOARD_REVISION_ENV = "SPIKENAUT_FPGA_BOARD_REVISION"
FPGA_BOARD_SERIAL_ENV = "SPIKENAUT_FPGA_BOARD_SERIAL"
FPGA_TRANSPORT_ENV = "SPIKENAUT_SILICON_BRIDGE"
FPGA_TRANSPORT_EXECUTABLE = "silicon-bridge"

_FPGA_DIAGNOSTIC_DETAILS = {
    "FPGA_DEVICE_NOT_DECLARED": f"{FPGA_DEVICE_ENV} is unset; no board is claimed and none is assumed",
    "FPGA_BITSTREAM_NOT_DECLARED": (
        f"{FPGA_BITSTREAM_ENV} is unset; a parity run without a pinned "
        "bitstream hash is not attributable"
    ),
    "FPGA_BITSTREAM_HASH_MALFORMED": (
        f"{FPGA_BITSTREAM_ENV} must pin the bitstream in canonical "
        "sha256:<64hex> form; a parity run without it is not attributable"
    ),
    "FPGA_BITSTREAM_TOOLCHAIN_NOT_DECLARED": (
        f"{FPGA_BITSTREAM_TOOLCHAIN_ENV} is unset; a bitstream whose "
        "synthesis toolchain is not declared is not attributable"
    ),
    "FPGA_BOARD_IDENTITY_NOT_DECLARED": (
        f"{FPGA_BOARD_REVISION_ENV} and {FPGA_BOARD_SERIAL_ENV} must both "
        "identify the physical board before a hardware claim is attributable"
    ),
    "FPGA_TRANSPORT_UNAVAILABLE": (
        f"the {FPGA_TRANSPORT_EXECUTABLE!r} adapter binary (crate "
        "silicon-bridge, rust/silicon-bridge) is not on PATH and "
        f"{FPGA_TRANSPORT_ENV} is unset; the board transport cannot be reached"
    ),
}

# Reasons whose recorded detail legitimately varies per environment (a device
# path, a transport error message); they match on a fixed prefix instead of
# the frozen detail text.
_FPGA_DIAGNOSTIC_DETAIL_PREFIXES = {
    "FPGA_DEVICE_ABSENT": ("declared device ", " does not exist"),
    "FPGA_TRANSPORT_UNAVAILABLE": (
        f"{FPGA_TRANSPORT_ENV} points at ",
        ", which is not executable",
    ),
    "FPGA_TRANSPORT_FAILED": ("transport exchange failed: ", None),
}


def _is_canonical_sha256(value):
    """True only for the canonical lowercase ``sha256:<64hex>`` spelling."""
    return (
        isinstance(value, str)
        and len(value) == len("sha256:") + 64
        and value.startswith("sha256:")
        and all(char in "0123456789abcdef" for char in value[len("sha256:"):])
    )


def _unavailable_status(reason, detail=None):
    return {
        "available": False,
        "reason_code": reason,
        "detail": _FPGA_DIAGNOSTIC_DETAILS[reason] if detail is None else detail,
    }


def fpga_diagnostic_matches(reason, detail):
    """Authenticate the historical diagnostic shape without probing a recorded path."""
    if not isinstance(reason, str) or not isinstance(detail, str):
        return False
    if detail == _FPGA_DIAGNOSTIC_DETAILS.get(reason):
        return True
    bounds = _FPGA_DIAGNOSTIC_DETAIL_PREFIXES.get(reason)
    if bounds is None:
        return False
    prefix, suffix = bounds
    if suffix is None:
        return detail.startswith(prefix) and bool(detail[len(prefix):].strip())
    return (
        detail.startswith(prefix) and detail.endswith(suffix)
        and bool(detail[len(prefix):-len(suffix)].strip())
    )


def _fpga_transport_binary(env):
    """The ``silicon-bridge`` adapter binary this run would drive, or None."""
    override = env.get(FPGA_TRANSPORT_ENV)
    if override:
        path = Path(override)
        if path.is_file() and os.access(path, os.X_OK):
            return override
        return None
    return shutil.which(FPGA_TRANSPORT_EXECUTABLE)


class FpgaHardwareAdapter(OracleAdapter):
    """Real FPGA execution target, driven over UART by the `silicon-bridge` crate.

    This adapter has no fallback. If no board is declared and reachable it
    reports unavailability with a reason code and ``run`` raises. When the
    device, bitstream provenance, board identity, and the ``silicon-bridge``
    transport binary are all present, ``run`` exchanges the stimulus with the
    board through the crate's dense Q8.8 codec and reports what came back;
    physical execution still reads as ``unverified`` because no attestation
    binds the wire frames to the claimed board.
    """

    name = "spikenaut_fpga"
    execution_target = TARGET_FPGA_HARDWARE
    runtime_class = "physical_hardware"

    def __init__(self, env=None):
        self.env = os.environ if env is None else env

    def availability(self):
        device = self.env.get(FPGA_DEVICE_ENV)
        if not device:
            return _unavailable_status("FPGA_DEVICE_NOT_DECLARED")
        if not Path(device).exists():
            return _unavailable_status("FPGA_DEVICE_ABSENT", f"declared device {device} does not exist")
        bitstream = self.env.get(FPGA_BITSTREAM_ENV)
        if not bitstream:
            return _unavailable_status("FPGA_BITSTREAM_NOT_DECLARED")
        if not _is_canonical_sha256(bitstream):
            return _unavailable_status("FPGA_BITSTREAM_HASH_MALFORMED")
        if not self.env.get(FPGA_BITSTREAM_TOOLCHAIN_ENV):
            return _unavailable_status("FPGA_BITSTREAM_TOOLCHAIN_NOT_DECLARED")
        if not (
            self.env.get(FPGA_BOARD_REVISION_ENV)
            and self.env.get(FPGA_BOARD_SERIAL_ENV)
        ):
            return _unavailable_status("FPGA_BOARD_IDENTITY_NOT_DECLARED")
        transport_override = self.env.get(FPGA_TRANSPORT_ENV)
        if _fpga_transport_binary(self.env) is None:
            if transport_override:
                return _unavailable_status(
                    "FPGA_TRANSPORT_UNAVAILABLE",
                    f"{FPGA_TRANSPORT_ENV} points at {transport_override}, "
                    "which is not executable",
                )
            return _unavailable_status("FPGA_TRANSPORT_UNAVAILABLE")
        return {
            "available": True,
            "reason_code": None,
            "detail": (
                f"device {device} via {FPGA_TRANSPORT_EXECUTABLE!r} "
                "(silicon-bridge 0.3.0 dense Q8.8 codec)"
            ),
        }

    def run(self, model, stimulus, repeats=1):
        status = self.availability()
        if not status["available"]:
            raise OracleUnavailable(status["reason_code"], status["detail"])
        model = normalize_model(model)
        stimulus = normalize_stimulus(stimulus, model["inputs"])
        _q_model, quantization = quantize_model(model)
        measured = self._exchange(model, stimulus, repeats)
        runs = measured["runs"]
        outcomes = [self._outcome(model, stimulus, run) for run in runs]
        repeat_digests = [run_digest(outcome) for outcome in outcomes]
        distinct = len(set(repeat_digests))
        latencies = [run["latency_ms"] for run in runs]
        latency = {
            "measured": True,
            "value_ms": max(latencies),
            "values_ms": latencies,
            "reason_code": None,
            "detail": (
                "wall-clock ms around the UART stimulus exchange, per run; "
                "value_ms is the slowest run"
            ),
        }
        # The retained observation is the first repeat, matching the capture
        # adapter's `primary == first repeat` convention; every repeat's
        # outcome and raw RX frame stays inside capture.source.payload.
        primary = outcomes[0]
        hardware = {
            "device": self.env[FPGA_DEVICE_ENV],
            "revision": self.env[FPGA_BOARD_REVISION_ENV],
            "board_serial": self.env[FPGA_BOARD_SERIAL_ENV],
        }
        bitstream = {
            "sha256": self.env[FPGA_BITSTREAM_ENV],
            "toolchain": self.env[FPGA_BITSTREAM_TOOLCHAIN_ENV],
        }
        recorded_at = datetime.now(timezone.utc).isoformat(timespec="milliseconds")
        capture_payload = dict(primary)
        capture_payload.update(
            {
                "repeats": len(runs),
                "repeat_digests": repeat_digests,
                "repeat_outputs": outcomes,
                "latency": latency,
                # The wire bytes the decoded outcome derives from: a reader
                # can re-decode every frame and check the transcript digests
                # without trusting this adapter's arithmetic.
                "rx_frames_hex": [run["rx_frames_hex"] for run in runs],
                "switches": [run["switches"] for run in runs],
            }
        )
        manifest = {
            "manifest_version": "silicon-bridge-uart-capture-v1",
            "recorded_at": recorded_at,
            "transport": "uart-dense-q88",
            "input_fixture_sha256": stimulus_fixture(stimulus)["sha256"],
            "payload_sha256": digest(capture_payload),
            "transcripts_sha256": [run["transcript_sha256"] for run in runs],
            "frames": measured["frames"],
            "baud_rate": measured["baud_rate"],
        }
        source = {
            "adapter": self.name,
            "execution_target": self.execution_target,
            "runtime_class": self.runtime_class,
            "quantization": quantization,
            "hardware": hardware,
            "bitstream": bitstream,
            "manifest": manifest,
            "payload": capture_payload,
        }
        capture = {
            "attestation": {"status": "unverified", "basis": "self_contained_checksums"},
            "recorded_at": recorded_at,
            "source_sha256": digest(source),
            "manifest_sha256": digest(manifest),
            "payload_sha256": digest(capture_payload),
            "source": source,
        }
        payload = {
            "adapter": self.name,
            "execution_target": self.execution_target,
            "runtime_class": self.runtime_class,
            "repeats": len(runs),
            "repeat_digests": repeat_digests,
            "determinism": {
                "identical_repeats": distinct == 1,
                "distinct_digests": distinct,
                "meaning": CAPTURE_DETERMINISM_MEANING,
            },
            "latency": latency,
            "output_digest": repeat_digests[0],
            "quantization": quantization,
            "hardware": hardware,
            "bitstream": bitstream,
            "capture": capture,
        }
        payload.update(primary)
        return payload

    def _exchange(self, model, stimulus, repeats):
        """One subprocess round-trip against the ``silicon-bridge`` binary."""
        binary = _fpga_transport_binary(self.env)
        request = {
            "device": self.env[FPGA_DEVICE_ENV],
            "model": model,
            "stimulus": stimulus,
            "repeats": repeats,
        }
        try:
            proc = subprocess.run(
                [binary, "execute"],
                input=json.dumps(request),
                capture_output=True,
                text=True,
                timeout=600,
                check=False,
            )
        except (OSError, subprocess.SubprocessError) as exc:
            raise OracleUnavailable(
                "FPGA_TRANSPORT_FAILED",
                f"transport exchange failed: {binary!r} could not be executed: {exc}",
            ) from exc
        try:
            envelope = json.loads(proc.stdout or "")
        except ValueError as exc:
            raise OracleUnavailable(
                "FPGA_TRANSPORT_FAILED",
                f"transport exchange failed: {binary!r} answered with "
                f"unparseable output: {exc}",
            ) from exc
        if proc.returncode == 0 and envelope.get("ok") is True:
            return envelope["result"]
        error = envelope.get("error") if isinstance(envelope, dict) else None
        error = error if isinstance(error, dict) else {}
        raise OracleUnavailable(
            "FPGA_TRANSPORT_FAILED",
            f"transport exchange failed: {error.get('detail') or binary!r}",
        )

    @staticmethod
    def _outcome(model, stimulus, run):
        """Shape the decoded board response the way every adapter shapes it."""
        spike_grid = run["spike_grid"]
        return {
            "spikes": spike_grid,
            "spike_events": _spike_events(spike_grid, stimulus["dt_ms"]),
            "membrane": {
                "observable": True,
                "units": "mV_q88",
                "trace": run["potentials"],
                "trace_q88_raw": run["potentials_raw"],
            },
            "action": _decode_action(spike_grid, model["action_labels"]),
            "arithmetic": {
                "format": "Q8.8",
                "saturation_events": run["saturation_events"],
            },
        }


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
