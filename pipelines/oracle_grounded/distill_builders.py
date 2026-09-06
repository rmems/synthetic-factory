#!/usr/bin/env python3
"""Block and record builders for the distillation contract (issue #78).

Generators propose, oracles decide: :class:`Proposal` carries the
generator-owned sections of a record and :class:`Verdict` the oracle-owned
ones, so :func:`build_record` can only be handed a record whose ownership
split is visible at the call site. Every builder refuses a value outside the
contract's vocabulary with ``ContractError`` rather than writing it.
"""

from __future__ import annotations

import copy
from dataclasses import dataclass
from typing import Any

from . import distill_vocabulary as vocab
from . import envelope
from .import_twins import bind_import_twin


def _copied(section: Any, name: str) -> Any:
    """A private copy of one caller-supplied section, or a ContractError.

    The record must hold copies so the caller's objects stay theirs, and the
    copy runs before the digest boundary; a section nested past the
    recursion limit, or holding a value that cannot be copied, is malformed
    input and is refused the same way uncanonicalisable content is, never as
    a raw copier exception. Only those two failures are translated.
    """

    try:
        return copy.deepcopy(section)
    except (RecursionError, TypeError) as exc:
        raise envelope.ContractError(
            f"record content cannot be copied into a record: the caller-supplied {name} "
            "section is nested past the recursion limit or holds a value that cannot be copied"
        ) from exc


@dataclass(frozen=True)
class MeasurementOptions:
    """The keyword refinements :func:`new_measurement` accepts.

    ``unit`` is the caller's claim about the quantity's unit, cross-checked
    against the registry rather than written; ``measured`` defaults to what
    the meter registry says (``True`` for an instrument, ``False`` for a meter
    in ``MODELED_METERS``), may be lowered to ``False`` for any meter, and can
    never be raised to ``True`` for a modelled meter; ``detail`` is free-form
    context copied into the measurement.
    """

    unit: str | None = None
    measured: bool | None = None
    detail: dict[str, Any] | None = None


def _canonical_unit(quantity: str, claimed_unit: str | None) -> str:
    """The registry unit, refusing an unknown quantity or a contradicting claim."""

    if quantity not in vocab.QUANTITY_UNITS:
        raise envelope.ContractError(f"unknown measurement quantity: {quantity!r}")
    canonical_unit = vocab.QUANTITY_UNITS[quantity]
    if claimed_unit is not None and claimed_unit != canonical_unit:
        raise envelope.ContractError(
            f"{quantity} must be reported in {canonical_unit!r}, got {claimed_unit!r}"
        )
    return canonical_unit


def _resolve_measured(meter: str, claimed: bool | None) -> bool:
    """``measured`` follows the meter registry; a modelled meter cannot claim it.

    For every quantity, not only energy: a reading from ``analytic_op_count``
    or ``synops_model`` is a model's output whatever it counts, and the
    curation gate's NO_MEASURED_READING check relies on ``measured`` meaning
    "an instrument took this" rather than "the producer said so".
    """

    if claimed is not None and not isinstance(claimed, bool):
        raise envelope.ContractError(f"measured must be True, False or None, got {claimed!r}")
    modelled = meter in vocab.MODELED_METERS
    if claimed is None:
        return not modelled
    if claimed and modelled:
        raise envelope.ContractError(
            f"meter {meter!r} models rather than measures; it cannot claim measured=True"
        )
    return bool(claimed)


def _check_energy_meter(quantity: str, meter: str, measured: bool) -> None:
    """An energy-class quantity must come measured from an energy meter."""

    if quantity not in vocab.ENERGY_QUANTITIES:
        return
    if measured and meter in vocab.MEASURED_ENERGY_METERS:
        return
    raise envelope.ContractError(
        f"{quantity} requires a measured energy meter "
        f"(one of {sorted(vocab.MEASURED_ENERGY_METERS)}), got {meter!r}"
    )


def new_measurement(
    quantity: str, value: float, meter: str, **options: Any
) -> dict[str, Any]:
    """Build one oracle-side measurement.

    Keyword options are the fields of :class:`MeasurementOptions`. Raises
    ``ContractError`` for an unknown quantity, a unit that disagrees with the
    registry, or an energy-class quantity from a non-energy meter.
    """

    chosen = MeasurementOptions(**options)
    canonical_unit = _canonical_unit(quantity, chosen.unit)
    if not envelope.is_number(value):
        raise envelope.ContractError(
            f"{quantity} value must be a finite number, got {value!r}"
        )
    measured = _resolve_measured(meter, chosen.measured)
    _check_energy_meter(quantity, meter, measured)
    if chosen.detail is not None and not isinstance(chosen.detail, dict):
        raise envelope.ContractError(f"{quantity} detail must be an object, got {chosen.detail!r}")
    payload: dict[str, Any] = {
        "quantity": quantity,
        # An exact integer stays one: float() would round a count past 2**53.
        "value": value if vocab.is_genuine_int(value) else float(value),
        "unit": canonical_unit,
        "meter": meter,
        "measured": measured,
        "source": "oracle",
    }
    if chosen.detail:
        payload["detail"] = _copied(chosen.detail, "measurement detail")
    return payload


@dataclass(frozen=True)
class GeneratorIdentity:
    """Who proposed: the generator's name, version, kind and (for an llm) model."""

    name: str
    version: str
    kind: str = "programmatic"
    model: str | None = None


def _refuse_generator_kind(identity: GeneratorIdentity) -> None:
    """A generator kind outside the vocabulary, or an llm without a model."""

    if identity.kind not in vocab.GENERATOR_KINDS:
        raise envelope.ContractError(f"unknown generator kind: {identity.kind!r}")
    if identity.kind == "llm" and not identity.model:
        raise envelope.ContractError("an llm generator must name its model")


def _refuse_generator_fields(identity: GeneratorIdentity, seed: Any) -> None:
    """The refusals the generator block check would raise later, raised now."""

    if vocab.missing_string(identity.name) or vocab.missing_string(identity.version):
        raise envelope.ContractError("a generator must carry a non-empty name and version")
    if seed is not None and not vocab.is_genuine_int(seed):
        raise envelope.ContractError(f"a generator seed must be an integer or None, got {seed!r}")


def new_generator(
    identity: GeneratorIdentity,
    *,
    seed: int | None = None,
    notes: str | None = None,
) -> dict[str, Any]:
    """Build the generator block. Authority is pinned to ``propose_only``."""

    _refuse_generator_kind(identity)
    _refuse_generator_fields(identity, seed)
    block: dict[str, Any] = {
        "name": identity.name,
        "kind": identity.kind,
        "version": identity.version,
        "seed": seed,
        "authority": vocab.GENERATOR_AUTHORITY,
    }
    if identity.model:
        block["model"] = identity.model
    if notes:
        block["notes"] = notes
    return block


@dataclass(frozen=True)
class OracleIdentity:
    """Who decided, and what its word is worth.

    ``authority`` is ``authoritative`` for an oracle whose output may ground a
    training label, and ``reference_only`` for a stand-in whose output proves
    the pipeline shape but must never be curated as teacher truth.
    """

    name: str
    oracle_type: str
    implementation: str
    version: str
    authority: str = vocab.AUTHORITY_AUTHORITATIVE


@dataclass(frozen=True)
class OracleRun:
    """How one oracle run was set up: its configuration and reproducibility pins."""

    configuration: dict[str, Any] | None = None
    seed: int | None = None
    commit: str | None = None
    fingerprint: dict[str, Any] | None = None


def new_oracle(identity: OracleIdentity, run: OracleRun | None = None) -> dict[str, Any]:
    """Build the oracle block from the oracle's identity and this run's setup."""

    if run is None:
        run = OracleRun()
    if identity.oracle_type not in vocab.ORACLE_TYPES:
        raise envelope.ContractError(f"unknown oracle type: {identity.oracle_type!r}")
    if identity.authority not in vocab.ORACLE_AUTHORITIES:
        raise envelope.ContractError(f"unknown oracle authority: {identity.authority!r}")
    _refuse_oracle_fields(identity)
    block: dict[str, Any] = {
        "name": identity.name,
        "type": identity.oracle_type,
        "implementation": identity.implementation,
        "version": identity.version,
        "authority": identity.authority,
        "configuration": _copied(run.configuration, "oracle") if run.configuration else {},
        "seed": run.seed,
        "commit": run.commit,
    }
    if run.fingerprint is not None:
        block["fingerprint"] = _copied(run.fingerprint, "oracle")
    return block


def _refuse_oracle_fields(identity: OracleIdentity) -> None:
    """The refusals the oracle block check would raise later, raised now."""

    for field in ("name", "implementation", "version"):
        if vocab.missing_string(getattr(identity, field)):
            raise envelope.ContractError(f"an oracle must carry a non-empty {field}")


def new_result(
    *,
    status: str = vocab.RESULT_MEASURED,
    measurements: list[dict[str, Any]] | None = None,
    abstention_reason: str | None = None,
    **fields: Any,
) -> dict[str, Any]:
    """Build the oracle-side result block."""

    if status not in vocab.RESULT_STATUSES:
        raise envelope.ContractError(f"unknown result status: {status!r}")
    payload: dict[str, Any] = {
        "status": status,
        "measurements": list(measurements or []),
    }
    if status == vocab.RESULT_MEASURED and not payload["measurements"]:
        raise envelope.ContractError("a measured result needs at least one measurement")
    if status == vocab.RESULT_ABSTAINED:
        if not (abstention_reason or "").strip():
            raise envelope.ContractError("an abstained result needs an abstention_reason")
        payload["abstention_reason"] = abstention_reason
    payload.update(_copied(fields, "result"))
    return payload


def new_provenance(producer: str, **fields: Any) -> dict[str, Any]:
    """Build the provenance block with a UTC production timestamp."""

    payload: dict[str, Any] = {"producer": producer, "produced_at": envelope.utc_now_iso()}
    payload.update(_copied(fields, "provenance"))
    return payload


def unvalidated() -> dict[str, Any]:
    """Return the only validation block a producer is allowed to write."""

    return {"status": vocab.VALIDATION_UNVALIDATED, "validator": None, "findings": []}


@dataclass(frozen=True)
class RecordIdentity:
    """The record id and the family it belongs to."""

    record_id: str
    family: str


@dataclass(frozen=True)
class Proposal:
    """The generator-owned sections: what was proposed, never what was measured."""

    generator: dict[str, Any]
    scenario: dict[str, Any]
    intervention: dict[str, Any] | None = None
    candidate_prediction: dict[str, Any] | None = None


@dataclass(frozen=True)
class Verdict:
    """The oracle-owned sections: the oracle that ran and what it measured."""

    oracle: dict[str, Any]
    result: dict[str, Any]




def build_record(
    *,
    identity: RecordIdentity,
    proposal: Proposal,
    verdict: Verdict,
    provenance: dict[str, Any],
) -> dict[str, Any]:
    """Assemble one oracle-grounded record and stamp its content digest."""

    if identity.family not in vocab.FAMILIES:
        raise envelope.ContractError(f"unknown family: {identity.family!r}")
    record: dict[str, Any] = {
        "id": identity.record_id,
        "family": identity.family,
        "schema_version": vocab.SCHEMA_VERSION,
        "generator": _copied(proposal.generator, "generator"),
        "scenario": _copied(proposal.scenario, "scenario"),
        "oracle": _copied(verdict.oracle, "oracle"),
        "result": _copied(verdict.result, "result"),
        "provenance": _copied(provenance, "provenance"),
        "validation": unvalidated(),
    }
    if proposal.intervention is not None:
        record["intervention"] = _copied(proposal.intervention, "intervention")
    if proposal.candidate_prediction is not None:
        record["candidate_prediction"] = _copied(
            proposal.candidate_prediction, "candidate_prediction"
        )
    digest, failure = vocab.digest_or_failure(record)
    if failure is not None:
        raise envelope.ContractError(
            "record content cannot take the envelope's canonical form: a caller-supplied "
            "section holds a value that is not canonical UTF-8 JSON"
        ) from failure
    record["provenance"]["record_sha256"] = digest
    return record


bind_import_twin(__name__)
