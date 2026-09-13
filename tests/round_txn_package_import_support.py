"""Fresh-interpreter probe for package-only round transaction imports."""

from __future__ import annotations

import json
import multiprocessing
import sys
from pathlib import Path

from tests.process_test_support import ProcessTimeout, spawned_process_exit_code


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


def _procedural_completion(factory: Path, batch: Path):
    marker = factory / "ROUND-r01.complete.json"
    manifest = json.loads(marker.read_bytes())
    return manifest, manifest["execution_verification"], batch


def _check_procedural_summary(round_txn, factory: Path, batch: Path) -> None:
    _manifest, recorded, _batch = _procedural_completion(factory, batch)
    validated = round_txn.validated_execution_verification_summary(recorded)
    _require(validated == recorded,
             "package import changed the valid procedural receipt")


def _check_procedural_completed(round_txn, factory: Path, batch: Path) -> None:
    manifest, recorded, batch = _procedural_completion(factory, batch)
    validated = round_txn.validate_completed_execution_verification(batch, manifest)
    _require(validated == recorded,
             "package import returned the wrong completed procedural verdict")


def _check_procedural_execution_gate(round_txn, factory: Path, batch: Path) -> None:
    del factory
    try:
        round_txn.execution_gate(batch, batch)
    except round_txn.TransactionError as exc:
        _require(str(exc) == "procedural publication requires the contextual fresh gate",
                 f"package import returned the wrong procedural gate refusal: {exc}")
    else:
        raise AssertionError("generic execution gate accepted a procedural batch")


_OPERATION_CHECKS = {
    "committed_jsonl_paths": _check_committed_paths,
    "valid_legacy_file": _check_legacy_file,
    "validate_legacy_payload": _check_legacy_payload,
    "validated_execution_verification_summary": _check_procedural_summary,
    "validate_completed_execution_verification": _check_procedural_completed,
    "execution_gate": _check_procedural_execution_gate,
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
    """Run one transaction consumer in a spawned interpreter with package-only imports."""

    return spawned_process_exit_code(
        _package_only_probe,
        (str(repo), str(factory), operation),
        timeout=ProcessTimeout(
            _PROCESS_TIMEOUT_SECONDS,
            _TERMINATION_TIMEOUT_SECONDS,
            (
                "package-only import probe timed out after "
                f"{_PROCESS_TIMEOUT_SECONDS:g} seconds"
            ),
        ),
        multiprocessing_module=multiprocessing,
    )
