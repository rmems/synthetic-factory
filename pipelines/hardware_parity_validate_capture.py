#!/usr/bin/env python3
"""The recorded-capture digest chain.

A capture is untrusted input: this module checks that its internal chain is
intact and that the record's claims follow from it, which is integrity, not
attestation. Nothing here can show the capture describes a run that happened.
"""

from __future__ import annotations

import sys

if __package__:
    # Import-twin helpers join the package import lock; import-order tests cover this edge.
    from . import _assert_direct_sibling, _expose_package_sibling  # pylint: disable=cyclic-import

    _assert_direct_sibling("hardware_parity_validate_capture")
    from .neuro_oracle import (  # noqa: E402
        FpgaHardwareAdapter,
        digest,
        run_digest,
    )
    from .hardware_parity_terms import contract  # noqa: E402
    from .hardware_parity_validate_observation import _physical_observation_errors  # noqa: E402
else:
    getattr(sys.modules.get("pipelines"), "_join_package_sibling", lambda name: None)(
        "hardware_parity_validate_capture"
    )
    from neuro_oracle import (  # noqa: E402
        FpgaHardwareAdapter,
        digest,
        run_digest,
    )
    from hardware_parity_terms import contract  # noqa: E402
    from hardware_parity_validate_observation import _physical_observation_errors  # noqa: E402

def _repeat_projection(observation):
    """The comparable half of a retained observation, or None if malformed."""
    if not isinstance(observation, dict):
        return None
    return {
        key: observation.get(key)
        for key in ("spikes", "spike_events", "membrane", "action", "arithmetic")
    }


def _repeat_cardinality_errors(payload, where):
    """repeat_outputs and repeat_digests must be non-empty equal-length lists."""
    repeat_outputs = payload.get("repeat_outputs")
    repeat_digests = payload.get("repeat_digests")
    if not isinstance(repeat_outputs, list) or not repeat_outputs:
        return None, [
            f"{where}: capture payload must retain one repeat_outputs entry per "
            "repeat digest [REPEATABILITY_UNPROVEN]"
        ]
    if not isinstance(repeat_digests, list) or len(repeat_outputs) != len(
        repeat_digests
    ):
        return None, [
            f"{where}: capture repeat_outputs and repeat_digests must have identical "
            "cardinality [REPEATABILITY_UNPROVEN]"
        ]
    return zip(repeat_outputs, repeat_digests), []


def _repeat_entry_errors(entry, scenario, where):
    """One retained repeat: well formed, and its digest derives from it.

    ``entry`` is ``(index, repeat_output, repeat_digest)``."""
    index, repeat_output, repeat_digest = entry
    errors = _physical_observation_errors(
        repeat_output,
        scenario,
        f"capture.source.payload.repeat_outputs[{index}]",
        where,
    )
    try:
        expected_digest = run_digest(repeat_output)
    except (KeyError, TypeError, ValueError, AttributeError, OverflowError) as exc:
        return errors + [
            f"{where}: capture repeat output {index} is malformed: {exc} "
            "[REPEATABILITY_UNPROVEN]"
        ]
    if repeat_digest != expected_digest:
        errors.append(
            f"{where}: capture repeat_digests[{index}] is not derived from "
            f"repeat_outputs[{index}] [REPEATABILITY_UNPROVEN]"
        )
    return errors


def _capture_repeat_errors(payload, scenario, where):
    """Every retained repeat must be well formed and match its digest."""
    repeats, errors = _repeat_cardinality_errors(payload, where)
    if repeats is None:
        return errors
    for index, pair in enumerate(repeats):
        errors += _repeat_entry_errors((index, *pair), scenario, where)
    repeat_outputs = payload["repeat_outputs"]
    primary_projection = _repeat_projection(payload)
    if not contract.strict_json_equal(
        _repeat_projection(repeat_outputs[0]), primary_projection
    ):
        errors.append(
            f"{where}: capture payload must equal its first retained repeat "
            "observation [REPEATABILITY_UNPROVEN]"
        )
    return errors


def _capture_output_digest_errors(deployment, payload, repeat_digests, where):
    """The deployment's digests must derive from the captured payload."""
    try:
        payload_output_digest = run_digest(payload)
    except (KeyError, TypeError, ValueError, AttributeError, OverflowError) as exc:
        return [f"{where}: capture payload is malformed: {exc} [ENVELOPE_MALFORMED]"]
    errors = []
    if deployment.get("output_digest") != payload_output_digest:
        errors.append(
            f"{where}: deployment output_digest is not derived from the captured "
            "payload [HW_PROVENANCE_MISSING]"
        )
    expected_repeats = list(repeat_digests) if isinstance(repeat_digests, list) else []
    if deployment.get("repeat_digests") != expected_repeats:
        errors.append(
            f"{where}: deployment repeat_digests are not the captured repeats "
            "[REPEATABILITY_UNPROVEN]"
        )
    return errors


def _bound_timestamp(recorded_at, manifest_recorded_at):
    """A non-empty capture timestamp must equal the manifest's."""
    if not isinstance(recorded_at, str) or not recorded_at.strip():
        return False
    return recorded_at == manifest_recorded_at


def _capture_manifest_binding_errors(capture, manifest, record, where):
    """capture.recorded_at and the input fixture must bind to the manifest."""
    errors = []
    bound_time = _bound_timestamp(capture.get("recorded_at"), manifest.get("recorded_at"))
    if not bound_time:
        errors.append(
            f"{where}: capture.recorded_at is not bound to "
            "capture.source.manifest.recorded_at [HW_PROVENANCE_MISSING]"
        )
    fixture_sha = ((record.get("scenario") or {}).get("input_fixture") or {}).get(
        "sha256"
    )
    if manifest.get("input_fixture_sha256") != fixture_sha:
        errors.append(
            f"{where}: capture manifest names a different input fixture "
            "[INPUT_FIXTURE_MISMATCH]"
        )
    return errors


def _capture_adapter_identity_errors(source, deployment, where):
    """The capture's adapter identity must agree with the deployment's."""
    source_adapter = source.get("adapter")
    source_runtime = source.get("runtime_class")
    deployment_identity = (
        deployment.get("adapter"),
        deployment.get("runtime_class"),
    )
    if (source_adapter, source_runtime) == deployment_identity:
        return []
    live_claim = deployment_identity == (
        FpgaHardwareAdapter.name,
        FpgaHardwareAdapter.runtime_class,
    )
    if live_claim:
        return [
            f"{where}: live FPGA evidence must bind capture.source.adapter and "
            "capture.source.runtime_class to the live board adapter "
            "[HW_PROVENANCE_MISSING]"
        ]
    if source_adapter is not None or source_runtime is not None:
        return [
            f"{where}: capture source adapter identity disagrees with the "
            "deployment [HW_PROVENANCE_MISSING]"
        ]
    return []


def _capture_identity_errors(source, deployment, payload, where):
    """Execution target, adapter identity, board/bitstream, and quantization."""
    errors = []
    if source.get("execution_target") != deployment.get("execution_target"):
        errors.append(
            f"{where}: capture source execution_target disagrees with the deployment "
            "[HW_TARGET_UNKNOWN]"
        )
    errors += _capture_adapter_identity_errors(source, deployment, where)
    for key in ("hardware", "bitstream"):
        if source.get(key) != deployment.get(key):
            errors.append(
                f"{where}: oracle.deployment.{key} does not match capture.source.{key} "
                "[HW_PROVENANCE_MISSING]"
            )
    return errors + _capture_quantization_errors(source, deployment, payload, where)


def _dual_quantization_pin_errors(source, payload, where):
    """When both locations pin quantization, the pins must agree."""
    if (
        "quantization" in source
        and "quantization" in payload
        and not contract.strict_json_equal(
            source["quantization"], payload["quantization"]
        )
    ):
        return [
            f"{where}: capture.source.quantization disagrees with "
            "capture.source.payload.quantization [Q88_PROVENANCE_MISMATCH]"
        ]
    return []


def _capture_quantization_errors(source, deployment, payload, where):
    """Distinguish an absent quantization pin from a present invalid value."""
    payload = payload if isinstance(payload, dict) else {}
    errors = _dual_quantization_pin_errors(source, payload, where)
    if "quantization" in source:
        source_quantization = source["quantization"]
    else:
        source_quantization = payload.get("quantization")
    # Strict JSON typing: an ordinary `!=` treats False as 0, letting a
    # capture source violate the documented quantization types while still
    # binding to the deployment.
    if not contract.strict_json_equal(source_quantization, deployment.get("quantization")):
        errors.append(
            f"{where}: deployment quantization is not the conversion stored with the "
            "capture [Q88_PROVENANCE_MISMATCH]"
        )
    return errors


def _capture_projection_errors(deployment, payload, where):
    """Each observation on the deployment must be the one stored in the payload."""
    normalized_payload = {
        "spikes": payload.get("spikes"),
        "spike_events": payload.get("spike_events"),
        "membrane": payload.get(
            "membrane", {"observable": False, "units": "mV_model", "trace": None}
        ),
        "action": payload.get("action"),
        "arithmetic": payload.get("arithmetic"),
        "latency": payload.get("latency"),
    }
    errors = []
    for key, expected in normalized_payload.items():
        # Strict JSON typing: `True == 1` under an ordinary comparison, so a
        # payload observation could violate its documented shape (for example
        # latency.measured as an integer) while still projecting onto the
        # deployment.
        if not contract.strict_json_equal(deployment.get(key), expected):
            errors.append(
                f"{where}: oracle.deployment.{key} is not the observation stored in "
                "capture.source.payload [HW_PROVENANCE_MISSING]"
            )
    return errors


def _capture_source_digest_errors(capture, source, where):
    """capture.source_sha256 must identify capture.source bytes.

    Returns ``(errors, fatal)`` — a non-canonical source stops the chain
    outright, while a digest mismatch is recorded and the remaining capture
    checks still run.
    """
    try:
        source_sha = digest(source)
    except (TypeError, ValueError, OverflowError) as exc:
        return [f"{where}: capture source is not canonical JSON: {exc}"], True
    if capture.get("source_sha256") != source_sha:
        return [
            f"{where}: capture.source_sha256 does not identify capture.source "
            "[HW_PROVENANCE_MISSING]"
        ], False
    return [], False


def _stored_digest_bindings(capture, manifest, shas, where):
    """capture's stored manifest/payload digests must identify the objects."""
    manifest_sha, payload_sha = shas
    errors = []
    if capture.get("manifest_sha256") != manifest_sha:
        errors.append(
            f"{where}: capture.manifest_sha256 does not identify the stored manifest "
            "[HW_PROVENANCE_MISSING]"
        )
    if (
        capture.get("payload_sha256") != payload_sha
        or manifest.get("payload_sha256") != payload_sha
    ):
        errors.append(
            f"{where}: capture payload digest is not bound to the stored manifest "
            "[HW_PROVENANCE_MISSING]"
        )
    return errors


def _capture_stored_object_errors(capture, source, where):
    """Return ``(manifest, payload, errors)``: capture.source's manifest and
    payload objects, plus the digest-binding errors between them."""
    manifest = source.get("manifest")
    payload = source.get("payload")
    if not isinstance(manifest, dict) or not isinstance(payload, dict):
        return None, None, [
            f"{where}: capture.source must contain object-valued manifest and payload "
            "[HW_PROVENANCE_MISSING]"
        ]
    try:
        shas = digest(manifest), digest(payload)
    except (TypeError, ValueError, OverflowError) as exc:
        return None, None, [
            f"{where}: capture manifest or payload is not canonical finite JSON: "
            f"{exc} [ENVELOPE_MALFORMED]"
        ]
    return manifest, payload, _stored_digest_bindings(
        capture, manifest, shas, where
    )


def _check_capture_chain(record, deployment, where):
    """Bind a physical claim to the replay source stored by the adapter.

    This verifies the record-level digest chain and catches a reference-model
    record relabelled as hardware.  It deliberately does not claim to prove
    that the source file came from a real board; that still requires the
    out-of-band attestation documented in ``docs/parity-oracles.md``.
    """
    errors = []
    capture = deployment.get("capture")
    if not isinstance(capture, dict):
        return [
            f"{where}: a physical target needs a capture object with replay source "
            "bytes [HW_PROVENANCE_MISSING]"
        ]
    expected_attestation = {"status": "unverified", "basis": "self_contained_checksums"}
    if not contract.strict_json_equal(capture.get("attestation"), expected_attestation):
        errors.append(f"{where}: capture attestation must remain unverified [HW_PROVENANCE_MISSING]")
    source = capture.get("source")
    if not isinstance(source, dict):
        return [
            f"{where}: oracle.deployment.capture.source is required to re-check the "
            "capture digest chain [HW_PROVENANCE_MISSING]"
        ]
    sha_errors, fatal = _capture_source_digest_errors(capture, source, where)
    errors += sha_errors
    if fatal:
        return errors
    manifest, payload, object_errors = _capture_stored_object_errors(
        capture, source, where
    )
    errors += object_errors
    if manifest is None:
        return errors
    return errors + _capture_evidence_errors(
        record, deployment, (capture, source, manifest, payload), where
    )


def _capture_evidence_errors(record, deployment, stored, where):
    """Everything past the digest chain: bindings, re-observation, identity."""
    capture, source, manifest, payload = stored
    errors = _capture_manifest_binding_errors(capture, manifest, record, where)
    scenario = record.get("scenario")
    errors += _physical_observation_errors(
        payload, scenario, "capture.source.payload", where
    )
    errors += _capture_identity_errors(source, deployment, payload, where)
    errors += _capture_projection_errors(deployment, payload, where)
    repeat_digests = payload.get("repeat_digests")
    errors += _capture_repeat_errors(payload, scenario, where)
    errors += _capture_output_digest_errors(deployment, payload, repeat_digests, where)
    return errors


if __package__:
    _expose_package_sibling(__name__)
