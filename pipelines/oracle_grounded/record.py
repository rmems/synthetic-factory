"""The shared oracle-grounded record envelope: build, validate, reproduce.

The envelope keeps generator-authored and oracle-authored content in disjoint
subtrees, and the split is enforced rather than assumed:

* ``proposal_hash`` covers exactly the generator sections, so a measurement
  cannot be back-written into a scenario after the fact without detection.
* generator sections are scanned for measurement-shaped keys and rejected if
  they carry any.
* ``result`` must name the oracle that produced it, and that name must be the
  oracle the record declares.

Validation fails closed. A record with a missing, unattributed, or unhashed
oracle result is rejected, never downgraded to "probably fine".
"""

import re
from dataclasses import dataclass

from . import canon, families, generators, oracles, schema_validation
from .rng import Rng, seed_from_label

SCHEMA_ID = "oracle-grounded/v1"
GENERATOR_SECTIONS = ("generator", "scenario", "intervention", "candidate_prediction")
ENVELOPE_KEYS = (
    "schema",
    "id",
    "family",
    "generator",
    "scenario",
    "intervention",
    "candidate_prediction",
    "proposal_hash",
    "oracle",
    "result",
    "result_hash",
    "provenance",
    "validation",
    "meta",
)
ORACLE_KEYS = (
    "id",
    "type",
    "implementation",
    "authority",
    "requested_runtime",
    "runtime_bound",
    "repo",
    "commit",
    "dirty",
    "module",
    "module_digest",
    "version",
    "configuration",
    "seed",
    "units",
    "stages",
    "availability",
)
# The oracle, provenance, and meta blocks are authoritative execution
# provenance that no content hash covers, so their vocabularies are closed: a
# sibling key nothing here wrote (an "attestation", say) would be an
# unsupported provenance claim.
ORACLE_ALLOWED_KEYS = frozenset(ORACLE_KEYS) | {"description"}
PROVENANCE_ALLOWED_KEYS = frozenset(
    {"kind", "claimed", "oracle_grounded", "generator_authored", "oracle_authored"}
)
META_ALLOWED_KEYS = frozenset({"factory", "round", "tags"})
STAGE_ALLOWED_KEYS = frozenset(
    {
        "stage",
        "requested_runtime",
        "implementation",
        "oracle_id",
        "version",
        "module_digest",
        "runtime_commit",
        "executable",
    }
)
# Measurement-shaped keys a generator must never author. The scan is over the
# generator subtrees only; the oracle is of course free to use them.
RESERVED_GENERATOR_KEYS = frozenset(
    {
        "ground_truth",
        "measured",
        "module_digest",
        "oracle_commit",
        "oracle_result",
        "produced_by",
        "result",
        "result_hash",
    }
)
# Same vocabulary as schemas/provenance.md. `real` is never emitted.
ALLOWED_PROVENANCE_KIND = frozenset({"designed", "simulated", "hil", "unknown"})
TRAINING_PROVENANCE_KIND = frozenset({"designed", "simulated", "hil"})


class GenerationError(RuntimeError):
    """A record could not be produced; the caller decides whether to skip."""


def _reserved_hits_in_mapping(value, path):
    hits = []
    for key, item in value.items():
        here = f"{path}.{key}" if path else str(key)
        if key in RESERVED_GENERATOR_KEYS:
            hits.append(here)
        hits.extend(_reserved_key_hits(item, here))
    return hits


def _reserved_key_hits(value, path=""):
    if isinstance(value, dict):
        return _reserved_hits_in_mapping(value, path)
    if isinstance(value, list):
        return [
            hit
            for index, item in enumerate(value)
            for hit in _reserved_key_hits(item, f"{path}[{index}]")
        ]
    return []


def proposal_of(record):
    """Exactly the generator-authored subtree that ``proposal_hash`` covers."""
    return {section: record.get(section) for section in GENERATOR_SECTIONS}


def build_record(
    family,
    index,
    seed,
    round_number=1,
    commit=None,
    dirty=None,
    environ=None,
    model=None,
    factory="oracle-grounded",
):
    """Propose a scenario, execute the oracle, and assemble one record."""
    spec = families.spec_for(family)
    record_seed = seed_from_label(seed, f"{family}:{index}")
    rng = Rng(record_seed)
    scenario, intervention, candidate = spec.propose(rng)
    # Round the proposal to canonical precision *before* the oracle sees it.
    # Otherwise the oracle measures full-precision inputs while the record
    # stores rounded ones, and replaying the stored scenario reproduces a
    # slightly different measurement.
    scenario = canon.normalize(scenario)
    intervention = canon.normalize(intervention)
    candidate = canon.normalize(candidate)

    generator = generators.generator_block(record_seed, f"{family}#{index}", model=model)
    proposal = {
        "generator": generator,
        "scenario": scenario,
        "intervention": intervention,
        "candidate_prediction": candidate,
    }
    reserved = _reserved_key_hits(proposal)
    if reserved:
        raise GenerationError(f"generator emitted oracle-reserved keys: {', '.join(reserved)}")

    request = spec.build_request(scenario, intervention)
    adapter = spec.oracle(environ)
    run = adapter.run(family, request)

    if commit is None:
        commit, resolved_dirty = oracles.resolve_commit()
        if dirty is None:
            dirty = resolved_dirty

    availability = oracles.availability_report(spec.runtimes, environ)
    oracle_block = {
        "id": adapter.oracle_id,
        "type": adapter.oracle_type,
        "implementation": adapter.implementation,
        "authority": adapter.authority,
        "requested_runtime": list(spec.runtimes),
        "runtime_bound": availability["all_bound"],
        "repo": oracles.REPO_SLUG,
        "commit": commit,
        "dirty": dirty,
        "module": oracles.MODULE_PATH,
        "module_digest": oracles.module_digest(),
        "version": adapter.version,
        "description": adapter.description,
        "configuration": request["configuration"],
        # The reference oracles draw no randomness of their own; this is the
        # seed that produced the scenario they were handed.
        "seed": record_seed,
        "units": run.units,
        "stages": run.stages,
        "availability": availability,
    }
    result = {
        "produced_by": adapter.oracle_id,
        "measured": run.measured,
        "units": run.units,
    }

    record = {
        "schema": SCHEMA_ID,
        "id": f"{family}-r{round_number:02d}-{index:04d}",
        "family": family,
        "generator": generator,
        "scenario": scenario,
        "intervention": intervention,
        "candidate_prediction": candidate,
        "proposal_hash": canon.digest(proposal),
        "oracle": oracle_block,
        "result": result,
        "result_hash": canon.digest(result),
        "provenance": {
            "kind": "simulated",
            "claimed": adapter.authority,
            "oracle_grounded": True,
            "generator_authored": list(GENERATOR_SECTIONS),
            "oracle_authored": ["result", "oracle.stages"],
        },
        "validation": {},
        "meta": {
            "factory": factory,
            "round": round_number,
            "tags": ["oracle-grounded", family, adapter.implementation],
        },
    }
    record["validation"] = assess(record)
    return canon.normalize(record)


def assess(record):
    """Run every check and produce the record's own validation block."""
    # The validation block is what this function is constructing.  Validate
    # every other schema and invariant now, then authenticate the completed
    # block when the record is read back through ``validate_record``.
    layers = classify(record, check_declared_status=False)
    findings = layers["envelope"] + layers["family"]
    spec = families.spec_for(record["family"])
    try:
        score = spec.score(record)
    except Exception:
        # A measurement in an unexpected shape cannot be scored. That is itself
        # reported by the family checks; scoring must not raise over it.
        score = None
    publishable, reason = publishability(record, findings)
    return {
        "status": "accepted" if not findings else "rejected",
        "reasons": findings,
        "checks": {
            "envelope": not layers["envelope"],
            "family_invariants": not layers["family"],
        },
        "candidate_prediction_correct": score,
        "publishable": publishable,
        "publishable_reason": reason,
    }


def publishability(record, findings=()):
    """Whether this record may be published as an authoritative measurement.

    A reference simulator is a real measurement of a small model, but it is not
    the runtime the issue names, so it never earns publication on its own.
    """
    oracle = record["oracle"]
    reasons = []
    if oracle["implementation"] != "named-runtime":
        unbound = oracle["availability"]["unbound"]
        reasons.append(
            "measured by a reference implementation, not by "
            f"{', '.join(unbound) if unbound else 'the named runtime'}; "
            "publication requires the named oracle to be bound"
        )
    if oracle["commit"] == "unknown":
        reasons.append("oracle commit could not be resolved")
    if oracle.get("dirty") is None:
        reasons.append(
            "oracle working-tree dirty state is unresolved; publication "
            "requires resolved provenance"
        )
    if findings:
        reasons.append("record failed validation")
    if reasons:
        return False, "; ".join(reasons)
    return (
        True,
        "measured through the named-runtime protocol with resolved stored "
        "provenance; the protocol does not provide external attestation",
    )


def classify(record, require_named_runtime=False, check_declared_status=True, expected_commit=None):
    """Split findings into layers so a rejected record still validates.

    * ``envelope`` — structure, hashes, attribution, provenance. Always fatal:
      a record with an envelope finding is corrupt, not merely low quality.
    * ``family`` — the family's own invariants and quality gate. These are what
      a record is *allowed* to fail, as long as it says so in its validation
      block and is filed as rejected.
    * ``status`` — disagreement between the record's declared verdict and the
      recomputed one. Always fatal.
    """
    envelope = []
    if not isinstance(record, dict):
        return {"envelope": ["record is not a JSON object"], "family": [], "status": []}
    if record.get("schema") != SCHEMA_ID:
        envelope.append(f"schema must be {SCHEMA_ID!r}, got {record.get('schema')!r}")
        return {"envelope": envelope, "family": [], "status": []}
    missing = [key for key in ENVELOPE_KEYS if key not in record]
    if missing:
        envelope.append(f"missing envelope keys: {', '.join(missing)}")
        return {"envelope": envelope, "family": [], "status": []}
    family = record["family"]
    if family not in families.SPECS:
        envelope.append(f"unknown dataset family: {family!r}")
        return {"envelope": envelope, "family": [], "status": []}
    if not isinstance(record.get("id"), str) or not record["id"]:
        envelope.append("id must be a non-empty string")

    # The checked-in JSON Schemas are executable curation constraints, not
    # documentation.  Keep this stdlib-only through the local subset validator.
    try:
        envelope.extend(
            schema_validation.validate_record_schemas(
                record,
                family,
                include_validation=check_declared_status,
            )
        )
    except Exception as exc:
        envelope.append(f"record schema validation could not run: {type(exc).__name__}")
    if envelope:
        return {"envelope": envelope, "family": [], "status": []}

    envelope.extend(_validate_generator_side(record))
    envelope.extend(_validate_oracle_side(record, require_named_runtime, expected_commit))
    if envelope:
        return {"envelope": envelope, "family": [], "status": []}

    try:
        family_findings = families.spec_for(family).checks(record)
    except Exception as exc:
        return {
            "envelope": [f"family checks could not run on this record: {type(exc).__name__}"],
            "family": [],
            "status": [],
        }
    status = _validate_declared_status(record, family_findings) if check_declared_status else []
    return {"envelope": envelope, "family": family_findings, "status": status}


def validate_record(record, check_declared_status=True, require_named_runtime=False):
    """Flat list of findings. Empty means the record is acceptable as-is."""
    layers = classify(
        record,
        require_named_runtime=require_named_runtime,
        check_declared_status=check_declared_status,
    )
    findings = layers["envelope"] + layers["family"]
    if check_declared_status:
        findings = findings + layers["status"]
    return findings


def _validate_generator_side(record):
    findings = []
    generator = record["generator"]
    if not isinstance(generator, dict):
        return ["generator must be an object"]
    if generator.get("authoritative") is not False:
        findings.append("generator.authoritative must be false")
    family = record["family"]
    identifier = record["id"]
    match = re.fullmatch(rf"{re.escape(family)}-r([0-9]+)-([0-9]+)", identifier)
    if match is None:
        findings.append("id does not encode the record family, round, and index")
    else:
        round_number, index = int(match.group(1)), int(match.group(2))
        if record["meta"]["round"] != round_number:
            findings.append("meta.round does not match the round encoded in id")
        if identifier != f"{family}-r{round_number:02d}-{index:04d}":
            findings.append("id is not in canonical family-round-index form")
        if generator.get("label") != f"{family}#{index}":
            findings.append("generator.label does not match the family and index in id")
        record_seed = generator.get("seed")
        if not isinstance(record_seed, int) or isinstance(record_seed, bool):
            findings.append("generator.seed must be an integer")
        else:
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
                    findings.append(
                        "generator.seed does not reproduce the stored scenario, "
                        "intervention, and candidate prediction"
                    )
            except Exception as exc:
                findings.append(
                    "generator proposal could not be reproduced from generator.seed: "
                    f"{type(exc).__name__}"
                )
    expected_tags = ["oracle-grounded", family, record["oracle"]["implementation"]]
    if record["meta"].get("tags") != expected_tags:
        findings.append("meta.tags do not match the record family and oracle implementation")
    unknown_meta = sorted(key for key in record["meta"] if key not in META_ALLOWED_KEYS)
    if unknown_meta:
        findings.append("meta carries unauthenticated sibling keys: " + ", ".join(unknown_meta))
    if not isinstance(record["scenario"], dict) or not record["scenario"]:
        findings.append("scenario must be a non-empty object")
    candidate = record["candidate_prediction"]
    if candidate is not None:
        if not isinstance(candidate, dict):
            findings.append("candidate_prediction must be an object or null")
        elif candidate.get("kind") != "non_authoritative_guess":
            findings.append("candidate_prediction.kind must be 'non_authoritative_guess'")
    reserved = _reserved_key_hits(proposal_of(record))
    if reserved:
        findings.append(
            "generator sections carry oracle-reserved keys: " + ", ".join(sorted(reserved))
        )
    expected = canon.digest(proposal_of(record))
    if record["proposal_hash"] != expected:
        findings.append(
            "proposal_hash does not cover the stored generator sections "
            "(the scenario or the prediction was edited after the oracle ran)"
        )
    try:
        request = families.spec_for(record["family"]).build_request(
            record["scenario"], record["intervention"]
        )
        rebuilt = canon.normalize(request.get("configuration"))
        retained = canon.normalize(record["oracle"].get("configuration"))
        if retained != rebuilt:
            findings.append(
                "oracle.configuration does not match the configuration rebuilt "
                "from scenario and intervention"
            )
    except Exception as exc:
        findings.append(
            "oracle request could not be rebuilt from scenario and intervention: "
            f"{type(exc).__name__}"
        )
    return findings


def _oracle_shape_findings(oracle, findings, expected_commit=None):
    """Shape and identity checks on the oracle envelope itself.

    ``expected_commit`` is a commit the caller has already resolved against
    the repository (a run manifest's oracle commit). When provided, a record
    stamped with a different commit is rejected by string comparison instead
    of launching its own repository resolution, so a run holding thousands of
    distinct forged commits cannot turn validation into repeated git calls.
    """
    if not isinstance(oracle["configuration"], dict) or not oracle["configuration"]:
        findings.append("oracle.configuration must be a non-empty object")
    if not isinstance(oracle["units"], dict) or not oracle["units"]:
        findings.append("oracle.units must be a non-empty object")
    if not isinstance(oracle["stages"], list) or not oracle["stages"]:
        findings.append("oracle.stages must list at least one executed stage")
    if oracle["repo"] != oracles.REPO_SLUG:
        findings.append(f"oracle must declare repo {oracles.REPO_SLUG!r}")
    commit = oracle["commit"]
    if not oracles.is_source_commit(commit):
        findings.append("oracle.commit must be a resolved lowercase 40- or 64-hex source commit")
    elif expected_commit is not None and commit != expected_commit:
        findings.append(
            "oracle.commit does not match the run manifest's resolved oracle commit"
        )
    elif oracles.resolve_source_commit(commit) != commit:
        findings.append(
            "oracle.commit does not resolve to that commit object in the source repository"
        )
    if not canon.is_digest(oracle.get("module_digest", "")):
        findings.append("oracle.module_digest must be a sha256 digest")


def _oracle_implementation_findings(oracle, family, findings):
    """Checks that apply once the declared implementation is a known kind."""
    findings.extend(_validate_stage_consistency(oracle, family))
    if oracle.get("module_digest") != oracles.module_digest():
        findings.append(
            "oracle.module_digest does not match the current reference implementation"
        )
    if oracle["implementation"] in ("reference", "mixed"):
        if oracle.get("module") != oracles.MODULE_PATH:
            findings.append(f"reference oracle.module must be {oracles.MODULE_PATH!r}")
    expected_authority = {
        "reference": "reference-simulator",
        "named-runtime": "measured-runtime",
        "mixed": "mixed-reference-and-runtime",
    }[oracle["implementation"]]
    if oracle.get("authority") != expected_authority:
        findings.append(
            f"oracle.authority must be {expected_authority!r} for "
            f"implementation {oracle['implementation']!r}"
        )


def _oracle_spec_findings(oracle, family, require_named_runtime, findings):
    """The oracle envelope must match the family's declared contract."""
    spec = families.spec_for(family)
    if oracle.get("type") != spec.oracle_type:
        findings.append(
            f"oracle.type {oracle.get('type')!r} does not match family oracle type "
            f"{spec.oracle_type!r}"
        )
    if oracle.get("requested_runtime") != list(spec.runtimes):
        findings.append(
            f"oracle.requested_runtime does not match the runtimes specified for {family!r}"
        )
    if oracle.get("units") != spec.units:
        findings.append("oracle.units does not match the family units contract")
    if require_named_runtime and oracle["implementation"] != "named-runtime":
        findings.append(
            "oracle.implementation is not 'named-runtime' and a named runtime was required"
        )


def _result_findings(record, oracle, findings):
    """Validate the result block. False when curation must stop here."""
    result = record["result"]
    if not isinstance(result, dict) or not result:
        findings.append("result must be a non-empty object (curation fails closed)")
        return False
    measured = result.get("measured")
    if not isinstance(measured, dict) or not measured:
        findings.append("result.measured must be a non-empty object")
    if result.get("produced_by") != oracle["id"]:
        findings.append(
            f"result.produced_by {result.get('produced_by')!r} does not match "
            f"oracle.id {oracle['id']!r}"
        )
    result_units = result.get("units")
    if not isinstance(result_units, dict) or not result_units:
        findings.append("result.units must be a non-empty object")
    elif result_units != oracle["units"]:
        findings.append("result.units does not exactly match oracle.units")
    if record["result_hash"] != canon.digest(result):
        findings.append("result_hash does not cover the stored result")
    return True


def _provenance_findings(record, oracle, findings):
    """The provenance block must describe a simulated, oracle-grounded record."""
    provenance = record["provenance"]
    if not isinstance(provenance, dict):
        findings.append("provenance must be an object")
        return
    unknown = sorted(key for key in provenance if key not in PROVENANCE_ALLOWED_KEYS)
    if unknown:
        findings.append(
            "provenance carries unauthenticated sibling keys: " + ", ".join(unknown)
        )
    kind = provenance.get("kind")
    if kind not in ALLOWED_PROVENANCE_KIND:
        findings.append(f"provenance.kind must be one of {sorted(ALLOWED_PROVENANCE_KIND)}")
    elif kind not in TRAINING_PROVENANCE_KIND:
        findings.append("provenance.kind must not be 'unknown' on a new record")
    elif kind != "simulated":
        findings.append(
            "provenance.kind must be 'simulated'; the sf-oracle protocol does "
            "not attest physical hardware execution"
        )
    if provenance.get("oracle_grounded") is not True:
        findings.append("provenance.oracle_grounded must be true")
    if provenance.get("claimed") != oracle.get("authority"):
        findings.append("provenance.claimed must match oracle.authority")
    if provenance.get("generator_authored") != list(GENERATOR_SECTIONS):
        findings.append("provenance.generator_authored does not match the generator sections")
    if provenance.get("oracle_authored") != ["result", "oracle.stages"]:
        findings.append("provenance.oracle_authored does not match the oracle-authored sections")


def _validate_oracle_side(record, require_named_runtime, expected_commit=None):
    findings = []
    oracle = record["oracle"]
    if not isinstance(oracle, dict):
        return ["oracle must be an object"]
    missing = [key for key in ORACLE_KEYS if key not in oracle]
    if missing:
        findings.append(f"oracle is missing: {', '.join(missing)}")
        return findings
    unknown = sorted(key for key in oracle if key not in ORACLE_ALLOWED_KEYS)
    if unknown:
        findings.append(
            "oracle carries unauthenticated sibling keys: " + ", ".join(unknown)
        )
    _oracle_shape_findings(oracle, findings, expected_commit)
    if oracle["implementation"] not in ("reference", "named-runtime", "mixed"):
        findings.append(f"unknown oracle.implementation: {oracle['implementation']!r}")
    else:
        _oracle_implementation_findings(oracle, record["family"], findings)
    _oracle_spec_findings(oracle, record["family"], require_named_runtime, findings)
    if not _result_findings(record, oracle, findings):
        return findings
    _provenance_findings(record, oracle, findings)
    return findings


@dataclass(frozen=True)
class _StageEvidence:
    """The canonical expectations one family's stages are checked against."""

    oracle: dict
    family: str
    spec: object
    reference_oracle: object
    reference_adapters: list
    findings: list


def _reference_adapters_for(reference_oracle):
    """The per-stage reference adapters behind one family oracle."""
    if isinstance(reference_oracle, oracles.ChainOracle):
        return [adapter for _name, adapter, _build in reference_oracle._steps]
    return [reference_oracle]


def _named_runtime_stage_findings(stage, position, requested_runtime, findings):
    """A stage claiming a named runtime must carry that runtime's own evidence."""
    for field_name in ("version", "runtime_commit"):
        value = stage.get(field_name)
        if not isinstance(value, str) or not value.strip():
            findings.append(
                f"oracle.stages[{position}] claims a named runtime but has no {field_name}"
            )
    if not oracles.is_runtime_commit(stage.get("runtime_commit")):
        findings.append(
            f"oracle.stages[{position}].runtime_commit must be a resolved "
            "7-64 digit hexadecimal revision"
        )
    if stage.get("oracle_id") != requested_runtime:
        findings.append(
            f"oracle.stages[{position}].oracle_id must match its requested runtime"
        )
    executable = stage.get("executable")
    if not isinstance(executable, str) or not executable.strip():
        findings.append(
            f"oracle.stages[{position}] claims a named runtime but has no executable"
        )


def _reference_stage_findings(stage, position, reference_adapter, evidence):
    """A reference stage must match the simulator source that actually ran."""
    findings = evidence.findings
    if reference_adapter is not None:
        if stage.get("oracle_id") != reference_adapter.oracle_id:
            findings.append(
                f"oracle.stages[{position}].oracle_id does not match the "
                "canonical reference adapter"
            )
        if stage.get("version") != reference_adapter.version:
            findings.append(
                f"oracle.stages[{position}].version does not match the "
                "canonical reference adapter"
            )
    if "runtime_commit" in stage or "executable" in stage:
        findings.append(
            f"oracle.stages[{position}] reference evidence carries named-runtime fields"
        )
    if stage.get("module_digest") != evidence.oracle["module_digest"]:
        findings.append(
            f"oracle.stages[{position}] module_digest does not match oracle.module_digest"
        )
    if stage.get("module_digest") != oracles.module_digest():
        findings.append(
            f"oracle.stages[{position}] module_digest does not match the "
            "current reference implementation"
        )


def _stage_kind_findings(stages, evidence):
    """Check each stage against the authority it claims. Returns the kinds seen."""
    findings = evidence.findings
    spec = evidence.spec
    kinds = set()
    for position, stage in enumerate(stages):
        if not isinstance(stage, dict):
            findings.append(f"oracle.stages[{position}] is not an object")
            continue
        unknown = sorted(key for key in stage if key not in STAGE_ALLOWED_KEYS)
        if unknown:
            findings.append(
                f"oracle.stages[{position}] carries unauthenticated sibling keys: "
                + ", ".join(unknown)
            )
        kind = stage.get("implementation")
        kinds.add(kind)
        requested_runtime = spec.runtimes[position] if position < len(spec.runtimes) else None
        reference_adapter = (
            evidence.reference_adapters[position]
            if position < len(evidence.reference_adapters)
            else None
        )
        if kind == "named-runtime":
            _named_runtime_stage_findings(stage, position, requested_runtime, findings)
        elif kind == "reference":
            _reference_stage_findings(stage, position, reference_adapter, evidence)
        else:
            findings.append(
                f"oracle.stages[{position}].implementation must be 'reference' or "
                f"'named-runtime', got {kind!r}"
            )
    return kinds


def _expected_stage_names(family):
    """The stage names one family's oracle path must produce, in order."""
    if family == families.CREDIT_FAMILY:
        return [f"{family}:critic", f"{family}:plasticity"]
    return [family]


def _stage_alignment_findings(stages, evidence):
    """Stage names and per-stage requested runtimes must follow the family path."""
    findings = evidence.findings
    expected_stage_names = _expected_stage_names(evidence.family)
    requested = evidence.oracle.get("requested_runtime")
    if len(stages) != len(expected_stage_names):
        findings.append("oracle.stages count does not match the family oracle path")
        return
    for position, (stage, expected_name) in enumerate(
        zip(stages, expected_stage_names, strict=True)
    ):
        if not isinstance(stage, dict):
            continue
        if stage.get("stage") != expected_name:
            findings.append(f"oracle.stages[{position}].stage does not match {expected_name!r}")
        if isinstance(requested, list) and position < len(requested):
            if stage.get("requested_runtime") != requested[position]:
                findings.append(
                    f"oracle.stages[{position}].requested_runtime does not match "
                    "oracle.requested_runtime"
                )


def _declared_kind_findings(kinds, evidence):
    """The declared implementation must agree with the kinds the stages show."""
    findings = evidence.findings
    declared = evidence.oracle["implementation"]
    seen = sorted(str(kind) for kind in kinds)
    if declared == "named-runtime" and kinds != {"named-runtime"}:
        findings.append(
            "oracle.implementation is 'named-runtime' but not every stage was run "
            f"by a named runtime: {seen}"
        )
    if declared == "reference" and kinds != {"reference"}:
        findings.append(f"oracle.implementation is 'reference' but the stages disagree: {seen}")
    if declared == "mixed" and kinds != {"reference", "named-runtime"}:
        findings.append(
            f"oracle.implementation is 'mixed' but the stages are not mixed: {seen}"
        )


def _oracle_identity_findings(stages, evidence):
    """oracle.id and oracle.version must follow from the stages that ran."""
    findings = evidence.findings
    oracle = evidence.oracle
    stage_ids = [
        stage.get("oracle_id")
        for stage in stages
        if isinstance(stage, dict) and isinstance(stage.get("oracle_id"), str)
    ]
    if len(stage_ids) == len(stages):
        if oracle.get("id") != "+".join(stage_ids):
            findings.append("oracle.id does not match the ordered identities of oracle.stages")
    if oracle.get("version") != evidence.reference_oracle.version:
        findings.append("oracle.version does not match the canonical adapter-envelope version")


def _probe_alignment_findings(probes, requested, stages, evidence):
    """The declared probes must describe the requested runtimes and the stages."""
    findings = evidence.findings
    expected_probes = [
        {
            "runtime": runtime,
            "binding_env": oracles.env_key(runtime),
            "bound": probe.get("bound") if isinstance(probe, dict) else None,
        }
        for runtime, probe in zip(requested, probes)
    ]
    if len(probes) != len(requested) or probes != expected_probes:
        findings.append(
            "oracle.availability.runtimes must exactly describe the requested runtimes"
        )
    if len(probes) == len(stages):
        for position, (probe, stage) in enumerate(zip(probes, stages, strict=True)):
            if isinstance(probe, dict) and isinstance(stage, dict):
                expected_kind = "named-runtime" if probe.get("bound") is True else "reference"
                if stage.get("implementation") != expected_kind:
                    findings.append(
                        f"oracle.stages[{position}].implementation disagrees "
                        "with the corresponding runtime binding"
                    )


def _availability_rollup_findings(availability, probes, requested, findings):
    """all_bound and unbound must be derived from the declared probes."""
    # A set keeps this linear on untrusted probe counts; non-string runtimes
    # can never match a string name, so excluding them changes no outcome.
    bound = {
        probe.get("runtime")
        for probe in probes
        if isinstance(probe, dict)
        and probe.get("bound") is True
        and isinstance(probe.get("runtime"), str)
    }
    unbound = [runtime for runtime in requested if runtime not in bound]
    if availability.get("all_bound") is not (not unbound):
        findings.append("oracle.availability.all_bound is not derived from runtimes")
    if availability.get("unbound") != unbound:
        findings.append("oracle.availability.unbound is not derived from runtimes")


def _availability_findings(stages, evidence):
    """Bind the oracle's availability block to its stages and declared runtimes."""
    findings = evidence.findings
    oracle = evidence.oracle
    availability = oracle.get("availability")
    if not isinstance(availability, dict):
        findings.append("oracle.availability must be an object")
        return
    if oracle.get("runtime_bound") != availability.get("all_bound"):
        findings.append("oracle.runtime_bound disagrees with oracle.availability.all_bound")
    probes = availability.get("runtimes")
    requested = oracle.get("requested_runtime")
    if isinstance(probes, list) and isinstance(requested, list):
        _probe_alignment_findings(probes, requested, stages, evidence)
        _availability_rollup_findings(availability, probes, requested, findings)
    if oracle["implementation"] == "named-runtime":
        unbound = availability.get("unbound") or []
        if unbound:
            findings.append(
                "oracle.implementation is 'named-runtime' but these runtimes were "
                f"not bound: {', '.join(str(name) for name in unbound)}"
            )


def _validate_stage_consistency(oracle, family):
    """A record cannot label itself with an authority its stages do not show.

    Without this, relabelling ``implementation`` from ``reference`` to
    ``named-runtime`` would be enough to make a simulator's output look like a
    measurement from the named runtime. The stages are the evidence: a
    named-runtime stage carries the runtime's own version and commit, and a
    reference stage carries the digest of the simulator source that ran.
    """
    findings = []
    stages = oracle["stages"]
    if not isinstance(stages, list) or not stages:
        return findings
    spec = families.spec_for(family)
    reference_oracle = spec.oracle({})
    evidence = _StageEvidence(
        oracle=oracle,
        family=family,
        spec=spec,
        reference_oracle=reference_oracle,
        reference_adapters=_reference_adapters_for(reference_oracle),
        findings=findings,
    )
    kinds = _stage_kind_findings(stages, evidence)
    _stage_alignment_findings(stages, evidence)
    _declared_kind_findings(kinds, evidence)
    _oracle_identity_findings(stages, evidence)
    _availability_findings(stages, evidence)
    return findings


def _validate_declared_status(record, findings_so_far):
    validation = record.get("validation")
    if not isinstance(validation, dict):
        return ["validation must be an object"]
    out = []
    expected_status = "rejected" if findings_so_far else "accepted"
    status = validation.get("status")
    if status != expected_status:
        out.append(
            f"validation.status is {status!r} but the recomputed status is {expected_status!r}"
        )
    expected_reasons = list(findings_so_far)
    if validation.get("reasons") != expected_reasons:
        # A rejected record is still evidence; its stated reason has to be the
        # exact deterministic finding sequence, or the rejection log is fiction.
        out.append(
            "validation.reasons do not match the recomputed findings: "
            f"stored {validation.get('reasons')!r}, recomputed {expected_reasons!r}"
        )
    expected_checks = {
        "envelope": True,
        "family_invariants": not findings_so_far,
    }
    if validation.get("checks") != expected_checks:
        out.append(
            "validation.checks do not match the recomputed validation layers: "
            f"stored {validation.get('checks')!r}, recomputed {expected_checks!r}"
        )
    spec = families.spec_for(record["family"])
    try:
        expected_score = spec.score(record)
    except Exception:
        expected_score = None
    if validation.get("candidate_prediction_correct") is not expected_score:
        out.append(
            "validation.candidate_prediction_correct does not match the "
            f"recomputed candidate score {expected_score!r}"
        )
    expected_publishable, expected_reason = publishability(record, findings_so_far)
    if validation.get("publishable") is not expected_publishable:
        out.append(
            f"validation.publishable is {validation.get('publishable')!r} but the "
            f"recomputed value is {expected_publishable!r}"
        )
    if validation.get("publishable_reason") != expected_reason:
        out.append(
            "validation.publishable_reason does not match the recomputed publishability decision"
        )
    return out


def reproduce(record, environ=None):
    """Re-run the oracle from the stored scenario and compare the measurement.

    Returns ``(status, detail)`` where status is one of ``reproduced``,
    ``mismatch``, ``unavailable``, or ``invalid``.  Malformed stored input is
    bounded as ``invalid`` instead of escaping as a validator traceback.
    """
    try:
        stored_oracle = record["oracle"]
        implementation = stored_oracle["implementation"]
        stored_commit = stored_oracle.get("commit")
        if oracles.resolve_source_commit(stored_commit) != stored_commit:
            return "invalid", "stored oracle.commit is not a resolved source commit"
        if stored_oracle.get("module_digest") != oracles.module_digest():
            return "mismatch", "stored oracle module digest is not current"
        if implementation in ("reference", "mixed"):
            if stored_oracle.get("module") != oracles.MODULE_PATH:
                return "mismatch", "stored reference module identity is not current"
        spec = families.spec_for(record["family"])
        request = spec.build_request(record["scenario"], record["intervention"])
        rebuilt_configuration = canon.normalize(request.get("configuration"))
        stored_configuration = canon.normalize(stored_oracle.get("configuration"))
    except Exception as exc:
        return "invalid", f"stored record cannot rebuild an oracle request: {type(exc).__name__}"
    if rebuilt_configuration != stored_configuration:
        return "mismatch", (
            "stored oracle.configuration does not match the configuration rebuilt "
            "from scenario and intervention"
        )
    try:
        adapter = spec.oracle(environ)
    except oracles.OracleError as exc:
        return "unavailable", str(exc)
    if adapter.implementation != record["oracle"]["implementation"]:
        return "unavailable", (
            f"record was measured by {record['oracle']['implementation']!r} but this "
            f"environment resolves to {adapter.implementation!r}"
        )
    try:
        run = adapter.run(record["family"], request)
    except oracles.OracleError as exc:
        return "unavailable", str(exc)
    try:
        replay_stages = canon.normalize(run.stages)
        stored_stages = canon.normalize(stored_oracle["stages"])
    except Exception as exc:
        return "invalid", f"stored stage identity is malformed: {type(exc).__name__}"
    if replay_stages != stored_stages:
        return "mismatch", "stored oracle stage code identity does not match the replay"
    replay = {
        "produced_by": adapter.oracle_id,
        "measured": run.measured,
        "units": run.units,
    }
    try:
        replay_digest = canon.digest(replay)
        expected_digest = record["result_hash"]
    except (KeyError, TypeError, ValueError) as exc:
        return "invalid", f"stored result digest is malformed: {type(exc).__name__}"
    if replay_digest == expected_digest:
        return "reproduced", expected_digest
    return "mismatch", f"expected {expected_digest}, recomputed {replay_digest}"
