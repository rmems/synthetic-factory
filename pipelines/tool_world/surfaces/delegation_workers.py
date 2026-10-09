#!/usr/bin/env python3
"""Worker members of the delegation surface: profile names, their shape at load, their effects.

A worker declares one reliability profile per name: ``default`` plus, for each
delegation fault kind it can show, a profile named after that kind. A profile
scripts what the worker reports and claims, how many awaits it takes, and the
effects it applies to the workspace tree when it completes. Every profile is
checked when the environment is built, so no effect is malformed by the time
``apply_effects`` runs it mid-episode.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from typing import Any

from .. import vocabulary as cv
from .._contract import bind_import_twin

__all__ = ["FAULT_KINDS", "PROFILE_DEFAULT", "apply_effects", "check_worker"]

PROFILE_DEFAULT = "default"
FAULT_LATE = "late"
FAULT_PARTIAL = "partial"
FAULT_WRONG_CLAIM = "wrong_claim"
FAULT_CONFLICTING = "conflicting"
FAULT_QUESTION = "question"
FAULT_KINDS = frozenset(
    {FAULT_LATE, FAULT_PARTIAL, FAULT_WRONG_CLAIM, FAULT_CONFLICTING, FAULT_QUESTION}
)
_PROFILE_NAMES = frozenset({PROFILE_DEFAULT, *FAULT_KINDS})
_PROFILE_TEXT_KEYS = ("report", "claim", "question")
_PROFILE_KEYS = frozenset({"awaits_needed", "effects", *_PROFILE_TEXT_KEYS})
_EFFECT_CONTENT = "content"


# --- effects on the workspace tree -----------------------------------------


def _write_effect(files: dict[str, str], effect: Mapping[str, Any]) -> None:
    files[effect["write"]] = effect[_EFFECT_CONTENT]


def _append_effect(files: dict[str, str], effect: Mapping[str, Any]) -> None:
    files[effect["append"]] = files.get(effect["append"], "") + effect[_EFFECT_CONTENT]


def _delete_effect(files: dict[str, str], effect: Mapping[str, Any]) -> None:
    files.pop(effect["delete"], None)


# A worker profile's effect names exactly one of these ops with the path it touches.
_EFFECT_OPS = {"write": _write_effect, "append": _append_effect, "delete": _delete_effect}


def apply_effects(files: dict[str, str], effects: Iterable[Mapping[str, Any]]) -> None:
    """Apply a checked profile's effects to a workspace tree, in declared order."""
    for effect in effects:
        op = next(op for op in _EFFECT_OPS if op in effect)
        _EFFECT_OPS[op](files, effect)


# --- load-time checks of worker members ------------------------------------


def _effect_op(effect: Any) -> str | None:
    """The one op a well-formed effect names with a nonempty path; None for any other shape."""
    if not isinstance(effect, Mapping):
        return None
    ops = [op for op in _EFFECT_OPS if op in effect]
    op = next(iter(ops), None)
    if op is None or len(ops) != 1:
        return None
    path = effect[op]
    return op if isinstance(path, str) and path else None


def _check_effect(where: str, effect: Any) -> None:
    op = _effect_op(effect)
    cv.refuse_when(
        op is None,
        cv.FINDING_PACK_FIELD_INVALID,
        f"{where}: must be an object with exactly one of {list(_EFFECT_OPS)} naming a path",
    )
    cv.refuse_when(
        (op != "delete") != isinstance(effect.get(_EFFECT_CONTENT), str),
        cv.FINDING_PACK_FIELD_INVALID,
        f"{where}: write and append need a string {_EFFECT_CONTENT}; delete takes none",
    )
    stray = sorted(set(effect) - {op, _EFFECT_CONTENT})
    cv.refuse_when(bool(stray), cv.FINDING_PACK_FIELD_INVALID, f"{where}: unknown keys {stray}")


def _check_profile(where: str, name: str, profile: Any) -> None:
    cv.refuse_first(
        (
            (
                name not in _PROFILE_NAMES,
                cv.FINDING_PACK_FIELD_INVALID,
                (
                    f"{where}: profile names must be {PROFILE_DEFAULT!r} or a fault kind "
                    f"{sorted(FAULT_KINDS)}"
                ),
            ),
            (
                not isinstance(profile, Mapping),
                cv.FINDING_PACK_FIELD_INVALID,
                f"{where}: must be an object",
            ),
        )
    )
    stray = sorted(set(profile) - _PROFILE_KEYS)
    cv.refuse_when(bool(stray), cv.FINDING_PACK_FIELD_INVALID, f"{where}: unknown keys {stray}")
    awaits = profile.get("awaits_needed", 1)
    cv.refuse_when(
        not cv.is_genuine_int(awaits) or awaits < 1,
        cv.FINDING_PACK_FIELD_INVALID,
        f"{where}: awaits_needed must be an integer >= 1",
    )
    for key in _PROFILE_TEXT_KEYS:
        cv.refuse_when(
            key in profile and not isinstance(profile[key], str),
            cv.FINDING_PACK_FIELD_INVALID,
            f"{where}: {key} must be a string",
        )
    effects = profile.get("effects", [])
    cv.refuse_when(
        not isinstance(effects, list),
        cv.FINDING_PACK_FIELD_INVALID,
        f"{where}: effects must be a list",
    )
    for index, effect in enumerate(effects):
        _check_effect(f"{where}.effects[{index}]", effect)


def check_worker(role: str, spec: Any) -> None:
    """Refuse a worker member whose profiles the surface could not play exactly as written."""
    where = f"worker {role}"
    profiles = spec.get("profiles") if isinstance(spec, Mapping) else None
    cv.refuse_when(
        not isinstance(profiles, Mapping) or PROFILE_DEFAULT not in profiles,
        cv.FINDING_PACK_FIELD_INVALID,
        f"{where} must declare a default profile",
    )
    cv.refuse_when(
        spec.get("role") != role,
        cv.FINDING_PACK_FIELD_INVALID,
        f"{where}: role field {spec.get('role')!r} must equal the member name {role!r}",
    )
    for name, profile in profiles.items():
        _check_profile(f"{where} profile {name}", name, profile)


bind_import_twin(__name__)
