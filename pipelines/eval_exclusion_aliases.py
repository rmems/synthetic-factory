#!/usr/bin/env python3
"""Offline repository canonicalization from the committed alias cache (#494).

Compose must stay deterministic and offline, so it never asks GitHub where a
renamed or transferred repository went. It reads
``config/eval-exclusion/repo-aliases.json`` (``repo-alias-cache-v1``) instead:
every entry maps one lowercased ``owner/name`` to the canonical
``owner/name`` it resolved to, with the UTC time it was resolved and how.

* ``github_api`` entries were resolved by ``scripts/refresh_repo_aliases.py``
  through ``gh api repos/<owner>/<name>`` (which follows rename and transfer
  redirects) and carry the stable numeric ``github_id``.
* ``reviewed_source_pin`` entries assert a name that a committed, reviewed
  source catalog already pins; they record that evidence path and make no
  network claim.

The cache is closed: every canonical target has its own self-entry, so
resolution is one lookup and never a chain. A name that is not in the cache
is *unresolved* and the caller excludes it; nothing here guesses.
"""

from __future__ import annotations

import re
import sys
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from types import MappingProxyType
from typing import Any, Mapping

if __package__:
    from . import _assert_direct_sibling, _expose_package_sibling

    _assert_direct_sibling("eval_exclusion_aliases")
    from . import eval_exclusion_lists as _lists
    from . import repo_identity as _repo_identity
else:
    getattr(sys.modules.get("pipelines"), "_join_package_sibling", lambda name: None)(
        "eval_exclusion_aliases"
    )
    import eval_exclusion_lists as _lists
    import repo_identity as _repo_identity

ExclusionPolicyError = _lists.ExclusionPolicyError

CACHE_SCHEMA_VERSION = "repo-alias-cache-v1"
METHOD_GITHUB_API = "github_api"
METHOD_REVIEWED_SOURCE_PIN = "reviewed_source_pin"
CACHE_KEYS = frozenset({"schema_version", "updated_at", "entries"})
_ENTRY_BASE_KEYS = frozenset({"name", "canonical", "method", "resolved_at"})
ENTRY_KEYS_BY_METHOD = MappingProxyType({
    METHOD_GITHUB_API: _ENTRY_BASE_KEYS | {"github_id"},
    METHOD_REVIEWED_SOURCE_PIN: _ENTRY_BASE_KEYS | {"evidence"},
})
TIMESTAMP_SHAPE = "YYYY-MM-DDTHH:MM:SSZ"
_TIMESTAMP_RE = re.compile(r"[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}Z", re.ASCII)
REASON_GITHUB_ID_MISMATCH = "alias_cache.github_id_mismatch"


@dataclass(frozen=True)
class AliasCache:
    """A validated alias cache, bound to the exact bytes it was read from."""

    canonical_by_name: Mapping[str, str]
    updated_at: str
    sha256: str

    def resolve(self, name: str) -> str | None:
        """Return the canonical ``owner/name`` for a canonical-spelled name, or ``None``."""

        return self.canonical_by_name.get(name)

    def is_alias(self, name: str) -> bool:
        """Whether ``name`` is a cached old name that resolves elsewhere."""

        canonical = self.canonical_by_name.get(name)
        return canonical is not None and canonical != name


def format_timestamp(moment: datetime) -> str:
    """Render one aware datetime as the cache's second-precision UTC form."""

    utc = moment.astimezone(UTC).replace(microsecond=0)
    return utc.isoformat().replace("+00:00", "Z")


def parse_timestamp(value: Any, where: str) -> datetime:
    """Parse one second-precision UTC ``YYYY-MM-DDTHH:MM:SSZ`` timestamp."""

    if not isinstance(value, str):
        raise ExclusionPolicyError(f"{where} must be a UTC timestamp string")
    if _TIMESTAMP_RE.fullmatch(value) is None:
        raise ExclusionPolicyError(f"{where} must match {TIMESTAMP_SHAPE}: {value!r}")
    try:
        return datetime.fromisoformat(value)
    except ValueError as exc:
        raise ExclusionPolicyError(f"{where} must match {TIMESTAMP_SHAPE}: {exc}") from exc


def _canonical_field(entry: Mapping[str, Any], key: str, where: str) -> str:
    value = entry[key]
    if not _repo_identity.is_canonical_repo(value):
        raise ExclusionPolicyError(f"{where}.{key} must be canonical lowercase owner/name")
    return value


def is_positive_id(value: Any) -> bool:
    """A GitHub repository id: a positive ``int`` that is not a ``bool``."""

    return isinstance(value, int) and not isinstance(value, bool) and value > 0


def _require_github_id(entry: Mapping[str, Any], where: str) -> None:
    if not is_positive_id(entry["github_id"]):
        raise ExclusionPolicyError(f"{where}.github_id must be a positive integer")


def _require_evidence(entry: Mapping[str, Any], where: str) -> None:
    _lists.require_text(entry["evidence"], f"{where}.evidence")


_EVIDENCE_CHECK_BY_METHOD = MappingProxyType({
    METHOD_GITHUB_API: _require_github_id,
    METHOD_REVIEWED_SOURCE_PIN: _require_evidence,
})


def _method_evidence(entry: Mapping[str, Any], where: str) -> None:
    _EVIDENCE_CHECK_BY_METHOD[entry["method"]](entry, where)


def _has_known_method(entry: Any) -> bool:
    return isinstance(entry, dict) and entry.get("method") in ENTRY_KEYS_BY_METHOD


def _validated_entry(entry: Any, where: str) -> tuple[str, str, datetime]:
    if not _has_known_method(entry):
        raise ExclusionPolicyError(
            f"{where} must be an object whose method is one of {sorted(ENTRY_KEYS_BY_METHOD)}"
        )
    _lists.require_exact_keys(entry, ENTRY_KEYS_BY_METHOD[entry["method"]], where)
    name = _canonical_field(entry, "name", where)
    canonical = _canonical_field(entry, "canonical", where)
    _method_evidence(entry, where)
    return name, canonical, parse_timestamp(entry["resolved_at"], f"{where}.resolved_at")


def _is_api_alias(name: str, canonical: str, github_id: Any) -> bool:
    """An old name (not a self-entry) that was resolved through the GitHub API."""

    return name != canonical and github_id is not None


def _require_one_identity(
    canonical_by_name: Mapping[str, str], github_id_by_name: Mapping[str, Any], where: str
) -> None:
    """An API-resolved alias must name the same GitHub repository as its target.

    A cached old name whose numeric id differs from its target's self-entry
    points at a different (for example reused) repository, so a list entry for
    the real target would not catch records filed under that name.
    """

    for name, canonical in canonical_by_name.items():
        alias_id = github_id_by_name.get(name)
        if not _is_api_alias(name, canonical, alias_id):
            continue
        target_id = github_id_by_name.get(canonical)
        if target_id != alias_id:
            raise ExclusionPolicyError(
                f"{where}: {REASON_GITHUB_ID_MISMATCH}: {name!r} (github_id {alias_id}) "
                f"resolves to {canonical!r} (github_id {target_id})"
            )


def _require_closed(canonical_by_name: Mapping[str, str], where: str) -> None:
    for name, canonical in canonical_by_name.items():
        if canonical_by_name.get(canonical) != canonical:
            raise ExclusionPolicyError(
                f"{where}: {name!r} resolves to {canonical!r}, which has no self-entry"
            )


@dataclass
class _EntryIndex:
    """What the entries of one cache say, collected in document order."""

    names: list[str]
    canonical_by_name: dict[str, str]
    github_id_by_name: dict[str, Any]


def _validated_cache_header(body: Mapping[str, Any], where: str) -> datetime:
    if body["schema_version"] != CACHE_SCHEMA_VERSION:
        raise ExclusionPolicyError(f"{where}.schema_version must be {CACHE_SCHEMA_VERSION!r}")
    updated_at = parse_timestamp(body["updated_at"], f"{where}.updated_at")
    if not isinstance(body["entries"], list):
        raise ExclusionPolicyError(f"{where}.entries must be a list")
    return updated_at


def _index_entries(entries: list[Any], updated_at: datetime, where: str) -> _EntryIndex:
    index = _EntryIndex([], {}, {})
    for position, entry in enumerate(entries):
        entry_where = f"{where}.entries[{position}]"
        name, canonical, resolved_at = _validated_entry(entry, entry_where)
        if resolved_at > updated_at:
            raise ExclusionPolicyError(f"{entry_where} postdates updated_at")
        index.names.append(name)
        index.canonical_by_name[name] = canonical
        index.github_id_by_name[name] = entry.get("github_id")
    return index


def _require_sorted_names(names: list[str], where: str) -> None:
    if names != sorted(set(names)):
        raise ExclusionPolicyError(f"{where}.entries must be sorted by unique name")


def validate_cache_document(document: Any, sha256: str, where: str) -> AliasCache:
    """Validate one alias-cache document; the result resolves in one lookup."""

    body = _lists.require_exact_keys(document, CACHE_KEYS, where)
    updated_at = _validated_cache_header(body, where)
    index = _index_entries(body["entries"], updated_at, where)
    _require_sorted_names(index.names, where)
    _require_closed(index.canonical_by_name, where)
    _require_one_identity(index.canonical_by_name, index.github_id_by_name, where)
    return AliasCache(MappingProxyType(index.canonical_by_name), body["updated_at"], sha256)


def load_cache(path: Path) -> AliasCache:
    """Load the alias cache from ``path``, failing closed."""

    document, payload = _lists.read_canonical_document(path, "repo alias cache")
    return validate_cache_document(document, _lists.sha256_hex(payload), str(path))


if __package__:
    _expose_package_sibling(__name__)
