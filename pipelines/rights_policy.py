#!/usr/bin/env python3
"""Strict loading and semantic validation for rights-policy v1."""

from __future__ import annotations

import sys
from itertools import product
from pathlib import Path
from types import MappingProxyType
from typing import NamedTuple

if __package__:
    from . import _assert_direct_sibling, _expose_package_sibling

    _assert_direct_sibling("rights_policy")
    from . import rights_mapping as _rights_mapping
    from .rights_policy_profiles import validate_policy_document as _validate_policy_document
else:
    getattr(sys.modules.get("pipelines"), "_join_package_sibling", lambda name: None)(
        "rights_policy"
    )
    import rights_mapping as _rights_mapping
    from rights_policy_profiles import validate_policy_document as _validate_policy_document


CANONICAL_PROVIDERS = _rights_mapping.CANONICAL_PROVIDERS
CHANNELS = _rights_mapping.CHANNELS
EVIDENCE_STATUSES = _rights_mapping.EVIDENCE_STATUSES
EVIDENCE_STATUS_FIELDS = _rights_mapping.EVIDENCE_STATUS_FIELDS
HOSTED_FRONTIER_PROFILE_ID = _rights_mapping.HOSTED_FRONTIER_PROFILE_ID
INTENDED_USES = _rights_mapping.INTENDED_USES
MAPPING_PATH = _rights_mapping.MAPPING_PATH
MAPPING_VERSION = _rights_mapping.MAPPING_VERSION
MAX_RIGHTS_JSON_BYTES = _rights_mapping.MAX_RIGHTS_JSON_BYTES
POLICY_DOCUMENT_TYPE = _rights_mapping.POLICY_DOCUMENT_TYPE
POLICY_VERSION = _rights_mapping.POLICY_VERSION
PROJECT_TRAINING_POLICIES = _rights_mapping.PROJECT_TRAINING_POLICIES
REQUIRED_PROFILE_IDS = _rights_mapping.REQUIRED_PROFILE_IDS
UNKNOWN_PROVENANCE_PROFILE_ID = _rights_mapping.UNKNOWN_PROVENANCE_PROFILE_ID
RightsPolicyError = _rights_mapping.RightsPolicyError
freeze_json = _rights_mapping.freeze_json
parse_strict_json_bytes = _rights_mapping.parse_strict_json_bytes
policy_error = _rights_mapping.policy_error
protect_frozen_slots = _rights_mapping.protect_frozen_slots
reject_unpaired_surrogates = _rights_mapping.reject_unpaired_surrogates
require_nonempty_string = _rights_mapping.require_nonempty_string
require_rights_json_size = _rights_mapping.require_rights_json_size
require_unique_strings = _rights_mapping.require_unique_strings
sha256_digest = _rights_mapping.sha256_digest


_POLICY_LABEL = "rights policy"


def _validate_policy_unicode(document: object, where: str) -> None:
    try:
        reject_unpaired_surrogates(document)
    except ValueError as exc:
        raise RightsPolicyError(
            f"{where}: invalid rights policy Unicode: {exc}"
        ) from exc


def validate_rights_policy(document: object, *, where: str = _POLICY_LABEL) -> dict:
    """Validate policy identity, catalogues, profiles, and authorizing rules."""
    _validate_policy_unicode(document, where)
    return _validate_policy_document(document, where)


def load_rights_policy_bytes(payload: bytes, *, where: str = "rights policy bytes") -> dict:
    """Strictly decode and validate rights-policy JSON bytes."""
    if not isinstance(payload, bytes):
        raise policy_error(where, "policy input must be bytes")
    require_rights_json_size(payload, where=where)
    try:
        document = parse_strict_json_bytes(payload)
    except (ValueError, RecursionError) as exc:
        raise RightsPolicyError(f"{where}: invalid rights policy JSON: {exc}") from exc
    return validate_rights_policy(document, where=where)


def _load_rights_policy(path: Path) -> tuple[dict, bytes]:
    try:
        payload = path.read_bytes()
    except (OSError, ValueError) as exc:
        raise RightsPolicyError(f"{path}: rights policy is unreadable: {exc}") from exc
    return load_rights_policy_bytes(payload, where=str(path)), payload


def load_rights_policy(path: str | Path | None = None) -> dict:
    """Load an explicit policy path, failing closed on bytes or semantics."""
    try:
        policy_path = Path(path) if path is not None else MAPPING_PATH
    except TypeError as exc:
        raise policy_error(_POLICY_LABEL, "policy path must be string or Path") from exc
    document, _ = _load_rights_policy(policy_path)
    return document


class _EvidenceStatuses(NamedTuple):
    research_retention_status: str
    research_evaluation_status: str
    redistribution_status: str
    provider_training_status: str
    weight_publication_status: str


class RightsAuthorization(NamedTuple):  # noqa: D203,D211
    """One fully compiled verdict containing no mutable policy nodes."""

    intended_use: str
    project_training_policy: str
    evidence_statuses: _EvidenceStatuses
    reason_codes: tuple[str, ...]

    @property
    def research_retention_status(self) -> str:
        """Return the sealed research-retention evidence status."""
        return self.evidence_statuses.research_retention_status

    @property
    def research_evaluation_status(self) -> str:
        """Return the sealed research-evaluation evidence status."""
        return self.evidence_statuses.research_evaluation_status

    @property
    def redistribution_status(self) -> str:
        """Return the sealed redistribution evidence status."""
        return self.evidence_statuses.redistribution_status

    @property
    def provider_training_status(self) -> str:
        """Return the sealed provider-training evidence status."""
        return self.evidence_statuses.provider_training_status

    @property
    def weight_publication_status(self) -> str:
        """Return the sealed weight-publication evidence status."""
        return self.evidence_statuses.weight_publication_status


def _compile_authorizations(document: dict) -> MappingProxyType:
    profiles = {profile["id"]: profile for profile in document["profiles"]}
    compiled = {}
    for rule in document["rules"]:
        profile = profiles[rule["rights_profile_id"]]
        statuses = profile["evidence_statuses"]
        authorization = RightsAuthorization(
            intended_use=rule["intended_use"],
            project_training_policy=rule["project_training_policy"],
            evidence_statuses=_EvidenceStatuses(
                research_retention_status=statuses["research_retention_status"],
                research_evaluation_status=statuses["research_evaluation_status"],
                redistribution_status=statuses["redistribution_status"],
                provider_training_status=statuses["provider_training_status"],
                weight_publication_status=statuses["weight_publication_status"],
            ),
            reason_codes=tuple(rule["reason_codes"]),
        )
        for provider, channel in product(rule["providers"], rule["channels"]):
            compiled[(provider, channel, rule["rights_profile_id"])] = authorization
    return MappingProxyType(compiled)


_RIGHTS_POLICY_DOCUMENT, RIGHTS_POLICY_BYTES = _load_rights_policy(MAPPING_PATH)
RIGHTS_POLICY_SHA256 = sha256_digest(RIGHTS_POLICY_BYTES)
PROVIDERS = frozenset(_RIGHTS_POLICY_DOCUMENT["vocabularies"]["providers"])
RIGHTS_CHANNELS = frozenset(_RIGHTS_POLICY_DOCUMENT["vocabularies"]["channels"])
RIGHTS_PROFILE_IDS = frozenset(
    profile["id"] for profile in _RIGHTS_POLICY_DOCUMENT["profiles"]
)
RIGHTS_AUTHORIZATIONS = _compile_authorizations(_RIGHTS_POLICY_DOCUMENT)
REASON_CODES = frozenset(item["id"] for item in _RIGHTS_POLICY_DOCUMENT["reason_codes"])
RIGHTS_POLICY = freeze_json(_RIGHTS_POLICY_DOCUMENT)


if __package__:
    _expose_package_sibling(__name__)
