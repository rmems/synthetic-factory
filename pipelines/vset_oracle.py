"""Deterministic fixture/reference oracle execution for VSET records."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any, Mapping

if __package__:
    from . import _assert_direct_sibling, _expose_package_sibling

    _assert_direct_sibling("vset_oracle")
    from .vset_constants import (
        VSetValidationError,
        _mapping_or_empty,
    )
    from .vset_oracle_exec import run_oracle
    from .vset_oracle_check import _execution_match_errors, _oracle_path_list_error
    from .vset_patch import pre_patches, record_patch
    from .vset_record import validate_record
else:
    getattr(sys.modules.get("pipelines"), "_join_package_sibling", lambda name: None)(
        "vset_oracle"
    )
    from vset_constants import (
        VSetValidationError,
        _mapping_or_empty,
    )
    from vset_oracle_exec import run_oracle
    from vset_oracle_check import _execution_match_errors, _oracle_path_list_error
    from vset_patch import pre_patches, record_patch
    from vset_record import validate_record

def _fail_first_stages(record: Mapping[str, Any], require_fail: bool) -> list[Any]:
    """Patch states whose hidden run must fail before the candidate pass counts."""

    if not require_fail:
        return []
    stages: list[Any] = [None]
    stages.extend(pre_patches(record))
    return stages


def _load_pack_manifest(pack_dir: Path) -> tuple[dict[str, Any], VSetValidationError | None]:
    meta_path = pack_dir / "PACK.json"
    if not meta_path.is_file():
        return {}, None
    try:
        meta = json.loads(meta_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return {}, VSetValidationError(
            "vset.oracle_pack_binding", f"unreadable PACK.json: {exc}"
        )
    return (meta if isinstance(meta, dict) else {}), None


def _load_task_manifest(path: Path) -> Mapping[str, Any] | None:
    try:
        manifest = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    return manifest if isinstance(manifest, Mapping) else None


def _task_manifest(pack_dir: Path, task_id: Any) -> Mapping[str, Any] | None:
    if not isinstance(task_id, str) or not task_id.strip():
        return None
    tasks_dir = pack_dir / "tasks"
    if not tasks_dir.is_dir():
        return None
    for path in sorted(tasks_dir.glob("*.json")):
        manifest = _load_task_manifest(path)
        if manifest is not None and manifest.get("task_id") == task_id:
            return manifest
    return None


def _oracle_decl_mismatch(
    declared: Mapping[str, Any], oracle: Mapping[str, Any], field: str
) -> bool:
    if field not in declared or field not in oracle:
        return False
    return oracle[field] != declared[field]


def _task_oracle_field_errors(
    declared_oracle: Any, oracle: Mapping[str, Any]
) -> list[VSetValidationError]:
    if not isinstance(declared_oracle, Mapping):
        return []
    fields = ["kind"]
    if oracle.get("status") == "validated":
        # A provisional run may execute only the reference half of the
        # manifest's oracle; a validated one must execute exactly what
        # the pack declared for this task.
        fields.extend(["reference_tests", "hidden_tests", "command"])
    return [
        VSetValidationError(
            "vset.oracle_pack_binding",
            f"oracle.{field} does not match the pack task manifest",
        )
        for field in fields
        if _oracle_decl_mismatch(declared_oracle, oracle, field)
    ]


def _task_binding_errors(
    record: Mapping[str, Any], manifest: Mapping[str, Any] | None, oracle: Mapping[str, Any]
) -> list[VSetValidationError]:
    task_id = _mapping_or_empty(record.get("environment")).get("task_id")
    if not isinstance(task_id, str) or not task_id.strip():
        return []
    if manifest is None:
        return [
            VSetValidationError(
                "vset.oracle_pack_binding",
                "environment.task_id is not declared by the selected pack",
            )
        ]
    errors: list[VSetValidationError] = []
    declared_kind = manifest.get("record_kind")
    if declared_kind is not None and declared_kind != record.get("record_kind"):
        errors.append(
            VSetValidationError(
                "vset.oracle_pack_binding",
                "record_kind does not match the pack task manifest",
            )
        )
    errors.extend(_task_oracle_field_errors(manifest.get("oracle"), oracle))
    return errors


def _pack_id_errors(
    pack_id: Any, env: dict[str, Any], oracle: dict[str, Any]
) -> list[VSetValidationError]:
    if not isinstance(pack_id, str):
        return []
    errors: list[VSetValidationError] = []
    if env.get("repo_pack_id") not in (None, pack_id):
        errors.append(
            VSetValidationError(
                "vset.oracle_pack_binding",
                "environment.repo_pack_id does not match the selected pack",
            )
        )
    if oracle.get("repo_commit") not in (None, pack_id):
        errors.append(
            VSetValidationError(
                "vset.oracle_pack_binding",
                "oracle.repo_commit does not match the selected pack",
            )
        )
    return errors


def _pack_binding_errors(
    record: Mapping[str, Any], pack_dir: Path
) -> list[VSetValidationError]:
    pack_meta, load_error = _load_pack_manifest(pack_dir)
    if load_error is not None:
        return [load_error]
    pack_id = pack_meta.get("pack_id")
    env = _mapping_or_empty(record.get("environment"))
    oracle = _mapping_or_empty(record.get("oracle"))
    errors = _pack_id_errors(pack_id, env, oracle)
    if isinstance(pack_id, str) or (pack_dir / "tasks").is_dir():
        manifest = _task_manifest(pack_dir, env.get("task_id"))
        errors.extend(_task_binding_errors(record, manifest, oracle))
    return errors


def validate_record_with_oracle(
    record: Any,
    pack_dir: Path,
    *,
    registry_path: Path | None = None,
    require_registry_sha: bool = False,
) -> tuple[list[VSetValidationError], dict[str, Any] | None]:
    errors = validate_record(
        record, registry_path=registry_path, require_registry_sha=require_registry_sha
    )
    if not isinstance(record, dict):
        return errors, None
    oracle: dict[str, Any] = _mapping_or_empty(record.get("oracle"))
    status = oracle.get("status")
    if status not in {"provisional", "validated"}:
        return errors, None
    paths_error = _oracle_path_list_error(oracle)
    if paths_error is not None:
        errors.append(paths_error)
        return errors, None
    errors.extend(_pack_binding_errors(record, Path(pack_dir)))
    try:
        execution = run_oracle(
            pack_dir,
            patch=record_patch(record),
            reference_tests=list(oracle.get("reference_tests") or ["tests/reference.py"]),
            hidden_suite=_hidden_suite_plan(record, oracle, status),
        )
    except VSetValidationError as exc:
        errors.append(exc)
        return errors, None
    errors.extend(_execution_match_errors(record, oracle, execution, status))
    return errors, execution


def _hidden_suite_plan(
    record: Mapping[str, Any], oracle: dict[str, Any], status: Any
) -> dict[str, Any]:
    tests = list(oracle.get("hidden_tests") or [])
    return {
        "tests": tests,
        "fail_first": _fail_first_stages(record, status == "validated" and bool(tests)),
    }


if __package__:
    _expose_package_sibling(__name__)
