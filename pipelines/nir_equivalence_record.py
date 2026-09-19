#!/usr/bin/env python3
"""Building the emitted record: evidence scope, lineage, envelope, batch.

Evidence scope is stated on the record rather than implied, because a record
naming two in-repo interpreters is not evidence about `nir-rs`.
"""

from __future__ import annotations

import copy
import sys

if __package__:
    # Import-twin helpers join the package import lock; import-order tests cover this edge.
    from . import _assert_direct_sibling, _expose_package_sibling  # pylint: disable=cyclic-import

    _assert_direct_sibling("nir_equivalence_record")
    from .neuro_oracle import digest  # noqa: E402
    from .nir_equivalence_base import _safe_digest  # noqa: E402
    from .nir_equivalence_catalog import build_scenarios  # noqa: E402
    from .nir_equivalence_compare import (  # noqa: E402
        _expected_verdict,
        _summarize,
        compare_runtimes,
        verdict_for,
    )
    from .nir_equivalence_execute import (  # noqa: E402
        _executed,
        execute_runtime,
    )
    from .nir_equivalence_provenance import _catalog_provenance_stamps  # noqa: E402
    from .nir_equivalence_runtimes import (  # noqa: E402
        IN_REPO_RUNTIMES,
        UPSTREAM_RUNTIMES,
    )
    from .nir_equivalence_terms import (  # noqa: E402
        FACTORY_SLUG,
        GENERATOR_BLOCK,
        ORACLE_PAIRING,
        RECORD_KIND,
        SCHEMA_VERSION,
        STATUS_EXECUTED,
        STATUS_UNAVAILABLE,
        STATUS_UNSUPPORTED,
        VALIDATOR,
        contract,
    )
else:
    getattr(sys.modules.get("pipelines"), "_join_package_sibling", lambda name: None)(
        "nir_equivalence_record"
    )
    from neuro_oracle import digest  # noqa: E402
    from nir_equivalence_base import _safe_digest  # noqa: E402
    from nir_equivalence_catalog import build_scenarios  # noqa: E402
    from nir_equivalence_compare import (  # noqa: E402
        _expected_verdict,
        _summarize,
        compare_runtimes,
        verdict_for,
    )
    from nir_equivalence_execute import (  # noqa: E402
        _executed,
        execute_runtime,
    )
    from nir_equivalence_provenance import _catalog_provenance_stamps  # noqa: E402
    from nir_equivalence_runtimes import (  # noqa: E402
        IN_REPO_RUNTIMES,
        UPSTREAM_RUNTIMES,
    )
    from nir_equivalence_terms import (  # noqa: E402
        FACTORY_SLUG,
        GENERATOR_BLOCK,
        ORACLE_PAIRING,
        RECORD_KIND,
        SCHEMA_VERSION,
        STATUS_EXECUTED,
        STATUS_UNAVAILABLE,
        STATUS_UNSUPPORTED,
        VALIDATOR,
        contract,
    )

def _evidence_scope(entries):
    executed = [entry.get("runtime") for entry in _executed(entries)]
    if len(executed) >= 2:
        execution = f"executed in-repo runtimes {executed!r}"
    elif len(executed) == 1:
        execution = f"only one in-repo runtime executed: {executed[0]!r}"
    else:
        execution = "no in-repo runtime executed this graph"
    return (
        f"{execution}; nir-rs and the other upstream NIR runtimes were unavailable, "
        "so this record is evidence only about the runtimes and diagnostics that "
        "actually executed"
    )


def _evidence_lineage(entries):
    """Derive one ordered identity-bearing lineage item per runtime entry.

    Each persisted item binds the runtime, status, and evidence digest. For an
    unavailable runtime the digest binds its recorded diagnostic. A fresh
    probe independently checks whether the runtime remains unavailable;
    installing an unimplemented package must not rewrite historical evidence.
    """
    lineage = []
    for entry in entries:
        if not isinstance(entry, dict):
            continue
        status = entry.get("status")
        if status == STATUS_EXECUTED:
            evidence_digest = entry.get("output_digest")
        elif status == STATUS_UNSUPPORTED:
            diagnostic = {
                "evidence_kind": "runtime_diagnostic",
                "runtime": entry.get("runtime"),
                "runtime_class": entry.get("runtime_class"),
                "status": status,
                "reason_code": entry.get("reason_code"),
                "detail": entry.get("detail"),
                "unsupported_node": entry.get("unsupported_node"),
                "unsupported_type": entry.get("unsupported_type"),
            }
            evidence_digest = _safe_digest(diagnostic)
        elif status == STATUS_UNAVAILABLE:
            diagnostic = {
                "evidence_kind": "runtime_capability",
                "runtime": entry.get("runtime"),
                "runtime_class": entry.get("runtime_class"),
                "status": status,
                "available": False,
                "reason_code": entry.get("reason_code"),
                "detail": entry.get("detail"),
            }
            evidence_digest = _safe_digest(diagnostic)
        else:
            continue
        lineage.append(
            {
                "runtime": entry.get("runtime"),
                "status": status,
                "digest": evidence_digest,
            }
        )
    return lineage


def _evidence_digests(entries):
    """Project exact ordered lineage to digests for diagnostics and migration."""
    return [item["digest"] for item in _evidence_lineage(entries)]


def _recorded_scenario(scenario):
    """Project catalog inputs while keeping fixture metadata independently mutable."""
    return {
        "id": scenario["id"],
        "name": scenario["name"],
        "family": scenario["family"],
        "class": scenario["class"],
        "description": scenario["description"],
        "graph": scenario["graph"],
        "graph_sha256": scenario["graph_sha256"],
        "structure_digest": scenario["structure_digest"],
        "stimulus": scenario["stimulus"],
        "input_fixture": copy.deepcopy(scenario["input_fixture"]),
    }


def build_record(scenario, entries, round_number):
    comparison = compare_runtimes(scenario, entries)
    verdict, reason_codes = verdict_for(comparison)
    prediction = {
        "source": "generator",
        "authoritative": False,
        "hypothesis": scenario["hypothesis"],
        "expected_verdict": _expected_verdict(scenario["class"]),
    }
    record = {
        "id": f"{scenario['id']}-r{round_number:02d}",
        "record_kind": RECORD_KIND,
        "dataset": contract.DATASET_FOR_KIND[RECORD_KIND],
        "schema_version": SCHEMA_VERSION,
        # Deep-copied so no two records (and no two fields of one record) share
        # a mutable sub-object: an edit to one would otherwise silently rewrite
        # the other, which is precisely the failure mode these records catch.
        "generator": copy.deepcopy(GENERATOR_BLOCK),
        "scenario": _recorded_scenario(scenario),
        "intervention": copy.deepcopy(scenario["intervention"]),
        "candidate_prediction": prediction,
        "oracle": {
            "pairing": ORACLE_PAIRING,
            "runtimes": entries,
            "identical_input_fixture": True,
            "input_fixture": copy.deepcopy(scenario["input_fixture"]),
            "evidence_scope": _evidence_scope(entries),
        },
        "result": _record_result(scenario, entries, comparison, verdict,
                                 reason_codes),
        "provenance": _record_provenance(scenario),
        "validation": {
            "validator": VALIDATOR,
            "validator_version": SCHEMA_VERSION,
            "checks": [
                "envelope_contract",
                "structure_digest_recomputed_from_graph",
                "in_repo_runtime_outputs_re_executed",
                "comparison_recomputed_from_outputs",
                "divergence_preserved",
            ],
            # No cached pass. A stored "validated" stamp is exactly what a
            # tampered record would forge, so the checks are named here and
            # re-run by the reader instead.
            "status": "revalidate_on_read",
        },
        "meta": {"round": round_number, "factory": FACTORY_SLUG},
    }
    return record


def _record_result(scenario, entries, comparison, verdict, reason_codes):
    """The result block: verdict, lineage, comparison, and its summary."""
    return {
        "oracle_backed": True,
        "verdict": verdict,
        "reason_codes": reason_codes,
        "derived_from": _evidence_lineage(entries),
        "comparison": comparison,
        "summary": _summarize(scenario, comparison, verdict),
    }


def _record_provenance(scenario):
    """Provenance pinned to the recorded graph+stimulus bytes."""
    return dict(
        {
            "kind": "simulated",
            "tool": VALIDATOR,
            "tool_version": SCHEMA_VERSION,
            "contract_version": contract.CONTRACT_VERSION,
            "scenario_sha256": digest(
                {"graph": scenario["graph"], "stimulus": scenario["stimulus"]}
            ),
            "units": {"time": "timesteps", "dt": "s", "membrane": "V_model"},
        },
        **_catalog_provenance_stamps(),
    )


def generate_records(round_number=1, steps=10):
    records = []
    runtimes = (*IN_REPO_RUNTIMES, *UPSTREAM_RUNTIMES)
    for scenario in build_scenarios(steps=steps):
        entries = [execute_runtime(runtime, scenario) for runtime in runtimes]
        records.append(build_record(scenario, entries, round_number))
    return records


if __package__:
    _expose_package_sibling(__name__)
