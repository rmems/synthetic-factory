#!/usr/bin/env python3
"""Building one record from a paired run, and a round from the catalog.

The generator side only. Nothing here certifies a result: the oracle legs are
whatever the adapters returned, and `result` is derived from them rather than
asserted alongside them.
"""

from __future__ import annotations

import copy
import sys

if __package__:
    # Import-twin helpers join the package import lock; import-order tests cover this edge.
    from . import _assert_direct_sibling, _expose_package_sibling  # pylint: disable=cyclic-import

    _assert_direct_sibling("hardware_parity_record")
    from . import neuro_oracle  # noqa: E402
    from .neuro_oracle import (  # noqa: E402
        FixedPointReferenceAdapter,
        OracleUnavailable,
        PHYSICAL_TARGETS,
        RecordedCaptureAdapter,
        SoftwareFloatAdapter,
        digest,
    )
    from .hardware_parity_terms import (  # noqa: E402
        FACTORY_SLUG,
        GENERATOR_BLOCK,
        ORACLE_PAIRING,
        RECORD_KIND,
        SCHEMA_VERSION,
        VALIDATOR,
        contract,
    )
    from .hardware_parity_catalog import build_scenarios  # noqa: E402
    from .hardware_parity_metrics import compute_parity  # noqa: E402
    from .hardware_parity_provenance import _catalog_provenance_stamps  # noqa: E402
else:
    getattr(sys.modules.get("pipelines"), "_join_package_sibling", lambda name: None)(
        "hardware_parity_record"
    )
    import neuro_oracle  # noqa: E402
    from neuro_oracle import (  # noqa: E402
        FixedPointReferenceAdapter,
        OracleUnavailable,
        PHYSICAL_TARGETS,
        RecordedCaptureAdapter,
        SoftwareFloatAdapter,
        digest,
    )
    from hardware_parity_terms import (  # noqa: E402
        FACTORY_SLUG,
        GENERATOR_BLOCK,
        ORACLE_PAIRING,
        RECORD_KIND,
        SCHEMA_VERSION,
        VALIDATOR,
        contract,
    )
    from hardware_parity_catalog import build_scenarios  # noqa: E402
    from hardware_parity_metrics import compute_parity  # noqa: E402
    from hardware_parity_provenance import _catalog_provenance_stamps  # noqa: E402

def availability_report(**kwargs):
    """The oracle's availability probe, resolved through its module each call."""
    return neuro_oracle.availability_report(**kwargs)



def _slim_run(run):
    """The oracle payload as stored on the record.

    The full Q8.8 model is dropped (it is exactly re-derivable from the float
    model, and validation re-derives it), but every observation is kept.
    """
    keep = (
        "adapter",
        "execution_target",
        "runtime_class",
        "repeats",
        "repeat_digests",
        "determinism",
        "latency",
        "output_digest",
        "spikes",
        "spike_events",
        "membrane",
        "action",
        "arithmetic",
        "quantization",
        "hardware",
        "bitstream",
        "capture",
    )
    return {key: run[key] for key in keep if key in run}


def run_pair(scenario, deployment_adapter, software_adapter=None, repeats=3):
    """Execute both sides of the pair against the identical input fixture."""
    software_adapter = software_adapter or SoftwareFloatAdapter()
    model = scenario["model_float"]
    stimulus = scenario["stimulus"]
    software_run = software_adapter.run(model, stimulus, repeats=repeats)
    try:
        deployment_run = deployment_adapter.run(model, stimulus, repeats=repeats)
        unavailable = None
    except OracleUnavailable as exc:
        deployment_run = None
        unavailable = {
            "adapter": deployment_adapter.name,
            "execution_target": deployment_adapter.execution_target,
            "reason_code": exc.reason_code,
            "detail": exc.detail,
        }
        if isinstance(deployment_adapter, RecordedCaptureAdapter):
            unavailable["adapter_config"] = {
                "capture_path": str(deployment_adapter.capture_path)
            }
    return software_run, deployment_run, unavailable


def build_record(scenario, runs, round_number, fpga_status):
    """Assemble one envelope record from a paired run.

    ``runs`` is ``(software_run, deployment_run, unavailable)`` — the
    ``run_pair`` outcome triple.
    """
    software_run, deployment_run, unavailable = runs
    # Deep-copied so no two records (and no two fields of one record) share a
    # mutable sub-object: an edit to one would otherwise silently rewrite the
    # other, which is precisely the failure mode these records exist to catch.
    fixture = copy.deepcopy(scenario["input_fixture"])
    oracle, requested_deployment = _oracle_block(fixture, unavailable, fpga_status)
    # A recorded physical target is a claim inside untrusted capture bytes.
    # The current adapter proves internal integrity only, so it cannot assign HIL.
    deployment_target = (deployment_run or {}).get("execution_target")
    record = {
        "id": f"{scenario['id']}-r{round_number:02d}",
        "record_kind": RECORD_KIND,
        "dataset": contract.DATASET_FOR_KIND[RECORD_KIND],
        "schema_version": SCHEMA_VERSION,
        "generator": copy.deepcopy(GENERATOR_BLOCK),
        "scenario": _record_scenario(scenario, fixture),
        "intervention": copy.deepcopy(scenario["intervention"]),
        "candidate_prediction": _prediction_block(scenario),
        "oracle": oracle,
        "result": None,
        "provenance": _record_provenance(
            scenario, deployment_target, requested_deployment
        ),
        "validation": {
            "validator": VALIDATOR,
            "validator_version": SCHEMA_VERSION,
            "checks": [
                "envelope_contract",
                "identical_input_fixture",
                "q88_conversion_reproducible",
                "parity_metrics_recomputed_from_traces",
                "verdict_consistent_with_traces",
            ],
            # No cached pass. A stored "validated" stamp is exactly what a
            # tampered record would forge, so the checks are named here and
            # re-run by the reader instead.
            "status": "revalidate_on_read",
        },
        "meta": {"round": round_number, "factory": FACTORY_SLUG},
    }

    if deployment_run is None:
        oracle["software"] = _slim_run(software_run)
        record["result"] = _unpaired_result(software_run, unavailable)
        return record

    oracle["software"] = _slim_run(software_run)
    oracle["deployment"] = _slim_run(deployment_run)
    record["result"] = _paired_result(scenario, software_run, deployment_run)
    return record


def _oracle_block(fixture, unavailable, fpga_status):
    """``(oracle, requested_deployment)`` for the record's oracle block."""
    oracle = {
        "pairing": ORACLE_PAIRING,
        "input_fixture": fixture,
        "identical_input_fixture": True,
        "software": None,
        "deployment": None,
        "unavailable": [],
        "environment": {
            "fpga_hardware": fpga_status,
            "note": (
                "the availability probe is recorded on every record so a reader can "
                "tell an unexecuted hardware leg from an omitted one"
            ),
        },
    }
    requested_deployment = None
    if unavailable:
        oracle["unavailable"].append(unavailable)
        requested_deployment = {
            key: copy.deepcopy(unavailable[key])
            for key in ("adapter", "execution_target", "adapter_config")
            if key in unavailable
        }
        oracle["requested_deployment"] = requested_deployment
    return oracle, requested_deployment


def _prediction_block(scenario):
    """The generator's expected verdict for the record's stress profile."""
    return {
        "source": "generator",
        "authoritative": False,
        "hypothesis": scenario["hypothesis"],
        "expected_verdict": (
            contract.VERDICT_MATCH if scenario["stress"] == "none"
            else contract.VERDICT_MISMATCH
        ),
    }


def _record_scenario(scenario, fixture):
    """The scenario block embedded in the record (input fixture deep-copied)."""
    return {
        "id": scenario["id"],
        "name": scenario["name"],
        "family": scenario["family"],
        "stress": scenario["stress"],
        "description": scenario["description"],
        "model_float": scenario["model_float"],
        "model_sha256": scenario["model_sha256"],
        "stimulus": scenario["stimulus"],
        "input_fixture": copy.deepcopy(fixture),
    }


def _record_provenance(scenario, deployment_target, requested_deployment):
    """Provenance: kind follows the recorded target; scenario digest binds the
    model, stimulus, and any requested-but-unavailable deployment."""
    scenario_evidence = {
        "model": scenario["model_float"],
        "stimulus": scenario["stimulus"],
    }
    if requested_deployment is not None:
        scenario_evidence["requested_deployment"] = requested_deployment
    provenance = {
        "kind": "unknown" if deployment_target in PHYSICAL_TARGETS else "simulated",
        "tool": VALIDATOR,
        "tool_version": SCHEMA_VERSION,
        "contract_version": contract.CONTRACT_VERSION,
        "scenario_sha256": digest(scenario_evidence),
        "units": {
            "time": "ms",
            "membrane": "mV_model",
            "weights": "dimensionless",
            "latency": "ms",
        },
    }
    provenance.update(_catalog_provenance_stamps())
    return provenance


def _unpaired_result(software_run, unavailable):
    """The result block for a round whose deployment oracle never ran."""
    unavailable_digest = _unavailable_evidence_digest(unavailable)
    return {
        "oracle_backed": True,
        "verdict": contract.VERDICT_INCONCLUSIVE,
        "reason_codes": ["ORACLE_UNAVAILABLE"],
        "derived_from": [software_run["output_digest"], unavailable_digest],
        "parity": None,
        "summary": _summarize_unpaired(unavailable),
    }


def _paired_result(scenario, software_run, deployment_run):
    """The result block computed from both executed oracle legs."""
    parity, verdict, reason_codes = compute_parity(scenario, software_run, deployment_run)
    derived_from = [software_run["output_digest"], deployment_run["output_digest"]]
    capture_digest = _capture_evidence_digest(deployment_run)
    if capture_digest is not None:
        derived_from.append(capture_digest)
    result = {
        "oracle_backed": True,
        "verdict": verdict,
        "reason_codes": reason_codes,
        "derived_from": derived_from,
        "parity": parity,
        "summary": _summarize(scenario, parity, verdict, deployment_run),
    }
    if capture_digest is not None:
        result["evidence_basis"] = "reference_execution_and_unverified_capture"
    return result


def _summarize(scenario, parity, verdict, deployment_run):
    bitmap = parity["spike_bitmap"]
    target = deployment_run.get("execution_target")
    if target in PHYSICAL_TARGETS:
        target = f"capture claiming {target} (physical execution unverified)"
    agreement = bitmap.get("agreement")
    agreement_text = f"{agreement:.4f}" if isinstance(agreement, float) else "n/a"
    return (
        f"{scenario['name']}: software float64 vs {target}. "
        f"spike bitmap agreement {agreement_text}, "
        f"hamming {bitmap.get('hamming_distance')}, "
        f"action {parity['action']['software']!r} vs {parity['action']['deployment']!r}, "
        f"max membrane error {parity['membrane'].get('max_abs_error')}, "
        f"verdict {verdict}."
    )


def _summarize_unpaired(unavailable):
    reason = unavailable.get("reason_code") if isinstance(unavailable, dict) else "unknown"
    return (
        "no paired run: the deployment-side oracle did not execute "
        f"({reason}). This record carries the software leg as evidence and makes no "
        "parity claim."
    )


def _unavailable_evidence_digest(unavailable):
    """Fingerprint the exact deployment diagnostic used instead of a run.

    The family validator separately replays the selected adapter's availability
    probe and requires this object to match it. Domain-separating the object here
    makes that authenticated diagnostic a first-class lineage item alongside the
    software output digest.
    """
    if not isinstance(unavailable, dict):
        raise TypeError("deployment diagnostic must be an object")
    return digest(
        {
            "evidence_kind": "deployment_unavailable_diagnostic",
            "diagnostic": unavailable,
        }
    )


def _capture_evidence_digest(deployment_run):
    """Fingerprint an unverified capture's claims for the lineage list.

    ``deployment_run["output_digest"]`` covers only the behavioural outcome
    (spikes/events/membrane/action/arithmetic). Two captures with identical
    behaviour but different board identity, bitstream, or capture source
    would otherwise collapse to the same ``result.derived_from`` lineage.
    Returns ``None`` for a non-physical (e.g. fixed-point model) deployment,
    which has no capture envelope to fingerprint.
    """
    if not isinstance(deployment_run, dict) or deployment_run.get("execution_target") not in PHYSICAL_TARGETS:
        return None
    capture = deployment_run.get("capture")
    if not isinstance(capture, dict):
        return None
    return digest(
        {
            "evidence_kind": "unverified_capture_claims",
            "hardware": deployment_run.get("hardware"),
            "bitstream": deployment_run.get("bitstream"),
            "capture_manifest_sha256": capture.get("manifest_sha256"),
            "capture_source_sha256": capture.get("source_sha256"),
            "latency": deployment_run.get("latency"),
        }
    )


def _expected_summary(record):
    """Re-derive supervised prose from structured, validated evidence."""
    oracle = record.get("oracle") or {}
    deployment = oracle.get("deployment")
    if deployment is None:
        return _summarize_unpaired(_first_unavailable(oracle))
    result = record.get("result") or {}
    parity = result.get("parity")
    if not isinstance(parity, dict) or not isinstance(deployment, dict):
        return None
    return _summarize(
        record.get("scenario") or {},
        parity,
        result.get("verdict"),
        deployment,
    )


def _first_unavailable(oracle):
    """The single unavailable diagnostic an unpaired record carries."""
    unavailable = oracle.get("unavailable") or []
    return unavailable[0] if unavailable else None


def generate_records(round_number=1, steps=12, deployment=None, repeats=3):
    """Generate one round of paired records for the whole scenario catalog.

    ``deployment`` packs the deployment side's two inputs as
    ``(adapter, probe_env)``: the oracle adapter, and the environment the
    availability probe reports against (``None`` = ambient). ``None`` is the
    in-repo fixed-point reference adapter on an ambient probe.
    """
    adapter, env = deployment if deployment is not None else (None, None)
    deployment_adapter = adapter or FixedPointReferenceAdapter()
    if env is None and isinstance(deployment_adapter, FixedPointReferenceAdapter):
        env = {}
    fpga_status = availability_report(env=env)["spikenaut_fpga"]
    records = []
    for scenario in build_scenarios(steps=steps):
        software_run, deployment_run, unavailable = run_pair(
            scenario, deployment_adapter, repeats=repeats
        )
        records.append(
            build_record(
                scenario, (software_run, deployment_run, unavailable), round_number,
                fpga_status,
            )
        )
    return records


if __package__:
    _expose_package_sibling(__name__)
