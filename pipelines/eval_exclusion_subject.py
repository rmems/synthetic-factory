#!/usr/bin/env python3
"""Where a record names its public source repository (#494).

Two record families derive from public repositories today:

* ``code_repair`` (``python-function-repair``) records name the upstream at
  ``scenario.source.upstream.repository`` with its pinned ``commit``, and the
  catalog program at ``scenario.source.program_id``.
* ``real_public_engineering`` records (``actor-provenance-v1``, including
  Operation Prometheus) must name the repository at ``environment.source_repo``
  with the board task at ``environment.task_id``.

``source_identity`` returns ``None`` for every other record: it makes no
public-source claim, so the exclusion gate does not govern it. A record that
does claim public provenance but omits the repository still yields an identity
(with ``repo=None``), so the gate excludes it as unresolved instead of letting
it through.
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
CODE_REPAIR_SOURCE = ("scenario", "source")
REAL_SOURCE_KIND_LOCATIONS = (("source_kind",), ("provenance", "source_kind"))


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


def source_identity(record: Any) -> tuple[str, SourceIdentity] | None:
    """Return ``(rule, identity)`` for a public-source record, else ``None``."""

    if not isinstance(record, Mapping):
        return None
    if classify_kind(record) == "code_repair":
        return RULE_CODE_REPAIR, _code_repair_identity(record)
    if _claims_real_public_engineering(record):
        return RULE_REAL_PUBLIC_ENGINEERING, _real_public_identity(record)
    return None


if __package__:
    _expose_package_sibling(__name__)
