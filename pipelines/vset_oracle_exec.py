"""Deterministic oracle execution against a pristine pack copy.

The worktree under test is a temporary copy: candidate patches may write
anything except declared oracle test files, and every declared suite file
is recopied from the pristine pack before it is loaded, so candidate code
can never rewrite the evidence that judges it.
"""

from __future__ import annotations

import contextlib
import importlib.util
import io
import os
import shutil
import sys
import tempfile
import unittest
from pathlib import Path
from typing import Any, Iterable, Mapping

if __package__:
    from . import _assert_direct_sibling, _expose_package_sibling

    _assert_direct_sibling("vset_oracle_exec")
    from .vset_constants import (
        VSetValidationError,
        _canonical_json,
        _mapping_or_empty,
        _sha256_text,
        pack_snapshot_hash,
    )
    from .vset_patch import apply_patch
else:
    getattr(sys.modules.get("pipelines"), "_join_package_sibling", lambda name: None)(
        "vset_oracle_exec"
    )
    from vset_constants import (
        VSetValidationError,
        _canonical_json,
        _mapping_or_empty,
        _sha256_text,
        pack_snapshot_hash,
    )
    from vset_patch import apply_patch

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
    return _load_suite(path, relative)


def _load_suite(path: Path, relative: str) -> unittest.TestSuite:
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


def _fail_first_reports(
    work: Path,
    pack_dir: Path,
    plan: Mapping[str, Any],
    protected: list[str],
) -> list[dict[str, Any]]:
    hidden_list = list(plan.get("tests") or ())
    stages: list[dict[str, Any]] = []
    for index, pre_state in enumerate(plan.get("fail_first") or ()):
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
    return stages


def run_oracle(
    pack_dir: Path,
    *,
    patch: Mapping[str, Any] | None = None,
    reference_tests: Iterable[str] = ("tests/reference.py",),
    hidden_suite: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Execute deterministic fixture/reference tests against a repo pack.

    A hidden-test pass is reported, but callers must still refuse to treat
    it as ``validated`` unless the oracle itself is independently valid.
    ``hidden_suite`` declares ``tests`` plus ``fail_first`` stages (``None``
    for the pristine pack, or an earlier recorded patch) that run the hidden
    suite before the candidate patch so a fail-to-pass claim is only
    credited when the pre-state really fails.
    """

    pack_dir = Path(pack_dir)
    if not pack_dir.is_dir():
        raise VSetValidationError("vset.oracle_execution_mismatch", f"not a pack directory: {pack_dir}")
    plan = _mapping_or_empty(hidden_suite)
    reference_list = list(reference_tests)
    hidden_list = list(plan.get("tests") or ())
    protected = list(reference_list) + list(hidden_list)
    with tempfile.TemporaryDirectory(prefix="vset-oracle-") as tmp:
        work = Path(tmp) / "pack"
        shutil.copytree(
            pack_dir,
            work,
            ignore=lambda directory, names: _ignore_pack_member(directory, names, pack_dir),
        )
        stages = _fail_first_reports(work, pack_dir, plan, protected)
        if patch is not None:
            apply_patch(work, patch, protected=protected)
        reference = _run_modules(work, pack_dir, reference_list)
        hidden = _run_modules(work, pack_dir, hidden_list) if hidden_list else None
        return {
            "pack_snapshot_hash": pack_snapshot_hash(pack_dir),
            "reference": reference,
            "hidden": hidden,
            "fail_first": stages,
            "hidden_suite_requires_valid_oracle": True,
        }


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


if __package__:
    _expose_package_sibling(__name__)
