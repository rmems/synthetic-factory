#!/usr/bin/env python3
"""Where a record names a public source, program, or task the exclusion gate matches.

``code_repair`` records name the upstream at ``scenario.source.upstream.repository``
and the catalog program at ``scenario.source.program_id``. ``real_public_engineering``
records name ``environment.source_repo`` and ``environment.task_id``. Every other
record kind is scanned for nested ``program_id``, ``task_id``, ``repository``,
``source_repo``, and Multi-SWE-bench ``instance_id`` values. An ``instance_id``
``owner__name-issue`` maps to ``owner/name``. Payload repo matches refuse only
when the name is on the eval denylist; unresolved or do-not-train-only names
are not a public-source claim.

A public-source claimant that omits the repository still yields an identity
(with ``repo=None``), so the gate treats it as unresolved instead of letting
it through. A payload with none of those fields is ungoverned.
"""

from __future__ import annotations

import sys
from typing import Any, Mapping

if __package__:
    from . import _assert_direct_sibling, _expose_package_sibling

    _assert_direct_sibling("eval_exclusion_subject")
    from .eval_exclusion_policy import SourceIdentity
    from .record_kind import classify_kind
else:
    getattr(sys.modules.get("pipelines"), "_join_package_sibling", lambda name: None)(
        "eval_exclusion_subject"
    )
    from eval_exclusion_policy import SourceIdentity
    from record_kind import classify_kind

REAL_PUBLIC_ENGINEERING = "real_public_engineering"
RULE_CODE_REPAIR = "code_repair_upstream"
RULE_REAL_PUBLIC_ENGINEERING = "real_public_engineering_environment"
RULE_PAYLOAD = "record_payload"
CODE_REPAIR_SOURCE = ("scenario", "source")
REAL_SOURCE_KIND_LOCATIONS = (("source_kind",), ("provenance", "source_kind"))
PROGRAM_KEYS = frozenset({"program_id"})
TASK_KEYS = frozenset({"task_id"})
REPO_KEYS = frozenset({"repository", "source_repo"})
INSTANCE_KEYS = frozenset({"instance_id"})


def _at(record: Any, path: tuple[str, ...]) -> Any:
    current = record
    for key in path:
        if not isinstance(current, Mapping):
            return None
        current = current.get(key)
    return current


def _text(value: Any) -> str | None:
    return value if isinstance(value, str) else None


def _code_repair_identity(record: Mapping[str, Any]) -> SourceIdentity:
    source = _at(record, CODE_REPAIR_SOURCE)
    return SourceIdentity(
        repo=_at(source, ("upstream", "repository")),
        program_id=_text(_at(source, ("program_id",))),
        base_commit=_text(_at(source, ("upstream", "commit"))),
    )


def _real_public_identity(record: Mapping[str, Any]) -> SourceIdentity:
    return SourceIdentity(
        repo=_at(record, ("environment", "source_repo")),
        task_id=_text(_at(record, ("environment", "task_id"))),
        base_commit=_text(_at(record, ("oracle", "repo_commit"))),
    )


def _claims_real_public_engineering(record: Mapping[str, Any]) -> bool:
    return any(_at(record, path) == REAL_PUBLIC_ENGINEERING for path in REAL_SOURCE_KIND_LOCATIONS)


def _named_strings_in_mapping(node: Mapping[str, Any], names: frozenset[str]) -> list[str]:
    return [value for key, value in node.items() if key in names and isinstance(value, str)]


def _walk_children(node: Any) -> list[Any]:
    if isinstance(node, Mapping):
        return list(node.values())
    if isinstance(node, (list, tuple)):
        return list(node)
    return []


def _strings_named(record: Mapping[str, Any], names: frozenset[str]) -> tuple[str, ...]:
    found: list[str] = []
    stack: list[Any] = [record]
    while stack:
        node = stack.pop()
        if isinstance(node, Mapping):
            found.extend(_named_strings_in_mapping(node, names))
        stack.extend(_walk_children(node))
    return tuple(dict.fromkeys(found))


def repo_from_instance_id(instance_id: str) -> str | None:
    """Map a Multi-SWE-bench ``owner__name-issue`` id to ``owner/name``."""

    owner, sep, rest = instance_id.partition("__")
    name, dash, issue = rest.rpartition("-")
    if not all((owner, sep, name, dash, issue)):
        return None
    return f"{owner}/{name}"


def _mapped_instance_repos(record: Mapping[str, Any]) -> tuple[str, ...]:
    mapped = []
    for instance_id in _strings_named(record, INSTANCE_KEYS):
        repo = repo_from_instance_id(instance_id)
        if repo is not None:
            mapped.append(repo)
    return tuple(mapped)


def _payload_repos(record: Mapping[str, Any]) -> tuple[str, ...]:
    names = list(_strings_named(record, REPO_KEYS))
    names.extend(_mapped_instance_repos(record))
    return tuple(dict.fromkeys(names))


def _payload_identities(record: Mapping[str, Any]) -> list[tuple[str, SourceIdentity]]:
    identities = [SourceIdentity(None, program_id=program_id)
                  for program_id in _strings_named(record, PROGRAM_KEYS)]
    identities.extend(SourceIdentity(None, task_id=task_id)
                      for task_id in _strings_named(record, TASK_KEYS))
    identities.extend(SourceIdentity(repo) for repo in _payload_repos(record))
    return [(RULE_PAYLOAD, identity) for identity in identities]


def source_identities(record: Any) -> list[tuple[str, SourceIdentity]]:
    """Every ``(rule, identity)`` the exclusion gate must evaluate for one record."""

    if not isinstance(record, Mapping):
        return []
    if classify_kind(record) == "code_repair":
        return [(RULE_CODE_REPAIR, _code_repair_identity(record))]
    if _claims_real_public_engineering(record):
        return [(RULE_REAL_PUBLIC_ENGINEERING, _real_public_identity(record))]
    return _payload_identities(record)


def source_identity(record: Any) -> tuple[str, SourceIdentity] | None:
    """Return ``(rule, identity)`` for a governed record, else ``None``."""

    found = source_identities(record)
    return found[0] if found else None


def requires_repo(rule: str) -> bool:
    """Public-source claimants fail closed on a missing or unresolved repository."""

    return rule != RULE_PAYLOAD


if __package__:
    _expose_package_sibling(__name__)
