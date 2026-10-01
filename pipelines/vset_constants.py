"""Shared VSET validator constants and leaf checks.

Split out of ``validate_vset.py`` so CodeScene file/method health stays
honest. Behavior is unchanged: factory trust stays in
``config/FACTORY-REGISTRY.json``.
"""

from __future__ import annotations

import hashlib
import json
import math
import re
import sys
from pathlib import Path
from typing import Any, Mapping

_PIPELINES = Path(__file__).resolve().parent
if str(_PIPELINES) not in sys.path:
    sys.path.insert(0, str(_PIPELINES))

from curate_identity import (  # noqa: E402
    FACTORY_REGISTRY_PATH,
    REGISTRY_SCHEMA_VERSION,
    load_registry,
)

SCHEMA_VERSION = "vset-record-v1"
ACTOR_PROVENANCE_VERSION = "actor-provenance-v1"
MANIFEST_SCHEMA_VERSION = "vset-release-manifest-v1"
# Identity-lane reason (missing state.sim_or_real / state.provenance).
# Not an actor-envelope code. See schemas/provenance.md.
IDENTITY_UNRESOLVED_PROVENANCE = "identity.unresolved_provenance"
MANIFEST_ROLES = (
    "task_author",
    "solver",
    "reviewer",
    "oracle",
    "curation",
    "environment",
    "release",
)
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
PROMETHEUS_MARKERS = ("operation-prometheus",)
PROMETHEUS_FAMILIES = frozenset({"prometheus", "prometheus-real"})
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
PACK_SNAPSHOT_ROOTS = ("src", "tests")
RECORD_TOP_LEVEL_KEYS = frozenset(
    {
        "schema_version",
        "record_kind",
        "actor_provenance_schema_version",
        "source_kind",
        "task_author",
        "solver",
        "reviewer",
        "oracle",
        "curation",
        "environment",
        "release",
        "payload",
        "training_view",
        "trace",
        "prometheus_lineage",
    }
)
ACTOR_FIELDS = frozenset(
    {"model", "version", "run_id", "prompt_hash", "tool_policy", "outcome"}
)
ENTRY_TOP_LEVEL_KEYS = frozenset(
    {
        "record_kind",
        "source_kind",
        "task_author",
        "solver",
        "reviewer",
        "oracle",
        "curation",
        "environment",
        "release",
    }
)
MANIFEST_TOP_LEVEL_KEYS = frozenset(
    {
        "schema_version",
        "actor_provenance_schema_version",
        "factory_contract_version",
        "factory_registry_sha256",
        "manifest_hash",
        "counts",
        "entries",
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


def _snapshot_excluded(pack_dir: Path, relative: Path) -> bool:
    parts = relative.parts
    if not parts:
        return True
    if parts[0] == "tasks" or parts[0] == "PACK.json":
        return True
    return "__pycache__" in parts or relative.suffix in {".pyc", ".pyo"}


def pack_snapshot_hash(pack_dir: Path) -> str:
    """Content-bind every file the oracle worktree can execute or read.

    Factory metadata (``PACK.json``), root-level task manifests
    (``tasks/``), and bytecode are not part of the snapshot. Every other
    file -- including root-level modules and fixtures a test may import
    or read -- is hashed so two packs cannot share a pin while running
    different code. The pin stays stable across ``compileall`` and
    Python minor versions.
    """

    pack_dir = Path(pack_dir)
    rows: list[str] = []
    for path in sorted(pack_dir.rglob("*")):
        if not path.is_file():
            continue
        relative = path.relative_to(pack_dir)
        if _snapshot_excluded(pack_dir, relative):
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


def _require_actor_identity(actor: dict[str, Any], role: str) -> None:
    for field in ("model", "version", "run_id"):
        if not _is_nonempty(actor.get(field)):
            raise VSetValidationError(
                "vset.actor_fields_invalid",
                f"{role}.{field} must be a non-empty normalized string",
            )


def _reject_bad_sha256(actor: dict[str, Any], role: str, field: str) -> None:
    if not _is_sha256(actor.get(field)):
        raise VSetValidationError(
            "vset.actor_fields_invalid",
            f"{role}.{field} must be sha256:<64 hex>",
        )


def _reject_bad_nonempty(actor: dict[str, Any], role: str, field: str) -> None:
    if not _is_nonempty(actor.get(field)):
        raise VSetValidationError(
            "vset.actor_fields_invalid",
            f"{role}.{field} must be a non-empty normalized string",
        )


def _require_actor_optionals(
    actor: dict[str, Any],
    role: str,
    *,
    require_prompt_hash: bool,
    require_tool_policy: bool,
) -> None:
    if require_prompt_hash:
        _reject_bad_sha256(actor, role, "prompt_hash")
    if require_tool_policy:
        _reject_bad_nonempty(actor, role, "tool_policy")
    if "prompt_hash" in actor:
        _reject_bad_sha256(actor, role, "prompt_hash")
    if "tool_policy" in actor:
        _reject_bad_nonempty(actor, role, "tool_policy")


def _check_actor(
    value: Any,
    role: str,
    *,
    require_prompt_hash: bool = False,
    require_tool_policy: bool = False,
) -> dict[str, Any]:
    actor = _require_object(value, role)
    unknown = sorted(set(actor) - ACTOR_FIELDS)
    if unknown:
        raise VSetValidationError(
            "vset.actor_fields_invalid",
            f"{role} has undeclared fields {unknown}",
        )
    _require_actor_identity(actor, role)
    _require_actor_optionals(
        actor, role, require_prompt_hash=require_prompt_hash, require_tool_policy=require_tool_policy
    )
    return actor


def _normalized_identity_text(value: str) -> str:
    return value.lower().replace("_", "-")


def _contains_prometheus_marker(value: Any) -> bool:
    if isinstance(value, str):
        lowered = _normalized_identity_text(value)
        return any(marker in lowered for marker in PROMETHEUS_MARKERS)
    if isinstance(value, Mapping):
        return any(_contains_prometheus_marker(item) for item in value.values())
    if isinstance(value, list):
        return any(_contains_prometheus_marker(item) for item in value)
    return False


def _reject_non_finite_constant(token: str) -> None:
    raise json.JSONDecodeError(f"non-finite constant {token}", token, 0)


def load_json(path: Path) -> Any:
    """Strict JSON: bare ``NaN``/``Infinity`` constants are rejected at load."""

    return json.loads(
        path.read_text(encoding="utf-8"), parse_constant=_reject_non_finite_constant
    )


def nonfinite_error(value: Any, where: str = "document") -> VSetValidationError | None:
    """Report NaN/Infinity handed to a validator by a direct API caller."""

    if isinstance(value, float) and not math.isfinite(value):
        return VSetValidationError(
            "vset.payload_invalid", f"{where} contains a non-finite number"
        )
    if isinstance(value, Mapping):
        for key, item in value.items():
            found = nonfinite_error(item, f"{where}.{key}")
            if found is not None:
                return found
    if isinstance(value, (list, tuple)):
        for index, item in enumerate(value):
            found = nonfinite_error(item, f"{where}[{index}]")
            if found is not None:
                return found
    return None


def _reason_token_invalid(item: Any) -> bool:
    return not isinstance(item, str) or not _REASON.fullmatch(item)


def reason_codes_error(reasons: Any, where: str) -> list[VSetValidationError]:
    """reason_codes must be a list of unique lowercase reason tokens."""

    if not isinstance(reasons, list) or any(_reason_token_invalid(item) for item in reasons):
        return [
            VSetValidationError(
                "vset.actor_fields_invalid",
                f"{where}.reason_codes must be a list of lowercase reason tokens",
            )
        ]
    if len(set(reasons)) != len(reasons):
        return [
            VSetValidationError(
                "vset.actor_fields_invalid",
                f"{where}.reason_codes must not contain duplicates",
            )
        ]
    return []


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
