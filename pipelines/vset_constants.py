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
import unicodedata
from pathlib import Path
from typing import Any, Iterable, Mapping

if __package__:  # pragma: no cover - package-child import path
    from . import _assert_direct_sibling, _expose_package_sibling

    _assert_direct_sibling("vset_constants")
    from .curate_identity import FACTORY_REGISTRY_PATH, load_registry
else:
    getattr(sys.modules.get("pipelines"), "_join_package_sibling", lambda name: None)(
        "vset_constants"
    )
    from curate_identity import FACTORY_REGISTRY_PATH, load_registry

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
ERR_ACTOR_FIELDS_INVALID = "vset.actor_fields_invalid"
ERR_PAYLOAD_INVALID = "vset.payload_invalid"
ERR_RELEASE_CONTRACT_MISMATCH = "vset.release_contract_mismatch"
ERR_ORACLE_PACK_BINDING = "vset.oracle_pack_binding"
ERR_ORACLE_SELF_CERTIFIED = "vset.oracle_self_certified"
ERR_ORACLE_EXECUTION_MISMATCH = "vset.oracle_execution_mismatch"
ERR_SOURCE_KIND_MASQUERADE = "vset.source_kind_masquerade"
ERR_RECORD_NOT_OBJECT = "vset.record_not_object"

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
    (
        "schema_version",
        "record_kind",
        "actor_provenance_schema_version",
        "source_kind",
    )
    + (
        "task_author",
        "solver",
        "reviewer",
        "oracle",
        "curation",
    )
    + (
        "environment",
        "release",
        "payload",
        "training_view",
        "trace",
        "prometheus_lineage",
    )
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


def content_hash(value: Any) -> str:
    """Hash the exact UTF-8 bytes of a declared content string."""

    if not isinstance(value, str):
        return ""
    return _sha256_text(value)


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


def _snapshot_excluded(relative: Path) -> bool:
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
        if _snapshot_excluded(relative):
            continue
        try:
            digest = hashlib.sha256(path.read_bytes()).hexdigest()
        except OSError as exc:
            raise VSetValidationError(
                ERR_PAYLOAD_INVALID, f"unreadable pack member {relative.as_posix()}: {exc}"
            ) from exc
        rows.append(f"{relative.as_posix()}:{digest}")
    return _sha256_text("\n".join(rows))


def _is_sha256(value: Any) -> bool:
    return isinstance(value, str) and bool(_SHA256.fullmatch(value))


def _mapping_or_empty(value: Any) -> dict[str, Any]:
    return dict(value) if isinstance(value, Mapping) else {}


def _pick(mapping: dict[str, Any], keys: Iterable[str]) -> dict[str, Any]:
    return {key: mapping[key] for key in keys if key in mapping}


def _is_nonempty(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip()) and value == value.strip()


def _require_object(value: Any, where: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise VSetValidationError(ERR_RECORD_NOT_OBJECT, f"{where} must be a JSON object")
    return value


def _require_actor_identity(actor: dict[str, Any], role: str) -> None:
    for field in ("model", "version", "run_id"):
        if not normalize_identity(actor.get(field)):
            raise VSetValidationError(
                ERR_ACTOR_FIELDS_INVALID,
                f"{role}.{field} must be a non-empty normalized string",
            )


def _reject_bad_sha256(actor: dict[str, Any], role: str, field: str) -> None:
    if not _is_sha256(actor.get(field)):
        raise VSetValidationError(
            ERR_ACTOR_FIELDS_INVALID,
            f"{role}.{field} must be sha256:<64 hex>",
        )


def _reject_bad_nonempty(actor: dict[str, Any], role: str, field: str) -> None:
    if not _is_nonempty(actor.get(field)):
        raise VSetValidationError(
            ERR_ACTOR_FIELDS_INVALID,
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
            ERR_ACTOR_FIELDS_INVALID,
            f"{role} has undeclared fields {unknown}",
        )
    _require_actor_identity(actor, role)
    _require_actor_optionals(
        actor, role, require_prompt_hash=require_prompt_hash, require_tool_policy=require_tool_policy
    )
    return actor


_INVISIBLE_CHARS = frozenset(
    {
        "\u00ad",
        "\u034f",
        "\u061c",
        "\u180e",
        "\u200b",
        "\u200c",
        "\u200d",
        "\u200e",
        "\u200f",
        "\u202a",
        "\u202b",
        "\u202c",
        "\u202d",
        "\u202e",
        "\u2060",
        "\u2066",
        "\u2067",
        "\u2068",
        "\u2069",
        "\ufeff",
    }
)
_IDENTITY_SENTINELS = frozenset(
    {"null", "none", "unknown", "n/a", "na", "-", "0", "tbd", "placeholder"}
)
# High-value Greek/Cyrillic lookalikes as code points, not a second copy of
# the preference-arms dict. Not a full confusables set.
_CONFUSABLE_ASCII = str.maketrans(
    {
        0x0430: "a",
        0x0251: "a",
        0x03B1: "a",
        0x0432: "b",
        0x03B2: "b",
        0x0441: "c",
        0x03F2: "c",
        0x0435: "e",
        0x03B5: "e",
        0x04BB: "h",
        0x043D: "h",
        0x0456: "i",
        0x03B9: "i",
        0x0458: "j",
        0x043A: "k",
        0x03BA: "k",
        0x043C: "m",
        0x03BC: "m",
        0x043E: "o",
        0x03BF: "o",
        0x0440: "p",
        0x03C1: "p",
        0x0455: "s",
        0x0442: "t",
        0x03C4: "t",
        0x0443: "y",
        0x03C5: "y",
        0x03BD: "v",
        0x0445: "x",
        0x03C7: "x",
        0x04CF: "l",
    }
)


def normalize_identity(value: Any) -> str:
    """Fold an actor token so lookalike spellings compare equal.

    NFKC, invisible-character stripping, casefold, and a basic confusable
    fold. Empty and sentinel results are not identities.
    """

    if not isinstance(value, str):
        return ""
    folded = unicodedata.normalize("NFKC", value)
    folded = "".join(char for char in folded if char not in _INVISIBLE_CHARS)
    folded = folded.casefold().translate(_CONFUSABLE_ASCII)
    folded = re.sub(r"\s+", "", folded)
    if not folded or folded in _IDENTITY_SENTINELS:
        return ""
    return folded


def _normalized_identity_text(value: str) -> str:
    folded = normalize_identity(value)
    return folded.replace("_", "-") if folded else value.lower().replace("_", "-")


def _contains_prometheus_marker(value: Any) -> bool:
    if isinstance(value, str):
        lowered = _normalized_identity_text(value)
        return any(marker in lowered for marker in PROMETHEUS_MARKERS)
    if isinstance(value, Mapping):
        return any(
            _contains_prometheus_marker(item)
            for pair in value.items()
            for item in pair
        )
    if isinstance(value, list):
        return any(_contains_prometheus_marker(item) for item in value)
    return False


def _reason_token_invalid(item: Any) -> bool:
    return not isinstance(item, str) or not _REASON.fullmatch(item)


def reason_codes_error(reasons: Any, where: str) -> list[VSetValidationError]:
    """reason_codes must be a list of unique lowercase reason tokens."""

    if not isinstance(reasons, list) or any(_reason_token_invalid(item) for item in reasons):
        return [
            VSetValidationError(
                ERR_ACTOR_FIELDS_INVALID,
                f"{where}.reason_codes must be a list of lowercase reason tokens",
            )
        ]
    if len(set(reasons)) != len(reasons):
        return [
            VSetValidationError(
                ERR_ACTOR_FIELDS_INVALID,
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


if __package__:  # pragma: no cover - package-child import path
    _expose_package_sibling(__name__)
