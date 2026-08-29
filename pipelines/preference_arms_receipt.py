#!/usr/bin/env python3
"""Revalidation of a persisted diagnosis handoff receipt against its bytes."""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass
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


_RECEIPT_KEYS = {
    "version",
    "factory",
    "round",
    "staging_dir",
    "reservation_token",
    "diagnosis_files",
}


@dataclass(frozen=True)
class ReceiptExpectation:
    """The reservation facts a persisted diagnosis receipt must agree with."""

    factory: str
    round_number: int
    staging_dir: Path
    reservation_token: str
    expected_count: int


def _diagnosis_artifact_root(artifact_dir: Path) -> Path:
    root = Path(artifact_dir)
    if not root.is_dir() or root.is_symlink():
        raise PreferenceArmsError(f"diagnosis artifact root is unsafe: {root}")
    return root


def _named_diagnosis_artifacts(root: Path, round_number: int) -> set[str]:
    round_suffix = f"-r{round_number:02d}."
    try:
        return {
            path.name
            for path in root.iterdir()
            if path.name.startswith("diagnosis-") and round_suffix in path.name
        }
    except OSError as exc:
        raise PreferenceArmsError(
            f"diagnosis artifact root cannot be inspected: {root}: {exc}"
        ) from exc


def _require_exact_artifact_set(root: Path, allowed: set[str], round_number: int) -> None:
    """The round's diagnosis artifacts are exactly the allowlist, no more, no less."""

    present = _named_diagnosis_artifacts(root, round_number)
    unexpected = sorted(present - allowed)
    missing = sorted(allowed - present)
    if unexpected:
        raise PreferenceArmsError("unexpected diagnosis artifact(s): " + ", ".join(unexpected))
    if missing:
        raise PreferenceArmsError("missing diagnosis artifact(s): " + ", ".join(missing))


def _is_bound_reservation_token(receipt: dict[str, Any], token: str) -> bool:
    if not isinstance(token, str):
        return False
    if re.fullmatch(r"[0-9a-f]{32}", token) is None:
        return False
    return receipt["reservation_token"] == token


def _validate_receipt_keys(receipt: dict[str, Any]) -> None:
    if set(receipt) != _RECEIPT_KEYS:
        raise PreferenceArmsError(
            "diagnosis receipt keys must be exactly " + ", ".join(sorted(_RECEIPT_KEYS))
        )


def _is_supported_receipt_version(receipt: dict[str, Any]) -> bool:
    if type(receipt["version"]) is not int:
        return False
    return receipt["version"] == HANDOFF_RECEIPT_VERSION


def _is_expected_receipt_round(receipt: dict[str, Any], round_number: int) -> bool:
    if type(receipt["round"]) is not int:
        return False
    return receipt["round"] == round_number


def _validate_receipt_identity(receipt: dict[str, Any], expectation: ReceiptExpectation) -> None:
    _validate_receipt_keys(receipt)
    if not _is_supported_receipt_version(receipt):
        raise PreferenceArmsError("diagnosis receipt has an unsupported version")
    if receipt["factory"] != expectation.factory:
        raise PreferenceArmsError("diagnosis receipt factory does not match the reservation")
    if not _is_expected_receipt_round(receipt, expectation.round_number):
        raise PreferenceArmsError("diagnosis receipt round does not match the reservation")


def _validate_receipt_binding(receipt: dict[str, Any], expectation: ReceiptExpectation) -> None:
    if receipt["staging_dir"] != str(expectation.staging_dir):
        raise PreferenceArmsError(
            "diagnosis receipt staging directory does not match the reservation"
        )
    if not _is_bound_reservation_token(receipt, expectation.reservation_token):
        raise PreferenceArmsError("diagnosis receipt token does not match the reservation")


def _is_expected_entry_name(name: Any, expected_name: str) -> bool:
    if not isinstance(name, str):
        return False
    if Path(name).name != name:
        return False
    return name == expected_name


def _is_valid_digest(digest: Any) -> bool:
    if not isinstance(digest, str):
        return False
    return re.fullmatch(r"[0-9a-f]{64}", digest) is not None


def _entry_fields(entry: Any, index: int) -> tuple[Any, Any, Any]:
    if not isinstance(entry, dict) or set(entry) != {"name", "bytes", "sha256"}:
        raise PreferenceArmsError(f"diagnosis receipt entry {index + 1} has invalid keys")
    return entry["name"], entry["bytes"], entry["sha256"]


def _is_valid_byte_count(byte_count: Any) -> bool:
    if type(byte_count) is not int:
        return False
    return byte_count >= 1


def _validated_entry(entry: Any, index: int, expected_name: str) -> tuple[str, int, str]:
    name, byte_count, digest = _entry_fields(entry, index)
    if not _is_expected_entry_name(name, expected_name):
        raise PreferenceArmsError(f"diagnosis receipt entry {index + 1} has invalid name")
    if not _is_valid_byte_count(byte_count):
        raise PreferenceArmsError(f"diagnosis receipt entry {name!r} has invalid byte count")
    if not _is_valid_digest(digest):
        raise PreferenceArmsError(f"diagnosis receipt entry {name!r} has invalid SHA-256")
    return name, byte_count, digest


def _validated_receipt_entries(
    receipt: dict[str, Any],
    expected_names: tuple[str, ...],
    expected_count: int,
) -> list[tuple[str, int, str]]:
    entries = receipt["diagnosis_files"]
    if not isinstance(entries, list) or len(entries) != expected_count:
        raise PreferenceArmsError("diagnosis receipt has the wrong number of file entries")
    return [
        _validated_entry(entry, index, expected_names[index])
        for index, entry in enumerate(entries)
    ]


def _reconcile_entry_bytes(root: Path, entry: tuple[str, int, str]) -> None:
    name, byte_count, digest = entry
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


def validate_diagnosis_handoff_receipt(
    artifact_dir: Path,
    expectation: ReceiptExpectation,
) -> dict[str, Any]:
    """Validate one persisted receipt against captured or committed bytes."""

    root = _diagnosis_artifact_root(artifact_dir)
    expected_names = diagnosis_filenames(expectation.round_number, expectation.expected_count)
    receipt_name = diagnosis_receipt_filename(expectation.round_number)
    _require_exact_artifact_set(root, {*expected_names, receipt_name}, expectation.round_number)
    receipt_bytes = _read_regular_artifact(
        root,
        receipt_name,
        label="diagnosis receipt",
        max_bytes=MAX_DIAGNOSIS_BYTES,
    )
    receipt = _strict_json_object(receipt_bytes, label="diagnosis receipt")
    _validate_receipt_identity(receipt, expectation)
    _validate_receipt_binding(receipt, expectation)
    # Every entry name is validated before any diagnosis file is opened, so a
    # forged name cannot cause a read outside the artifact root.
    entries = _validated_receipt_entries(receipt, expected_names, expectation.expected_count)
    for entry in entries:
        _reconcile_entry_bytes(root, entry)
    return receipt
