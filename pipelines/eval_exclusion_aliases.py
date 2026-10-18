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
TIMESTAMP_FORMAT = "%Y-%m-%dT%H:%M:%SZ"


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


def parse_timestamp(value: Any, where: str) -> datetime:
    """Parse one second-precision UTC ``YYYY-MM-DDTHH:MM:SSZ`` timestamp."""

    if not isinstance(value, str):
        raise ExclusionPolicyError(f"{where} must be a UTC timestamp string")
    try:
        parsed = datetime.strptime(value, TIMESTAMP_FORMAT).replace(tzinfo=UTC)
    except ValueError as exc:
        raise ExclusionPolicyError(f"{where} must match {TIMESTAMP_FORMAT}: {exc}") from exc
    if parsed.strftime(TIMESTAMP_FORMAT) != value:
        raise ExclusionPolicyError(f"{where} is not in canonical timestamp form")
    return parsed


def _canonical_field(entry: Mapping[str, Any], key: str, where: str) -> str:
    value = entry[key]
    if not _repo_identity.is_canonical_repo(value):
        raise ExclusionPolicyError(f"{where}.{key} must be canonical lowercase owner/name")
    return value


def _method_evidence(entry: Mapping[str, Any], where: str) -> None:
    if entry["method"] == METHOD_GITHUB_API:
        github_id = entry["github_id"]
        if isinstance(github_id, bool) or not isinstance(github_id, int) or github_id < 1:
            raise ExclusionPolicyError(f"{where}.github_id must be a positive integer")
    else:
        _lists.require_text(entry["evidence"], f"{where}.evidence")


def _validated_entry(entry: Any, where: str) -> tuple[str, str, datetime]:
    if not isinstance(entry, dict) or entry.get("method") not in ENTRY_KEYS_BY_METHOD:
        raise ExclusionPolicyError(
            f"{where} must be an object whose method is one of {sorted(ENTRY_KEYS_BY_METHOD)}"
        )
    _lists.require_exact_keys(entry, ENTRY_KEYS_BY_METHOD[entry["method"]], where)
    name = _canonical_field(entry, "name", where)
    canonical = _canonical_field(entry, "canonical", where)
    _method_evidence(entry, where)
    return name, canonical, parse_timestamp(entry["resolved_at"], f"{where}.resolved_at")


def _require_closed(canonical_by_name: Mapping[str, str], where: str) -> None:
    for name, canonical in canonical_by_name.items():
        if canonical_by_name.get(canonical) != canonical:
            raise ExclusionPolicyError(
                f"{where}: {name!r} resolves to {canonical!r}, which has no self-entry"
            )


def validate_cache_document(document: Any, sha256: str, where: str) -> AliasCache:
    """Validate one alias-cache document; the result resolves in one lookup."""

    body = _lists.require_exact_keys(document, CACHE_KEYS, where)
    if body["schema_version"] != CACHE_SCHEMA_VERSION:
        raise ExclusionPolicyError(f"{where}.schema_version must be {CACHE_SCHEMA_VERSION!r}")
    updated_at = parse_timestamp(body["updated_at"], f"{where}.updated_at")
    entries = body["entries"]
    if not isinstance(entries, list):
        raise ExclusionPolicyError(f"{where}.entries must be a list")
    canonical_by_name: dict[str, str] = {}
    names: list[str] = []
    for index, entry in enumerate(entries):
        name, canonical, resolved_at = _validated_entry(entry, f"{where}.entries[{index}]")
        if resolved_at > updated_at:
            raise ExclusionPolicyError(f"{where}.entries[{index}] postdates updated_at")
        names.append(name)
        canonical_by_name[name] = canonical
    if names != sorted(set(names)):
        raise ExclusionPolicyError(f"{where}.entries must be sorted by unique name")
    _require_closed(canonical_by_name, where)
    return AliasCache(MappingProxyType(canonical_by_name), body["updated_at"], sha256)


def load_cache(path: Path) -> AliasCache:
    """Load the alias cache from ``path``, failing closed."""

    document, payload = _lists.read_canonical_document(path, "repo alias cache")
    return validate_cache_document(document, _lists.sha256_hex(payload), str(path))


if __package__:
    _expose_package_sibling(__name__)
