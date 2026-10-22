"""Deterministic oracle execution against a pristine pack copy.

The worktree under test is a temporary copy: candidate patches may write
anything except declared oracle test files, and every declared suite file
is recopied from the pristine pack before it is loaded, so candidate code
can never rewrite the evidence that judges it.

Reference and hidden tests run one id per child interpreter. The child
calls the suite function from the class body and does not consult
``TestCase.run`` or a ``TestResult``. ``ok`` is decided here from those
calls' exit codes and a nonce this process generated, and only when every
id counted from the restored suite files ran and passed.
"""

from __future__ import annotations

import importlib.util
import shutil
import sys
import tempfile
import unittest
from pathlib import Path
from typing import Any, Iterable, Mapping

if __package__:  # pragma: no cover - package-child import path
    from . import _assert_direct_sibling, _expose_package_sibling

    _assert_direct_sibling("vset_oracle_exec")
    from .vset_constants import (
        ERR_ORACLE_EXECUTION_MISMATCH,
        VSetValidationError,
        _canonical_json,
        _mapping_or_empty,
        _sha256_text,
        pack_snapshot_hash,
)
    from .vset_oracle_grade import declared_test_ids as _declared_test_ids
    from .vset_oracle_grade import grade_suite as _grade_suite
    from .vset_patch import apply_patch, escapes_work, illegal_work_relative
else:
    getattr(sys.modules.get("pipelines"), "_join_package_sibling", lambda name: None)(
        "vset_oracle_exec"
    )
    from vset_constants import (
        ERR_ORACLE_EXECUTION_MISMATCH,
        VSetValidationError,
        _canonical_json,
        _mapping_or_empty,
        _sha256_text,
        pack_snapshot_hash,
)
    from vset_oracle_grade import declared_test_ids as _declared_test_ids
    from vset_oracle_grade import grade_suite as _grade_suite
    from vset_patch import apply_patch, escapes_work, illegal_work_relative

def _oracle_module_name(relative: str) -> str:
    return "vset_oracle_" + relative.replace("/", "_").removesuffix(".py")


def _resolve_under_work(work: Path, relative: str, *, code: str) -> Path:
    if illegal_work_relative(relative):
        raise VSetValidationError(code, f"illegal path {relative!r}")
    dest = (work / relative).resolve()
    if escapes_work(work, dest):
        raise VSetValidationError(code, f"path escapes worktree {relative!r}")
    return dest


def _restore_oracle_file(pack_dir: Path, work: Path, relative: str) -> None:
    """Recopy a declared oracle test from the pristine pack before loading.

    Candidate code -- the patch itself or module side effects from an
    earlier suite -- must never rewrite the evidence that judges it.
    """

    source = pack_dir / relative
    dest = _resolve_under_work(work, relative, code=ERR_ORACLE_EXECUTION_MISMATCH)
    if source.is_file():
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, dest)


def load_tests(
    work: Path, pack_dir: Path | str, relative: str | None = None
) -> unittest.TestSuite:
    if relative is None:
        # Pre-split signature: _load_tests(work, relative).
        relative = str(pack_dir)
        pack_dir = work
    _restore_oracle_file(Path(pack_dir), work, relative)
    path = _resolve_under_work(work, relative, code=ERR_ORACLE_EXECUTION_MISMATCH)
    if not path.is_file():
        raise VSetValidationError(ERR_ORACLE_EXECUTION_MISMATCH, f"missing test module {relative}")
    return _load_suite(path, relative)


def _load_suite(path: Path, relative: str) -> unittest.TestSuite:
    module_name = "vset_oracle_" + relative.replace("/", "_").removesuffix(".py")
    spec = importlib.util.spec_from_file_location(module_name, path)
    if spec is None or spec.loader is None:
        raise VSetValidationError(ERR_ORACLE_EXECUTION_MISMATCH, f"cannot load {relative}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    try:
        spec.loader.exec_module(module)
        return unittest.defaultTestLoader.loadTestsFromModule(module)
    except VSetValidationError:
        raise
    except Exception as exc:
        raise VSetValidationError(
            ERR_ORACLE_EXECUTION_MISMATCH,
            f"test module {relative} failed to load: {exc}",
        ) from exc


def _prepare_module(work: Path, pack_dir: Path, relative: str) -> tuple[dict[str, str], list[str]]:
    _restore_oracle_file(pack_dir, work, relative)
    path = _resolve_under_work(work, relative, code=ERR_ORACLE_EXECUTION_MISMATCH)
    if not path.is_file():
        raise VSetValidationError(ERR_ORACLE_EXECUTION_MISMATCH, f"missing test module {relative}")
    module_name = _oracle_module_name(relative)
    try:
        expected = _declared_test_ids(path, module_name)
    except (OSError, SyntaxError) as exc:
        raise VSetValidationError(
            ERR_ORACLE_EXECUTION_MISMATCH,
            f"test module {relative} failed to load: {exc}",
        ) from exc
    spec = {"path": str(path), "module": module_name, "relative": relative}
    return spec, expected


def _run_modules(work: Path, pack_dir: Path, relatives: Iterable[str]) -> dict[str, Any]:
    """Grade every declared test id in its own child interpreter."""

    modules: list[dict[str, str]] = []
    expected: list[str] = []
    for relative in relatives:
        spec, ids = _prepare_module(work, pack_dir, relative)
        modules.append(spec)
        expected.extend(ids)
    return _grade_suite(work, modules, expected)


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
        raise VSetValidationError(ERR_ORACLE_EXECUTION_MISMATCH, f"not a pack directory: {pack_dir}")
    plan = _mapping_or_empty(hidden_suite)
    reference_list = list(reference_tests)
    hidden_list = list(plan.get("tests") or ())
    protected = list(reference_list) + list(hidden_list)
    with tempfile.TemporaryDirectory(prefix="vset-oracle-") as tmp:
        work = Path(tmp) / "pack"
        try:
            shutil.copytree(
                pack_dir,
                work,
                ignore=lambda directory, names: _ignore_pack_member(directory, names, pack_dir),
            )
        except OSError as exc:
            raise VSetValidationError(
                ERR_ORACLE_EXECUTION_MISMATCH, f"cannot stage pack worktree: {exc}"
            ) from exc
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


def execution_result_hash(execution: Mapping[str, Any]) -> str:
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


if __package__:  # pragma: no cover - package-child import path
    _expose_package_sibling(__name__)
