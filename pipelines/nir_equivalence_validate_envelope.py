#!/usr/bin/env python3
"""Envelope identity, graph structure, and the catalog claim.

The graph and structure digests are recomputed from `scenario.graph`; a record
claiming a catalog scenario must be that scenario.
"""

from __future__ import annotations

import sys

if __package__:
    # Import-twin helpers join the package import lock; import-order tests cover this edge.
    from . import _assert_direct_sibling, _expose_package_sibling  # pylint: disable=cyclic-import

    _assert_direct_sibling("nir_equivalence_validate_envelope")
    from .neuro_oracle import digest  # noqa: E402
    from .nir_equivalence_base import _strict_json_equal  # noqa: E402
    from .nir_equivalence_catalog import _catalog_entry  # noqa: E402
    from .nir_equivalence_compare import _expected_verdict  # noqa: E402
    from .nir_equivalence_graph import structural_digest  # noqa: E402
    from .nir_equivalence_provenance import _catalog_provenance_stamps  # noqa: E402
    from .oracle_grounded.parity_history import reviewed_catalog_stamps
    from .nir_equivalence_terms import (  # noqa: E402
        CANONICAL_DATA_ERRORS,
        FACTORY_SLUG,
        GENERATOR_BLOCK,
        SCHEMA_VERSION,
        VALIDATOR,
        contract,
    )
else:
    getattr(sys.modules.get("pipelines"), "_join_package_sibling", lambda name: None)(
        "nir_equivalence_validate_envelope"
    )
    from neuro_oracle import digest  # noqa: E402
    from nir_equivalence_base import _strict_json_equal  # noqa: E402
    from nir_equivalence_catalog import _catalog_entry  # noqa: E402
    from nir_equivalence_compare import _expected_verdict  # noqa: E402
    from nir_equivalence_graph import structural_digest  # noqa: E402
    from nir_equivalence_provenance import _catalog_provenance_stamps  # noqa: E402
    from oracle_grounded.parity_history import reviewed_catalog_stamps
    from nir_equivalence_terms import (  # noqa: E402
        CANONICAL_DATA_ERRORS,
        FACTORY_SLUG,
        GENERATOR_BLOCK,
        SCHEMA_VERSION,
        VALIDATOR,
        contract,
    )

def _check_envelope_identity(record, scenario, where):
    """id/meta/generator/provenance/validation must match their canonical values."""
    errors = []
    meta = record.get("meta")
    round_number = meta.get("round") if isinstance(meta, dict) else None
    scenario_id = scenario.get("id")
    if isinstance(round_number, int) and not isinstance(round_number, bool):
        expected_id = f"{scenario_id}-r{round_number:02d}"
        if record.get("id") != expected_id:
            errors.append(
                f"{where}: id must be {expected_id!r} for this scenario and round "
                "[ENVELOPE_MALFORMED]"
            )
    expected_meta = {"round": round_number, "factory": FACTORY_SLUG}
    if not _strict_json_equal(meta, expected_meta):
        errors.append(
            f"{where}: meta must exactly identify factory {FACTORY_SLUG!r} and its "
            "round [ENVELOPE_MALFORMED]"
        )
    if not _strict_json_equal(record.get("generator"), GENERATOR_BLOCK):
        errors.append(
            f"{where}: generator does not match the NIR catalog identity "
            "[ENVELOPE_MALFORMED]"
        )
    errors += _provenance_identity_errors(record.get("provenance"), where)
    errors += _validation_identity_errors(record.get("validation"), where)
    errors += _scenario_digest_errors(record, scenario, where)
    return errors


def _provenance_identity_errors(provenance, where):
    errors = []
    expected_provenance_identity = {
        "kind": "simulated",
        "tool": VALIDATOR,
        "tool_version": SCHEMA_VERSION,
        "contract_version": contract.CONTRACT_VERSION,
        "units": {"time": "timesteps", "dt": "s", "membrane": "V_model"},
    }
    expected_provenance_identity.update(reviewed_catalog_stamps(provenance, _catalog_provenance_stamps()))
    if not isinstance(provenance, dict) or any(
        not _strict_json_equal(provenance.get(key), value)
        for key, value in expected_provenance_identity.items()
    ):
        errors.append(
            f"{where}: provenance identity does not match the NIR validator "
            "[ENVELOPE_MALFORMED]"
        )
    return errors


def _validation_identity_errors(validation, where):
    errors = []
    expected_validation = {
        "validator": VALIDATOR,
        "validator_version": SCHEMA_VERSION,
        "checks": [
            "envelope_contract",
            "structure_digest_recomputed_from_graph",
            "in_repo_runtime_outputs_re_executed",
            "comparison_recomputed_from_outputs",
            "divergence_preserved",
        ],
        "status": "revalidate_on_read",
    }
    if not _strict_json_equal(validation, expected_validation):
        errors.append(
            f"{where}: validation block does not match the NIR validator contract "
            "[ENVELOPE_MALFORMED]"
        )
    return errors


def _scenario_digest_errors(record, scenario, where):
    errors = []
    try:
        expected_scenario_digest = digest(
            {"graph": scenario.get("graph"), "stimulus": scenario.get("stimulus")}
        )
    except CANONICAL_DATA_ERRORS as exc:
        errors.append(
            f"{where}: scenario is not canonical JSON: {exc} [ENVELOPE_MALFORMED]"
        )
    else:
        provenance = record.get("provenance")
        if (
            not isinstance(provenance, dict)
            or provenance.get("scenario_sha256") != expected_scenario_digest
        ):
            errors.append(
                f"{where}: provenance.scenario_sha256 does not identify the recorded "
                "graph and stimulus [STRUCTURE_DIGEST_MISMATCH]"
            )
    return errors


def _check_graph_structure(record, scenario, graph, where):
    """Re-derive structure/graph digests and bind the scenario to its catalog entry.

    Returns ``(errors, graph_shape_valid)``; the caller must not attempt
    re-execution when ``graph_shape_valid`` is false.
    """
    if not isinstance(graph, dict):
        return (
            [f"{where}: scenario.graph must be an object [ENVELOPE_MALFORMED]"],
            False,
        )
    errors, fresh_graph_sha256, fresh_structure_digest = _recompute_graph_digests(
        graph, where
    )
    graph_shape_valid = fresh_structure_digest is not None
    errors += _declared_digest_errors(
        scenario, fresh_graph_sha256, fresh_structure_digest, where
    )
    catalog_entry = _catalog_entry(scenario.get("id"))
    if catalog_entry is None:
        errors.append(
            f"{where}: scenario.id {scenario.get('id')!r} is not in the validated "
            "graph catalog [STRUCTURE_DIGEST_MISMATCH]"
        )
        return errors, graph_shape_valid
    errors += _catalog_scenario_errors(
        scenario, catalog_entry, fresh_graph_sha256, where
    )
    errors += _catalog_claim_errors(
        record, catalog_entry, scenario.get("id"), where
    )
    return errors, graph_shape_valid


def _recompute_graph_digests(graph, where):
    """Recompute both graph digests, reporting whichever the graph defeats.

    Returns ``(errors, graph_sha256, structure_digest)``; a digest is None
    when it could not be derived, which is also what tells the caller the
    graph is too malformed to re-execute.
    """
    errors = []
    try:
        fresh_graph_sha256 = digest(graph)
    except CANONICAL_DATA_ERRORS as exc:
        errors.append(
            f"{where}: scenario.graph is not canonical JSON: {exc} "
            "[ENVELOPE_MALFORMED]"
        )
        fresh_graph_sha256 = None
    try:
        fresh_structure_digest = structural_digest(graph)
    # GraphError (malformed graph) and UnicodeEncodeError (uncanonical text)
    # are ValueError subclasses and are caught by the ValueError arm.
    except (TypeError, ValueError, OverflowError, RecursionError) as exc:
        errors.append(f"{where}: malformed scenario.graph: {exc} [ENVELOPE_MALFORMED]")
        fresh_structure_digest = None
    return errors, fresh_graph_sha256, fresh_structure_digest


def _declared_digest_errors(scenario, graph_sha256, structure_digest, where):
    """The scenario's own declared digests must identify the graph it carries."""
    errors = []
    if (
        structure_digest is not None
        and scenario.get("structure_digest") != structure_digest
    ):
        errors.append(
            f"{where}: scenario.structure_digest does not match the recorded graph "
            "[STRUCTURE_DIGEST_MISMATCH]"
        )
    if graph_sha256 is not None and scenario.get("graph_sha256") != graph_sha256:
        errors.append(
            f"{where}: scenario.graph_sha256 does not match the recorded graph "
            "[STRUCTURE_DIGEST_MISMATCH]"
        )
    return errors


def _catalog_scenario_errors(scenario, catalog_entry, graph_sha256, where):
    """The scenario's graph and prose must be the reviewed catalog entry's."""
    errors = []
    if graph_sha256 != catalog_entry["graph_sha256"]:
        errors.append(
            f"{where}: scenario.graph does not match the validated catalog "
            f"digest for {scenario.get('id')!r} [STRUCTURE_DIGEST_MISMATCH]"
        )
    for key in ("name", "family", "class", "description"):
        if not _strict_json_equal(scenario.get(key), catalog_entry[key]):
            errors.append(
                f"{where}: scenario.{key} {scenario.get(key)!r} does not match "
                f"the validated graph catalog value {catalog_entry[key]!r} for "
                f"{scenario.get('id')!r} [COMPARISON_MISMATCH]"
            )
    return errors


def _catalog_claim_errors(record, catalog_entry, scenario_id, where):
    """The intervention and prediction a record claims must be the catalog's."""
    errors = []
    if not _strict_json_equal(record.get("intervention"), catalog_entry["intervention"]):
        errors.append(
            f"{where}: intervention does not match the validated graph catalog "
            f"for {scenario_id!r} [COMPARISON_MISMATCH]"
        )
    prediction = record.get("candidate_prediction")
    if not isinstance(prediction, dict):
        return errors
    expected_prediction = {
        "hypothesis": catalog_entry["hypothesis"],
        "expected_verdict": _expected_verdict(catalog_entry["class"]),
    }
    for key, expected in expected_prediction.items():
        if not _strict_json_equal(prediction.get(key), expected):
            errors.append(
                f"{where}: candidate_prediction.{key} does not match the "
                f"validated graph catalog for {scenario_id!r} "
                "[COMPARISON_MISMATCH]"
            )
    return errors


if __package__:
    _expose_package_sibling(__name__)
