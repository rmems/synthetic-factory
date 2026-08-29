#!/usr/bin/env python3
"""Validate VSET actor-provenance records against the #154 contract.

Stdlib-only. Existing factory pipelines import ``validate_record`` /
``run_oracle``; this CLI is the operator surface.

Factory trust stays in ``config/FACTORY-REGISTRY.json`` (issue #32).
This module does not classify payload kinds for identity, does not
hard-code generator slugs, and does not write into ``outputs/raw/``.

Usage:
  python3 pipelines/validate_vset.py <record.json|records-dir>
  python3 pipelines/validate_vset.py --oracle <record.json> --pack <repo-pack>
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import re
import shutil
import sys
import tempfile
import unittest
from pathlib import Path
from typing import Any, Iterable, Mapping

_PIPELINES = Path(__file__).resolve().parent
if str(_PIPELINES) not in sys.path:
    sys.path.insert(0, str(_PIPELINES))

from curate_coding import contains_hidden_reasoning_key  # noqa: E402
from curate_identity import (  # noqa: E402
    FACTORY_REGISTRY_PATH,
    REGISTRY_SCHEMA_VERSION,
    load_registry,
)

SCHEMA_VERSION = "vset-record-v1"
ACTOR_PROVENANCE_VERSION = "actor-provenance-v1"
RECORD_KINDS = frozenset(
    {"issue_patch_v1", "review_remediation_v1", "failure_recovery_v1"}
)
REVIEW_REQUIRED_KINDS = frozenset({"review_remediation_v1"})
SOURCE_KINDS = frozenset({"synthetic", "real_public_engineering"})
ORACLE_STATUSES = frozenset({"invalid", "provisional", "validated"})
CURATION_DECISIONS = frozenset({"accept", "exclude", "measure"})
SELF_CERTIFY_ORACLE_KINDS = frozenset({"solver_self_report", "task_author_claim"})
VALIDATING_ORACLE_KINDS = frozenset(
    {
        "deterministic_fixture_reference",
        "trusted_reference_implementation",
        "fail_to_pass_pass_to_pass",
        "property_metamorphic",
        "mutation_threshold",
        "adversarial_independent",
        "human_adjudication",
    }
)
SHA256_RE = r"^sha256:[0-9a-f]{64}$"
_SHA256 = re.compile(SHA256_RE)
_REASON = re.compile(r"^[a-z][a-z0-9_.]*$")
PROMETHEUS_MARKERS = ("operation-prometheus", "rmems/operation-prometheus")
SYNTHETIC_PACK_PREFIX = "vset-"
IDENTITY_ENV_KEYS = frozenset(
    {
        "prometheus_lineage",
        "source_family",
        "claimed_source_kind",
        "github_repo",
        "upstream_source",
        "lineage_id",
    }
)
KIND_PAYLOAD_KEYS = {
    "issue_patch_v1": (
        "task_specification",
        "patch",
        "validation_evidence",
        "outcome",
    ),
    "review_remediation_v1": (
        "initial_patch",
        "review_finding",
        "revised_patch",
        "validation_evidence",
        "outcome",
    ),
    "failure_recovery_v1": (
        "failed_state",
        "failure_evidence",
        "recovery_action",
        "execution_evidence",
        "outcome",
    ),
}


class VSetValidationError(ValueError):
    """One fail-closed contract violation."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(f"{code}: {message}")
        self.code = code
        self.message = message


def _sha256_bytes(payload: bytes) -> str:
    return "sha256:" + hashlib.sha256(payload).hexdigest()


def _sha256_text(payload: str) -> str:
    return _sha256_bytes(payload.encode("utf-8"))


def _canonical_json(value: Any) -> str:
    return json.dumps(
        value, ensure_ascii=False, allow_nan=False, sort_keys=True, separators=(",", ":")
    )


def registry_pin(registry_path: Path | None = None) -> dict[str, str]:
    """Return the reviewed registry version and bytes hash.

    Authority is the #32 table. Records carry this pin so a later reader
    can reproduce the provenance/authority decision.
    """

    path = Path(registry_path) if registry_path is not None else FACTORY_REGISTRY_PATH
    registry = load_registry(path)
    return {
        "schema_version": registry.schema_version,
        "sha256": "sha256:" + registry.sha256,
        "path": str(path),
    }


PACK_SNAPSHOT_ROOTS = ("src", "tests")


def pack_snapshot_hash(pack_dir: Path) -> str:
    """Content-bind repo-pack sources under ``src/`` and ``tests/``.

    Factory metadata (``PACK.json``), task manifests, bytecode, and
    other bookkeeping are not part of the snapshot. The pin must be
    stable across ``compileall`` and Python minor versions.
    """

    pack_dir = Path(pack_dir)
    rows: list[str] = []
    for path in sorted(pack_dir.rglob("*")):
        if not path.is_file():
            continue
        relative = path.relative_to(pack_dir)
        parts = relative.parts
        if not parts or parts[0] not in PACK_SNAPSHOT_ROOTS:
            continue
        if "__pycache__" in parts or relative.suffix in {".pyc", ".pyo"}:
            continue
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        rows.append(f"{relative.as_posix()}:{digest}")
    return _sha256_text("\n".join(rows))


def _is_sha256(value: Any) -> bool:
    return isinstance(value, str) and bool(_SHA256.fullmatch(value))


def _is_nonempty(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip()) and value == value.strip()


def _require_object(value: Any, where: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise VSetValidationError("vset.record_not_object", f"{where} must be a JSON object")
    return value


def _check_actor(
    value: Any,
    role: str,
    *,
    require_prompt_hash: bool = False,
    require_tool_policy: bool = False,
) -> dict[str, Any]:
    actor = _require_object(value, role)
    for field in ("model", "version", "run_id"):
        if not _is_nonempty(actor.get(field)):
            raise VSetValidationError(
                "vset.actor_fields_invalid",
                f"{role}.{field} must be a non-empty normalized string",
            )
    if require_prompt_hash and not _is_sha256(actor.get("prompt_hash")):
        raise VSetValidationError(
            "vset.actor_fields_invalid",
            f"{role}.prompt_hash must be sha256:<64 hex>",
        )
    if require_tool_policy and not _is_nonempty(actor.get("tool_policy")):
        raise VSetValidationError(
            "vset.actor_fields_invalid",
            f"{role}.tool_policy must be a non-empty normalized string",
        )
    if "prompt_hash" in actor and not _is_sha256(actor["prompt_hash"]):
        raise VSetValidationError(
            "vset.actor_fields_invalid",
            f"{role}.prompt_hash must be sha256:<64 hex>",
        )
    if "tool_policy" in actor and not _is_nonempty(actor["tool_policy"]):
        raise VSetValidationError(
            "vset.actor_fields_invalid",
            f"{role}.tool_policy must be a non-empty normalized string",
        )
    return actor


def _contains_prometheus_marker(value: Any) -> bool:
    if isinstance(value, str):
        lowered = value.lower()
        return any(marker in lowered for marker in PROMETHEUS_MARKERS)
    if isinstance(value, Mapping):
        return any(_contains_prometheus_marker(item) for item in value.values())
    if isinstance(value, list):
        return any(_contains_prometheus_marker(item) for item in value)
    return False


def _source_kind_errors(record: Mapping[str, Any]) -> list[VSetValidationError]:
    errors: list[VSetValidationError] = []
    source_kind = record.get("source_kind")
    if source_kind not in SOURCE_KINDS:
        errors.append(
            VSetValidationError(
                "vset.source_kind_invalid",
                "source_kind must be synthetic or real_public_engineering",
            )
        )
        return errors
    environment = record.get("environment")
    env = environment if isinstance(environment, Mapping) else {}
    if source_kind == "synthetic":
        if _contains_prometheus_marker(
            {key: env.get(key) for key in IDENTITY_ENV_KEYS if key in env}
        ) or _contains_prometheus_marker(record.get("prometheus_lineage")):
            errors.append(
                VSetValidationError(
                    "vset.source_kind_masquerade",
                    "synthetic records must not claim Operation Prometheus as source identity",
                )
            )
        claimed = env.get("claimed_source_kind")
        family = env.get("source_family")
        if claimed == "real_public_engineering" or (
            isinstance(family, str) and family.lower() in {"prometheus_real", "prometheus"}
        ):
            errors.append(
                VSetValidationError(
                    "vset.source_kind_masquerade",
                    "synthetic records must not masquerade as real_public_engineering / Prometheus",
                )
            )
    if source_kind == "real_public_engineering":
        pack_id = env.get("repo_pack_id")
        if isinstance(pack_id, str) and pack_id.startswith(SYNTHETIC_PACK_PREFIX):
            errors.append(
                VSetValidationError(
                    "vset.source_kind_masquerade",
                    "real_public_engineering must not use a synthetic VSET repo pack as its identity",
                )
            )
    return errors


def _oracle_errors(record: Mapping[str, Any], oracle: Mapping[str, Any]) -> list[VSetValidationError]:
    errors: list[VSetValidationError] = []
    status = oracle.get("status")
    kind = oracle.get("kind")
    if status not in ORACLE_STATUSES:
        errors.append(
            VSetValidationError(
                "vset.oracle_status_invalid",
                "oracle.status must be invalid, provisional, or validated",
            )
        )
        return errors
    if not _is_nonempty(kind):
        errors.append(
            VSetValidationError("vset.oracle_status_invalid", "oracle.kind must be a non-empty string")
        )
        return errors
    solver = record.get("solver") if isinstance(record.get("solver"), Mapping) else {}
    author = record.get("task_author") if isinstance(record.get("task_author"), Mapping) else {}
    certifier = oracle.get("certifier")
    solver_success = solver.get("outcome") == "success"
    evidence = oracle.get("signals")
    only_solver_signal = (
        isinstance(evidence, list)
        and evidence == ["solver_success"]
    ) or oracle.get("upgraded_from_solver_success") is True

    if status == "validated":
        if kind in SELF_CERTIFY_ORACLE_KINDS:
            errors.append(
                VSetValidationError(
                    "vset.oracle_self_certified",
                    "a solver or task-author claim cannot certify oracle_status=validated",
                )
            )
        if kind not in VALIDATING_ORACLE_KINDS:
            errors.append(
                VSetValidationError(
                    "vset.oracle_self_certified",
                    f"oracle.kind {kind!r} cannot independently certify validated",
                )
            )
        if not _is_nonempty(oracle.get("command")) or not _is_sha256(oracle.get("result_hash")):
            errors.append(
                VSetValidationError(
                    "vset.oracle_validated_without_evidence",
                    "validated oracle requires command and result_hash",
                )
            )
        if not _is_nonempty(certifier):
            errors.append(
                VSetValidationError(
                    "vset.oracle_self_certified",
                    "validated oracle requires an independent certifier",
                )
            )
        elif certifier in {"solver", "task_author"} or certifier in {
            solver.get("run_id"),
            author.get("run_id"),
            solver.get("model"),
            author.get("model"),
        }:
            errors.append(
                VSetValidationError(
                    "vset.oracle_self_certified",
                    "oracle.certifier must not be the solver or task_author",
                )
            )
        if only_solver_signal or (
            solver_success and kind in SELF_CERTIFY_ORACLE_KINDS
        ):
            errors.append(
                VSetValidationError(
                    "vset.oracle_self_certified",
                    "solver success must not upgrade oracle_status to validated",
                )
            )
    return errors


def _payload_errors(kind: str, payload: Any) -> list[VSetValidationError]:
    if not isinstance(payload, dict) or not payload:
        return [
            VSetValidationError("vset.payload_invalid", "payload must be a non-empty object")
        ]
    missing = [key for key in KIND_PAYLOAD_KEYS[kind] if key not in payload]
    if missing:
        return [
            VSetValidationError(
                "vset.payload_invalid",
                f"{kind} payload missing {missing}",
            )
        ]
    return []


def validate_record(
    record: Any,
    *,
    registry_path: Path | None = None,
    require_registry_sha: bool = False,
) -> list[VSetValidationError]:
    """Return every fail-closed violation. Empty means the record is well-formed."""

    errors: list[VSetValidationError] = []
    if not isinstance(record, dict):
        return [VSetValidationError("vset.record_not_object", "record must be a JSON object")]

    if record.get("schema_version") != SCHEMA_VERSION:
        errors.append(
            VSetValidationError(
                "vset.schema_version_invalid",
                f"schema_version must be {SCHEMA_VERSION}",
            )
        )
    if record.get("actor_provenance_schema_version") != ACTOR_PROVENANCE_VERSION:
        errors.append(
            VSetValidationError(
                "vset.schema_version_invalid",
                f"actor_provenance_schema_version must be {ACTOR_PROVENANCE_VERSION}",
            )
        )
    kind = record.get("record_kind")
    if kind not in RECORD_KINDS:
        errors.append(
            VSetValidationError(
                "vset.record_kind_invalid",
                "record_kind must be issue_patch_v1, review_remediation_v1, or failure_recovery_v1",
            )
        )
        kind = None

    errors.extend(_source_kind_errors(record))

    for role in ("task_author", "solver", "oracle", "curation", "environment", "release"):
        if role not in record or record[role] is None:
            errors.append(
                VSetValidationError("vset.missing_actor_role", f"required role {role} is missing")
            )

    author = None
    solver = None
    if isinstance(record.get("task_author"), dict):
        try:
            author = _check_actor(record["task_author"], "task_author", require_prompt_hash=True)
        except VSetValidationError as exc:
            errors.append(exc)
    if isinstance(record.get("solver"), dict):
        try:
            solver = _check_actor(record["solver"], "solver", require_tool_policy=True)
        except VSetValidationError as exc:
            errors.append(exc)
    if author is not None and solver is not None and author["run_id"] == solver["run_id"]:
        errors.append(
            VSetValidationError(
                "vset.actors_conflated",
                "task_author.run_id and solver.run_id must remain distinct",
            )
        )

    reviewer = record.get("reviewer", None)
    if kind in REVIEW_REQUIRED_KINDS:
        if not isinstance(reviewer, dict):
            errors.append(
                VSetValidationError(
                    "vset.reviewer_required",
                    "review_remediation_v1 requires an explicit reviewer object",
                )
            )
        else:
            try:
                _check_actor(reviewer, "reviewer")
            except VSetValidationError as exc:
                errors.append(exc)
    elif reviewer is not None:
        if not isinstance(reviewer, dict):
            errors.append(
                VSetValidationError(
                    "vset.actor_fields_invalid",
                    "reviewer must be an object when present",
                )
            )
        else:
            try:
                _check_actor(reviewer, "reviewer")
            except VSetValidationError as exc:
                errors.append(exc)

    if isinstance(record.get("oracle"), dict):
        errors.extend(_oracle_errors(record, record["oracle"]))

    curation = record.get("curation")
    if isinstance(curation, dict):
        if not _is_nonempty(curation.get("pipeline_version")):
            errors.append(
                VSetValidationError(
                    "vset.actor_fields_invalid",
                    "curation.pipeline_version must be a non-empty string",
                )
            )
        decision = curation.get("decision")
        if decision not in CURATION_DECISIONS:
            errors.append(
                VSetValidationError(
                    "vset.actor_fields_invalid",
                    "curation.decision must be accept, exclude, or measure",
                )
            )
        reasons = curation.get("reason_codes")
        if not isinstance(reasons, list) or any(
            not isinstance(item, str) or not _REASON.fullmatch(item) for item in reasons
        ):
            errors.append(
                VSetValidationError(
                    "vset.actor_fields_invalid",
                    "curation.reason_codes must be a list of lowercase reason tokens",
                )
            )
        oracle_status = (
            record["oracle"].get("status") if isinstance(record.get("oracle"), dict) else None
        )
        if decision == "accept":
            if record.get("source_kind") != "synthetic":
                errors.append(
                    VSetValidationError(
                        "vset.accept_requires_synthetic",
                        "positive VSET accept requires source_kind=synthetic",
                    )
                )
            if oracle_status != "validated":
                errors.append(
                    VSetValidationError(
                        "vset.accept_requires_validated_oracle",
                        "positive accept requires oracle.status=validated",
                    )
                )

    environment = record.get("environment")
    if isinstance(environment, dict):
        if not _is_sha256(environment.get("repo_snapshot_hash")):
            errors.append(
                VSetValidationError(
                    "vset.actor_fields_invalid",
                    "environment.repo_snapshot_hash must be sha256:<64 hex>",
                )
            )
        if not _is_nonempty(environment.get("task_id")):
            errors.append(
                VSetValidationError(
                    "vset.actor_fields_invalid",
                    "environment.task_id must be a non-empty string",
                )
            )

    release = record.get("release")
    pin = registry_pin(registry_path)
    if isinstance(release, dict):
        if release.get("factory_contract_version") != pin["schema_version"]:
            errors.append(
                VSetValidationError(
                    "vset.release_contract_mismatch",
                    f"release.factory_contract_version must be {pin['schema_version']}",
                )
            )
        if not _is_sha256(release.get("manifest_hash")):
            errors.append(
                VSetValidationError(
                    "vset.actor_fields_invalid",
                    "release.manifest_hash must be sha256:<64 hex>",
                )
            )
        stamped = release.get("factory_registry_sha256")
        if stamped is not None or require_registry_sha:
            if stamped != pin["sha256"]:
                errors.append(
                    VSetValidationError(
                        "vset.release_contract_mismatch",
                        "release.factory_registry_sha256 must match the reviewed FACTORY-REGISTRY.json bytes",
                    )
                )
        if pin["schema_version"] != REGISTRY_SCHEMA_VERSION:
            errors.append(
                VSetValidationError(
                    "vset.release_contract_mismatch",
                    "loaded registry schema_version drifted from identity's REGISTRY_SCHEMA_VERSION",
                )
            )

    if kind is not None:
        errors.extend(_payload_errors(kind, record.get("payload")))

    training_view = record.get("training_view")
    if not isinstance(training_view, dict):
        errors.append(
            VSetValidationError(
                "vset.hidden_reasoning_in_training_view",
                "training_view is required and must be an object",
            )
        )
    elif contains_hidden_reasoning_key(training_view):
        errors.append(
            VSetValidationError(
                "vset.hidden_reasoning_in_training_view",
                "training_view must not contain thought / internal_reasoning*",
            )
        )
    return errors


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


def _record_patch(record: Mapping[str, Any]) -> Mapping[str, Any] | None:
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
    execution = None
    if status in {"provisional", "validated"}:
        reference_tests = oracle.get("reference_tests") or ["tests/reference.py"]
        hidden_tests = oracle.get("hidden_tests") or []
        if not isinstance(reference_tests, list) or not all(
            isinstance(item, str) for item in reference_tests
        ):
            errors.append(
                VSetValidationError(
                    "vset.oracle_execution_mismatch",
                    "oracle.reference_tests must be a list of paths",
                )
            )
            return errors, None
        if hidden_tests and (
            not isinstance(hidden_tests, list)
            or not all(isinstance(item, str) for item in hidden_tests)
        ):
            errors.append(
                VSetValidationError(
                    "vset.oracle_execution_mismatch",
                    "oracle.hidden_tests must be a list of paths",
                )
            )
            return errors, None
        try:
            execution = run_oracle(
                pack_dir,
                patch=_record_patch(record),
                reference_tests=reference_tests,
                hidden_tests=hidden_tests,
            )
        except VSetValidationError as exc:
            errors.append(exc)
            return errors, None
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
        if status == "validated":
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
    return errors, execution


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def iter_record_paths(target: Path) -> list[Path]:
    if target.is_file():
        return [target]
    return sorted(path for path in target.rglob("*.json") if path.is_file())


def summarize(errors: list[VSetValidationError]) -> dict[str, Any]:
    return {
        "ok": not errors,
        "error_count": len(errors),
        "reason_codes": [item.code for item in errors],
        "errors": [str(item) for item in errors],
    }


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate VSET actor-provenance records.")
    parser.add_argument("target", help="record JSON file or directory of records")
    parser.add_argument(
        "--oracle",
        action="store_true",
        help="execute deterministic fixture/reference tests when the record claims an oracle",
    )
    parser.add_argument(
        "--pack",
        help="repo-pack directory for --oracle (defaults next to fixtures)",
    )
    parser.add_argument(
        "--require-registry-sha",
        action="store_true",
        help="require release.factory_registry_sha256 to match the reviewed registry bytes",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    target = Path(args.target)
    if not target.exists():
        print(f"not found: {target}", file=sys.stderr)
        return 2
    pack = Path(args.pack) if args.pack else None
    if args.oracle and pack is None:
        print("--oracle requires --pack", file=sys.stderr)
        return 2
    reports = []
    failed = False
    for path in iter_record_paths(target):
        record = load_json(path)
        if args.oracle:
            assert pack is not None
            errors, execution = validate_record_with_oracle(record, pack)
        else:
            errors = validate_record(
                record, require_registry_sha=args.require_registry_sha
            )
            execution = None
        item = {"path": str(path), **summarize(errors)}
        if execution is not None:
            item["oracle_execution"] = {
                "reference_ok": execution["reference"]["ok"],
                "hidden_ok": None if execution["hidden"] is None else execution["hidden"]["ok"],
                "result_hash": execution["reference"]["result_hash"],
            }
        reports.append(item)
        if errors:
            failed = True
            for error in errors:
                print(f"ERROR: {path}: {error}", file=sys.stderr)
    print(json.dumps({"records": reports, "ok": not failed}, indent=2))
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
