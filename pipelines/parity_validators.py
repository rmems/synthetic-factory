#!/usr/bin/env python3
"""Map a parity record kind to its family validator module, lazily.

``check_records`` is imported both ways (a direct ``pipelines/``-on-sys.path
sibling and the ``pipelines.check_records`` package child ``round_txn``
uses); the family validator module must resolve through whichever form
loaded the caller, so the import happens here rather than at
``check_records`` top level. Only the literal names below are ever
imported -- a record selects the module but never spells it.
"""

import importlib
import json
import sys

if __package__:
    # Import-twin helpers join the package import lock; import-order tests cover this edge.
    from . import _assert_direct_sibling, _expose_package_sibling  # pylint: disable=cyclic-import

    _assert_direct_sibling("parity_validators")
    from .exact_json import dumps_exact_json  # noqa: E402
    from .oracle_grounded import parity_contract  # noqa: E402
else:
    getattr(sys.modules.get("pipelines"), "_join_package_sibling", lambda name: None)(
        "parity_validators"
    )
    from exact_json import dumps_exact_json  # noqa: E402
    from oracle_grounded import parity_contract  # noqa: E402


_PARITY_VALIDATOR_NAMES = frozenset(("hardware_parity", "nir_equivalence"))


def validator_module(name):
    """The family validator module ``name`` refers to (literal names only)."""
    if name not in _PARITY_VALIDATOR_NAMES:
        raise ValueError(f"no parity validator module named {name!r}")
    if __package__:
        return _package_module(name)
    return _direct_module(name)


def _package_module(name):
    """Package-child form: resolve through ``pipelines.``."""
    if name == "hardware_parity":
        return importlib.import_module(".hardware_parity", __package__)
    return importlib.import_module(".nir_equivalence", __package__)


def _direct_module(name):
    """Direct-CLI form: resolve through ``sys.path``."""
    if name == "hardware_parity":
        return importlib.import_module("hardware_parity")
    return importlib.import_module("nir_equivalence")


# Each parity kind is validated by the family module of the same name.
_PARITY_VALIDATOR_MODULES = {
    "hardware_parity": "hardware_parity",
    "nir_equivalence": "nir_equivalence",
}


def family_record_view(obj):
    """The record exactly as the family readers decode it.

    ``check_jsonl`` decodes every non-integer number as an
    ``exact_json.ExactJSONFloat`` so the exact-JSON contract can be held over
    the whole record. The family validators compare evidence type-strictly
    (``strict_json_equal``, ``type(value) is float``) against catalog entries
    and re-derived measurements that are plain floats, so the deep layer hands
    them the same tokens decoded through the families' own parse hooks: what
    ``hardware_parity.py validate`` reads from the line itself.
    """
    return json.loads(
        dumps_exact_json(obj, ensure_ascii=False, sort_keys=False),
        parse_constant=parity_contract.reject_json_constant,
        parse_float=parity_contract.reject_nonfinite_float,
    )


def check_parity_record(obj, kind, where):
    """Deep layer for the oracle-grounded parity families.

    The family validators re-derive every parity number from the record's own
    traces, re-simulate the in-repo oracles, and for NIR re-execute the
    interpreters outright, so a fabricated result cannot pass. All of that is
    far too expensive for the shape layer, which is why it lives here.
    """
    module_name = _PARITY_VALIDATOR_MODULES.get(kind)
    if module_name is None:
        # No silent fallthrough: an unrouted kind must be loud, not validated
        # by whichever validator happened to be last.
        return [f"{where}: no parity validator for record_kind {kind!r}"]
    try:
        record = family_record_view(obj)
    except (ValueError, RecursionError) as exc:
        return [f"{where}: record cannot be re-read as exact JSON for the {kind} validator: {exc}"]
    return validator_module(module_name).validate_record(record, where)


def _nir_owned_streams(oracle):
    """Canonical NIR evidence streams: ``oracle.runtimes[*].outputs.spike_events``."""
    runtimes = oracle.get("runtimes")
    for entry in runtimes if isinstance(runtimes, list) else ():
        outputs = entry.get("outputs") if isinstance(entry, dict) else None
        if isinstance(outputs, dict) and "spike_events" in outputs:
            yield outputs["spike_events"]


def _hardware_owned_streams(oracle):
    """Canonical hardware evidence streams: ``oracle.deployment/software.spike_events``."""
    for side in ("deployment", "software"):
        block = oracle.get(side)
        if isinstance(block, dict) and "spike_events" in block:
            yield block["spike_events"]


def family_owned_streams(obj, kind):
    """Stream objects whose validity the parity family validator owns.

    NIR runtime outputs and hardware capture sides carry ``spike_events``
    in family-specific shapes (discrete steps, integer channel/neuron ids)
    that the family validators check against a re-execution. Returned by
    identity so a literal key elsewhere in the record cannot claim the
    exemption by name.
    """
    oracle = obj.get("oracle") if isinstance(obj, dict) else None
    if not isinstance(oracle, dict):
        return ()
    if kind == "nir_equivalence":
        return tuple(_nir_owned_streams(oracle))
    return tuple(_hardware_owned_streams(oracle))


if __package__:
    _expose_package_sibling(__name__)
