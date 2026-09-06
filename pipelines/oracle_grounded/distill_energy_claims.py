#!/usr/bin/env python3
"""The no-theoretical-energy rule for the distillation contract (issue #78).

No energy number may be modelled rather than measured -- whether it sits in
``result.measurements`` with a modelling meter, anywhere else under
``result`` as a bare number or inside an object that identifies itself as
energy, or as the denomination of a preference with no measured energy
behind it.

The energy-claim scan (D3) is structural. Energy numbers are legal in three
places only: a ``result.measurements`` entry from a measuring meter, the
preference's ``cost_value`` when a measured reading of its ``cost_quantity``
exists, and any other object that identifies energy through its own
``quantity`` / ``cost_quantity`` / ``unit`` / ``cost_unit`` fields, under the
same backing rule for every quantity it declares and, when it names a meter,
only from an energy meter. Everything else that
identifies itself as energy -- a bare number under an energy key, the numbers
in a list under one, an unbacked energy object -- is a theoretical claim, and
that identity survives containers: an identified object is a claim whenever a
number sits anywhere beneath it, and a dict or list under an energy key is a
claim whenever a number sits anywhere beneath that. Backing exempts only the
object itself: the numbers beneath a backed object are still judged by their
own keys, so a modelled reading cannot shelter inside a measured one, and
``result`` gains no shelter from an identity of its own. ``result.measurements``
entries, their ``detail`` included, stay with the measurement rule in
``distill_measurements`` (row 15 of the D3 matrix is held).

The walk is flat: an explicit stack, so a deeply nested result is reported
rather than raising ``RecursionError``. The hit cap
``envelope.MAX_RESERVED_KEY_HITS`` bounds how many findings are collected
before the walk stops; it bounds neither the work of visiting the record up
to that point nor the length of a path in the listing.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, NamedTuple

from . import distill_vocabulary as vocab
from . import envelope
from .import_twins import bind_import_twin


def _is_energy_key(key: str) -> bool:
    """True when a field name identifies an energy value: a quantity name or a unit token."""

    lowered = key.lower()
    if lowered in vocab.ENERGY_QUANTITIES:
        return True
    return any(token in vocab.ENERGY_TOKENS for token in lowered.split("_"))


def _energy_claim_error(item: dict[str, Any], quantity: str, spot: str) -> str | None:
    """Why this energy reading is a theoretical claim, or None when measured."""

    meter = item.get("meter")
    if envelope.is_enum_value(meter, vocab.MODELED_METERS) or item.get("measured") is not True:
        return (
            f"{spot}: THEORETICAL_ENERGY_CLAIM — {quantity} came from "
            f"meter {meter!r}; energy must be physically measured"
        )
    if not envelope.is_enum_value(meter, vocab.MEASURED_ENERGY_METERS):
        return (
            f"{spot}: THEORETICAL_ENERGY_CLAIM — {quantity} needs a meter in "
            f"{sorted(vocab.MEASURED_ENERGY_METERS)}, got {meter!r}"
        )
    return None


def _energy_measurement_claims(
    measurements: list[Any], where: str
) -> tuple[list[str], set[str]]:
    """Errors for modeled energy readings, plus the honestly measured ones."""

    errors: list[str] = []
    measured_energy_quantities: set[str] = set()
    for index, item in enumerate(measurements):
        if not isinstance(item, dict):
            continue
        quantity = item.get("quantity")
        if not envelope.is_enum_value(quantity, vocab.ENERGY_QUANTITIES):
            continue
        error = _energy_claim_error(item, quantity, f"{where}.result.measurements[{index}]")
        if error is not None:
            errors.append(error)
            continue
        measured_energy_quantities.add(quantity)
    return errors, measured_energy_quantities


# An object's energy identity is a set of requirements, one per declaring
# field pair; each requirement is the set of quantities whose measured reading
# would satisfy it (one named quantity, or every quantity carrying a unit).
Identity = frozenset[frozenset[str]]


def _energy_identity(value: dict[str, Any]) -> Identity | None:
    """The energy requirements an object declares through its own fields, or None.

    The regular pair (``quantity``, else ``unit``) and the cost pair
    (``cost_quantity``, else ``cost_unit``) are read independently, so a
    non-energy field on one side masks nothing on the other, and every
    declared quantity needs its own backing. A named quantity must itself be
    measured; a unit is satisfied by any quantity carrying it (``J`` is either
    joule quantity, ``Wh`` names none and so can never be backed).
    """

    requirements = frozenset(
        requirement
        for pair in (("quantity", "unit"), ("cost_quantity", "cost_unit"))
        if (requirement := _pair_requirement(value, *pair)) is not None
    )
    return requirements or None


def _pair_requirement(
    value: dict[str, Any], quantity_key: str, unit_key: str
) -> frozenset[str] | None:
    """What one quantity/unit field pair requires, or None when it names no energy."""

    quantity = value.get(quantity_key)
    if envelope.is_enum_value(quantity, vocab.ENERGY_QUANTITIES):
        return frozenset({quantity})
    unit = value.get(unit_key)
    if envelope.is_enum_value(unit, vocab.ENERGY_UNITS):
        return frozenset(q for q in vocab.ENERGY_QUANTITIES if vocab.QUANTITY_UNITS[q] == unit)
    return None


def _unbacked(identity: Identity, measured: set[str]) -> str:
    """The requirements no measured reading satisfies, listed; empty when all are met."""

    missing = sorted(
        "/".join(sorted(requirement)) or "that unit"
        for requirement in identity
        if not requirement & measured
    )
    return " and ".join(missing)


def _object_reason(
    value: dict[str, Any], identity: Identity, measured: set[str]
) -> str | None:
    """Why an energy-identified object is a claim, or None when it is legal (S3).

    Legal means every quantity it declares is backed by a measured reading
    from a measuring meter; a modelled meter or a declared ``measured: false``
    is a claim whatever backs it.
    """

    meter = value.get("meter") if "meter" in value else value.get("cost_meter")
    if envelope.is_enum_value(meter, vocab.MODELED_METERS):
        return f"modelled meter {meter!r}"
    if meter is not None and not envelope.is_enum_value(meter, vocab.MEASURED_ENERGY_METERS):
        # Backing never launders the meter an object names: the measurement
        # rule refuses energy from a measuring but non-energy meter, and so
        # does the object rule.
        return f"meter {meter!r} is not an energy meter"
    if "measured" in value and value["measured"] is not True:
        return "declared unmeasured"
    unbacked = _unbacked(identity, measured)
    if not unbacked:
        return None
    return f"no measured {unbacked} reading backs it"


# The energy context a container hands to everything beneath it: None (no
# energy claim in force) or a ``(root_path, finding_text)`` claim that the
# first number beneath confirms.
Context = tuple[str, str] | None


class _Frame(NamedTuple):
    """One entry on the walk's explicit stack: where it sits and the context it inherits."""

    path: str
    key: str
    value: Any
    context: Context


@dataclass
class _Hits:
    """What the walk collects: bare energy numbers (R2) and the claims numbers confirmed."""

    bare: list[str] = field(default_factory=list)
    claims: dict[str, str] = field(default_factory=dict)

    def __len__(self) -> int:
        return len(self.bare) + len(self.claims)

    def listing(self) -> list[str]:
        return self.bare + list(self.claims.values())


def _dict_context(frame: _Frame, measured: set[str]) -> Context:
    """The context a dict hands its children.

    Its own identity (R1) comes first: an unbacked or modelled identified
    object is a claim, and a backed one hands its children no context at all,
    so the numbers beneath it are still judged by their own keys (R2 has no
    backing exemption). Without an identity, a dict under an energy key (R2)
    is a claim container, and otherwise the inherited context carries on.
    ``result.preference`` itself is the preference rule's business (S2) and
    hands its children the inherited context untouched.
    """

    if frame.path != "result.preference":
        identity = _energy_identity(frame.value)
        if identity is not None:
            reason = _object_reason(frame.value, identity, measured)
            return None if reason is None else (frame.path, f"{frame.path} ({reason})")
    if frame.context is None and _is_energy_key(frame.key):
        return frame.path, f"{frame.path} (energy-keyed container)"
    return frame.context


def _dict_frames(frame: _Frame, context: Context) -> list[_Frame]:
    """Stack frames for a dict's entries, in source order once popped."""

    return [
        _Frame(f"{frame.path}.{child}", child, item, context)
        for child, item in reversed(list(frame.value.items()))
    ]


def _list_frames(frame: _Frame) -> list[_Frame]:
    """Stack frames for a list's items: a list keeps its key and its context.

    The numbers in a list under an energy key are energy numbers (R3), and
    every element of a list inside a claim confirms that claim.
    """

    return [
        _Frame(f"{frame.path}[{index}]", frame.key, item, frame.context)
        for index, item in reversed(list(enumerate(frame.value)))
    ]


def _note_number(frame: _Frame, hits: _Hits) -> None:
    """A number under no context is judged by its key (R2); under a claim it confirms it."""

    if frame.context is None:
        if _is_energy_key(frame.key):
            hits.bare.append(frame.path)
    else:
        hits.claims.setdefault(frame.context[0], frame.context[1])


def _energy_scan_hits(result: dict[str, Any], measured: set[str]) -> list[str]:
    """Paths of energy claims outside ``result.measurements``.

    Identity propagates through containers as a per-frame context, so a
    number confirms the nearest enclosing claim (an identified object, or a
    container under an energy key) rather than being judged by its own key
    alone; a number under no context is judged by its key (R2). ``result``
    itself is an object too: ``cost_quantity`` flipped to an energy quantity
    beside numeric content is the relabelling the energy family's review
    reproduced. The walk stops once the cap is reached; see the module
    docstring for what the cap does and does not bound.
    """

    hits = _Hits()
    root = _Frame("result", "result", result, None)
    stack = [
        frame for frame in _dict_frames(root, _dict_context(root, measured))
        if frame.key != "measurements"
    ]
    while stack and len(hits) < envelope.MAX_RESERVED_KEY_HITS:
        frame = stack.pop()
        if isinstance(frame.value, dict):
            stack.extend(_dict_frames(frame, _dict_context(frame, measured)))
        elif isinstance(frame.value, list):
            stack.extend(_list_frames(frame))
        elif envelope.is_number(frame.value):
            _note_number(frame, hits)
    return hits.listing()


def _energy_scan_errors(result: dict[str, Any], measured: set[str], where: str) -> list[str]:
    """One finding listing every energy claim the structural scan found."""

    hits = _energy_scan_hits(result, measured)
    if not hits:
        return []
    listed = ", ".join(sorted(hits))
    if len(hits) >= envelope.MAX_RESERVED_KEY_HITS:
        listed += ", ... (scan capped)"
    return [
        f"{where}.result: THEORETICAL_ENERGY_CLAIM — energy numbers outside "
        f"measurements at {listed} (an energy value must be carried as a "
        "measurement with a meter, or sit in an object backed by a measured "
        "reading of its quantity)"
    ]


def _energy_preference_errors(
    result: dict[str, Any], measured_energy_quantities: set[str], where: str
) -> list[str]:
    """A preference denominated in energy needs a measured energy reading."""

    preference = result.get("preference")
    if not isinstance(preference, dict):
        return []
    identity = _energy_identity(preference)
    if identity is None or not _unbacked(identity, measured_energy_quantities):
        return []
    denomination = "/".join(sorted(frozenset().union(*identity))) or "an energy unit"
    return [
        f"{where}.result.preference: THEORETICAL_ENERGY_CLAIM — preference "
        f"is denominated in {denomination!r} with no measured energy "
        f"measurement behind it"
    ]


def check_no_theoretical_energy_claim(record: dict[str, Any], where: str) -> list[str]:
    """Refuse an energy number that was modeled rather than measured.

    Covers both directions: an energy-class quantity produced by a modeled
    meter, and a preference/comparison denominated in an energy quantity that
    has no measured energy behind it.
    """

    result = record.get("result")
    if not isinstance(result, dict):
        return []
    measurements = result.get("measurements")
    measurements = measurements if isinstance(measurements, list) else []
    errors, measured_energy_quantities = _energy_measurement_claims(
        measurements, where
    )
    errors += _energy_scan_errors(result, measured_energy_quantities, where)
    return errors + _energy_preference_errors(result, measured_energy_quantities, where)


bind_import_twin(__name__)
