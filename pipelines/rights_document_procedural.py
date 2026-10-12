"""Procedural route for public ``rights.json`` schema 0.2.0 documents.

Schema 0.1.0 models hosted-frontier provider routes only.  Schema 0.2.0 adds a
``source_type: procedural`` route for a dataset produced by a procedural
registry row (``python-function-repair-factory``, ``oracle-grounded``).  The
sidecar names the row (``path_id``, ``payload_factory``, ``generator``,
``generator_version``), repeats its ``intended_use``,
``project_training_policy``, ``source_license_evidence``, catalog pins and
``procedural_policy_sha256`` exactly as the loaded registry states them, and
declares the release license and ``training_ready: false``.  A missing, extra,
or disagreeing field raises at load.

The registry is the identity authority here as everywhere else.  The
procedural rows are loaded once at import through ``curate_identity_registry``,
which has already required each row to equal its independently sealed source
policy, and an invalid registry stops the import.  The sidecar grants nothing:
training eligibility stays the registry row plus the fresh replay and
completed-round gates, and publication authority is separate.  Hosted documents
keep schema 0.1.0 and never reach this module.
"""

from __future__ import annotations

import re
import sys
from collections.abc import Mapping
from pathlib import Path
from types import MappingProxyType
from typing import NamedTuple, TypeGuard

if __package__:
    from . import _assert_direct_sibling, _expose_package_sibling

    _assert_direct_sibling("rights_document_procedural")
    from . import rights_document_support as _support
    from .curate_identity_registry import FACTORY_REGISTRY_PATH, FactoryRow, load_registry
    from .rights_mapping import (
        INTENDED_USES,
        PROJECT_TRAINING_POLICIES,
        is_exact_string,
        policy_error,
        require_nonempty_string,
    )
else:
    getattr(sys.modules.get("pipelines"), "_join_package_sibling", lambda name: None)(
        "rights_document_procedural"
    )
    import rights_document_support as _support
    from curate_identity_registry import FACTORY_REGISTRY_PATH, FactoryRow, load_registry
    from rights_mapping import (
        INTENDED_USES,
        PROJECT_TRAINING_POLICIES,
        is_exact_string,
        policy_error,
        require_nonempty_string,
    )


PROCEDURAL_DOCUMENT_SCHEMA_VERSION = "0.2.0"
PROCEDURAL_SOURCE_TYPE = "procedural"
# The Hub license tag the procedural datasets ship under; the release verifier
# requires the card, LICENSE and release-status.json to repeat it.
PROCEDURAL_RELEASE_LICENSES = frozenset({"apache-2.0"})
# Field groups in document order; each group is validated by one step below.
_IDENTITY_FIELDS = ("schema_version", "dataset_id", "policy_source")
_ROW_FIELDS = ("source_type", "path_id")
_ROUTE_FIELDS = ("payload_factory", "generator", "generator_version")
_DECISION_FIELDS = ("intended_use", "project_training_policy")
_EVIDENCE_FIELDS = ("source_license_evidence", "catalog_id")
_REGISTRY_DIGEST_FIELDS = ("catalog_sha256", "programs_sha256", "procedural_policy_sha256")
_RELEASE_FIELDS = ("release_license", "training_ready", "reviewed_at")
PROCEDURAL_REQUIRED_FIELDS = frozenset(
    _IDENTITY_FIELDS + _ROW_FIELDS + _ROUTE_FIELDS + _DECISION_FIELDS
    + _EVIDENCE_FIELDS + _REGISTRY_DIGEST_FIELDS + _RELEASE_FIELDS
)
PROCEDURAL_OPTIONAL_FIELDS = frozenset({"notes"})

# Registry pins are bare lowercase hex, unlike the ``sha256:``-prefixed terms
# snapshots of the hosted route; the document repeats the registry spelling.
_BARE_SHA256_RE = re.compile(r"^[0-9a-f]{64}$", re.ASCII)


class _ProceduralIdentity(NamedTuple):
    schema_version: str
    dataset_id: str
    policy_source: str


class _ProceduralRoute(NamedTuple):
    source_type: str
    path_id: str
    payload_factory: str
    generator: str
    generator_version: str


class _ProceduralDecision(NamedTuple):
    intended_use: str
    project_training_policy: str


class _ProceduralEvidence(NamedTuple):
    source_license_evidence: Mapping[str, str]
    catalog_id: str
    catalog_sha256: str
    programs_sha256: str
    procedural_policy_sha256: str


class _ProceduralRelease(NamedTuple):
    release_license: str
    training_ready: bool
    reviewed_at: str


class ProceduralRightsDocument(NamedTuple):
    """Normalized immutable public rights declaration for a procedural registry row."""

    identity: _ProceduralIdentity
    route: _ProceduralRoute
    decision: _ProceduralDecision
    evidence: _ProceduralEvidence
    release: _ProceduralRelease
    notes: str | None

    def __getattr__(self, name: str) -> object:
        """Expose immutable aggregate fields through a flat API like the hosted route."""
        section_names = {"identity", "route", "decision", "evidence", "release"}
        if name.startswith("__") or name in section_names:
            raise AttributeError(name)
        for section in (self.identity, self.route, self.decision, self.evidence, self.release):
            if hasattr(section, name):
                return getattr(section, name)
        raise AttributeError(name)


def _procedural_registry_rows(path: Path) -> Mapping[str, FactoryRow]:
    """The reviewed procedural rows of the registry at ``path``, keyed by exact ``path_id``."""
    registry = load_registry(path)
    return MappingProxyType(
        {
            path_id: row
            for path_id, row in registry.by_path_id.items()
            if row.source_type == PROCEDURAL_SOURCE_TYPE
        }
    )


PROCEDURAL_REGISTRY_ROWS = _procedural_registry_rows(FACTORY_REGISTRY_PATH)


def declares_procedural_schema(document: object) -> bool:
    """Whether a parsed document routes to the schema 0.2.0 procedural validator."""
    if not isinstance(document, dict):
        return False
    version = document.get("schema_version")
    return is_exact_string(version) and version == PROCEDURAL_DOCUMENT_SCHEMA_VERSION


def _require_procedural_source_type(document: dict[object, object], where: str) -> str:
    source_type = document.get("source_type")
    if not is_exact_string(source_type) or source_type != PROCEDURAL_SOURCE_TYPE:
        raise policy_error(
            where,
            f"schema_version {PROCEDURAL_DOCUMENT_SCHEMA_VERSION} documents must declare "
            f"source_type {PROCEDURAL_SOURCE_TYPE}",
        )
    return source_type


def _registry_value(
    document: dict[str, object], field: str, row: FactoryRow, where: str
) -> str:
    """Require the document's ``field`` to be one exact string repeating the registry row's."""
    value = document[field]
    if not is_exact_string(value) or value != getattr(row, field):
        raise policy_error(where, f"{field} differs from the registry row {row.path_id}")
    return value


def _registry_digest(
    document: dict[str, object], field: str, row: FactoryRow, where: str
) -> str:
    value = document[field]
    if not is_exact_string(value) or _BARE_SHA256_RE.fullmatch(value) is None:
        raise policy_error(where, f"{field} must be lowercase 64 hex")
    return _registry_value(document, field, row, where)


def _is_nonempty_exact_string(value: object) -> bool:
    return is_exact_string(value) and bool(value.strip())


def _is_string_field(item: tuple[object, object]) -> bool:
    name, value = item
    return is_exact_string(name) and _is_nonempty_exact_string(value)


def _is_string_object(value: object) -> TypeGuard[dict[str, str]]:
    """Whether ``value`` is a nonempty object of exact, nonempty string fields."""
    if not isinstance(value, dict) or not value:
        return False
    return all(_is_string_field(item) for item in value.items())


def _exact_string_mapping(value: object, field: str, where: str) -> dict[str, str]:
    """Require a nonempty object whose member names and values are exact nonempty strings."""
    if not _is_string_object(value):
        raise policy_error(where, f"{field} must be an object of nonempty string fields")
    return dict(value)


def _is_json_false(value: object) -> bool:
    """Only the JSON boolean ``false``: neither ``0`` nor ``null`` nor a string counts."""
    return isinstance(value, bool) and not value


def _validate_identity(document: dict[str, object], where: str) -> _ProceduralIdentity:
    return _ProceduralIdentity(
        _support.closed_value(
            document["schema_version"],
            "schema_version",
            frozenset({PROCEDURAL_DOCUMENT_SCHEMA_VERSION}),
            where,
        ),
        _support.require_dataset_id(document["dataset_id"], where),
        require_nonempty_string(document["policy_source"], "policy_source", where=where),
    )


def _registry_row(document: dict[str, object], where: str) -> FactoryRow:
    path_id = document["path_id"]
    row = PROCEDURAL_REGISTRY_ROWS.get(path_id) if is_exact_string(path_id) else None
    if row is None:
        raise policy_error(where, "path_id does not name a procedural registry row")
    return row


def _validate_route(
    document: dict[str, object], source_type: str, where: str
) -> tuple[_ProceduralRoute, FactoryRow]:
    row = _registry_row(document, where)
    bound = [_registry_value(document, field, row, where) for field in _ROUTE_FIELDS]
    return _ProceduralRoute(source_type, row.path_id, *bound), row


def _validate_decision(
    document: dict[str, object], row: FactoryRow, where: str
) -> _ProceduralDecision:
    intended_use = _support.closed_value(
        document["intended_use"], "intended_use", INTENDED_USES, where
    )
    training_policy = _support.closed_value(
        document["project_training_policy"],
        "project_training_policy",
        PROJECT_TRAINING_POLICIES,
        where,
    )
    if intended_use != row.intended_use or training_policy != row.project_training_policy:
        raise policy_error(
            where,
            f"public rights decision differs from the registry row {row.path_id}: "
            f"received {intended_use}/{training_policy}; registry row states "
            f"{row.intended_use}/{row.project_training_policy}",
        )
    return _ProceduralDecision(intended_use, training_policy)


def _validate_evidence(
    document: dict[str, object], row: FactoryRow, where: str
) -> _ProceduralEvidence:
    evidence = _exact_string_mapping(
        document["source_license_evidence"], "source_license_evidence", where
    )
    if evidence != dict(row.source_license_evidence or {}):
        raise policy_error(
            where, f"source_license_evidence differs from the registry row {row.path_id}"
        )
    catalog_id = _registry_value(document, "catalog_id", row, where)
    digests = [_registry_digest(document, field, row, where) for field in _REGISTRY_DIGEST_FIELDS]
    return _ProceduralEvidence(MappingProxyType(evidence), catalog_id, *digests)


def _validate_release(document: dict[str, object], where: str) -> _ProceduralRelease:
    release_license = _support.closed_value(
        document["release_license"], "release_license", PROCEDURAL_RELEASE_LICENSES, where
    )
    if not _is_json_false(document["training_ready"]):
        raise policy_error(
            where,
            "training_ready must be the JSON boolean false; "
            "a rights document never certifies training readiness",
        )
    reviewed_at = _support.calendar_date(document["reviewed_at"], "reviewed_at", where)
    return _ProceduralRelease(release_license, False, reviewed_at)


def validate_procedural_document(
    document: object, *, where: str = "rights document"
) -> ProceduralRightsDocument:
    """Validate one parsed schema 0.2.0 procedural sidecar against the loaded registry."""
    if not isinstance(document, dict):
        raise policy_error(where, "rights document must be an object")
    source_type = _require_procedural_source_type(document, where)
    checked = _support.exact_document(
        document, PROCEDURAL_REQUIRED_FIELDS, PROCEDURAL_OPTIONAL_FIELDS, where
    )
    _support.reject_document_surrogates(checked, where)
    identity = _validate_identity(checked, where)
    route, row = _validate_route(checked, source_type, where)
    decision = _validate_decision(checked, row, where)
    evidence = _validate_evidence(checked, row, where)
    release = _validate_release(checked, where)
    notes = (
        require_nonempty_string(checked["notes"], "notes", where=where)
        if "notes" in checked
        else None
    )
    return ProceduralRightsDocument(
        identity=identity,
        route=route,
        decision=decision,
        evidence=evidence,
        release=release,
        notes=notes,
    )


if __package__:
    _expose_package_sibling(__name__)
