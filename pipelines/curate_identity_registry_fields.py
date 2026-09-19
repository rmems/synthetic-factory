#!/usr/bin/env python3
"""Hosted-row field rules for the identity factory registry.

The tables spell refusal order: ``_apply_field_rules`` raises on the first
rule that does not hold. ``curate_identity_registry`` composes these with
the reviewed-rights and kind-contract checks.
"""

from __future__ import annotations

import sys
from pathlib import PurePosixPath
from typing import Any, Callable, Mapping, NamedTuple

if __package__:
    from . import _assert_direct_sibling, _expose_package_sibling

    _assert_direct_sibling("curate_identity_registry_fields")
    from .curate_identity_json import IdentityCurationError
    from .record_kind import PREFERENCE_SIDE_KINDS, SUPPORTED_RECORD_KINDS
    from .rights_mapping import (
        HOSTED_FRONTIER_PROFILE_ID,
        INTENDED_USES,
        PROJECT_TRAINING_POLICIES,
    )
    from .rights_policy import (
        PROVIDERS,
        RIGHTS_CHANNELS,
        RIGHTS_PROFILE_IDS,
    )
else:
    getattr(sys.modules.get("pipelines"), "_join_package_sibling", lambda name: None)(
        "curate_identity_registry_fields"
    )
    from curate_identity_json import IdentityCurationError
    from record_kind import PREFERENCE_SIDE_KINDS, SUPPORTED_RECORD_KINDS
    from rights_mapping import (
        HOSTED_FRONTIER_PROFILE_ID,
        INTENDED_USES,
        PROJECT_TRAINING_POLICIES,
    )
    from rights_policy import (
        PROVIDERS,
        RIGHTS_CHANNELS,
        RIGHTS_PROFILE_IDS,
    )


# ---------------------------------------------------------------------------
# Field rules: ``(field, holds, message, detail)``; ``message`` is a template
# over ``{index}`` and ``{detail}``.  Rules run in table order and the first
# one that does not hold raises, so the tables spell the refusal order.
# ---------------------------------------------------------------------------


class FieldRule(NamedTuple):
    field: str
    holds: Callable[[Any], bool]
    message: str
    detail: Callable[[Any], Any] = repr


def _apply_field_rules(raw: Mapping[str, Any], rules: tuple[FieldRule, ...], index: int) -> None:
    """Raise the first rule ``raw`` fails, formatted for ``factories[index]``."""

    for field, holds, message, detail in rules:
        value = raw[field]
        if not holds(value):
            raise IdentityCurationError(message.format(index=index, detail=detail(value)))


def _is_nonblank_string(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _has_path_separator_or_nul(value: str) -> bool:
    return "/" in value or "\\" in value or "\x00" in value


def _is_single_posix_part(value: str) -> bool:
    return PurePosixPath(value).parts == (value,)


def _is_directory_component(value: str) -> bool:
    if value != value.strip() or value in {".", ".."}:
        return False
    if _has_path_separator_or_nul(value):
        return False
    return _is_single_posix_part(value)


def _in_vocabulary(vocabulary: Any) -> Callable[[Any], bool]:
    def holds(value: Any) -> bool:
        return isinstance(value, str) and value in vocabulary

    return holds


def _is_nonempty_list(value: Any) -> bool:
    return isinstance(value, list) and bool(value)


def _all_nonempty_strings(value: list[Any]) -> bool:
    return all(isinstance(item, str) and item for item in value)


def _all_strings(value: list[Any]) -> bool:
    return all(isinstance(item, str) for item in value)


def _no_duplicates(value: list[Any]) -> bool:
    return len(value) == len(set(value))


def _all_supported(supported: frozenset[str]) -> Callable[[list[str]], bool]:
    def holds(value: list[str]) -> bool:
        return not set(value) - supported

    return holds


def _unsupported(supported: frozenset[str]) -> Callable[[list[str]], list[str]]:
    def detail(value: list[str]) -> list[str]:
        return sorted(set(value) - supported)

    return detail


def _is_null_or_string(value: Any) -> bool:
    return value is None or isinstance(value, str)


def _is_string_list(value: Any) -> bool:
    return isinstance(value, list) and all(isinstance(item, str) for item in value)


_PATH_RULES: tuple[FieldRule, ...] = (
    FieldRule("path_id", _is_nonblank_string, "factories[{index}].path_id must be a string"),
    FieldRule(
        "path_id",
        _is_directory_component,
        "factories[{index}].path_id must be exactly one normalized directory component",
    ),
    FieldRule(
        "payload_factory",
        _is_nonblank_string,
        "factories[{index}].payload_factory must be a string",
    ),
)

_RIGHTS_VOCABULARY_BASE_RULES: tuple[FieldRule, ...] = (
    FieldRule("provider", _in_vocabulary(PROVIDERS), "factories[{index}] has unknown provider"),
    FieldRule("channel", _in_vocabulary(RIGHTS_CHANNELS), "factories[{index}] has unknown channel"),
    FieldRule(
        "rights_profile_id",
        _in_vocabulary(RIGHTS_PROFILE_IDS),
        "factories[{index}] has unknown rights_profile_id",
    ),
    FieldRule(
        "intended_use",
        _in_vocabulary(INTENDED_USES),
        "factories[{index}] has unknown intended_use",
    ),
    FieldRule(
        "project_training_policy",
        _in_vocabulary(PROJECT_TRAINING_POLICIES),
        "factories[{index}] has unknown project_training_policy",
    ),
)

_HOSTED_PROFILE_RULE = FieldRule(
    "rights_profile_id",
    HOSTED_FRONTIER_PROFILE_ID.__eq__,
    f"factories[{{index}}].rights_profile_id must be {HOSTED_FRONTIER_PROFILE_ID}",
)

_RIGHTS_VOCABULARY_RULES: tuple[FieldRule, ...] = (
    *_RIGHTS_VOCABULARY_BASE_RULES,
    _HOSTED_PROFILE_RULE,
)
_MODEL_CHANNEL_RIGHTS_RULES = _RIGHTS_VOCABULARY_BASE_RULES

_SHAPE_RULES: tuple[FieldRule, ...] = (
    FieldRule(
        "record_kinds",
        _is_nonempty_list,
        "factories[{index}].record_kinds must be a non-empty list",
    ),
    FieldRule(
        "record_kinds",
        _all_nonempty_strings,
        "factories[{index}].record_kinds must be strings",
    ),
    FieldRule(
        "record_kinds",
        _no_duplicates,
        "factories[{index}].record_kinds must not contain duplicates",
    ),
    FieldRule(
        "record_kinds",
        _all_supported(SUPPORTED_RECORD_KINDS),
        "factories[{index}].record_kinds contains unsupported kinds: {detail}",
        _unsupported(SUPPORTED_RECORD_KINDS),
    ),
    FieldRule(
        "identity_authoritative",
        lambda value: isinstance(value, bool),
        "factories[{index}].identity_authoritative must be a boolean",
    ),
    FieldRule(
        "publication_target",
        _is_null_or_string,
        "factories[{index}].publication_target must be null or a string",
    ),
    FieldRule(
        "training_ready_policy",
        {"never", "compose_eligible"}.__contains__,
        "factories[{index}].training_ready_policy must be never or compose_eligible",
    ),
    FieldRule(
        "allowed_curation_lanes",
        _is_string_list,
        "factories[{index}].allowed_curation_lanes must be a list of strings",
    ),
    FieldRule(
        "provenance_contract_by_kind",
        lambda value: isinstance(value, Mapping),
        "factories[{index}].provenance_contract_by_kind must be an object",
    ),
)

_PREFERENCE_SIDE_RULES: tuple[FieldRule, ...] = (
    FieldRule(
        "preference_side_kinds",
        _is_nonempty_list,
        "factories[{index}].preference_side_kinds must be a non-empty list",
    ),
    FieldRule(
        "preference_side_kinds",
        _all_strings,
        "factories[{index}].preference_side_kinds must be strings",
    ),
    FieldRule(
        "preference_side_kinds",
        _no_duplicates,
        "factories[{index}].preference_side_kinds must not contain duplicates",
    ),
    FieldRule(
        "preference_side_kinds",
        _all_supported(PREFERENCE_SIDE_KINDS),
        "factories[{index}].preference_side_kinds contains unsupported kinds: {detail}",
        _unsupported(PREFERENCE_SIDE_KINDS),
    ),
)


if __package__:
    _expose_package_sibling(__name__)
