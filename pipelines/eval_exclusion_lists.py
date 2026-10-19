#!/usr/bin/env python3
"""Strict loading of the vendored eval denylist and do-not-train list (#494).

Both lists share one document shape (``eval-exclusion-list-v1``, documented in
``schemas/eval-exclusion-list-v1.schema.json``) and differ only in their
``list`` slot. A list names canonical source repositories plus the
``program_id`` and ``task_id`` keys that the generator-side consumers (#496,
#499) exclude. Every value is matched whole, never by substring.

The loader raises on anything it does not recognise: a missing or unreadable
file, non-canonical bytes, an unknown key, an unsorted or duplicated value, or
a repository spelling that is not canonical ``owner/name``. A ``placeholder``
list must be empty, so a placeholder can never silently carry entries.
"""

from __future__ import annotations

import hashlib
import json
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

if __package__:
    from . import _assert_direct_sibling, _expose_package_sibling

    _assert_direct_sibling("eval_exclusion_lists")
    from . import repo_identity as _repo_identity
    from .exact_json import dumps_exact_json
else:
    getattr(sys.modules.get("pipelines"), "_join_package_sibling", lambda name: None)(
        "eval_exclusion_lists"
    )
    import repo_identity as _repo_identity
    from exact_json import dumps_exact_json

LIST_SCHEMA_VERSION = "eval-exclusion-list-v1"
LIST_EVAL_DENYLIST = "eval_denylist"
LIST_DO_NOT_TRAIN = "do_not_train"
LIST_SLOTS = (LIST_EVAL_DENYLIST, LIST_DO_NOT_TRAIN)
STATUS_PLACEHOLDER = "placeholder"
STATUS_REVIEWED = "reviewed"
LIST_STATUSES = frozenset({STATUS_PLACEHOLDER, STATUS_REVIEWED})
KEY_REPOS = "repos"
KEY_PROGRAM_IDS = "program_ids"
KEY_TASK_IDS = "task_ids"
VALUE_KEYS = (KEY_REPOS, KEY_PROGRAM_IDS, KEY_TASK_IDS)
LIST_KEYS = frozenset({"schema_version", "list", "status", "note", *VALUE_KEYS})
MAX_LIST_BYTES = 8 * 1024 * 1024


class ExclusionPolicyError(RuntimeError):
    """A vendored exclusion list or alias cache is missing or invalid."""


@dataclass(frozen=True)
class ExclusionList:
    """One validated list, bound to the exact bytes it was read from."""

    slot: str
    status: str
    repos: frozenset[str]
    program_ids: frozenset[str]
    task_ids: frozenset[str]
    sha256: str

    def values(self, key: str) -> frozenset[str]:
        """Return the whole values held under one of ``VALUE_KEYS``."""

        if key not in VALUE_KEYS:
            raise ExclusionPolicyError(f"unknown exclusion key {key!r}")
        return getattr(self, key)


def _reject_duplicate_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    document: dict[str, Any] = {}
    for key, value in pairs:
        if key in document:
            raise ValueError(f"duplicate object key {key!r}")
        document[key] = value
    return document


def _reject_number(token: str) -> Any:
    raise ValueError(f"non-integer number {token!r} is not allowed")


def _read_bounded(path: Path, label: str) -> bytes:
    """Read one policy file, refusing an unreadable or oversized one."""

    try:
        payload = path.read_bytes()
    except OSError as exc:
        raise ExclusionPolicyError(f"{label} {path} is unreadable: {exc}") from exc
    if len(payload) > MAX_LIST_BYTES:
        raise ExclusionPolicyError(f"{label} {path} exceeds {MAX_LIST_BYTES} bytes")
    return payload


def _decode_strict(payload: bytes, path: Path, label: str) -> Any:
    """Decode UTF-8 strict JSON: unique keys, integers only, no NaN or Infinity."""

    try:
        return json.loads(
            payload.decode("utf-8"),
            object_pairs_hook=_reject_duplicate_keys,
            parse_constant=_reject_number,
            parse_float=_reject_number,
        )
    except (ValueError, RecursionError) as exc:  # UnicodeDecodeError is a ValueError
        raise ExclusionPolicyError(f"{label} {path} is not strict JSON: {exc}") from exc


def _require_canonical(document: Any, payload: bytes, path: Path, label: str) -> None:
    if payload != canonical_bytes(document):
        raise ExclusionPolicyError(
            f"{label} {path} is not in canonical form; rewrite it with canonical_bytes()"
        )


def read_canonical_document(path: Path, label: str) -> tuple[Any, bytes]:
    """Read strict JSON whose bytes are exactly its canonical exact-JSON form."""

    payload = _read_bounded(path, label)
    document = _decode_strict(payload, path, label)
    _require_canonical(document, payload, path, label)
    return document, payload


def canonical_bytes(document: Any) -> bytes:
    """The one byte form a vendored policy document may take."""

    return (dumps_exact_json(document, indent=2) + "\n").encode("utf-8")


def sha256_hex(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def require_exact_keys(document: Any, expected: frozenset[str], where: str) -> dict[str, Any]:
    if not isinstance(document, dict):
        raise ExclusionPolicyError(f"{where} must be a JSON object")
    if set(document) != expected:
        missing = sorted(expected - set(document))
        extra = sorted(set(document) - expected)
        raise ExclusionPolicyError(f"{where} keys differ: missing {missing}, unexpected {extra}")
    return document


def _is_trimmed_text(value: Any) -> bool:
    """A non-empty string with no leading or trailing whitespace."""

    return isinstance(value, str) and bool(value) and value == value.strip()


def require_text(value: Any, where: str) -> str:
    if not _is_trimmed_text(value):
        raise ExclusionPolicyError(f"{where} must be a non-empty string without edge whitespace")
    return value


def _sorted_unique_strings(value: Any, where: str) -> list[str]:
    if not isinstance(value, list):
        raise ExclusionPolicyError(f"{where} must be a list")
    items = [require_text(item, f"{where}[{index}]") for index, item in enumerate(value)]
    if items != sorted(set(items)):
        raise ExclusionPolicyError(f"{where} must be sorted and free of duplicates")
    return items


def _canonical_repos(value: Any, where: str) -> frozenset[str]:
    repos = _sorted_unique_strings(value, where)
    for repo in repos:
        if not _repo_identity.is_canonical_repo(repo):
            raise ExclusionPolicyError(
                f"{where} holds {repo!r}; entries must be canonical lowercase owner/name"
            )
    return frozenset(repos)


def _validated_header(body: dict[str, Any], slot: str, where: str) -> str:
    """Check the identity fields of one list and return its status."""

    if body["schema_version"] != LIST_SCHEMA_VERSION:
        raise ExclusionPolicyError(f"{where}.schema_version must be {LIST_SCHEMA_VERSION!r}")
    if body["list"] != slot:
        raise ExclusionPolicyError(f"{where}.list must be {slot!r}, not {body['list']!r}")
    if body["status"] not in LIST_STATUSES:
        raise ExclusionPolicyError(f"{where}.status must be one of {sorted(LIST_STATUSES)}")
    require_text(body["note"], f"{where}.note")
    return body["status"]


def validate_list_document(document: Any, slot: str, sha256: str, where: str) -> ExclusionList:
    """Validate one list document and bind it to the slot it was loaded for."""

    body = require_exact_keys(document, LIST_KEYS, where)
    status = _validated_header(body, slot, where)
    values = _list_values(body, where)
    if _placeholder_with_entries(status, values):
        raise ExclusionPolicyError(f"{where}: a placeholder list must not carry entries")
    return ExclusionList(slot, status, *values, sha256)


def _list_values(body: dict[str, Any], where: str) -> tuple[frozenset[str], ...]:
    """The validated ``repos``, ``program_ids`` and ``task_ids`` sets, in that order."""

    return (
        _canonical_repos(body[KEY_REPOS], f"{where}.{KEY_REPOS}"),
        frozenset(_sorted_unique_strings(body[KEY_PROGRAM_IDS], f"{where}.program_ids")),
        frozenset(_sorted_unique_strings(body[KEY_TASK_IDS], f"{where}.task_ids")),
    )


def _placeholder_with_entries(status: str, values: tuple[frozenset[str], ...]) -> bool:
    """A placeholder list that nonetheless names something: never allowed."""

    return status == STATUS_PLACEHOLDER and any(values)


def load_list(path: Path, slot: str) -> ExclusionList:
    """Load one vendored list from ``path`` for ``slot``, failing closed."""

    if slot not in LIST_SLOTS:
        raise ExclusionPolicyError(f"unknown exclusion list slot {slot!r}")
    document, payload = read_canonical_document(path, f"{slot} list")
    return validate_list_document(document, slot, sha256_hex(payload), str(path))


if __package__:
    _expose_package_sibling(__name__)
