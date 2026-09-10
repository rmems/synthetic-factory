"""Fresh-interpreter probe for package-only round transaction imports."""

from __future__ import annotations

import multiprocessing
import sys
from pathlib import Path


_PROCESS_TIMEOUT_SECONDS = 30.0
_TERMINATION_TIMEOUT_SECONDS = 5.0
_ROUND_TRANSACTION_MODULES = frozenset({
    "round_txn",
    "pipelines.round_txn",
    "check_records",
    "pipelines.check_records",
    "code_repair",
    "pipelines.code_repair",
})


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def _require_clean_import_state() -> None:
    loaded = _ROUND_TRANSACTION_MODULES.intersection(sys.modules)
    _require(not loaded, f"round transaction modules were already loaded: {sorted(loaded)}")


def _package_only_paths(repo: Path) -> None:
    excluded = {repo, repo / "pipelines"}
    sys.path[:] = [entry for entry in sys.path if Path(entry or ".").resolve() not in excluded]
    sys.path.insert(0, str(repo))


def _check_committed_paths(round_txn, factory: Path, batch: Path) -> None:
    _require(round_txn.committed_jsonl_paths(factory) == [batch],
             "package import returned the wrong committed path")


def _check_legacy_file(round_txn, factory: Path, batch: Path) -> None:
    del factory
    _require(round_txn.valid_legacy_file(batch) == 1,
             "package import rejected the valid legacy batch")


def _check_legacy_payload(round_txn, factory: Path, batch: Path) -> None:
    count, errors = round_txn.validate_legacy_payload(batch, factory, 1)
    _require(count == 1 and not errors,
             f"package import returned invalid legacy payload results: {(count, errors)}")


_OPERATION_CHECKS = {
    "committed_jsonl_paths": _check_committed_paths,
    "valid_legacy_file": _check_legacy_file,
    "validate_legacy_payload": _check_legacy_payload,
}


def _package_only_probe(repo_text: str, factory_text: str, operation: str) -> None:
    _require_clean_import_state()

    repo = Path(repo_text).resolve()
    _package_only_paths(repo)

    from pipelines import round_txn

    _require("round_txn" not in sys.modules,
             "package-only probe loaded the direct round_txn module")
    factory = Path(factory_text)
    batch = factory / "batch-r01.jsonl"
    _OPERATION_CHECKS[operation](round_txn, factory, batch)


def package_only_probe_exit_code(repo: Path, factory: Path, operation: str) -> int | None:
    """Run one legacy consumer in a spawned interpreter with package-only imports."""

    process = multiprocessing.get_context("spawn").Process(
        target=_package_only_probe,
        args=(str(repo), str(factory), operation),
    )
    process.start()
    process.join(_PROCESS_TIMEOUT_SECONDS)
    if process.is_alive():
        process.terminate()
        process.join(_TERMINATION_TIMEOUT_SECONDS)
        if process.is_alive():
            process.kill()
            process.join(_TERMINATION_TIMEOUT_SECONDS)
        raise TimeoutError(
            "package-only import probe timed out after "
            f"{_PROCESS_TIMEOUT_SECONDS:g} seconds"
        )
    return process.exitcode
