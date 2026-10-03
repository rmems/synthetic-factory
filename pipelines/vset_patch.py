"""Candidate-patch application for the VSET oracle worktree.

Split out of ``vset_oracle.py`` for file health. Patch paths are
untrusted record data: they must stay inside the worktree, must name a
real file, and must never overwrite a declared oracle test module.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any, Iterable, Mapping

if __package__:  # pragma: no cover - package-child import path
    from . import _assert_direct_sibling, _expose_package_sibling

    _assert_direct_sibling("vset_patch")
    from .vset_constants import (
        ERR_PAYLOAD_INVALID,
        VSetValidationError,
    )
else:
    getattr(sys.modules.get("pipelines"), "_join_package_sibling", lambda name: None)(
        "vset_patch"
    )
    from vset_constants import (
        ERR_PAYLOAD_INVALID,
        VSetValidationError,
    )

def _patch_path_shape_illegal(candidate: Path) -> bool:
    if candidate.is_absolute():
        return True
    if ".." in candidate.parts:
        return True
    return not candidate.parts


def _illegal_patch_path(relative: Any) -> bool:
    if not isinstance(relative, str) or not relative.strip():
        return True
    candidate = Path(relative)
    if _patch_path_shape_illegal(candidate):
        return True
    # Candidate patches may only rewrite application source. Suite trees,
    # pack metadata, and root-level modules are oracle-owned.
    return candidate.parts[0] != "src"


def _patch_path_key(relative: str) -> str:
    return Path(relative).as_posix().lstrip("./")


def _escapes_work(work: Path, dest: Path) -> bool:
    root = work.resolve()
    return dest != root and root not in dest.parents


def _resolve_patch_dest(work: Path, relative: str) -> Path:
    dest = (work / relative).resolve()
    if _escapes_work(work, dest):
        raise VSetValidationError(
            ERR_PAYLOAD_INVALID, f"patch path escapes the worktree {relative!r}"
        )
    if dest == work.resolve() or dest.is_dir():
        raise VSetValidationError(
            ERR_PAYLOAD_INVALID, f"patch destination is a directory: {relative!r}"
        )
    return dest


def _check_patch_write(relative: Any, contents: Any, protected: frozenset[str]) -> None:
    if _illegal_patch_path(relative):
        raise VSetValidationError(ERR_PAYLOAD_INVALID, f"illegal patch path {relative!r}")
    if _patch_path_key(relative) in protected:
        raise VSetValidationError(
            ERR_PAYLOAD_INVALID,
            f"patch must not overwrite a declared oracle test: {relative!r}",
        )
    if not isinstance(contents, str):
        raise VSetValidationError(ERR_PAYLOAD_INVALID, f"patch file {relative} must be a string")


def _write_patch_file(
    work: Path, relative: Any, contents: Any, protected: frozenset[str]
) -> None:
    _check_patch_write(relative, contents, protected)
    dest = _resolve_patch_dest(work, relative)
    try:
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(contents, encoding="utf-8")
    except OSError as exc:
        raise VSetValidationError(
            ERR_PAYLOAD_INVALID, f"cannot write patch file {relative!r}: {exc}"
        ) from exc


def apply_patch(
    work: Path, patch: Any, *, protected: Iterable[str] = ()
) -> None:
    if not isinstance(patch, Mapping):
        raise VSetValidationError(ERR_PAYLOAD_INVALID, "patch must be an object")
    files = patch.get("files")
    if not isinstance(files, Mapping) or not files:
        raise VSetValidationError(ERR_PAYLOAD_INVALID, "patch.files must be a non-empty object")
    protected_keys = frozenset(_patch_path_key(item) for item in protected)
    for relative, contents in files.items():
        _write_patch_file(work, relative, contents, protected_keys)


def _kind_patch(kind: Any, payload: Mapping[str, Any]) -> Any:
    if kind == "review_remediation_v1":
        return payload.get("revised_patch")
    if kind == "failure_recovery_v1":
        action = payload.get("recovery_action")
        return action.get("patch") if isinstance(action, Mapping) else None
    return payload.get("patch")


def record_patch(record: Mapping[str, Any]) -> Mapping[str, Any] | None:
    payload = record.get("payload")
    if not isinstance(payload, Mapping):
        return None
    patch = _kind_patch(record.get("record_kind"), payload)
    return patch if isinstance(patch, Mapping) else None


def pre_patches(record: Mapping[str, Any]) -> list[Mapping[str, Any]]:
    """Earlier recorded states that must still fail the hidden suite.

    ``review_remediation_v1`` declares the reviewed ``initial_patch``;
    running the hidden suite against it proves the finding was real.
    """

    if record.get("record_kind") != "review_remediation_v1":
        return []
    payload = record.get("payload")
    if not isinstance(payload, Mapping):
        return []
    initial = payload.get("initial_patch")
    return [initial] if isinstance(initial, Mapping) else []


if __package__:  # pragma: no cover - package-child import path
    _expose_package_sibling(__name__)
