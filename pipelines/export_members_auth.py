#!/usr/bin/env python3
"""Digest and entry-count authentication for COMPOSE member descriptors."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable

from export_contract import ExportError
from export_members_jsonl import lf_jsonl_documents
from export_members_read import read_exact_regular_file


_ReadExactRegularFile = Callable[[Path, str, str], tuple[Path, bytes]]
_ParseJsonlDocuments = Callable[[bytes, str], list[Any]]


@dataclass(frozen=True)
class AuthenticationRequest:
    """One descriptor coordinate to authenticate."""

    curated_root: Path
    summary: dict[str, Any]
    key: str
    expected_path: str


@dataclass(frozen=True)
class AuthenticationDependencies:
    """Call-time filesystem and JSONL boundaries for authentication."""

    read_file: _ReadExactRegularFile
    parse_documents: _ParseJsonlDocuments


def _required_descriptor(summary: dict[str, Any], key: str) -> dict[str, Any]:
    """Return one object-valued descriptor from COMPOSE.json."""

    descriptor = summary.get(key)
    if not isinstance(descriptor, dict):
        raise ExportError(f"COMPOSE.json: {key} descriptor must be an object")
    return descriptor


def _require_descriptor_path(
    descriptor: dict[str, Any], key: str, expected_path: str
) -> None:
    """Require a descriptor to name its one contract-defined member path."""

    actual_path = descriptor.get("path")
    if actual_path != expected_path:
        raise ExportError(
            f"COMPOSE.json: {key} path must be {expected_path!r}, "
            f"got {actual_path!r}"
        )


def _descriptor_payload(
    curated_root: Path,
    descriptor: dict[str, Any],
    key: str,
    read_file: _ReadExactRegularFile,
) -> bytes:
    """Capture one descriptor's exact member bytes."""

    _path, payload = read_file(
        curated_root, descriptor["path"], f"COMPOSE {key}"
    )
    return payload


def _require_descriptor_digest(
    descriptor: dict[str, Any], payload: bytes, key: str
) -> None:
    """Bind the descriptor digest to the bytes just captured."""

    digest = hashlib.sha256(payload).hexdigest()
    if descriptor.get("sha256") != digest:
        raise ExportError(f"COMPOSE.json: {key} digest mismatch")


def _descriptor_entries(descriptor: dict[str, Any], key: str) -> int:
    """Return one nonnegative, non-boolean entry count."""

    entries = descriptor.get("entries")
    if isinstance(entries, bool):
        raise ExportError(f"COMPOSE.json: {key}.entries must be nonnegative")
    if not isinstance(entries, int):
        raise ExportError(f"COMPOSE.json: {key}.entries must be nonnegative")
    if entries < 0:
        raise ExportError(f"COMPOSE.json: {key}.entries must be nonnegative")
    return entries


def _require_entry_count(
    descriptor: dict[str, Any], documents: list[Any], key: str
) -> None:
    """Bind a descriptor's declared count to its authenticated documents."""

    entries = _descriptor_entries(descriptor, key)
    if entries != len(documents):
        raise ExportError(
            f"COMPOSE.json: {key} entry count {entries} != {len(documents)}"
        )


def authenticated_descriptor(
    curated_root: Path,
    summary: dict[str, Any],
    key: str,
    expected_path: str,
) -> tuple[dict[str, Any], list[Any]]:
    """Authenticate one descriptor's path, bytes, digest, JSON, and count."""
    request = AuthenticationRequest(curated_root, summary, key, expected_path)
    dependencies = AuthenticationDependencies(
        read_exact_regular_file,
        lf_jsonl_documents,
    )
    return authenticate_descriptor(request, dependencies)


def authenticate_descriptor(
    request: AuthenticationRequest,
    dependencies: AuthenticationDependencies,
) -> tuple[dict[str, Any], list[Any]]:
    """Authenticate a request through its explicit call-time dependencies."""

    descriptor = _required_descriptor(request.summary, request.key)
    _require_descriptor_path(descriptor, request.key, request.expected_path)
    payload = _descriptor_payload(
        request.curated_root,
        descriptor,
        request.key,
        dependencies.read_file,
    )
    _require_descriptor_digest(descriptor, payload, request.key)
    documents = dependencies.parse_documents(payload, descriptor["path"])
    _require_entry_count(descriptor, documents, request.key)
    return dict(descriptor), documents
