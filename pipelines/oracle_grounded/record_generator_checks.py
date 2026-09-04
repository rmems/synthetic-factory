"""Generator-side validation: the proposal must be reproducible and unarmed.

The generator's sections are bound three ways: the stored id/seed must
regenerate the exact stored proposal, the sections must carry none of the
oracle-reserved measurement keys, and ``proposal_hash`` must cover exactly
what is stored. A record that fails any of these was edited after the oracle
ran, or was produced by something other than the deterministic generator.
"""

import re

from . import canon, families, generators
from .record_envelope import (
    META_ALLOWED_KEYS,
    _reserved_key_hits,
    _reserved_key_listing,
    proposal_of,
)
from .rng import Rng


def _generator_reproduction_findings(record, generator, identity):
    """generator.seed must regenerate the generator block and oracle seed."""
    findings = []
    family, index = identity
    record_seed = generator.get("seed")
    if not isinstance(record_seed, int) or isinstance(record_seed, bool):
        findings.append("generator.seed must be an integer")
        return findings
    expected_generator = generators.generator_block(
        record_seed,
        f"{family}#{index}",
        model=generator.get("name"),
    )
    if generator != expected_generator:
        findings.append("generator does not match the deterministic generator contract")
    oracle_seed = record["oracle"].get("seed")
    if oracle_seed != record_seed:
        findings.append(
            "oracle.seed does not match the generator seed that produced this record"
        )
    findings.extend(_proposal_reproduction_findings(record, family, record_seed))
    return findings


def _proposal_reproduction_findings(record, family, record_seed):
    """The stored proposal must replay exactly from the stored seed."""
    try:
        expected_scenario, expected_intervention, expected_candidate = families.spec_for(
            family
        ).propose(Rng(record_seed))
        expected_proposal = {
            "scenario": canon.normalize(expected_scenario),
            "intervention": canon.normalize(expected_intervention),
            "candidate_prediction": canon.normalize(expected_candidate),
        }
        retained_proposal = {
            key: record[key] for key in ("scenario", "intervention", "candidate_prediction")
        }
        if retained_proposal != expected_proposal:
            return [
                "generator.seed does not reproduce the stored scenario, "
                "intervention, and candidate prediction"
            ]
    except Exception as exc:
        return [
            "generator proposal could not be reproduced from generator.seed: "
            f"{type(exc).__name__}"
        ]
    return []


def _identity_findings(record, generator):
    """The id must encode family, round, and index, and agree with the metadata."""
    findings = []
    family = record["family"]
    identifier = record["id"]
    match = re.fullmatch(rf"{re.escape(family)}-r([0-9]+)-([0-9]+)", identifier)
    if match is None:
        findings.append("id does not encode the record family, round, and index")
        return findings
    round_number, index = int(match.group(1)), int(match.group(2))
    if record["meta"]["round"] != round_number:
        findings.append("meta.round does not match the round encoded in id")
    if identifier != f"{family}-r{round_number:02d}-{index:04d}":
        findings.append("id is not in canonical family-round-index form")
    if generator.get("label") != f"{family}#{index}":
        findings.append("generator.label does not match the family and index in id")
    findings.extend(_generator_reproduction_findings(record, generator, (family, index)))
    return findings


def _meta_findings(record):
    """meta.tags restate the family and implementation; meta keys are closed."""
    findings = []
    family = record["family"]
    expected_tags = ["oracle-grounded", family, record["oracle"]["implementation"]]
    if record["meta"].get("tags") != expected_tags:
        findings.append("meta.tags do not match the record family and oracle implementation")
    unknown_meta = sorted(key for key in record["meta"] if key not in META_ALLOWED_KEYS)
    if unknown_meta:
        findings.append("meta carries unauthenticated sibling keys: " + ", ".join(unknown_meta))
    return findings


def _proposal_shape_findings(record):
    """The scenario must be substantive and the candidate a labelled guess."""
    findings = []
    if not isinstance(record["scenario"], dict) or not record["scenario"]:
        findings.append("scenario must be a non-empty object")
    candidate = record["candidate_prediction"]
    if candidate is not None:
        if not isinstance(candidate, dict):
            findings.append("candidate_prediction must be an object or null")
        elif candidate.get("kind") != "non_authoritative_guess":
            findings.append("candidate_prediction.kind must be 'non_authoritative_guess'")
    return findings


def _proposal_integrity_findings(record):
    """Reserved-key scan, proposal hash, and the configuration rebuild."""
    findings = []
    reserved = _reserved_key_hits(proposal_of(record))
    if reserved:
        findings.append(
            "generator sections carry oracle-reserved keys: " + _reserved_key_listing(reserved)
        )
    expected = canon.digest(proposal_of(record))
    if record["proposal_hash"] != expected:
        findings.append(
            "proposal_hash does not cover the stored generator sections "
            "(the scenario or the prediction was edited after the oracle ran)"
        )
    findings.extend(_configuration_rebuild_findings(record))
    return findings


def _configuration_rebuild_findings(record):
    """oracle.configuration must be derivable from the stored proposal."""
    try:
        request = families.spec_for(record["family"]).build_request(
            record["scenario"], record["intervention"]
        )
        rebuilt = canon.normalize(request.get("configuration"))
        retained = canon.normalize(record["oracle"].get("configuration"))
        if retained != rebuilt:
            return [
                "oracle.configuration does not match the configuration rebuilt "
                "from scenario and intervention"
            ]
    except Exception as exc:
        return [
            "oracle request could not be rebuilt from scenario and intervention: "
            f"{type(exc).__name__}"
        ]
    return []


def _validate_generator_side(record):
    generator = record["generator"]
    if not isinstance(generator, dict):
        return ["generator must be an object"]
    findings = []
    if generator.get("authoritative") is not False:
        findings.append("generator.authoritative must be false")
    findings.extend(_identity_findings(record, generator))
    findings.extend(_meta_findings(record))
    findings.extend(_proposal_shape_findings(record))
    findings.extend(_proposal_integrity_findings(record))
    return findings
