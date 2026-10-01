"""Deterministic fixture/reference oracle execution for VSET records."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any, Iterable, Mapping

if __package__:
    from . import _assert_direct_sibling, _expose_package_sibling

    _assert_direct_sibling("vset_oracle")
    from .vset_constants import (
        SELF_CERTIFY_ORACLE_KINDS,
        VSetValidationError,
        _mapping_or_empty,
    )
    from .vset_oracle_exec import _execution_result_hash, run_oracle
    from .vset_patch import pre_patches, record_patch
    from .vset_record import validate_record
else:
    getattr(sys.modules.get("pipelines"), "_join_package_sibling", lambda name: None)(
        "vset_oracle"
    )
    from vset_constants import (
        SELF_CERTIFY_ORACLE_KINDS,
        VSetValidationError,
        _mapping_or_empty,
    )
    from vset_oracle_exec import _execution_result_hash, run_oracle
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


def _task_manifest(pack_dir: Path, task_id: Any) -> Mapping[str, Any] | None:
    tasks_dir = pack_dir / "tasks"
    if not isinstance(task_id, str) or not task_id.strip() or not tasks_dir.is_dir():
        return None
    for path in sorted(tasks_dir.glob("*.json")):
        try:
            manifest = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        if isinstance(manifest, Mapping) and manifest.get("task_id") == task_id:
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


def _illegal_pack_relative(path: str) -> bool:
    candidate = Path(path)
    return not path.strip() or candidate.is_absolute() or ".." in candidate.parts


def _string_path_list_error(value: Any, field: str, *, required: bool) -> VSetValidationError | None:
    if not value and not required:
        return None
    if isinstance(value, list) and all(isinstance(item, str) for item in value):
        return None
    return VSetValidationError(
        "vset.oracle_execution_mismatch",
        f"oracle.{field} must be a list of paths",
    )


def _first_illegal_pack_path(paths: Iterable[Any]) -> VSetValidationError | None:
    for item in paths:
        if isinstance(item, str) and _illegal_pack_relative(item):
            return VSetValidationError(
                "vset.oracle_execution_mismatch",
                f"oracle test path must stay under the pack: {item!r}",
            )
    return None


def _oracle_path_list_error(oracle: Mapping[str, Any]) -> VSetValidationError | None:
    reference_tests = oracle.get("reference_tests") or ["tests/reference.py"]
    hidden_tests = oracle.get("hidden_tests") or []
    typed = _string_path_list_error(reference_tests, "reference_tests", required=True)
    if typed is not None:
        return typed
    typed = _string_path_list_error(hidden_tests, "hidden_tests", required=False)
    if typed is not None:
        return typed
    return _first_illegal_pack_path(list(reference_tests) + list(hidden_tests or []))


def _execution_match_errors(
    record: Mapping[str, Any],
    oracle: Mapping[str, Any],
    execution: Mapping[str, Any],
    status: Any,
) -> list[VSetValidationError]:
    errors: list[VSetValidationError] = []
    expected = record.get("environment", {})
    if isinstance(expected, Mapping) and expected.get("repo_snapshot_hash") not in {
        None,
        execution["pack_snapshot_hash"],
    }:
        errors.append(
            VSetValidationError(
                "vset.oracle_execution_mismatch",
                "environment.repo_snapshot_hash does not match the repo pack",
            )
        )
    errors.extend(_fail_first_errors(execution["fail_first"]))
    if status != "validated":
        return errors
    errors.extend(_validated_execution_errors(oracle, execution))
    return errors


def _fail_first_errors(stages: Iterable[Mapping[str, Any]]) -> list[VSetValidationError]:
    errors: list[VSetValidationError] = []
    for stage in stages:
        if stage["ok"]:
            errors.append(
                VSetValidationError(
                    "vset.oracle_execution_mismatch",
                    f"hidden suite passes before the candidate patch at {stage['stage']}; "
                    "the recorded fail-to-pass claim is not demonstrated",
                )
            )
    return errors


def _hidden_suite_errors(hidden: Any) -> list[VSetValidationError]:
    if hidden is None or hidden["ok"]:
        return []
    return [
        VSetValidationError(
            "vset.oracle_execution_mismatch",
            "validated oracle requires declared hidden tests to pass",
        )
    ]


def _validated_execution_errors(
    oracle: Mapping[str, Any], execution: Mapping[str, Any]
) -> list[VSetValidationError]:
    errors: list[VSetValidationError] = []
    if not execution["reference"]["ok"]:
        errors.append(
            VSetValidationError(
                "vset.oracle_execution_mismatch",
                "validated oracle requires the reference suite to pass",
            )
        )
    errors.extend(_hidden_suite_errors(execution["hidden"]))
    if oracle.get("result_hash") != _execution_result_hash(execution):
        errors.append(
            VSetValidationError(
                "vset.oracle_execution_mismatch",
                "oracle.result_hash does not match deterministic fixture execution",
            )
        )
    if oracle.get("kind") in SELF_CERTIFY_ORACLE_KINDS:
        errors.append(
            VSetValidationError(
                "vset.oracle_self_certified",
                "hidden-test pass is meaningless unless the oracle itself is valid",
            )
        )
    return errors


if __package__:
    _expose_package_sibling(__name__)
