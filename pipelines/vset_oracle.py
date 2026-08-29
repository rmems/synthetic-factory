"""Deterministic fixture/reference oracle execution for VSET records."""

from __future__ import annotations

import importlib.util
import shutil
import sys
import tempfile
import unittest
from pathlib import Path
from typing import Any, Iterable, Mapping

_PIPELINES = Path(__file__).resolve().parent
if str(_PIPELINES) not in sys.path:
    sys.path.insert(0, str(_PIPELINES))

from vset_constants import (  # noqa: E402
    SELF_CERTIFY_ORACLE_KINDS,
    VSetValidationError,
    _canonical_json,
    _sha256_text,
    pack_snapshot_hash,
)
from vset_record import validate_record  # noqa: E402


class _OracleResult(unittest.TestResult):
    def __init__(self) -> None:
        super().__init__()
        self.rows: list[dict[str, str]] = []

    def addSuccess(self, test: unittest.TestCase) -> None:
        super().addSuccess(test)
        self.rows.append({"id": test.id(), "status": "ok"})

    def addFailure(self, test: unittest.TestCase, err: Any) -> None:
        super().addFailure(test, err)
        self.rows.append({"id": test.id(), "status": "FAIL"})

    def addError(self, test: unittest.TestCase, err: Any) -> None:
        super().addError(test, err)
        self.rows.append({"id": test.id(), "status": "ERROR"})

    def addSkip(self, test: unittest.TestCase, reason: str) -> None:
        super().addSkip(test, reason)
        self.rows.append({"id": test.id(), "status": "SKIP"})


def _illegal_work_relative(relative: Any) -> bool:
    if not isinstance(relative, str) or not relative.strip():
        return True
    candidate = Path(relative)
    return candidate.is_absolute() or ".." in candidate.parts


def _escapes_work(work: Path, dest: Path) -> bool:
    root = work.resolve()
    return dest != root and root not in dest.parents


def _resolve_under_work(work: Path, relative: str, *, code: str) -> Path:
    if _illegal_work_relative(relative):
        raise VSetValidationError(code, f"illegal path {relative!r}")
    dest = (work / relative).resolve()
    if _escapes_work(work, dest):
        raise VSetValidationError(code, f"path escapes worktree {relative!r}")
    return dest


def _load_tests(work: Path, relative: str) -> unittest.TestSuite:
    path = _resolve_under_work(work, relative, code="vset.oracle_execution_mismatch")
    if not path.is_file():
        raise VSetValidationError("vset.oracle_execution_mismatch", f"missing test module {relative}")
    module_name = "vset_oracle_" + relative.replace("/", "_").removesuffix(".py")
    spec = importlib.util.spec_from_file_location(module_name, path)
    if spec is None or spec.loader is None:
        raise VSetValidationError("vset.oracle_execution_mismatch", f"cannot load {relative}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return unittest.defaultTestLoader.loadTestsFromModule(module)


def _restore_sys_modules(snapshot: dict[str, Any]) -> None:
    for name in list(sys.modules):
        if name not in snapshot:
            del sys.modules[name]
    for name, module in snapshot.items():
        sys.modules[name] = module


def _suite_ok(result: _OracleResult) -> bool:
    if not result.wasSuccessful():
        return False
    executed = [row for row in result.rows if row["status"] != "SKIP"]
    return bool(executed)


def _push_pack_path(work: Path) -> list[str]:
    inserted: list[str] = []
    for entry in (str(work / "src"), str(work)):
        if entry not in sys.path:
            sys.path.insert(0, entry)
            inserted.append(entry)
    return inserted


def _pop_pack_path(inserted: list[str]) -> None:
    for entry in inserted:
        if entry in sys.path:
            sys.path.remove(entry)


def _execute_suite(work: Path, relatives: Iterable[str]) -> _OracleResult:
    suite = unittest.TestSuite()
    for relative in relatives:
        suite.addTests(_load_tests(work, relative))
    result = _OracleResult()
    suite.run(result)
    return result


def _suite_report(result: _OracleResult) -> dict[str, Any]:
    rows = sorted(result.rows, key=lambda item: item["id"])
    report = {
        "tests": rows,
        "failures": len(result.failures),
        "errors": len(result.errors),
        "ok": _suite_ok(result),
    }
    report["result_hash"] = _sha256_text(_canonical_json(report["tests"]))
    return report


def _run_modules(work: Path, relatives: Iterable[str]) -> dict[str, Any]:
    snapshot = sys.modules.copy()
    inserted = _push_pack_path(work)
    try:
        result = _execute_suite(work, relatives)
    finally:
        _pop_pack_path(inserted)
        _restore_sys_modules(snapshot)
    return _suite_report(result)


def _patch_files(patch: Any) -> Mapping[str, Any]:
    if not isinstance(patch, Mapping):
        raise VSetValidationError("vset.payload_invalid", "patch must be an object")
    files = patch.get("files")
    if not isinstance(files, Mapping) or not files:
        raise VSetValidationError("vset.payload_invalid", "patch.files must be a non-empty object")
    return files


def _illegal_patch_path(relative: Any) -> bool:
    if not isinstance(relative, str):
        return True
    candidate = Path(relative)
    return candidate.is_absolute() or ".." in candidate.parts


def _write_patch_file(work: Path, relative: Any, contents: Any) -> None:
    if _illegal_patch_path(relative):
        raise VSetValidationError("vset.payload_invalid", f"illegal patch path {relative!r}")
    if not isinstance(contents, str):
        raise VSetValidationError("vset.payload_invalid", f"patch file {relative} must be a string")
    dest = work / relative
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(contents)


def apply_patch(work: Path, patch: Any) -> None:
    for relative, contents in _patch_files(patch).items():
        _write_patch_file(work, relative, contents)


def run_oracle(
    pack_dir: Path,
    *,
    patch: Mapping[str, Any] | None = None,
    reference_tests: Iterable[str] = ("tests/reference.py",),
    hidden_tests: Iterable[str] = (),
) -> dict[str, Any]:
    """Execute deterministic fixture/reference tests against a repo pack.

    A hidden-test pass is reported, but callers must still refuse to treat
    it as ``validated`` unless the oracle itself is independently valid.
    """

    pack_dir = Path(pack_dir)
    if not pack_dir.is_dir():
        raise VSetValidationError("vset.oracle_execution_mismatch", f"not a pack directory: {pack_dir}")
    with tempfile.TemporaryDirectory(prefix="vset-oracle-") as tmp:
        work = Path(tmp) / "pack"
        shutil.copytree(
            pack_dir,
            work,
            ignore=shutil.ignore_patterns("tasks"),
        )
        if patch is not None:
            apply_patch(work, patch)
        reference_list = list(reference_tests)
        hidden_list = list(hidden_tests)
        reference = _run_modules(work, reference_list)
        hidden = _run_modules(work, hidden_list) if hidden_list else None
        return {
            "pack_snapshot_hash": pack_snapshot_hash(pack_dir),
            "reference": reference,
            "hidden": hidden,
            "hidden_pass_is_meaningless_unless_oracle_valid": True,
        }


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
    oracle = record.get("oracle") if isinstance(record.get("oracle"), Mapping) else {}
    status = oracle.get("status")
    if status not in {"provisional", "validated"}:
        return errors, None
    paths_error = _oracle_path_list_error(oracle)
    if paths_error is not None:
        errors.append(paths_error)
        return errors, None
    reference_tests = list(oracle.get("reference_tests") or ["tests/reference.py"])
    hidden_tests = list(oracle.get("hidden_tests") or [])
    try:
        execution = run_oracle(
            pack_dir,
            patch=record_patch(record),
            reference_tests=reference_tests,
            hidden_tests=hidden_tests,
        )
    except VSetValidationError as exc:
        errors.append(exc)
        return errors, None
    errors.extend(_execution_match_errors(record, oracle, execution, status))
    return errors, execution


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
    if status != "validated":
        return errors
    errors.extend(_validated_execution_errors(oracle, execution))
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


def _execution_result_hash(execution: Mapping[str, Any]) -> str:
    hidden = execution["hidden"]
    if hidden is None:
        return execution["reference"]["result_hash"]
    return _sha256_text(
        _canonical_json(
            {
                "reference": execution["reference"]["tests"],
                "hidden": hidden["tests"],
            }
        )
    )


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
