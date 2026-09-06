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
from collections.abc import Iterable
from dataclasses import dataclass
from typing import Any

from . import distill_vocabulary as vocab
from . import envelope
from .import_twins import bind_import_twin


def _refuse(problems: Iterable[tuple[bool, str]]) -> None:
    """Raise ``ContractError`` with the message of the first problem that holds."""

    for holds, message in problems:
        if holds:
            raise envelope.ContractError(message)


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

    canonical_unit = vocab.QUANTITY_UNITS.get(quantity)
    _refuse((
        (canonical_unit is None, f"unknown measurement quantity: {quantity!r}"),
        (
            claimed_unit not in (None, canonical_unit),
            f"{quantity} must be reported in {canonical_unit!r}, got {claimed_unit!r}",
        ),
    ))
    return canonical_unit


def _resolve_measured(meter: str, claimed: bool | None) -> bool:
    """``measured`` follows the meter registry; a modelled meter cannot claim it.

    For every quantity, not only energy: a reading from ``analytic_op_count``
    or ``synops_model`` is a model's output whatever it counts, and the
    curation gate's NO_MEASURED_READING check relies on ``measured`` meaning
    "an instrument took this" rather than "the producer said so".
    """

    _refuse_measured_claim(meter, claimed)
    if claimed is None:
        return meter not in vocab.MODELED_METERS
    return claimed


def _refuse_measured_claim(meter: str, claimed: Any) -> None:
    """A claim that is not a boolean, or a modelled meter claiming ``measured=True``."""

    _refuse((
        (
            claimed is not None and not isinstance(claimed, bool),
            f"measured must be True, False or None, got {claimed!r}",
        ),
        (
            claimed is True and meter in vocab.MODELED_METERS,
            f"meter {meter!r} models rather than measures; it cannot claim measured=True",
        ),
    ))


def _check_energy_meter(quantity: str, meter: str, measured: bool) -> None:
    """An energy-class quantity must come measured from an energy meter."""

    if quantity not in vocab.ENERGY_QUANTITIES:
        return
    _refuse(((
        not (measured and meter in vocab.MEASURED_ENERGY_METERS),
        f"{quantity} requires a measured energy meter "
        f"(one of {sorted(vocab.MEASURED_ENERGY_METERS)}), got {meter!r}",
    ),))


def _refuse_measurement_shape(quantity: str, value: Any, detail: Any) -> None:
    """A value that is not a finite number, or a detail that is not an object."""

    _refuse((
        (not envelope.is_number(value), f"{quantity} value must be a finite number, got {value!r}"),
        (
            detail is not None and not isinstance(detail, dict),
            f"{quantity} detail must be an object, got {detail!r}",
        ),
    ))


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
    _refuse_measurement_shape(quantity, value, chosen.detail)
    measured = _resolve_measured(meter, chosen.measured)
    _check_energy_meter(quantity, meter, measured)
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

    _refuse((
        (identity.kind not in vocab.GENERATOR_KINDS, f"unknown generator kind: {identity.kind!r}"),
        (identity.kind == "llm" and not identity.model, "an llm generator must name its model"),
    ))


def _refuse_generator_fields(identity: GeneratorIdentity, seed: Any) -> None:
    """The refusals the generator block check would raise later, raised now."""

    _refuse((
        (
            vocab.missing_string(identity.name) or vocab.missing_string(identity.version),
            "a generator must carry a non-empty name and version",
        ),
        (
            seed is not None and not vocab.is_genuine_int(seed),
            f"a generator seed must be an integer or None, got {seed!r}",
        ),
    ))


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
    _refuse_oracle_identity(identity)
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


def _refuse_oracle_identity(identity: OracleIdentity) -> None:
    """The refusals the oracle block check would raise later, raised now."""

    _refuse((
        (identity.oracle_type not in vocab.ORACLE_TYPES, f"unknown oracle type: {identity.oracle_type!r}"),
        (
            identity.authority not in vocab.ORACLE_AUTHORITIES,
            f"unknown oracle authority: {identity.authority!r}",
        ),
        *(
            (vocab.missing_string(getattr(identity, name)), f"an oracle must carry a non-empty {name}")
            for name in ("name", "implementation", "version")
        ),
    ))


def new_result(
    *,
    status: str = vocab.RESULT_MEASURED,
    measurements: list[dict[str, Any]] | None = None,
    abstention_reason: str | None = None,
    **fields: Any,
) -> dict[str, Any]:
    """Build the oracle-side result block."""

    readings = list(measurements or [])
    _refuse_result_shape(status, readings, abstention_reason)
    payload: dict[str, Any] = {"status": status, "measurements": readings}
    if status == vocab.RESULT_ABSTAINED:
        payload["abstention_reason"] = abstention_reason
    payload.update(_copied(fields, "result"))
    return payload


def _refuse_result_shape(status: str, readings: list[Any], abstention_reason: str | None) -> None:
    """An unknown status, a measured result with no reading, or a silent abstention."""

    _refuse((
        (status not in vocab.RESULT_STATUSES, f"unknown result status: {status!r}"),
        (
            status == vocab.RESULT_MEASURED and not readings,
            "a measured result needs at least one measurement",
        ),
        (
            status == vocab.RESULT_ABSTAINED and vocab.missing_string(abstention_reason),
            "an abstained result needs an abstention_reason",
        ),
    ))


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

    _refuse(((identity.family not in vocab.FAMILIES, f"unknown family: {identity.family!r}"),))
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
