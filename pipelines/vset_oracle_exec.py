"""Deterministic oracle execution against a pristine pack copy.

The worktree under test is a temporary copy: candidate patches may write
anything except declared oracle test files, and every declared suite file
is recopied from the pristine pack before it is loaded, so candidate code
can never rewrite the evidence that judges it.

Reference and hidden suites run in a child interpreter. The candidate is
imported only there, so a patched module cannot rewrite this process's
``unittest`` harness. ``ok`` is decided from the test ids in the files this
process restored, not from a child that reports nothing or all skips.
"""

from __future__ import annotations

import ast
import importlib.util
import json
import shutil
import subprocess  # nosec B404
import sys
import tempfile
import textwrap
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
    from vset_patch import apply_patch, escapes_work, illegal_work_relative

_CAPTURE_LIMIT = 4000
_INTERPRETER_FLAGS = ("-I", "-B", "-X", "utf8")

# The child re-binds every test callable captured from the class body after
# ``type`` finishes constructing the class. The forge calls the original
# ``TestCase.__init_subclass__`` and then replaces each ``test*`` method, so
# noticing that the hook was swapped would not run the real assertions.
_RUNNER_SOURCE = textwrap.dedent(
    """\
    import importlib.util
    import io
    import json
    import os
    import sys
    import unittest
    from pathlib import Path


    def _install_body_preserving_case() -> None:
        original = unittest.case.TestCase

        class _KeepMeta(type(original)):
            def __new__(mcs, name, bases, namespace, **kwargs):
                saved = {
                    key: value
                    for key, value in namespace.items()
                    if key.startswith("test") and callable(value)
                }
                cls = super().__new__(mcs, name, bases, namespace, **kwargs)
                for key, value in saved.items():
                    if cls.__dict__.get(key) is not value:
                        setattr(cls, key, value)
                return cls

        class _KeepCase(original, metaclass=_KeepMeta):
            pass

        unittest.case.TestCase = _KeepCase
        unittest.TestCase = _KeepCase


    class _Result(unittest.TestResult):
        def __init__(self) -> None:
            super().__init__()
            self.rows = []

        def addSuccess(self, test):
            super().addSuccess(test)
            self.rows.append({"id": test.id(), "status": "ok"})

        def addFailure(self, test, err):
            super().addFailure(test, err)
            self.rows.append({"id": test.id(), "status": "FAIL"})

        def addError(self, test, err):
            super().addError(test, err)
            self.rows.append({"id": test.id(), "status": "ERROR"})

        def addSkip(self, test, reason):
            super().addSkip(test, reason)
            self.rows.append({"id": test.id(), "status": "SKIP"})

        def addExpectedFailure(self, test, err):
            super().addExpectedFailure(test, err)
            self.rows.append({"id": test.id(), "status": "expectedFailure"})

        def addUnexpectedSuccess(self, test):
            super().addUnexpectedSuccess(test)
            self.rows.append({"id": test.id(), "status": "unexpectedSuccess"})


    def _emit(stream, payload) -> None:
        stream.write(json.dumps(payload))
        stream.flush()


    def _load(path, module_name):
        spec = importlib.util.spec_from_file_location(module_name, path)
        if spec is None or spec.loader is None:
            raise ImportError(f"cannot load {path}")
        module = importlib.util.module_from_spec(spec)
        sys.modules[module_name] = module
        spec.loader.exec_module(module)
        return unittest.defaultTestLoader.loadTestsFromModule(module)


    def main() -> int:
        stdout = sys.stdout
        try:
            job = json.loads(sys.argv[1])
            work = Path(job["work"])
            os.chdir(work)
            sys.path.insert(0, str(work / "src"))
            _install_body_preserving_case()
            captured = io.StringIO()
            sys.stdout = captured
            sys.stderr = captured
            suite = unittest.TestSuite()
            for item in job["modules"]:
                try:
                    suite.addTests(_load(item["path"], item["module"]))
                except Exception as exc:
                    sys.stdout = stdout
                    relative = item["relative"]
                    _emit(stdout, {
                        "load_error": f"test module {relative} failed to load: {exc}",
                    })
                    return 1
            result = _Result()
            suite.run(result)
            sys.stdout = stdout
            _emit(stdout, {
                "tests": result.rows,
                "captured_output": captured.getvalue(),
            })
            return 0
        except Exception as exc:
            sys.stdout = stdout
            _emit(stdout, {"load_error": f"oracle runner failed: {exc}"})
            return 1


    raise SystemExit(main())
    """
)


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


def _base_tail(node: ast.expr) -> str:
    if isinstance(node, ast.Attribute):
        return node.attr
    return getattr(node, "id", "")


def _declared_test_ids(path: Path, module_name: str) -> list[str]:
    """Test ids this process counts from a suite file it restored.

    Only class-body ``test*`` methods on a ``TestCase`` subclass count.
    The child may not shrink or skip that set and still be treated as a pass.
    """

    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    ids: list[str] = []
    for node in tree.body:
        if not isinstance(node, ast.ClassDef):
            continue
        if not any(_base_tail(base) == "TestCase" for base in node.bases):
            continue
        for item in node.body:
            if not isinstance(item, ast.FunctionDef):
                continue
            if item.name.startswith("test"):
                ids.append(f"{module_name}.{node.name}.{item.name}")
    return ids


def _suite_ok(rows: list[dict[str, str]], expected: list[str]) -> bool:
    """A passing suite is evidence only if every declared test ran clean.

    Skips, expected failures, unexpected successes, and a child report that
    drops a declared id are not oracle evidence.
    """

    reported = sorted(row["id"] for row in rows)
    declared = sorted(expected)
    if reported != declared or not declared:
        return False
    return all(row["status"] == "ok" for row in rows)


def _is_test_row(item: Any) -> bool:
    if not isinstance(item, Mapping):
        return False
    return isinstance(item.get("id"), str) and isinstance(item.get("status"), str)


def _rows_from_report(report: Mapping[str, Any]) -> list[dict[str, str]]:
    raw = report.get("tests")
    if not isinstance(raw, list) or any(not _is_test_row(item) for item in raw):
        raise VSetValidationError(
            ERR_ORACLE_EXECUTION_MISMATCH, "oracle runner failed: bad test report"
        )
    return [{"id": item["id"], "status": item["status"]} for item in raw]


def _runner_failure(detail: str) -> VSetValidationError:
    text = " ".join(detail.split())
    if len(text) > 500:
        text = text[:500]
    return VSetValidationError(ERR_ORACLE_EXECUTION_MISMATCH, f"oracle runner failed: {text}")


def _parse_runner_stdout(
    stdout: str, stderr: str, returncode: int
) -> tuple[list[dict[str, str]], str]:
    try:
        report = json.loads(stdout)
    except json.JSONDecodeError as exc:
        detail = stderr.strip() or stdout.strip() or str(exc)
        raise _runner_failure(detail) from exc
    if not isinstance(report, dict):
        raise _runner_failure("report is not an object")
    load_error = report.get("load_error")
    if isinstance(load_error, str) and load_error:
        raise VSetValidationError(ERR_ORACLE_EXECUTION_MISMATCH, load_error)
    if returncode != 0:
        raise _runner_failure(stderr.strip() or "non-zero exit")
    captured = report.get("captured_output") or ""
    if not isinstance(captured, str):
        raise _runner_failure("captured output is not text")
    return _rows_from_report(report), captured


def _execute_in_subprocess(
    work: Path, modules: list[dict[str, str]]
) -> tuple[list[dict[str, str]], str]:
    payload = json.dumps({"work": str(work), "modules": modules})
    argv = [sys.executable, *_INTERPRETER_FLAGS, "-c", _RUNNER_SOURCE, payload]
    try:
        # Literal argv: this interpreter and the runner constant. No shell.
        # nosemgrep: python.lang.security.audit.dangerous-subprocess-use-audit.dangerous-subprocess-use-audit
        completed = subprocess.run(  # nosec B603
            argv,
            cwd=work,
            capture_output=True,
            text=True,
            check=False,
        )
    except OSError as exc:
        raise VSetValidationError(
            ERR_ORACLE_EXECUTION_MISMATCH, f"oracle runner failed: {exc}"
        ) from exc
    return _parse_runner_stdout(completed.stdout, completed.stderr, completed.returncode)


def _suite_report(
    rows: list[dict[str, str]], expected: list[str], captured: str = ""
) -> dict[str, Any]:
    ordered = sorted(rows, key=lambda item: item["id"])
    report: dict[str, Any] = {
        "tests": ordered,
        "failures": sum(item["status"] == "FAIL" for item in ordered),
        "errors": sum(item["status"] == "ERROR" for item in ordered),
        "ok": _suite_ok(ordered, expected),
    }
    report["result_hash"] = _sha256_text(_canonical_json(report["tests"]))
    if captured.strip():
        report["captured_output"] = captured[-_CAPTURE_LIMIT:]
    return report


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
    """Grade one suite list in a child interpreter.

    Declared ids are counted here, from the recopied test files, before the
    child result is trusted.
    """

    modules: list[dict[str, str]] = []
    expected: list[str] = []
    for relative in relatives:
        spec, ids = _prepare_module(work, pack_dir, relative)
        modules.append(spec)
        expected.extend(ids)
    rows, captured = _execute_in_subprocess(work, modules)
    return _suite_report(rows, expected, captured)


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
