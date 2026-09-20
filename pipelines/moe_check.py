#!/usr/bin/env python3
"""Family validator for ``moe-router-distillation-trajectories``.

Split out of ``moe_router.py`` verbatim: :func:`check_family` re-derives the
routing labels from the recorded context, pins the teacher identity against
the sealed Hub cards, and recomputes the reference router's layers. Every name
here is re-exported from ``moe_router`` so existing call sites resolve
unchanged.
"""

from __future__ import annotations

import hashlib
import sys
from collections import Counter
from pathlib import Path
from typing import Any

_PIPELINES = Path(__file__).resolve().parent
if str(_PIPELINES) not in sys.path:
    sys.path.insert(0, str(_PIPELINES))

from oracle_grounded import distill_contract as oc  # noqa: E402


if __package__:
    from .moe_featurizer import (
        COMMIT_SHA_RE,
        COMPACT_SUMMARY_STATS,
        FEATURE_DIM,
        FEATURIZER_ID,
        MAX_RECOMPUTE_DIM,
        NON_TEACHER_IMPLEMENTATIONS,
        NON_TEACHER_ORACLE_NAMES,
        NON_TEACHER_ORACLE_TYPES,
        RECOMPUTE_TOLERANCE,
        SEALED_HUB_MOE_CARDS,
        SEALED_HUB_MOE_REVISIONS,
        TEACHER_ORACLE_TYPES,
        TRANSFORMERS_MOE_IMPLEMENTATION,
        _DEFAULT_REFERENCE_SEED,
        compact_view,
        entropy_nats,
        featurize,
        resolve_checkpoint,
        softmax,
    )
    from .moe_layers import (
        LayerRouting,
        _check_declared_trajectory_authority,
        _check_derived_routing_labels,
        _check_layer_count,
        _check_routing_layers,
        _declared_expert_count,
        _declared_layer_count,
        _declared_top_k,
        _recomputed_layer_mismatches,
    )
    from .moe_oracles import (
        ReferenceMoERouter,
        TransformersMoERouter,
    )
else:
    from moe_featurizer import (
        COMMIT_SHA_RE,
        COMPACT_SUMMARY_STATS,
        FEATURE_DIM,
        FEATURIZER_ID,
        MAX_RECOMPUTE_DIM,
        NON_TEACHER_IMPLEMENTATIONS,
        NON_TEACHER_ORACLE_NAMES,
        NON_TEACHER_ORACLE_TYPES,
        RECOMPUTE_TOLERANCE,
        SEALED_HUB_MOE_CARDS,
        SEALED_HUB_MOE_REVISIONS,
        TEACHER_ORACLE_TYPES,
        TRANSFORMERS_MOE_IMPLEMENTATION,
        _DEFAULT_REFERENCE_SEED,
        compact_view,
        entropy_nats,
        featurize,
        resolve_checkpoint,
        softmax,
    )
    from moe_layers import (
        LayerRouting,
        _check_declared_trajectory_authority,
        _check_derived_routing_labels,
        _check_layer_count,
        _check_routing_layers,
        _declared_expert_count,
        _declared_layer_count,
        _declared_top_k,
        _recomputed_layer_mismatches,
    )
    from moe_oracles import (
        ReferenceMoERouter,
        TransformersMoERouter,
    )


def _check_context_digest(scenario: dict[str, Any], where: str) -> list[str]:
    """The student-visible context and the digest that pins it."""

    context = scenario.get("context")
    if not isinstance(context, str) or not context.strip():
        return [f"{where}.scenario.context must be a non-empty string"]
    if scenario.get("context_sha256") != hashlib.sha256(
        context.encode("utf-8")
    ).hexdigest():
        return [f"{where}.scenario.context_sha256 does not match the context"]
    return []


def _check_compact_input(scenario: dict[str, Any], where: str) -> list[str]:
    """The compact student input the baseline is evaluated on."""

    compact = scenario.get("compact_input")
    if not isinstance(compact, dict):
        return [f"{where}.scenario.compact_input must be an object"]
    features = compact.get("features")
    if not isinstance(features, list) or not features:
        return [
            f"{where}.scenario.compact_input.features must carry the "
            "student input the baseline is evaluated on"
        ]
    if not all(oc.is_number(value) for value in features):
        # router_baseline silently skips a record whose features are not
        # finite numbers, so without this a curated corpus could contain
        # no usable student input at all.
        return [
            f"{where}.scenario.compact_input.features must be finite "
            "numbers — the baseline extractor drops anything else"
        ]
    declared = compact.get("compact_dim")
    if isinstance(declared, int) and not isinstance(declared, bool):
        expected = declared + COMPACT_SUMMARY_STATS
        if len(features) != expected:
            return [
                f"{where}.scenario.compact_input.features has "
                f"{len(features)} values but compact_dim {declared} "
                f"declares {expected}"
            ]
    return _check_compact_recompute(scenario, compact, features, where)


def _positive_dim(value: Any, floor: int) -> int | None:
    if (
        isinstance(value, int)
        and not isinstance(value, bool)
        and floor <= value <= MAX_RECOMPUTE_DIM
    ):
        return value
    return None


def _check_compact_recompute(
    scenario: dict[str, Any],
    compact: dict[str, Any],
    features: list[Any],
    where: str,
) -> list[str]:
    """The features must recompute from the context they claim to describe.

    Width and finiteness alone let a correctly rehashed record replace the
    student input with arbitrary finite values of the same length while
    ``router_baseline`` consumes them as the input paired with the teacher's
    label — a corrupted input-label pairing that could change the baseline
    and the escalation verdict. The featurizer is deterministic, so the
    validator recomputes ``compact_view(featurize(context))`` instead of
    trusting the vector.
    """

    if compact.get("featurizer") != FEATURIZER_ID:
        return [
            f"{where}.scenario.compact_input.featurizer must be "
            f"{FEATURIZER_ID!r} so the student input can be recomputed, got "
            f"{compact.get('featurizer')!r}"
        ]
    feature_dim = _positive_dim(compact.get("feature_dim"), 4)
    compact_dim = _positive_dim(compact.get("compact_dim"), 1)
    if feature_dim is None or compact_dim is None:
        return [
            f"{where}.scenario.compact_input must declare integer "
            f"feature_dim (4..{MAX_RECOMPUTE_DIM}) and compact_dim "
            f"(1..{MAX_RECOMPUTE_DIM}) so the student input can be recomputed"
        ]
    context = scenario.get("context")
    if not isinstance(context, str) or not context.strip():
        # Reported by the context-digest check; nothing to recompute from.
        return []
    expected = compact_view(featurize(context, feature_dim), compact_dim)
    if len(features) != len(expected) or any(
        abs(float(value) - target) > 1e-9
        for value, target in zip(features, expected)
    ):
        return [
            f"{where}.scenario.compact_input.features: "
            "COMPACT_INPUT_NOT_REPRODUCIBLE — the recorded features do not "
            "recompute from the context with the declared featurizer"
        ]
    return []


def _check_scenario_context(scenario: Any, where: str) -> list[str]:
    """The student-visible context, its digest, and the compact input."""

    if not isinstance(scenario, dict):
        return []
    return _check_context_digest(scenario, where) + _check_compact_input(
        scenario, where
    )


def _check_fingerprint_identity(fingerprint: dict[str, Any], where: str) -> list[str]:
    """Model, checkpoint, configuration digest, and the teacher flag."""

    errors: list[str] = []
    for field in ("model", "revision_or_checkpoint", "configuration_sha256"):
        value = fingerprint.get(field)
        if not isinstance(value, str) or not value.strip():
            errors.append(f"{where}.oracle.fingerprint.{field} must be recorded")
    # "not-a-digest" satisfied the non-empty check above, so the promised
    # configuration digest could be absent in everything but name and the
    # teacher configuration could never be audited.
    configuration_digest = fingerprint.get("configuration_sha256")
    if isinstance(configuration_digest, str) and configuration_digest.strip():
        if not oc.SHA256_RE.match(configuration_digest):
            errors.append(
                f"{where}.oracle.fingerprint.configuration_sha256 must be a "
                f"64-character sha256 hex digest, got "
                f"{configuration_digest!r}"
            )
    if not isinstance(fingerprint.get("is_llm_teacher"), bool):
        errors.append(
            f"{where}.oracle.fingerprint.is_llm_teacher must be a boolean"
        )
    return errors


def _non_teacher_identity(oracle: dict[str, Any], fingerprint: dict[str, Any]) -> str | None:
    """The stand-in identity an oracle block carries, if it carries one.

    The fingerprint's ``model`` is caller-controlled prose; the oracle's own
    name, type and implementation are what the producing code wrote. All four
    are checked so renaming one field cannot launder a stand-in.
    """

    if oc.is_enum_value(fingerprint.get("model"), NON_TEACHER_ORACLE_NAMES):
        return f"fingerprint.model {fingerprint.get('model')!r}"
    if oc.is_enum_value(oracle.get("name"), NON_TEACHER_ORACLE_NAMES):
        return f"oracle.name {oracle.get('name')!r}"
    if oc.is_enum_value(oracle.get("type"), NON_TEACHER_ORACLE_TYPES):
        return f"oracle.type {oracle.get('type')!r}"
    if oc.is_enum_value(oracle.get("implementation"), NON_TEACHER_IMPLEMENTATIONS):
        return f"oracle.implementation {oracle.get('implementation')!r}"
    return None


def _check_laundered_oracle(
    oracle: Any, fingerprint: dict[str, Any], where: str
) -> list[str]:
    """A non-teacher stand-in may not be recorded as an authoritative teacher."""

    if not isinstance(oracle, dict) or oracle.get("authority") != oc.AUTHORITY_AUTHORITATIVE:
        return []
    identity = _non_teacher_identity(oracle, fingerprint)
    if identity is not None:
        return [
            f"{where}.oracle: LAUNDERED_REFERENCE_ORACLE — {identity} names a "
            "non-teacher stand-in and may not be recorded as an authoritative "
            "teacher"
        ]
    return []


def _sealed_hub_card(fingerprint: Any) -> dict[str, int] | None:
    """The sealed Hub MoE card for ``fingerprint.model``, when one exists."""

    if not isinstance(fingerprint, dict):
        return None
    model = fingerprint.get("model")
    if isinstance(model, str):
        return SEALED_HUB_MOE_CARDS.get(model.strip())
    return None


def _is_authoritative_teacher_grounded(oracle: Any, result: Any) -> bool:
    """True when the record claims an authoritative LLM teacher trajectory."""

    return (
        isinstance(oracle, dict)
        and oracle.get("authority") == oc.AUTHORITY_AUTHORITATIVE
        and isinstance(result, dict)
        and result.get("is_llm_teacher") is True
        and result.get("teacher_grounded") is True
    )


def _claims_transformers(oracle: Any) -> bool:
    """Either known producer field keeps the Transformers contract active."""

    return isinstance(oracle, dict) and (
        oracle.get("name") == TransformersMoERouter.name
        or oracle.get("implementation") == TRANSFORMERS_MOE_IMPLEMENTATION
    )


def _claims_transformers_or_sealed_moe(oracle: Any, fingerprint: Any) -> bool:
    """A Transformers producer identity or a sealed Hub MoE card model."""

    return _claims_transformers(oracle) or _sealed_hub_card(fingerprint) is not None


def _check_transformers_identity(oracle: Any, where: str) -> list[str]:
    """Known producer claims must retain their implementation and oracle type."""

    if not _claims_transformers(oracle):
        return []
    return [
        f"{where}.oracle.{field}: TRANSFORMERS_IDENTITY_MISMATCH — expected {expected!r}"
        for field, expected in (
            ("implementation", TRANSFORMERS_MOE_IMPLEMENTATION),
            ("type", TransformersMoERouter.oracle_type),
        )
        if oracle.get(field) != expected
    ]


def _check_authoritative_checkpoint(
    oracle: Any, fingerprint: Any, where: str
) -> list[str]:
    """An authoritative router record must pin an immutable checkpoint.

    ``resolve_checkpoint`` protects the live Transformers adapter, but a
    replayed recording could otherwise carry ``revision_or_checkpoint:
    "main"`` — a mutable name under which different weight revisions share
    one teacher identity while the configuration digest stays the same.

    For models on :data:`SEALED_HUB_MOE_CARDS`, a format-valid 40-hex string is
    still insufficient: the ``(model, revision)`` pair must appear in
    :data:`SEALED_HUB_MOE_REVISIONS` with a matching ``configuration_sha256``.
    No Hub network calls — unbound digests fail closed.
    """

    if not (
        isinstance(oracle, dict)
        and oracle.get("authority") == oc.AUTHORITY_AUTHORITATIVE
        and isinstance(fingerprint, dict)
    ):
        return []
    revision = fingerprint.get("revision_or_checkpoint")
    if not (isinstance(revision, str) and COMMIT_SHA_RE.match(revision.strip())):
        return [
            f"{where}.oracle.fingerprint.revision_or_checkpoint must be a "
            f"resolved 40-hex commit for an authoritative router record, got "
            f"{revision!r} — a mutable name can serve different weights under "
            "one recorded identity"
        ]
    revision = revision.strip()
    model = fingerprint.get("model")
    if not isinstance(model, str) or model.strip() not in SEALED_HUB_MOE_CARDS:
        return []
    model = model.strip()
    sealed_digest = SEALED_HUB_MOE_REVISIONS.get((model, revision))
    config_digest = fingerprint.get("configuration_sha256")
    if sealed_digest is None:
        return [
            f"{where}.oracle.fingerprint: UNBOUND_HUB_REVISION — "
            f"revision_or_checkpoint {revision!r} is not a sealed "
            f"(model, revision) for {model!r}; format-valid 40-hex alone "
            "does not bind an authoritative teacher checkpoint"
        ]
    if not isinstance(config_digest, str) or config_digest != sealed_digest:
        return [
            f"{where}.oracle.fingerprint: UNBOUND_HUB_REVISION — "
            f"configuration_sha256 must match the sealed digest for "
            f"({model!r}, {revision!r})"
        ]
    return []


def _check_sealed_hub_cardinality(
    fingerprint: Any, oracle: Any, result: Any, where: str
) -> list[str]:
    """Bind declared depth/experts to the sealed Hub card for the model.

    Authoritative teacher-grounded records whose ``fingerprint.model`` matches
    a sealed card may not self-attest a different ``num_layers`` /
    ``num_local_experts`` / ``num_experts_per_tok``.
    """

    if not _is_authoritative_teacher_grounded(oracle, result):
        return []
    card = _sealed_hub_card(fingerprint)
    if card is None or not isinstance(fingerprint, dict):
        return []
    errors: list[str] = []
    checks = (
        ("num_layers", card["num_hidden_layers"], "num_hidden_layers"),
        ("num_local_experts", card["num_local_experts"], "num_local_experts"),
        ("num_experts_per_tok", card["num_experts_per_tok"], "num_experts_per_tok"),
    )
    model = str(fingerprint.get("model")).strip()
    for field, expected, card_field in checks:
        declared = fingerprint.get(field)
        if declared != expected:
            errors.append(
                f"{where}.oracle.fingerprint: SEALED_HUB_MOE_CARDINALITY — "
                f"{field} is {declared!r} but sealed Hub card for {model!r} "
                f"has {card_field}={expected}"
            )
    return errors


def _check_teacher_router_logits(
    layers: list[Any], oracle: Any, fingerprint: Any, result: Any, where: str
) -> list[str]:
    """Authoritative Transformers / sealed-card teachers must expose logits.

    Fabricated top-k without a teacher run omits ``router_logits``; requiring
    them (with the existing ordering check) closes that launder. Recorded
    teachers that are not TransformersMoERouter and not on a sealed card may
    still omit logits.
    """

    if not _is_authoritative_teacher_grounded(oracle, result):
        return []
    if not _claims_transformers_or_sealed_moe(oracle, fingerprint):
        return []
    errors: list[str] = []
    for index, layer in enumerate(layers):
        spot = f"{where}.result.routing.layers[{index}]"
        if not isinstance(layer, dict):
            continue
        logits = layer.get("router_logits")
        if logits is None:
            errors.append(
                f"{spot}: TEACHER_ROUTER_LOGITS_REQUIRED — authoritative "
                "TransformersMoERouter / sealed Hub MoE teacher records must "
                "expose router_logits so top_k can be rebound to a real gate"
            )
    return errors


def _check_teacher_fingerprint(oracle: Any, fingerprint: Any, where: str) -> list[str]:
    """The recorded teacher identity: model, checkpoint, configuration digest."""

    if not isinstance(fingerprint, dict):
        return [
            f"{where}.oracle.fingerprint must record the teacher model, checkpoint "
            "and configuration"
        ]
    return (
        _check_fingerprint_identity(fingerprint, where)
        + _check_laundered_oracle(oracle, fingerprint, where)
        + _check_transformers_identity(oracle, where)
        + _check_teacher_oracle_type(oracle, where)
    )


def _check_teacher_oracle_type(oracle: Any, where: str) -> list[str]:
    """An authoritative router record must name a teacher-capable oracle type."""

    if not (
        isinstance(oracle, dict)
        and oracle.get("authority") == oc.AUTHORITY_AUTHORITATIVE
    ):
        return []
    oracle_type = oracle.get("type")
    if oc.is_enum_value(oracle_type, TEACHER_ORACLE_TYPES):
        return []
    return [
        f"{where}.oracle.type: {oracle_type!r} is not a teacher-capable oracle "
        f"type {sorted(TEACHER_ORACLE_TYPES)} — an authoritative routing label "
        "must come from a model router or a recording of one"
    ]


def _check_is_llm_teacher(
    result: dict[str, Any], fingerprint: Any, where: str
) -> list[str]:
    """The result's teacher flag must be a boolean and match the fingerprint."""

    if not isinstance(result.get("is_llm_teacher"), bool):
        return [f"{where}.result.is_llm_teacher must be a boolean"]
    if (
        isinstance(fingerprint, dict)
        and isinstance(fingerprint.get("is_llm_teacher"), bool)
        and result["is_llm_teacher"] != fingerprint["is_llm_teacher"]
    ):
        return [
            f"{where}.result.is_llm_teacher disagrees with the oracle fingerprint"
        ]
    return []


def _check_teacher_grounded(
    result: dict[str, Any], oracle: dict[str, Any], where: str
) -> list[str]:
    """teacher_grounded follows from the teacher flag and the oracle authority."""

    errors: list[str] = []
    expected = bool(
        result.get("is_llm_teacher")
        and oracle.get("authority") == oc.AUTHORITY_AUTHORITATIVE
    )
    if result.get("teacher_grounded") is not expected:
        errors.append(
            f"{where}.result.teacher_grounded must be {expected} for an "
            f"{oracle.get('authority')!r} oracle with is_llm_teacher="
            f"{result.get('is_llm_teacher')!r}"
        )
    # An authoritative router oracle must be a teacher. Otherwise a
    # stand-in's routing reaches curation with teacher_grounded false and
    # nothing downstream objecting.
    if (
        oracle.get("authority") == oc.AUTHORITY_AUTHORITATIVE
        and result.get("teacher_grounded") is not True
    ):
        errors.append(
            f"{where}.oracle: an authoritative router oracle must be "
            "teacher-grounded; mark a non-teacher oracle reference_only"
        )
    return errors


def _check_teacher_grounding(
    result: dict[str, Any], oracle: Any, fingerprint: Any, where: str
) -> list[str]:
    """`is_llm_teacher` and `teacher_grounded` against the oracle's authority."""

    errors = _check_is_llm_teacher(result, fingerprint, where)
    if isinstance(oracle, dict):
        errors += _check_teacher_grounded(result, oracle, where)
    return errors


def _check_measurement_reconciliation(
    result: dict[str, Any], routing: dict[str, Any], layers: list[Any], where: str
) -> list[str]:
    """Reconcile the compact targets with the routing they summarise.

    The compact targets in result.measurements describe the last layer and
    the cross-layer agreement.
    """

    errors: list[str] = []
    last = layers[-1] if isinstance(layers[-1], dict) else {}
    expected_measurements = {
        "top1_top2_margin": last.get("top1_top2_margin"),
        "routing_entropy": last.get("routing_entropy"),
        "expert_agreement": routing.get("expert_agreement"),
    }
    measurements = result.get("measurements")
    reconciled: set[str] = set()
    for item, quantity, expected in _numeric_router_measurements(measurements, expected_measurements):
        if oc.is_true(item.get("measured")):
            # A `measured: false` reading is a modelled value wearing a
            # promised router target's name — it does not satisfy the
            # completeness requirement below.
            reconciled.add(quantity)
        if abs(float(item["value"]) - float(expected)) > 1e-6:
            errors.append(
                f"{where}.result: measured {quantity} is {item['value']} but the "
                f"recorded routing says {expected}"
            )
        detail = item.get("detail")
        detail = detail if isinstance(detail, dict) else {}
        if quantity in ("top1_top2_margin", "routing_entropy"):
            # These targets summarise the last layer; claiming another layer
            # keeps the value right while the trajectory attribution lies.
            if detail.get("layer") != last.get("layer"):
                errors.append(
                    f"{where}.result: {quantity} is attributed to layer "
                    f"{detail.get('layer')!r} but the routing's last layer is "
                    f"{last.get('layer')!r}"
                )
        elif quantity == "expert_agreement" and detail.get("across_layers") != len(layers):
            errors.append(
                f"{where}.result: expert_agreement claims to cover "
                f"{detail.get('across_layers')!r} layers but the routing "
                f"records {len(layers)}"
            )
    return errors + _missing_promised_measurements(
        expected_measurements, reconciled, where
    )


def _check_router_measurement_meters(result: dict[str, Any], oracle: Any, where: str) -> list[str]:
    """The producer stamps its own name on each compact router reading."""

    meter = oracle.get("name") if isinstance(oracle, dict) else None
    measurements = result.get("measurements")
    if not isinstance(measurements, list):
        return []
    quantities = ("top1_top2_margin", "routing_entropy", "expert_agreement")
    return [
        f"{where}.result.measurements[{index}].meter: MEASUREMENT_ORACLE_MISMATCH "
        "— router measurements must name the producing oracle"
        for index, item in enumerate(measurements)
        if isinstance(item, dict) and item.get("quantity") in quantities
        and (not isinstance(meter, str) or not meter.strip() or item.get("meter") != meter)
    ]


def _numeric_router_measurements(measurements, expected_measurements):
    """Yield numeric readings whose quantities are promised by the routing."""

    for item in measurements if isinstance(measurements, list) else []:
        if not isinstance(item, dict):
            continue
        quantity = item.get("quantity")
        if not isinstance(quantity, str):
            # An unhashable quantity raised TypeError out of the dict lookup
            # and aborted validation of the whole run; the shared measurement
            # checker already reports the malformed item as a finding.
            continue
        expected = expected_measurements.get(quantity)
        if expected is None or not oc.is_number(expected):
            continue
        if not oc.is_number(item.get("value")):
            continue
        yield item, quantity, expected


def _missing_promised_measurements(
    expected_measurements: dict[str, Any], reconciled: set[str], where: str
) -> list[str]:
    """Every promised compact target must be present, not just the survivors.

    Validating only the readings that happen to be present would let a record
    delete ``routing_entropy`` and ``expert_agreement`` while keeping its
    digest and curation eligibility — measurement-based consumers would
    silently lose two of the three promised router targets.
    """

    return [
        f"{where}.result.measurements must record {quantity} as a measured "
        "numeric reading — the recorded routing promises it"
        for quantity, expected in sorted(expected_measurements.items())
        if oc.is_number(expected) and quantity not in reconciled
    ]


def _check_declared_count_authority(
    expert_count: int | None, oracle: Any, where: str
) -> list[str]:
    if (
        expert_count is None
        and isinstance(oracle, dict)
        and oracle.get("authority") == oc.AUTHORITY_AUTHORITATIVE
    ):
        # Without a declared count the per-layer range check is disabled, so
        # an authoritative recording with no logits could carry expert ids
        # like [-1, 999] straight into curation.
        return [
            f"{where}.oracle.fingerprint.num_local_experts must declare a "
            "positive expert count for an authoritative router record — "
            "without it the routed expert ids cannot be range-checked"
        ]
    return []


_CONFIGURATION_FINGERPRINT_PAIRS = (
    ("num_experts", "num_local_experts"),
    ("num_layers", "num_layers"),
    ("top_k", "num_experts_per_tok"),
)


def _check_configuration_binding(
    record: dict[str, Any], oracle: Any, fingerprint: Any, where: str
) -> list[str]:
    """The declared gate configuration must agree with its fingerprint."""

    if not isinstance(oracle, dict):
        return []
    configuration = oracle.get("configuration")
    if not isinstance(configuration, dict) or not isinstance(fingerprint, dict):
        return []
    errors: list[str] = []
    for configuration_key, fingerprint_key in _CONFIGURATION_FINGERPRINT_PAIRS:
        declared = configuration.get(configuration_key)
        fingerprinted = fingerprint.get(fingerprint_key)
        if declared is not None and fingerprinted is not None and declared != fingerprinted:
            errors.append(
                f"{where}.oracle.configuration.{configuration_key} is "
                f"{declared!r} but oracle.fingerprint.{fingerprint_key} is "
                f"{fingerprinted!r}"
            )
    feature_dim = configuration.get("feature_dim")
    scenario = record.get("scenario")
    compact = scenario.get("compact_input") if isinstance(scenario, dict) else None
    declared_dim = compact.get("feature_dim") if isinstance(compact, dict) else None
    if (
        isinstance(feature_dim, int)
        and not isinstance(feature_dim, bool)
        and declared_dim is not None
        and declared_dim != feature_dim
    ):
        errors.append(
            f"{where}.scenario.compact_input.feature_dim is {declared_dim!r} "
            f"but oracle.configuration.feature_dim is {feature_dim!r} — the "
            "compact input must be a view of the features the router gated on"
        )
    return errors


def _reference_seed(fingerprint: dict[str, Any]) -> int | None:
    revision = fingerprint.get("revision_or_checkpoint")
    if not (isinstance(revision, str) and revision.startswith("seed:")):
        return None
    try:
        return int(revision[5:])
    except ValueError:
        return None


def _check_reference_recompute(
    record: dict[str, Any], oracle: Any, fingerprint: Any, layers: list[Any], where: str
) -> list[str]:
    """Re-run the declared deterministic reference router and compare layers.

    Internal consistency checks cannot catch a record whose whole ``result``
    was copied from another row: only re-running the oracle over the recorded
    context pins the routing to this scenario. That is only possible for the
    known deterministic implementation — a teacher recording is intentionally
    not recomputable — so the check is scoped to it and fails closed when the
    declared dimensions or seed are missing.
    """

    if not (
        isinstance(oracle, dict)
        and oracle.get("implementation") == ReferenceMoERouter.implementation
        and isinstance(fingerprint, dict)
    ):
        return []
    scenario = record.get("scenario")
    context = scenario.get("context") if isinstance(scenario, dict) else None
    if not isinstance(context, str):
        return []  # reported by the scenario context check; nothing to recompute
    configuration = oracle.get("configuration")
    configuration = configuration if isinstance(configuration, dict) else {}
    # Dimensions the record does not declare fall back to the reference
    # defaults — not as a trust decision but because recompute is itself the
    # check: a record whose gate really ran at other dimensions mismatches
    # layer-for-layer, and one that ran at the defaults reproduces cleanly.
    def _declared(key: str, default: int) -> int:
        value = configuration.get(key)
        return value if isinstance(value, int) and not isinstance(value, bool) else default

    dim = _declared("feature_dim", FEATURE_DIM)
    seed = _reference_seed(fingerprint)
    if seed is None:
        seed = _DEFAULT_REFERENCE_SEED
    num_experts = _declared_expert_count(fingerprint) or _declared("num_experts", 8)
    num_layers = _declared_layer_count(fingerprint) or _declared("num_layers", 4)
    top_k = _declared_top_k(fingerprint) or _declared("top_k", 2)
    if not (
        0 < dim <= MAX_RECOMPUTE_DIM
        and 0 < num_experts <= MAX_RECOMPUTE_DIM
        and 0 < num_layers <= MAX_RECOMPUTE_DIM
        and top_k > 0
    ):
        # Recompute would allocate gates at whatever dimensions a forged
        # record declares; outside a bounded domain the routing cannot be
        # reproduced here — refused, not skipped.
        return [
            f"{where}.oracle: declared reference dimensions (feature_dim "
            f"{dim!r}, num_experts {num_experts!r}, num_layers "
            f"{num_layers!r}, top_k {top_k!r}) are outside the recomputable "
            f"domain [1, {MAX_RECOMPUTE_DIM}]; the routing cannot be verified"
        ]
    try:
        engine = ReferenceMoERouter(
            seed=seed,
            num_experts=num_experts,
            num_layers=num_layers,
            top_k=top_k,
            dim=dim,
        )
    except oc.ContractError as exc:
        return [
            f"{where}.oracle: declared reference configuration cannot run "
            f"({exc}); the recorded routing cannot be reproduced"
        ]
    observed = engine.route(context)
    if len(layers) != len(observed.layers):
        return [
            f"{where}.result.routing.layers has {len(layers)} layers but the "
            f"reference router computes {len(observed.layers)} for this context"
        ]
    errors: list[str] = []
    for index, (layer, actual) in enumerate(zip(layers, observed.layers)):
        spot = f"{where}.result.routing.layers[{index}]"
        if isinstance(layer, dict):
            errors += _recomputed_layer_mismatches(layer, actual, spot)
    if errors:
        errors.append(
            f"{where}.result: REFERENCE_RECOMPUTE_MISMATCH — the recorded "
            "routing does not match a recomputed run of the declared "
            "reference router"
        )
    return errors


def check_family(record: dict[str, Any], where: str) -> list[str]:
    """Family checks: real routing, recorded teacher identity, sane targets."""

    errors = _check_scenario_context(record.get("scenario"), where)
    errors += oc.check_oracle_label_leak(record, where)

    oracle = record.get("oracle")
    fingerprint = oracle.get("fingerprint") if isinstance(oracle, dict) else None
    errors += _check_teacher_fingerprint(oracle, fingerprint, where)
    errors += _check_configuration_binding(record, oracle, fingerprint, where)

    result = record.get("result")
    if not isinstance(result, dict):
        return errors + [f"{where}.result must be an object"]
    errors += _check_teacher_grounding(result, oracle, fingerprint, where)

    routing = result.get("routing")
    if not isinstance(routing, dict):
        return errors + [f"{where}.result.routing must be an object"]
    layers = routing.get("layers")
    if not isinstance(layers, list) or not layers:
        return errors + [f"{where}.result.routing.layers must be a non-empty array"]

    expert_count = _declared_expert_count(fingerprint)
    errors += _check_declared_count_authority(expert_count, oracle, where)
    errors += _check_declared_trajectory_authority(fingerprint, oracle, where)
    errors += _check_authoritative_checkpoint(oracle, fingerprint, where)
    errors += _check_sealed_hub_cardinality(fingerprint, oracle, result, where)
    errors += _check_routing_layers(
        layers, expert_count, _declared_top_k(fingerprint), where
    )
    errors += _check_teacher_router_logits(
        layers, oracle, fingerprint, result, where
    )
    errors += _check_layer_count(layers, fingerprint, where)
    errors += _check_reference_recompute(record, oracle, fingerprint, layers, where)
    errors += _check_derived_routing_labels(result, routing, layers, where)
    errors += _check_measurement_reconciliation(result, routing, layers, where)
    errors += _check_router_measurement_meters(result, oracle, where)
    return errors
