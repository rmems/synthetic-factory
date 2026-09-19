#!/usr/bin/env python3
"""Parity-family checks for the operator driver's ``smoke`` command.

Three properties, because they are the ones that would silently rot: the
unavailable oracles still say so, the generated records validate, and a
verdict that contradicts its own evidence is refused.
"""

import json


def _check_oracle_availability_reasons(neuro_oracle, nir_equivalence):
    """The unavailable oracles must still say so, with a reason code."""
    failures = []
    fpga = neuro_oracle.availability_report()["spikenaut_fpga"]
    if not fpga["available"] and not fpga.get("reason_code"):
        failures.append(
            "FPGA adapter must report unavailability with a reason code unless a "
            "board transport exists"
        )
    nir_status = nir_equivalence.availability_report()["nir_rs"]
    if not nir_status["available"] and not nir_status.get("reason_code"):
        failures.append("nir_rs must report unavailability with a reason code")
    return failures


def _generate_and_validate_smoke_families(hardware_parity, nir_equivalence, oracle_contract):
    """One round of each family must validate and actually contain a mismatch."""
    failures = []
    hardware = hardware_parity.generate_records(round_number=1, steps=6, repeats=2)
    errors = hardware_parity.validate_records(hardware, source="smoke-hw")
    if errors:
        failures.append(f"generated hardware-parity records do not validate: {errors[0]}")
    verdicts = {record["result"]["verdict"] for record in hardware}
    if oracle_contract.VERDICT_MISMATCH not in verdicts:
        failures.append(
            "hardware-parity catalog produced no mismatch; a parity corpus in which "
            "nothing ever disagrees is not testing parity"
        )

    graphs = nir_equivalence.generate_records(round_number=1, steps=6)
    errors = nir_equivalence.validate_records(graphs, source="smoke-nir")
    if errors:
        failures.append(f"generated NIR records do not validate: {errors[0]}")
    graph_verdicts = {record["result"]["verdict"] for record in graphs}
    if oracle_contract.VERDICT_MISMATCH not in graph_verdicts:
        failures.append(
            "NIR catalog produced no divergence; without one the relabelling check "
            "below silently tests nothing"
        )
    return failures, hardware, graphs


def _check_relabelled_mismatch_is_refused(cases, oracle_contract):
    """A verdict that contradicts its own evidence must be refused.

    ``cases`` pairs each family's records with its validator and the reason
    code a relabelled mismatch must surface.
    """
    failures = []
    for records, validate, code in cases:
        divergent = [
            record
            for record in records
            if record["result"]["verdict"] == oracle_contract.VERDICT_MISMATCH
        ]
        if not divergent:
            continue
        forged = json.loads(json.dumps(divergent[0]))
        forged["result"]["verdict"] = oracle_contract.VERDICT_MATCH
        if not any(code in error for error in validate(forged, "smoke:1")):
            failures.append(f"a relabelled mismatch was not caught with {code}")
    return failures


def smoke_parity_families():
    """Check the two oracle-grounded parity families end to end."""
    import hardware_parity
    import neuro_oracle
    import nir_equivalence
    from oracle_grounded import parity_contract as oracle_contract

    failures = _check_oracle_availability_reasons(neuro_oracle, nir_equivalence)
    family_failures, hardware, graphs = _generate_and_validate_smoke_families(
        hardware_parity, nir_equivalence, oracle_contract
    )
    failures += family_failures
    failures += _check_relabelled_mismatch_is_refused(
        (
            (
                hardware,
                hardware_parity.validate_record,
                "PARITY_VERDICT_INCONSISTENT",
            ),
            (graphs, nir_equivalence.validate_record, "DIVERGENCE_SUPPRESSED"),
        ),
        oracle_contract,
    )
    return failures
