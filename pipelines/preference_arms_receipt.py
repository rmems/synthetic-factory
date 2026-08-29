#!/usr/bin/env python3
"""Revalidation of a persisted diagnosis handoff receipt against its bytes."""

from __future__ import annotations

import hashlib
import re
from pathlib import Path
from typing import Any

import sys

_PIPELINES = Path(__file__).resolve().parent
if str(_PIPELINES) not in sys.path:
    sys.path.insert(0, str(_PIPELINES))

from preference_arms_diagnosis import (  # noqa: E402
    HANDOFF_RECEIPT_VERSION,
    MAX_DIAGNOSIS_BYTES,
    _strict_json_object,
    diagnosis_filenames,
    diagnosis_receipt_filename,
    validate_diagnosis_document,
)
from preference_arms_fs import _read_regular_artifact  # noqa: E402
from preference_arms_text import PreferenceArmsError  # noqa: E402


def validate_diagnosis_handoff_receipt(
    artifact_dir: Path,
    *,
    factory: str,
    round_number: int,
    staging_dir: Path,
    reservation_token: str,
    expected_count: int,
) -> dict[str, Any]:
    """Validate one persisted receipt against captured or committed bytes."""

    root = Path(artifact_dir)
    if not root.is_dir() or root.is_symlink():
        raise PreferenceArmsError(f"diagnosis artifact root is unsafe: {root}")
    expected_names = diagnosis_filenames(round_number, expected_count)
    receipt_name = diagnosis_receipt_filename(round_number)
    allowed_diagnosis_names = {*expected_names, receipt_name}
    round_suffix = f"-r{round_number:02d}."
    try:
        diagnosis_named = {
            path.name
            for path in root.iterdir()
            if path.name.startswith("diagnosis-") and round_suffix in path.name
        }
    except OSError as exc:
        raise PreferenceArmsError(
            f"diagnosis artifact root cannot be inspected: {root}: {exc}"
        ) from exc
    unexpected = sorted(diagnosis_named - allowed_diagnosis_names)
    missing = sorted(allowed_diagnosis_names - diagnosis_named)
    if unexpected:
        raise PreferenceArmsError("unexpected diagnosis artifact(s): " + ", ".join(unexpected))
    if missing:
        raise PreferenceArmsError("missing diagnosis artifact(s): " + ", ".join(missing))

    receipt_bytes = _read_regular_artifact(
        root,
        receipt_name,
        label="diagnosis receipt",
        max_bytes=MAX_DIAGNOSIS_BYTES,
    )
    receipt = _strict_json_object(receipt_bytes, label="diagnosis receipt")
    required_keys = {
        "version",
        "factory",
        "round",
        "staging_dir",
        "reservation_token",
        "diagnosis_files",
    }
    if set(receipt) != required_keys:
        raise PreferenceArmsError(
            "diagnosis receipt keys must be exactly " + ", ".join(sorted(required_keys))
        )
    if type(receipt["version"]) is not int or receipt["version"] != HANDOFF_RECEIPT_VERSION:
        raise PreferenceArmsError("diagnosis receipt has an unsupported version")
    if receipt["factory"] != factory:
        raise PreferenceArmsError("diagnosis receipt factory does not match the reservation")
    if type(receipt["round"]) is not int or receipt["round"] != round_number:
        raise PreferenceArmsError("diagnosis receipt round does not match the reservation")
    if receipt["staging_dir"] != str(staging_dir):
        raise PreferenceArmsError(
            "diagnosis receipt staging directory does not match the reservation"
        )
    if (
        not isinstance(reservation_token, str)
        or re.fullmatch(r"[0-9a-f]{32}", reservation_token) is None
        or receipt["reservation_token"] != reservation_token
    ):
        raise PreferenceArmsError("diagnosis receipt token does not match the reservation")

    entries = receipt["diagnosis_files"]
    if not isinstance(entries, list) or len(entries) != expected_count:
        raise PreferenceArmsError("diagnosis receipt has the wrong number of file entries")
    validated_entries: list[tuple[str, int, str]] = []
    for index, entry in enumerate(entries):
        if not isinstance(entry, dict) or set(entry) != {"name", "bytes", "sha256"}:
            raise PreferenceArmsError(f"diagnosis receipt entry {index + 1} has invalid keys")
        name = entry["name"]
        byte_count = entry["bytes"]
        digest = entry["sha256"]
        expected_name = expected_names[index]
        if not isinstance(name, str) or Path(name).name != name or name != expected_name:
            raise PreferenceArmsError(f"diagnosis receipt entry {index + 1} has invalid name")
        if type(byte_count) is not int or byte_count < 1:
            raise PreferenceArmsError(f"diagnosis receipt entry {name!r} has invalid byte count")
        if not isinstance(digest, str) or re.fullmatch(r"[0-9a-f]{64}", digest) is None:
            raise PreferenceArmsError(f"diagnosis receipt entry {name!r} has invalid SHA-256")
        validated_entries.append((name, byte_count, digest))

    for name, byte_count, digest in validated_entries:
        payload = _read_regular_artifact(
            root,
            name,
            label="diagnosis file",
            max_bytes=MAX_DIAGNOSIS_BYTES,
        )
        validate_diagnosis_document(payload, label=f"diagnosis file {name}")
        if len(payload) != byte_count:
            raise PreferenceArmsError(f"diagnosis file byte count does not match receipt: {name}")
        if hashlib.sha256(payload).hexdigest() != digest:
            raise PreferenceArmsError(f"diagnosis file SHA-256 does not match receipt: {name}")

    return receipt
