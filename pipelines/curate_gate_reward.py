#!/usr/bin/env python3
"""Reward ontology coverage and reward semantics for the curation gate.

Split out of ``curate_gate.py`` (CodeScene: Lines of Code in a Single File) by
responsibility; every name is re-exported from ``curate_gate`` so existing
``curate_gate.X`` call sites resolve unchanged.

Two questions live here. ``_reward_ontology_gate`` asks whether every
reward-bearing row in a cleaned corpus carries a valid ``reward_training``
annotation at all. The rest answers the harder one: whether that annotation
*is true*. The gate never trusts a lane's claim -- it re-enumerates the reward
values out of the retained output, re-runs the arithmetic assessment and the
comparability classification from ``curate_rewards``, binds any external
calibration back to the sealed units-migration catalog, and refuses when the
recorded classification, magnitude or order differs from that independent
derivation. The mapping in ``schemas/reward-ontology-v1.mapping.json`` is the
source of truth throughout; nothing here re-decides what a reward means.

``curate_gate_reward_sidecars`` reads this module for the per-record
authentication it performs while walking the sealed sidecar artifacts.
"""

from __future__ import annotations

import copy
import sys
from collections import Counter
from pathlib import Path
from typing import Any, Iterable, NamedTuple, Sequence

if __package__:
    from . import _assert_direct_sibling, _expose_package_sibling

    _assert_direct_sibling("curate_gate_reward")
    from . import curate_gate_contract as _contract
    from . import curate_gate_digest as _digest
    from . import curate_gate_merge as _merge
    from . import curate_gate_records as _records
    from . import curate_rewards
else:
    getattr(sys.modules.get("pipelines"), "_join_package_sibling", lambda name: None)(
        "curate_gate_reward"
    )
    _PIPELINES = Path(__file__).resolve().parent
    if str(_PIPELINES) not in sys.path:
        sys.path.insert(0, str(_PIPELINES))
    import curate_gate_contract as _contract
    import curate_gate_digest as _digest
    import curate_gate_merge as _merge
    import curate_gate_records as _records
    import curate_rewards

GateError = _contract.GateError
REWARD_CALIBRATION_KIND = _contract.REWARD_CALIBRATION_KIND

record_sha256 = _digest.record_sha256
_json_pointer = _merge._json_pointer
iter_records = _records.iter_records


# ---------------------------------------------------------------------------
# ontology coverage
# ---------------------------------------------------------------------------


def _reward_field_count(value: Any) -> int:
    if isinstance(value, dict):
        count = 0
        for key, child in value.items():
            if key == curate_rewards.ANNOTATION_FIELD:
                continue
            if key in curate_rewards.REWARD_KEYS:
                count += 1
            count += _reward_field_count(child)
        return count
    if isinstance(value, list):
        return sum(_reward_field_count(item) for item in value)
    return 0


def _reward_ontology_gate(cleaned: Path) -> dict[str, Any]:
    reward_bearing = 0
    annotated = 0
    missing: list[str] = []
    invalid: list[dict[str, str]] = []
    comparability: Counter[str] = Counter()

    for relative, line, record in iter_records(cleaned):
        if not isinstance(record, dict):
            continue
        reward_count = _reward_field_count(record)
        if not reward_count:
            continue
        reward_bearing += 1
        where = f"{relative}:{line}"
        annotation = record.get(curate_rewards.ANNOTATION_FIELD)
        if annotation is None:
            missing.append(where)
            continue
        annotated += 1
        try:
            curate_rewards.validate_ontology_document(annotation)
            if annotation.get("source_reward_count") != reward_count:
                raise curate_rewards.RewardOntologyError(
                    "source_reward_count does not match record reward fields"
                )
        except curate_rewards.RewardOntologyError as exc:
            invalid.append({"source": where, "error": str(exc)})
            continue
        comparability[str(annotation["comparability"])] += 1

    return {
        "tool": "curate_rewards.validate_ontology_document",
        "passed": not missing and not invalid,
        "reward_bearing_records": reward_bearing,
        "annotated_records": annotated,
        "missing_annotations": len(missing),
        "invalid_annotations": len(invalid),
        "comparability": dict(sorted(comparability.items())),
        "examples": [
            *(
                {"source": source, "error": "reward_training annotation missing"}
                for source in missing[:5]
            ),
            *invalid[:5],
        ][:5],
    }


# ---------------------------------------------------------------------------
# reward values in the retained output
# ---------------------------------------------------------------------------


def _pointer_value(document: Any, pointer: Any) -> Any:
    if not isinstance(pointer, str) or not pointer.startswith("/"):
        raise curate_rewards.RewardOntologyError(f"invalid JSON pointer: {pointer!r}")
    value = document
    for raw_token in pointer[1:].split("/"):
        token = raw_token.replace("~1", "/").replace("~0", "~")
        if isinstance(value, list):
            try:
                value = value[int(token)]
            except (ValueError, IndexError) as exc:
                raise curate_rewards.RewardOntologyError(
                    f"sidecar pointer does not resolve: {pointer}"
                ) from exc
        elif isinstance(value, dict) and token in value:
            value = value[token]
        else:
            raise curate_rewards.RewardOntologyError(f"sidecar pointer does not resolve: {pointer}")
    return value


def _walk_reward_values(value: Any, path: tuple[str | int, ...] = ()) -> Iterable[tuple[str, Any]]:
    """Yield reward scopes from retained output, independent of sidecar claims."""
    if isinstance(value, dict):
        for key, child in value.items():
            if key == curate_rewards.ANNOTATION_FIELD:
                continue
            child_path = (*path, key)
            if key in curate_rewards.REWARD_KEYS:
                yield _json_pointer(child_path), child
            yield from _walk_reward_values(child, child_path)
    elif isinstance(value, list):
        for index, child in enumerate(value):
            yield from _walk_reward_values(child, (*path, index))


# ---------------------------------------------------------------------------
# external calibration, bound back to the sealed units-migration catalog
# ---------------------------------------------------------------------------


def _reward_calibration_catalog(
    prepared_lanes: Sequence[dict[str, Any]],
) -> dict[str, dict[str, Any]]:
    catalogs = [
        dict(artifact.get("_catalog") or {})
        for lane in prepared_lanes
        for artifact in lane.get("artifacts", [])
        if artifact.get("kind") == REWARD_CALIBRATION_KIND
    ]
    if len(catalogs) > 1:
        raise GateError("more than one calibration artifact across all lanes")
    return catalogs[0] if catalogs else {}


def _authenticated_calibration_lookup(
    source_record: dict[str, Any] | None,
    sidecar: dict[str, Any],
) -> Any:
    """Return the record id a calibration claim may be looked up under."""
    source = sidecar.get("source") if isinstance(sidecar.get("source"), dict) else {}
    sidecar_record_id = source.get("record_id")
    authenticated_id = (
        curate_rewards.canonical_source_record_id(source_record)
        if source_record is not None
        else None
    )
    if (
        source_record is not None
        and sidecar_record_id is not None
        and (
            authenticated_id is None
            or not isinstance(sidecar_record_id, str)
            or curate_rewards.catalog_record_key(authenticated_id)
            != curate_rewards.catalog_record_key(sidecar_record_id)
        )
    ):
        raise curate_rewards.RewardOntologyError(
            "sidecar calibration source identity does not match the authenticated record"
        )
    return authenticated_id or sidecar_record_id


def _catalog_calibration(catalog: dict[str, dict[str, Any]], lookup_id: Any) -> dict[str, Any] | None:
    return (
        catalog.get(curate_rewards.catalog_record_key(lookup_id))
        if isinstance(lookup_id, str) and lookup_id.strip()
        else None
    )


def _unclaimed_calibration(
    sidecar: dict[str, Any],
    expected: dict[str, Any] | None,
) -> dict[str, Any] | None:
    """A sidecar that claims no calibration may still not hide one."""
    classification = sidecar.get("classification")
    comparability = (
        classification.get("comparability") if isinstance(classification, dict) else None
    )
    if expected is not None and comparability == curate_rewards.MAGNITUDE_COMPARABLE:
        raise curate_rewards.RewardOntologyError(
            "sidecar omits calibration evidence present in the migration artifact"
        )
    return expected


def _claimed_calibration(claimed: Any, expected: dict[str, Any] | None) -> dict[str, Any] | None:
    normalized_claimed = curate_rewards.normalize_calibration(claimed)
    if expected is None:
        raise curate_rewards.RewardOntologyError(
            "external calibration has no matching record in the migration artifact"
        )
    normalized_expected = curate_rewards.normalize_calibration(expected)
    if normalized_claimed["source_unit_usd"] != normalized_expected["source_unit_usd"]:
        raise curate_rewards.RewardOntologyError(
            "sidecar calibration does not match the migration artifact for its source record"
        )
    return expected


def _authenticated_record_calibration(
    source_record: dict[str, Any] | None,
    sidecar: dict[str, Any],
    catalog: dict[str, dict[str, Any]],
) -> dict[str, Any] | None:
    claimed = sidecar.get("calibration")
    lookup_id = _authenticated_calibration_lookup(source_record, sidecar)
    expected = _catalog_calibration(catalog, lookup_id)
    if claimed is None:
        return _unclaimed_calibration(sidecar, expected)
    return _claimed_calibration(claimed, expected)


# ---------------------------------------------------------------------------
# independent derivation of the reward contract
# ---------------------------------------------------------------------------


def _derived_reward_contract(
    record: dict[str, Any],
    sidecar: dict[str, Any],
    calibration_catalog: dict[str, dict[str, Any]],
    source_record: dict[str, Any] | None,
) -> dict[str, Any]:
    """Recompute ontology semantics from row values and authenticated evidence."""
    calibration = _authenticated_record_calibration(
        source_record,
        sidecar,
        calibration_catalog,
    )
    output_record = copy.deepcopy(record)
    output_record.pop(curate_rewards.ANNOTATION_FIELD, None)
    reward_items = sorted(_walk_reward_values(output_record), key=lambda item: item[0])
    source_rewards = [
        {
            "json_pointer": pointer,
            "value_sha256": "sha256:" + record_sha256(value),
            "value": copy.deepcopy(value),
        }
        for pointer, value in reward_items
    ]
    arithmetic = [
        curate_rewards.assess_arithmetic(value, pointer) for pointer, value in reward_items
    ]
    comparability, reason_codes, payload = curate_rewards.classify_source_rewards(
        source_rewards,
        arithmetic,
        calibration,
    )
    return {
        "source_rewards": source_rewards,
        "arithmetic": arithmetic,
        "classification": {
            "comparability": comparability,
            "reason_codes": reason_codes,
        },
        "payload": payload,
    }


class RewardSemanticsInputs(NamedTuple):
    """Everything ``_authenticate_reward_semantics`` derives its answer from."""

    record: dict[str, Any]
    sidecar: dict[str, Any]
    calibration_catalog: dict[str, dict[str, Any]]
    source_record: dict[str, Any] | None


def _assert_sidecar_matches_derived(sidecar: dict[str, Any], derived: dict[str, Any]) -> None:
    if sidecar.get("source_rewards") != derived["source_rewards"]:
        raise curate_rewards.RewardOntologyError(
            "source_rewards do not match independently enumerated reward values"
        )
    if sidecar.get("arithmetic") != derived["arithmetic"]:
        raise curate_rewards.RewardOntologyError(
            "sidecar arithmetic does not match independent recomputation"
        )
    if sidecar.get("classification") != derived["classification"]:
        raise curate_rewards.RewardOntologyError(
            "sidecar classification does not match independent derivation"
        )


def _assert_annotation_matches_derived(
    annotation: dict[str, Any], derived: dict[str, Any]
) -> None:
    classification = derived["classification"]
    if (
        annotation.get("comparability") != classification["comparability"]
        or annotation.get("reason_codes") != classification["reason_codes"]
    ):
        raise curate_rewards.RewardOntologyError(
            "record classification does not match independent derivation"
        )
    if annotation.get("source_reward_count") != len(derived["source_rewards"]):
        raise curate_rewards.RewardOntologyError(
            "record annotation reward count mismatches independent enumeration"
        )


def _assert_payload_claims(annotation: dict[str, Any], derived: dict[str, Any]) -> None:
    """Only the derived comparability class may carry a magnitude or an order."""
    comparability = derived["classification"]["comparability"]
    if comparability == curate_rewards.MAGNITUDE_COMPARABLE:
        if annotation.get("magnitude") != derived["payload"] or "order" in annotation:
            raise curate_rewards.RewardOntologyError(
                "canonical magnitude or calibration does not match independent derivation"
            )
    elif comparability == curate_rewards.SIGN_ORDER_ONLY:
        if annotation.get("order") != derived["payload"] or "magnitude" in annotation:
            raise curate_rewards.RewardOntologyError(
                "preference order does not match independent derivation"
            )
    elif "magnitude" in annotation or "order" in annotation:
        raise curate_rewards.RewardOntologyError(
            "excluded reward class must not carry magnitude or order claims"
        )


def _authenticate_reward_semantics(
    annotation: dict[str, Any],
    inputs: RewardSemanticsInputs,
) -> None:
    derived = _derived_reward_contract(
        inputs.record,
        inputs.sidecar,
        inputs.calibration_catalog,
        inputs.source_record,
    )
    _assert_sidecar_matches_derived(inputs.sidecar, derived)
    _assert_annotation_matches_derived(annotation, derived)
    _assert_payload_claims(annotation, derived)


if __package__:
    _expose_package_sibling(__name__)
