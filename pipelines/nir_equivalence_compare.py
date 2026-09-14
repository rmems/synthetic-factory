#!/usr/bin/env python3
"""Comparing runtime entries and deciding the verdict.

Pure functions over recorded entries: no catalog, no runtime objects. The
expected verdict and the summary live here too because the record builder and
the validator both need them, and putting them in either would make the other
import it back.
"""

from __future__ import annotations

import sys
from pathlib import Path

_PIPELINES = Path(__file__).resolve().parent

if __package__:
    # Import-twin helpers join the package import lock; import-order tests cover this edge.
    from . import _assert_direct_sibling, _expose_package_sibling  # pylint: disable=cyclic-import

    _assert_direct_sibling("nir_equivalence_compare")
    from .nir_equivalence_compare_pair import (  # noqa: E402,F401
        _candidate_causes,
        _compare_pair,
        _incomparable_pair,
        _pair_identity,
        _pair_reason_codes,
        _spike_events_agree,
        _state_error,
        _trace_divergence,
        _trace_shapes_differ,
        convention_delta,
        relevant_conventions,
    )
    from .nir_equivalence_execute import _executed  # noqa: E402
    from .nir_equivalence_terms import (  # noqa: E402
        NUMERIC_TOL,
        STATUS_UNAVAILABLE,
        STATUS_UNSUPPORTED,
        contract,
    )
else:
    getattr(sys.modules.get("pipelines"), "_join_package_sibling", lambda name: None)(
        "nir_equivalence_compare"
    )
    if str(_PIPELINES) not in sys.path:
        sys.path.insert(0, str(_PIPELINES))
    from nir_equivalence_compare_pair import (  # noqa: E402,F401
        _candidate_causes,
        _compare_pair,
        _incomparable_pair,
        _pair_identity,
        _pair_reason_codes,
        _spike_events_agree,
        _state_error,
        _trace_divergence,
        _trace_shapes_differ,
        convention_delta,
        relevant_conventions,
    )
    from nir_equivalence_execute import _executed  # noqa: E402
    from nir_equivalence_terms import (  # noqa: E402
        NUMERIC_TOL,
        STATUS_UNAVAILABLE,
        STATUS_UNSUPPORTED,
        contract,
    )

def compare_runtimes(scenario, entries):
    """Compare every executed runtime pairwise and classify what differs."""
    executed = _executed(entries)
    unsupported = _unsupported_block(entries)
    unavailable = _unavailable_block(entries)
    roundtrip_block = _parse_write_parity(entries)
    structure_block = _structure_parity(scenario, entries)
    pairs = _executed_pairs(executed)
    delta = convention_delta(entries)
    output_agree = all(pair["agree"] for pair in pairs) if pairs else None
    state_agree = (
        all(pair["state_agree"] for pair in pairs) if pairs else None
    )
    relevant = relevant_conventions(scenario.get("graph"), entries)
    candidate_causes = _candidate_causes(delta, relevant, output_agree, state_agree)

    return {
        "executed_runtimes": [entry["runtime"] for entry in executed],
        "executed_count": len(executed),
        "parse_write_parity": roundtrip_block,
        "structure_parity": structure_block,
        "output_parity": {
            "comparable": bool(pairs),
            "agree": output_agree,
            "pairs": pairs,
            "tolerance": NUMERIC_TOL,
        },
        "state_parity": {
            "comparable": bool(pairs),
            "agree": state_agree,
            "note": (
                "internal membrane state at the end of the window. It can diverge while "
                "the event outputs agree, which means the agreement may not survive a "
                "longer stimulus"
            ),
        },
        "unsupported": unsupported,
        "unavailable": unavailable,
        "convention_delta": delta,
        "attribution": {
            "candidate_reason_codes": sorted(set(candidate_causes)),
            "relevant_conventions": sorted(relevant),
            "basis": (
                "declared convention differences that this graph actually exercises; a "
                "candidate explanation for the observed divergence, not a proven cause"
            ),
        },
    }


def _unsupported_block(entries):
    """Every runtime that refused a construct, with the construct it refused."""
    return [
        {
            "runtime": entry["runtime"],
            "reason_code": entry.get("reason_code"),
            "node": entry.get("unsupported_node"),
            "node_type": entry.get("unsupported_type"),
            "detail": entry.get("detail"),
        }
        for entry in entries
        if entry["status"] == STATUS_UNSUPPORTED
    ]


def _unavailable_block(entries):
    """Every runtime that never ran, with the class of evidence it would have been."""
    return [
        {
            "runtime": entry["runtime"],
            "runtime_class": entry["runtime_class"],
            "reason_code": entry.get("reason_code"),
            "detail": entry.get("detail"),
        }
        for entry in entries
        if entry["status"] == STATUS_UNAVAILABLE
    ]


def _parse_write_parity(entries):
    """Per-adapter parse/write evidence. No adapter reported it: no agreement."""
    per_runtime = {
        entry["runtime"]: entry.get("roundtrip")
        for entry in entries
        if entry.get("roundtrip") is not None
    }
    return {
        "per_runtime": per_runtime,
        "agree": all(
            value and value.get("parse_ok") and value.get("canonical_stable")
            and value.get("structure_stable")
            for value in per_runtime.values()
        ) if per_runtime else False,
    }


def _structure_parity(scenario, entries):
    """Every adapter's post-roundtrip structure digest against the declared one."""
    structure_digests = {
        entry["runtime"]: (entry.get("roundtrip") or {}).get("structure_digest")
        for entry in entries
        if entry.get("roundtrip") is not None
    }
    return {
        "digests": structure_digests,
        "declared": scenario["structure_digest"],
        "agree": (
            len(set(structure_digests.values())) <= 1
            and all(
                value == scenario["structure_digest"] for value in structure_digests.values()
            )
        )
        if structure_digests
        else False,
    }


def _executed_pairs(executed):
    """Every unordered pair of executed runtimes, in inventory order."""
    return [
        _compare_pair(executed[index_a], executed[index_b])
        for index_a in range(len(executed))
        for index_b in range(index_a + 1, len(executed))
    ]


def verdict_for(comparison):
    """Derive the verdict and observed reason codes from a comparison block."""
    reason_codes = _observed_reason_codes(comparison)
    if comparison["executed_count"] < 2:
        reason_codes.append("NO_EXECUTED_RUNTIME_PAIR")
        verdict = (
            contract.VERDICT_UNSUPPORTED
            if comparison["unsupported"]
            else contract.VERDICT_INCONCLUSIVE
        )
        return verdict, sorted(set(reason_codes))
    agree = (
        comparison["output_parity"]["agree"]
        and comparison["structure_parity"]["agree"]
        and comparison["parse_write_parity"]["agree"]
    )
    return (
        contract.VERDICT_MATCH if agree else contract.VERDICT_MISMATCH,
        sorted(set(reason_codes)),
    )


def _observed_reason_codes(comparison):
    """Every reason code the comparison evidence itself reports, before policy."""
    reason_codes = []
    if comparison["unsupported"]:
        reason_codes.append("UNSUPPORTED_CONSTRUCT")
    if comparison["unavailable"]:
        reason_codes.append("ORACLE_UNAVAILABLE")
    reason_codes += _roundtrip_reason_codes(comparison["parse_write_parity"])
    structure = comparison["structure_parity"]
    if structure["digests"] and not structure["agree"]:
        reason_codes.append("STRUCTURE_DIGEST_MISMATCH")
    for pair in comparison["output_parity"]["pairs"]:
        reason_codes.extend(pair["reason_codes"])
    return reason_codes


def _roundtrip_reason_codes(parse_write_parity):
    """The codes the adapters themselves reported for a failed round trip."""
    per_runtime = parse_write_parity["per_runtime"]
    if not per_runtime or parse_write_parity["agree"]:
        return []
    return [
        value["reason_code"]
        for value in per_runtime.values()
        if value and value.get("reason_code")
    ]


def _expected_verdict(graph_class):
    if graph_class == "unsupported":
        return contract.VERDICT_UNSUPPORTED
    if graph_class in ("feed_forward",):
        return contract.VERDICT_MATCH
    if graph_class == "coverage_gap":
        return contract.VERDICT_UNSUPPORTED
    return contract.VERDICT_MISMATCH


def _summarize(scenario, comparison, verdict):
    executed = ", ".join(comparison["executed_runtimes"]) or "none"
    pairs = comparison["output_parity"]["pairs"]
    detail = ""
    if pairs:
        pair = pairs[0]
        detail = (
            f" spike counts {pair['spike_count_a']} vs {pair['spike_count_b']},"
            f" first divergent step {pair['first_divergent_step']},"
            f" max abs error {pair['max_abs_error']}."
        )
    elif comparison["unsupported"]:
        detail = " " + "; ".join(
            f"{item['runtime']} rejected {item['node_type']} at node {item['node']}"
            for item in comparison["unsupported"]
        ) + "."
    return (
        f"{scenario['name']}: executed on [{executed}]."
        f"{detail} verdict {verdict}."
    )


if __package__:
    _expose_package_sibling(__name__)
