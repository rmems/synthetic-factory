#!/usr/bin/env python3
"""Replaying a recorded hardware capture, and authenticating its digest chain.

A capture is trusted input. This module checks the chain inside it is intact;
nothing here can show the capture describes a run that actually happened, which
is why a physical claim needs out-of-band attestation as well.
"""

from __future__ import annotations

from pathlib import Path
import json
import math
import os
import stat
import sys

_PIPELINES = Path(__file__).resolve().parent
if str(_PIPELINES) not in sys.path:
    sys.path.insert(0, str(_PIPELINES))

from neuro_oracle_adapter import (  # noqa: E402
    CAPTURE_DETERMINISM_MEANING,
    EXECUTION_TARGETS,
    OracleAdapter,
    OracleUnavailable,
    run_digest,
)
from neuro_oracle_digest import (  # noqa: E402
    canonical_json,
    digest,
)
from neuro_oracle_model import (  # noqa: E402
    normalize_model,
    normalize_stimulus,
    stimulus_fixture,
)


MAX_CAPTURE_BYTES = 16 * 1024 * 1024


def _reject_json_constant(value):
    """Reject Python's non-standard NaN/Infinity JSON extensions.

    Mirrors ``canonical_json``'s ``allow_nan=False`` on the read side: a
    capture file smuggling ``NaN``/``Infinity`` must fail to parse rather
    than load a value ``digest()`` (which forbids non-finite floats) can
    never re-derive.
    """
    raise ValueError(f"non-standard JSON numeric constant {value}")


def _reject_nonfinite_float(text):
    """Parse a JSON float token, rejecting overflow-to-infinity values.

    ``parse_constant`` never sees an ordinary numeric token like ``1e9999``,
    which ``float()`` silently turns into infinity; that value would crash
    ``digest()`` with an uncaught ValueError deep in generation instead of a
    coded capture diagnostic at the parse.
    """
    value = float(text)
    if not math.isfinite(value):
        raise ValueError(f"non-finite JSON number {text}")
    return value


class RecordedCaptureAdapter(OracleAdapter):
    """Replays a previously recorded hardware capture from disk.

    The capture's own ``execution_target`` is preserved verbatim, and the
    payload digest is verified against the manifest before anything is
    returned, so a hand-edited capture cannot be replayed as a real run.
    """

    name = "recorded_capture"
    runtime_class = "recorded_capture"

    def __init__(self, capture_path):
        self.capture_path = Path(capture_path)
        self.execution_target = None
        self._capture = None
        self._error = None
        try:
            payload = self._read_capture_bytes()
            self._capture = json.loads(
                payload.decode("utf-8"),
                parse_constant=_reject_json_constant,
                parse_float=_reject_nonfinite_float,
            )
        except FileNotFoundError:
            self._error = ("CAPTURE_FILE_ABSENT", f"no capture at {self.capture_path}")
        except OSError as exc:
            self._error = (
                "CAPTURE_UNREADABLE",
                f"cannot read {self.capture_path}: {exc}",
            )
        # ValueError covers json.JSONDecodeError and UnicodeDecodeError, both
        # of which derive from it, along with the refusals the two parse hooks
        # raise directly for non-standard and non-finite numbers.
        except ValueError as exc:
            self._error = ("CAPTURE_UNREADABLE", str(exc))
        # Keyed on the error, not on `self._capture`: a capture file whose
        # whole content is `null` parses to None, which is also the "nothing
        # loaded" value set above. Testing the capture would skip the binding
        # for it, leaving no error behind -- `availability()` would call such a
        # capture available and `run()` would reach `None.get` instead of
        # raising CAPTURE_UNREADABLE. No error means the parse returned
        # something, and `_bind_execution_target` decides whether that
        # something is a capture.
        if self._error is None:
            self._bind_execution_target()

    def _read_capture_bytes(self):
        """The capture file's bytes, read without trusting the path.

        The path is stat'ed before it is opened and the descriptor is proved
        to be that same file afterwards; every refusal here is an OSError, so
        the caller reports one CAPTURE_UNREADABLE reason for all of them.
        """
        path_metadata = self.capture_path.lstat()
        if not stat.S_ISREG(path_metadata.st_mode):
            raise OSError("capture path is not a regular file")
        if path_metadata.st_size > MAX_CAPTURE_BYTES:
            raise OSError(
                f"capture is {path_metadata.st_size} bytes; limit is "
                f"{MAX_CAPTURE_BYTES}"
            )
        flags = os.O_RDONLY | getattr(os, "O_NONBLOCK", 0) | getattr(
            os, "O_NOFOLLOW", 0
        )
        descriptor = os.open(self.capture_path, flags)
        try:
            return self._read_opened_capture(descriptor, path_metadata)
        finally:
            os.close(descriptor)

    @staticmethod
    def _read_opened_capture(descriptor, path_metadata):
        """Bytes from a descriptor proved to be the file that was stat'ed.

        `path_metadata` is what the path claimed before the open, so a file
        swapped between the two calls -- for a symlink, a device, or a larger
        file -- is refused rather than read. The read itself stays bounded.
        """
        metadata = os.fstat(descriptor)
        if not stat.S_ISREG(metadata.st_mode):
            raise OSError("capture path is not a regular file")
        if (metadata.st_dev, metadata.st_ino) != (
            path_metadata.st_dev,
            path_metadata.st_ino,
        ):
            raise OSError("capture path changed while it was being opened")
        if metadata.st_size > MAX_CAPTURE_BYTES:
            raise OSError(
                f"capture is {metadata.st_size} bytes; limit is "
                f"{MAX_CAPTURE_BYTES}"
            )
        with os.fdopen(descriptor, "rb", closefd=False) as handle:
            payload = handle.read(MAX_CAPTURE_BYTES + 1)
        if len(payload) > MAX_CAPTURE_BYTES:
            raise OSError(f"capture exceeds {MAX_CAPTURE_BYTES} bytes")
        return payload

    def _bind_execution_target(self):
        """Adopt the target the parsed capture declares, refusing an unknown one."""
        if not isinstance(self._capture, dict):
            self._error = ("CAPTURE_UNREADABLE", "capture must be a JSON object")
            return
        self.execution_target = self._capture.get("execution_target")
        if self.execution_target not in EXECUTION_TARGETS:
            self._error = (
                "CAPTURE_TARGET_UNKNOWN",
                f"execution_target {self.execution_target!r} is not a known target",
            )

    def availability(self):
        if self._error:
            return {"available": False, "reason_code": self._error[0], "detail": self._error[1]}
        return {
            "available": True,
            "reason_code": None,
            "detail": f"capture {self.capture_path.name}",
        }

    def _authenticated_manifest_and_payload(self):
        """The capture's manifest and payload, with the digest chain checked."""
        capture = self._capture
        manifest = capture.get("manifest") or {}
        if not isinstance(manifest, dict):
            raise OracleUnavailable(
                "CAPTURE_UNREADABLE", "capture manifest must be a JSON object"
            )
        payload = capture.get("payload")
        if not isinstance(payload, dict):
            raise OracleUnavailable(
                "CAPTURE_UNREADABLE", "capture payload must be a JSON object"
            )
        try:
            actual = digest(payload)
        except (TypeError, ValueError, OverflowError) as exc:
            raise OracleUnavailable(
                "CAPTURE_UNREADABLE",
                f"capture payload is not canonical finite JSON: {exc}",
            ) from exc
        if manifest.get("payload_sha256") != actual:
            raise OracleUnavailable(
                "CAPTURE_DIGEST_MISMATCH",
                f"capture payload digest {actual} != manifest "
                f"{manifest.get('payload_sha256')}",
            )
        return manifest, payload, actual

    @staticmethod
    def _check_fixture_binding(manifest, model, stimulus):
        """The capture must name the exact encoded input fixture it saw."""
        model = normalize_model(model)
        fixture = stimulus_fixture(normalize_stimulus(stimulus, model["inputs"]))
        if manifest.get("input_fixture_sha256") != fixture["sha256"]:
            raise OracleUnavailable(
                "CAPTURE_INPUT_FIXTURE_MISMATCH",
                "capture was taken against a different encoded input fixture",
            )

    def _quantization_provenance(self, payload):
        """The Q8.8 conversion the capture claims produced its bitstream.

        Top-level ``capture.quantization`` and ``payload.quantization`` are both
        supported locations. When both are present they must agree exactly;
        otherwise the adapter would silently prefer the top-level block while
        retaining a conflicting payload conversion in the authenticated source.
        """
        top = self._capture.get("quantization")
        nested = payload.get("quantization") if isinstance(payload, dict) else None
        if top and nested:
            try:
                if canonical_json(top) != canonical_json(nested):
                    raise OracleUnavailable(
                        "CAPTURE_QUANTIZATION_CONFLICT",
                        "capture.quantization and payload.quantization disagree; "
                        "exactly one location or identical blocks are required",
                    )
            except (TypeError, ValueError, OverflowError) as exc:
                raise OracleUnavailable(
                    "CAPTURE_UNREADABLE",
                    f"capture quantization is not canonical finite JSON: {exc}",
                ) from exc
            quantization = top
        else:
            quantization = top or nested
        if not quantization:
            raise OracleUnavailable(
                "CAPTURE_QUANTIZATION_MISSING",
                "capture must record the Q8.8 conversion that produced the bitstream",
            )
        # A truthy non-object (e.g. an array) would flow into the record as
        # provenance and crash `quantization_metrics` with an uncaught
        # AttributeError mid-generation instead of a coded diagnostic.
        if not isinstance(quantization, dict):
            raise OracleUnavailable(
                "CAPTURE_UNREADABLE",
                "capture quantization must be a JSON object describing the "
                "Q8.8 conversion",
            )
        return quantization

    @staticmethod
    def _retained_observation_fingerprint(payload):
        """The payload must carry a complete, digestible observation."""
        missing = [
            key
            for key in (
                "spikes",
                "spike_events",
                "membrane",
                "action",
                "arithmetic",
                "repeat_outputs",
                "repeat_digests",
            )
            if key not in payload
        ]
        if missing:
            raise OracleUnavailable(
                "CAPTURE_UNREADABLE", f"capture payload is missing {missing}"
            )
        try:
            return run_digest(payload)
        except (KeyError, TypeError, AttributeError) as exc:
            raise OracleUnavailable(
                "CAPTURE_UNREADABLE", f"capture payload is malformed: {exc}"
            ) from exc

    @staticmethod
    def _authenticated_repeats(payload):
        """Every retained repeat must re-derive the digest recorded for it."""
        repeat_outputs = payload["repeat_outputs"]
        repeat_digests = payload["repeat_digests"]
        if (
            not isinstance(repeat_outputs, list)
            or not repeat_outputs
            or not isinstance(repeat_digests, list)
            or len(repeat_outputs) != len(repeat_digests)
        ):
            raise OracleUnavailable(
                "CAPTURE_UNREADABLE",
                "capture repeat_outputs and repeat_digests must be nonempty arrays "
                "with identical cardinality",
            )
        for index, (repeat_output, recorded_digest) in enumerate(
            zip(repeat_outputs, repeat_digests)
        ):
            try:
                expected_digest = run_digest(repeat_output)
            except (KeyError, TypeError, ValueError, AttributeError) as exc:
                raise OracleUnavailable(
                    "CAPTURE_UNREADABLE",
                    f"capture repeat_outputs[{index}] is malformed: {exc}",
                ) from exc
            if recorded_digest != expected_digest:
                raise OracleUnavailable(
                    "CAPTURE_DIGEST_MISMATCH",
                    f"capture repeat_digests[{index}] is not derived from "
                    f"repeat_outputs[{index}]",
                )
        return repeat_outputs, repeat_digests

    @staticmethod
    def _check_primary_matches_first_repeat(payload, repeat_outputs):
        """The payload's primary observation must equal its first repeat."""
        primary = {
            key: payload.get(key)
            for key in ("spikes", "spike_events", "membrane", "action", "arithmetic")
        }
        first = (
            {
                key: repeat_outputs[0].get(key)
                for key in (
                    "spikes",
                    "spike_events",
                    "membrane",
                    "action",
                    "arithmetic",
                )
            }
            if isinstance(repeat_outputs[0], dict)
            else None
        )
        try:
            first_json = canonical_json(first)
            primary_json = canonical_json(primary)
        except (TypeError, ValueError, OverflowError) as exc:
            raise OracleUnavailable(
                "CAPTURE_UNREADABLE",
                f"capture retained observation is not canonical finite JSON: {exc}",
            ) from exc
        if first_json != primary_json:
            raise OracleUnavailable(
                "CAPTURE_DIGEST_MISMATCH",
                "capture payload does not match its first retained repeat output",
            )

    def run(self, model, stimulus, repeats=1):
        if self._error:
            raise OracleUnavailable(*self._error)
        capture = self._capture
        manifest, payload, actual = self._authenticated_manifest_and_payload()
        self._check_fixture_binding(manifest, model, stimulus)
        # The Q8.8 export is what was loaded onto the board. Report its absence
        # before checking the retained observation so the failure identifies
        # the actual missing provenance rather than a secondary shape detail.
        quantization = self._quantization_provenance(payload)
        fingerprint = self._retained_observation_fingerprint(payload)
        repeat_outputs, repeat_digests = self._authenticated_repeats(payload)
        self._check_primary_matches_first_repeat(payload, repeat_outputs)
        return {
            "quantization": quantization,
            "adapter": self.name,
            "execution_target": self.execution_target,
            "runtime_class": self.runtime_class,
            "repeats": len(repeat_digests),
            "repeat_digests": repeat_digests,
            "determinism": {
                "identical_repeats": len(set(repeat_digests)) == 1,
                "distinct_digests": len(set(repeat_digests)),
                "meaning": CAPTURE_DETERMINISM_MEANING,
            },
            "latency": payload.get("latency"),
            "output_digest": fingerprint,
            "spikes": payload["spikes"],
            "spike_events": payload["spike_events"],
            "membrane": payload["membrane"],
            "action": payload["action"],
            "arithmetic": payload["arithmetic"],
            "hardware": capture.get("hardware"),
            "bitstream": capture.get("bitstream"),
            "capture": {
                "path": self.capture_path.name,
                # Keep the replay source on the record so validation can
                # re-check the same digest chain the adapter checked.  A bare
                # manifest label is not evidence: without these source bytes a
                # fixed-point record could be relabelled as a capture and
                # decorated with plausible-looking hashes.
                "source_sha256": digest(capture),
                "manifest_sha256": digest(manifest),
                "payload_sha256": actual,
                "recorded_at": manifest.get("recorded_at"),
                "source": capture,
            },
        }
