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


def _load_tests(work: Path, relative: str) -> unittest.TestSuite:
    path = work / relative
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


def _run_modules(work: Path, relatives: Iterable[str]) -> dict[str, Any]:
    src = str(work / "src")
    inserted = []
    for entry in (src, str(work)):
        if entry not in sys.path:
            sys.path.insert(0, entry)
            inserted.append(entry)
    # A prior oracle run must not leak `counter` or the generated test modules.
    for name in list(sys.modules):
        if name == "counter" or name.startswith("vset_oracle_"):
            del sys.modules[name]
    suite = unittest.TestSuite()
    try:
        for relative in relatives:
            suite.addTests(_load_tests(work, relative))
        result = _OracleResult()
        suite.run(result)
    finally:
        for entry in inserted:
            if entry in sys.path:
                sys.path.remove(entry)
        for name in list(sys.modules):
            if name == "counter" or name.startswith("vset_oracle_"):
                del sys.modules[name]
    rows = sorted(result.rows, key=lambda item: item["id"])
    report = {
        "tests": rows,
        "failures": len(result.failures),
        "errors": len(result.errors),
        "ok": result.wasSuccessful(),
    }
    report["result_hash"] = _sha256_text(_canonical_json(report["tests"]))
    return report


def apply_patch(work: Path, patch: Any) -> None:
    if not isinstance(patch, Mapping):
        raise VSetValidationError("vset.payload_invalid", "patch must be an object")
    files = patch.get("files")
    if not isinstance(files, Mapping) or not files:
        raise VSetValidationError("vset.payload_invalid", "patch.files must be a non-empty object")
    for relative, contents in files.items():
        if not isinstance(relative, str) or Path(relative).is_absolute() or ".." in Path(relative).parts:
            raise VSetValidationError("vset.payload_invalid", f"illegal patch path {relative!r}")
        if not isinstance(contents, str):
            raise VSetValidationError("vset.payload_invalid", f"patch file {relative} must be a string")
        dest = work / relative
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(contents)


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
        reference = _run_modules(work, list(reference_tests))
        hidden = _run_modules(work, list(hidden_tests)) if list(hidden_tests) else None
        return {
            "pack_snapshot_hash": pack_snapshot_hash(pack_dir),
            "reference": reference,
            "hidden": hidden,
            "hidden_pass_is_meaningless_unless_oracle_valid": True,
        }


def record_patch(record: Mapping[str, Any]) -> Mapping[str, Any] | None:
    payload = record.get("payload")
    if not isinstance(payload, Mapping):
        return None
    kind = record.get("record_kind")
    if kind == "review_remediation_v1":
        patch = payload.get("revised_patch")
    elif kind == "failure_recovery_v1":
        action = payload.get("recovery_action")
        patch = action.get("patch") if isinstance(action, Mapping) else None
    else:
        patch = payload.get("patch")
    return patch if isinstance(patch, Mapping) else None


def validate_record_with_oracle(
    record: Any,
    pack_dir: Path,
    *,
    registry_path: Path | None = None,
) -> tuple[list[VSetValidationError], dict[str, Any] | None]:
    errors = validate_record(record, registry_path=registry_path)
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
    try:
        execution = run_oracle(
            pack_dir,
            patch=record_patch(record),
            reference_tests=oracle.get("reference_tests") or ["tests/reference.py"],
            hidden_tests=oracle.get("hidden_tests") or [],
        )
    except VSetValidationError as exc:
        errors.append(exc)
        return errors, None
    errors.extend(_execution_match_errors(record, oracle, execution, status))
    return errors, execution


def _oracle_path_list_error(oracle: Mapping[str, Any]) -> VSetValidationError | None:
    reference_tests = oracle.get("reference_tests") or ["tests/reference.py"]
    hidden_tests = oracle.get("hidden_tests") or []
    if not isinstance(reference_tests, list) or not all(
        isinstance(item, str) for item in reference_tests
    ):
        return VSetValidationError(
            "vset.oracle_execution_mismatch",
            "oracle.reference_tests must be a list of paths",
        )
    if hidden_tests and (
        not isinstance(hidden_tests, list) or not all(isinstance(item, str) for item in hidden_tests)
    ):
        return VSetValidationError(
            "vset.oracle_execution_mismatch",
            "oracle.hidden_tests must be a list of paths",
        )
    return None


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
    hidden = execution["hidden"]
    if hidden is not None and not hidden["ok"]:
        errors.append(
            VSetValidationError(
                "vset.oracle_execution_mismatch",
                "validated oracle requires declared hidden tests to pass",
            )
        )
    claimed = oracle.get("result_hash")
    actual = execution["reference"]["result_hash"]
    if hidden is not None:
        actual = _sha256_text(
            _canonical_json(
                {
                    "reference": execution["reference"]["tests"],
                    "hidden": hidden["tests"],
                }
            )
        )
    if claimed != actual:
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
