"""Deterministic fixture/reference oracle execution for VSET records."""

from __future__ import annotations

import contextlib
import importlib.util
import io
import json
import os
import shutil
import sys
import tempfile
import unittest
from pathlib import Path
from typing import Any, Iterable, Mapping

if __package__:
    from . import _assert_direct_sibling, _expose_package_sibling

    _assert_direct_sibling("vset_oracle")
    from .vset_constants import (
        SELF_CERTIFY_ORACLE_KINDS,
        VSetValidationError,
        _canonical_json,
        _sha256_text,
        pack_snapshot_hash,
    )
    from .vset_patch import apply_patch, pre_patches, record_patch
    from .vset_record import validate_record
else:
    getattr(sys.modules.get("pipelines"), "_join_package_sibling", lambda name: None)(
        "vset_oracle"
    )
    from vset_constants import (
        SELF_CERTIFY_ORACLE_KINDS,
        VSetValidationError,
        _canonical_json,
        _sha256_text,
        pack_snapshot_hash,
    )
    from vset_patch import apply_patch, pre_patches, record_patch
    from vset_record import validate_record

_CAPTURE_LIMIT = 4000


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


def _restore_oracle_file(pack_dir: Path, work: Path, relative: str) -> None:
    """Recopy a declared oracle test from the pristine pack before loading.

    Candidate code -- the patch itself or module side effects from an
    earlier suite -- must never rewrite the evidence that judges it.
    """

    source = pack_dir / relative
    dest = _resolve_under_work(work, relative, code="vset.oracle_execution_mismatch")
    if source.is_file():
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, dest)


def _load_tests(
    work: Path, pack_dir: Path | str, relative: str | None = None
) -> unittest.TestSuite:
    if relative is None:
        # Pre-split signature: _load_tests(work, relative).
        relative = str(pack_dir)
        pack_dir = work
    _restore_oracle_file(Path(pack_dir), work, relative)
    path = _resolve_under_work(work, relative, code="vset.oracle_execution_mismatch")
    if not path.is_file():
        raise VSetValidationError("vset.oracle_execution_mismatch", f"missing test module {relative}")
    module_name = "vset_oracle_" + relative.replace("/", "_").removesuffix(".py")
    spec = importlib.util.spec_from_file_location(module_name, path)
    if spec is None or spec.loader is None:
        raise VSetValidationError("vset.oracle_execution_mismatch", f"cannot load {relative}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    try:
        spec.loader.exec_module(module)
        return unittest.defaultTestLoader.loadTestsFromModule(module)
    except VSetValidationError:
        raise
    except Exception as exc:
        raise VSetValidationError(
            "vset.oracle_execution_mismatch",
            f"test module {relative} failed to load: {exc}",
        ) from exc


def _restore_sys_modules(snapshot: dict[str, Any]) -> None:
    for name in list(sys.modules):
        if name not in snapshot:
            del sys.modules[name]
    for name, module in snapshot.items():
        sys.modules[name] = module


def _suite_ok(result: _OracleResult) -> bool:
    """A passing suite is evidence only if every declared test ran clean.

    Skips, expected failures, and unexpected successes are not oracle
    evidence: an empty or dodged suite can never certify a record.
    """

    if not result.wasSuccessful():
        return False
    if result.expectedFailures or result.unexpectedSuccesses:
        return False
    return bool(result.rows) and all(row["status"] == "ok" for row in result.rows)


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


def _execute_suite(work: Path, pack_dir: Path, relatives: Iterable[str]) -> _OracleResult:
    suite = unittest.TestSuite()
    for relative in relatives:
        suite.addTests(_load_tests(work, pack_dir, relative))
    result = _OracleResult()
    cwd = os.getcwd()
    try:
        os.chdir(work)
        suite.run(result)
    finally:
        os.chdir(cwd)
    return result


def _suite_report(result: _OracleResult, captured: str = "") -> dict[str, Any]:
    rows = sorted(result.rows, key=lambda item: item["id"])
    report = {
        "tests": rows,
        "failures": len(result.failures),
        "errors": len(result.errors),
        "ok": _suite_ok(result),
    }
    report["result_hash"] = _sha256_text(_canonical_json(report["tests"]))
    if captured.strip():
        report["captured_output"] = captured[-_CAPTURE_LIMIT:]
    return report


def _run_modules(
    work: Path, pack_dir: Path, relatives: Iterable[str]
) -> dict[str, Any]:
    snapshot = sys.modules.copy()
    inserted = _push_pack_path(work)
    captured = io.StringIO()
    try:
        with contextlib.redirect_stdout(captured), contextlib.redirect_stderr(captured):
            result = _execute_suite(work, pack_dir, relatives)
    finally:
        _pop_pack_path(inserted)
        _restore_sys_modules(snapshot)
    return _suite_report(result, captured.getvalue())


def _ignore_pack_member(directory: str, names: list[str], root: Path) -> set[str]:
    ignored = {
        name
        for name in names
        if name == "__pycache__" or name.endswith((".pyc", ".pyo"))
    }
    # Only the root task-manifest directory is oracle bookkeeping; an
    # application package named ``tasks`` under src/ stays executable.
    if Path(directory) == root and "tasks" in names:
        ignored.add("tasks")
    return ignored


def _fail_first_stages(record: Mapping[str, Any], require_fail: bool) -> list[Any]:
    """Patch states whose hidden run must fail before the candidate pass counts."""

    if not require_fail:
        return []
    stages: list[Any] = [None]
    stages.extend(pre_patches(record))
    return stages


def run_oracle(
    pack_dir: Path,
    *,
    patch: Mapping[str, Any] | None = None,
    reference_tests: Iterable[str] = ("tests/reference.py",),
    hidden_tests: Iterable[str] = (),
    fail_first: Iterable[Mapping[str, Any] | None] = (),
) -> dict[str, Any]:
    """Execute deterministic fixture/reference tests against a repo pack.

    A hidden-test pass is reported, but callers must still refuse to treat
    it as ``validated`` unless the oracle itself is independently valid.
    ``fail_first`` stages (``None`` for the pristine pack, or an earlier
    recorded patch) run the hidden suite before the candidate patch so a
    fail-to-pass claim is only credited when the pre-state really fails.
    """

    pack_dir = Path(pack_dir)
    if not pack_dir.is_dir():
        raise VSetValidationError("vset.oracle_execution_mismatch", f"not a pack directory: {pack_dir}")
    reference_list = list(reference_tests)
    hidden_list = list(hidden_tests)
    protected = list(reference_list) + list(hidden_list)
    with tempfile.TemporaryDirectory(prefix="vset-oracle-") as tmp:
        work = Path(tmp) / "pack"
        shutil.copytree(
            pack_dir,
            work,
            ignore=lambda directory, names: _ignore_pack_member(directory, names, pack_dir),
        )
        stages: list[dict[str, Any]] = []
        for index, pre_state in enumerate(fail_first):
            if pre_state is not None:
                apply_patch(work, pre_state, protected=protected)
            stage = _run_modules(work, pack_dir, hidden_list)
            stages.append(
                {
                    "stage": "pristine" if pre_state is None else f"pre_patch_{index}",
                    "ok": stage["ok"],
                    "result_hash": stage["result_hash"],
                }
            )
        if patch is not None:
            apply_patch(work, patch, protected=protected)
        reference = _run_modules(work, pack_dir, reference_list)
        hidden = _run_modules(work, pack_dir, hidden_list) if hidden_list else None
        return {
            "pack_snapshot_hash": pack_snapshot_hash(pack_dir),
            "reference": reference,
            "hidden": hidden,
            "fail_first": stages,
            "hidden_pass_is_meaningless_unless_oracle_valid": True,
        }


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


def _task_binding_errors(
    record: Mapping[str, Any], manifest: Mapping[str, Any] | None, oracle: Mapping[str, Any]
) -> list[VSetValidationError]:
    environment = record.get("environment")
    task_id = environment.get("task_id") if isinstance(environment, Mapping) else None
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
    declared_oracle = manifest.get("oracle")
    if isinstance(declared_oracle, Mapping):
        fields = ["kind"]
        if oracle.get("status") == "validated":
            # A provisional run may execute only the reference half of the
            # manifest's oracle; a validated one must execute exactly what
            # the pack declared for this task.
            fields.extend(["reference_tests", "hidden_tests", "command"])
        for field in fields:
            if _oracle_decl_mismatch(declared_oracle, oracle, field):
                errors.append(
                    VSetValidationError(
                        "vset.oracle_pack_binding",
                        f"oracle.{field} does not match the pack task manifest",
                    )
                )
    return errors


def _pack_binding_errors(
    record: Mapping[str, Any], pack_dir: Path
) -> list[VSetValidationError]:
    pack_meta, load_error = _load_pack_manifest(pack_dir)
    if load_error is not None:
        return [load_error]
    errors: list[VSetValidationError] = []
    pack_id = pack_meta.get("pack_id")
    environment = record.get("environment")
    env = environment if isinstance(environment, Mapping) else {}
    oracle = record.get("oracle") if isinstance(record.get("oracle"), Mapping) else {}
    if isinstance(pack_id, str):
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
    oracle: Mapping[str, Any] = (
        record["oracle"] if isinstance(record.get("oracle"), Mapping) else {}
    )
    status = oracle.get("status")
    if status not in {"provisional", "validated"}:
        return errors, None
    paths_error = _oracle_path_list_error(oracle)
    if paths_error is not None:
        errors.append(paths_error)
        return errors, None
    errors.extend(_pack_binding_errors(record, Path(pack_dir)))
    reference_tests = list(oracle.get("reference_tests") or ["tests/reference.py"])
    hidden_tests = list(oracle.get("hidden_tests") or [])
    try:
        execution = run_oracle(
            pack_dir,
            patch=record_patch(record),
            reference_tests=reference_tests,
            hidden_tests=hidden_tests,
            fail_first=_fail_first_stages(record, status == "validated" and bool(hidden_tests)),
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


if __package__:
    _expose_package_sibling(__name__)
