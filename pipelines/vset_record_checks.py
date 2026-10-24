"""Curation, environment, release, and training-view checks for VSET records.

Fail-closed predicates over a record's downstream-claim sections: an
invalid or impossible task stays a measured outcome, accepts require the
validated-oracle gate, release fields are pinned to the reviewed registry
bytes, and the training view mirrors the record's own verdicts.
"""

from __future__ import annotations

import hashlib
import json
import math
import re
import sys
from pathlib import Path
from typing import Any, Mapping

if __package__:  # pragma: no cover - package-child import path
    from . import _assert_direct_sibling, _expose_package_sibling

    _assert_direct_sibling("vset_record_checks")
    from .curate_coding import contains_hidden_reasoning_key
    from .curate_identity import REGISTRY_SCHEMA_VERSION
    from .vset_constants import (
        CURATION_DECISIONS,
        ERR_ACTOR_FIELDS_INVALID,
        ERR_PAYLOAD_INVALID,
        ERR_RELEASE_CONTRACT_MISMATCH,
        IDENTITY_UNRESOLVED_PROVENANCE,
        VSetValidationError,
        _is_nonempty,
        _is_sha256,
        normalize_identity,
        reason_codes_error,
        registry_pin,
)
else:
    getattr(sys.modules.get("pipelines"), "_join_package_sibling", lambda name: None)(
        "vset_record_checks"
    )
    from curate_coding import contains_hidden_reasoning_key
    from curate_identity import REGISTRY_SCHEMA_VERSION
    from vset_constants import (
        CURATION_DECISIONS,
        ERR_ACTOR_FIELDS_INVALID,
        ERR_PAYLOAD_INVALID,
        ERR_RELEASE_CONTRACT_MISMATCH,
        IDENTITY_UNRESOLVED_PROVENANCE,
        VSetValidationError,
        _is_nonempty,
        _is_sha256,
        normalize_identity,
        reason_codes_error,
        registry_pin,
)


def _reject_non_finite_constant(token: str) -> None:
    raise json.JSONDecodeError(f"non-finite constant {token}", token, 0)


def load_json(path: Path) -> Any:
    """Strict JSON: bare ``NaN``/``Infinity`` constants are rejected at load."""

    return json.loads(
        path.read_text(encoding="utf-8"), parse_constant=_reject_non_finite_constant
    )


def _nonfinite_children(value: Any, where: str) -> list[tuple[Any, str]]:
    if isinstance(value, Mapping):
        return [(item, f"{where}.{key}") for key, item in value.items()]
    if isinstance(value, (list, tuple)):
        return [(item, f"{where}[{index}]") for index, item in enumerate(value)]
    return []


def nonfinite_error(value: Any, where: str = "document") -> VSetValidationError | None:
    """Report NaN/Infinity handed to a validator by a direct API caller."""

    if isinstance(value, float) and not math.isfinite(value):
        return VSetValidationError(
            ERR_PAYLOAD_INVALID, f"{where} contains a non-finite number"
        )
    for child, label in _nonfinite_children(value, where):
        found = nonfinite_error(child, label)
        if found is not None:
            return found
    return None


def _curation_errors(
    record: dict[str, Any], curation: dict[str, Any]
) -> list[VSetValidationError]:
    errors: list[VSetValidationError] = []
    if not _is_nonempty(curation.get("pipeline_version")):
        errors.append(
            VSetValidationError(
                ERR_ACTOR_FIELDS_INVALID,
                "curation.pipeline_version must be a non-empty string",
            )
        )
    decision = curation.get("decision")
    if decision not in CURATION_DECISIONS:
        errors.append(
            VSetValidationError(
                ERR_ACTOR_FIELDS_INVALID,
                "curation.decision must be accept, exclude, or measure",
            )
        )
    errors.extend(_curation_reason_errors(curation.get("reason_codes")))
    oracle_status = (
        record["oracle"].get("status") if isinstance(record.get("oracle"), dict) else None
    )
    errors.extend(_accept_gate_errors(record, decision, oracle_status))
    errors.extend(_invalid_outcome_errors(curation, decision, oracle_status))
    return errors


def _invalid_outcome_errors(
    curation: dict[str, Any], decision: Any, oracle_status: Any
) -> list[VSetValidationError]:
    """Invalid or impossible tasks stay first-class measured outcomes."""

    reasons = curation.get("reason_codes")
    if not isinstance(reasons, list):
        reasons = ()
    impossible = "vset.impossible_task" in reasons
    if oracle_status != "invalid" and not impossible:
        return []
    if decision == "measure" and reasons:
        return []
    return [
        VSetValidationError(
            "vset.invalid_outcome_dropped",
            "invalid or impossible tasks require decision=measure with an "
            "explanatory reason code",
        )
    ]


def _accept_gate_errors(
    record: dict[str, Any], decision: Any, oracle_status: Any
) -> list[VSetValidationError]:
    if decision != "accept":
        return []
    errors: list[VSetValidationError] = []
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
    return errors


def _curation_reason_errors(reasons: Any) -> list[VSetValidationError]:
    errors = reason_codes_error(reasons, "curation")
    if errors:
        return errors
    if IDENTITY_UNRESOLVED_PROVENANCE not in reasons:
        return []
    return [
        VSetValidationError(
            "vset.identity_reason_collision",
            "identity.unresolved_provenance is the state.sim_or_real remap gap; "
            "missing actor roles use vset.missing_actor_role",
        )
    ]


def _environment_errors(environment: dict[str, Any]) -> list[VSetValidationError]:
    errors: list[VSetValidationError] = []
    if not _is_sha256(environment.get("repo_snapshot_hash")):
        errors.append(
            VSetValidationError(
                ERR_ACTOR_FIELDS_INVALID,
                "environment.repo_snapshot_hash must be sha256:<64 hex>",
            )
        )
    if not _is_nonempty(environment.get("task_id")):
        errors.append(
            VSetValidationError(
                ERR_ACTOR_FIELDS_INVALID,
                "environment.task_id must be a non-empty string",
            )
        )
    return errors


def _release_errors(
    release: Any,
    registry_path: Path | None,
) -> list[VSetValidationError]:
    pin = registry_pin(registry_path)
    if not isinstance(release, dict):
        return []
    errors: list[VSetValidationError] = []
    if release.get("factory_contract_version") != pin["schema_version"]:
        errors.append(
            VSetValidationError(
                ERR_RELEASE_CONTRACT_MISMATCH,
                f"release.factory_contract_version must be {pin['schema_version']}",
            )
        )
    if not _is_sha256(release.get("manifest_hash")):
        errors.append(
            VSetValidationError(
                ERR_ACTOR_FIELDS_INVALID,
                "release.manifest_hash must be sha256:<64 hex>",
            )
        )
    errors.extend(_stamped_registry_errors(release, pin))
    if pin["schema_version"] != REGISTRY_SCHEMA_VERSION:
        errors.append(
            VSetValidationError(
                ERR_RELEASE_CONTRACT_MISMATCH,
                "loaded registry schema_version drifted from identity's REGISTRY_SCHEMA_VERSION",
            )
        )
    return errors


def _stamped_registry_errors(
    release: dict[str, Any], pin: dict[str, str]
) -> list[VSetValidationError]:
    stamped = release.get("factory_registry_sha256")
    if stamped == pin["sha256"]:
        return []
    return [
        VSetValidationError(
            ERR_RELEASE_CONTRACT_MISMATCH,
            "release.factory_registry_sha256 must match the reviewed FACTORY-REGISTRY.json bytes",
        )
    ]


_TRAINING_VIEW_LEAKS = frozenset(
    {
        "hidden_tests",
        "hidden_suite",
        "reference_tests",
        "reference_suite",
        "private_tests",
        "oracle_suite",
        "grading_tests",
        "tests_source",
        "oracle",
        "payload",
        "patch",
        "solver",
        "solver_run_id",
    }
)

# Shorter than this, a hidden file is not a safe substring: a generic line
# such as ``def test_`` would flag the factory's own visible edits.
_MIN_HIDDEN_SNIPPET = 64

_CAMEL_BOUNDARY = re.compile(r"(?<=[a-z0-9])(?=[A-Z])|(?<=[A-Z])(?=[A-Z][a-z])")

_EMPTY_DIGESTS: frozenset[str] = frozenset()


def _training_view_key(key: Any) -> str:
    """Fold case, camel-case, and lookalikes so ``HIDDEN_TESTS`` matches.

    Camel boundaries are split before the identity fold. ``normalize_identity``
    maps confusable letters such as Cyrillic ``т``; splitting every capital
    would turn ``HIDDEN_TESTS`` into a string of single letters.
    """

    folded = normalize_identity(_CAMEL_BOUNDARY.sub("_", str(key)))
    return folded.replace("-", "_")


def _hidden_suite_pins(pack_dir: Path | None) -> tuple[frozenset[str], tuple[str, ...]]:
    """sha256 and source text of each ``tests/hidden_*.py`` in the pack.

    A string leaks when it is one of those files or contains one. Ordinary
    ``def test_`` code does not, because the marker is the hidden file itself.
    """

    if pack_dir is None:
        return _EMPTY_DIGESTS, ()
    tests = Path(pack_dir) / "tests"
    if not tests.is_dir():
        return _EMPTY_DIGESTS, ()
    digests: list[str] = []
    snippets: list[str] = []
    for path in sorted(tests.iterdir()):
        if not path.is_file() or not path.name.startswith("hidden_") or path.suffix != ".py":
            continue
        raw = path.read_bytes()
        digest = hashlib.sha256(raw).hexdigest()
        digests.append(digest)
        snippet = raw.decode("utf-8").strip()
        if len(snippet) >= _MIN_HIDDEN_SNIPPET:
            snippets.append(snippet)
    return frozenset(digests), tuple(snippets)


def _text_matches_hidden(
    value: str, digests: frozenset[str], snippets: tuple[str, ...]
) -> bool:
    if hashlib.sha256(value.encode("utf-8")).hexdigest() in digests:
        return True
    if any(digest in value for digest in digests):
        return True
    return any(snippet in value for snippet in snippets)


def _key_leaks(key: Any, digests: frozenset[str], snippets: tuple[str, ...]) -> bool:
    if _training_view_key(key) in _TRAINING_VIEW_LEAKS:
        return True
    return isinstance(key, str) and _text_matches_hidden(key, digests, snippets)


def _mapping_leaks(
    value: dict[str, Any], digests: frozenset[str], snippets: tuple[str, ...]
) -> bool:
    if any(_key_leaks(key, digests, snippets) for key in value):
        return True
    return any(_training_view_leaks(item, digests, snippets) for item in value.values())


def _training_view_leaks(
    value: Any, digests: frozenset[str], snippets: tuple[str, ...]
) -> bool:
    """Walk dicts and lists. Keys are case-insensitive; strings match the pack."""
    if isinstance(value, str):
        return _text_matches_hidden(value, digests, snippets)
    if isinstance(value, dict):
        return _mapping_leaks(value, digests, snippets)
    if isinstance(value, list):
        return any(_training_view_leaks(item, digests, snippets) for item in value)
    return False


def _training_view_errors(
    training_view: Any, pack_dir: Path | None = None
) -> list[VSetValidationError]:
    if not isinstance(training_view, dict):
        return [
            VSetValidationError(
                "vset.hidden_reasoning_in_training_view",
                "training_view is required and must be an object",
            )
        ]
    digests, snippets = _hidden_suite_pins(pack_dir)
    leaked = _training_view_leaks(training_view, digests, snippets)
    if contains_hidden_reasoning_key(training_view) or leaked:
        return [
            VSetValidationError(
                "vset.hidden_reasoning_in_training_view",
                "training_view must not carry hidden suites, oracle, payload, patch, or solver",
            )
        ]
    return []




if __package__:  # pragma: no cover - package-child import path
    _expose_package_sibling(__name__)
