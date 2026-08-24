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

from . import canon, families, generators, oracles
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
    "module",
    "module_digest",
    "version",
    "configuration",
    "seed",
    "units",
    "stages",
    "availability",
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


def _reserved_key_hits(value, path=""):
    hits = []
    if isinstance(value, dict):
        for key, item in value.items():
            here = f"{path}.{key}" if path else str(key)
            if key in RESERVED_GENERATOR_KEYS:
                hits.append(here)
            hits.extend(_reserved_key_hits(item, here))
    elif isinstance(value, list):
        for index, item in enumerate(value):
            hits.extend(_reserved_key_hits(item, f"{path}[{index}]"))
    return hits


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
        raise GenerationError(
            f"generator emitted oracle-reserved keys: {', '.join(reserved)}"
        )

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
    layers = classify(record)
    findings = layers["envelope"] + layers["family"]
    spec = families.spec_for(record["family"])
    try:
        score = spec.score(record)
    except (KeyError, IndexError, TypeError, ValueError):
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
    if findings:
        reasons.append("record failed validation")
    if reasons:
        return False, "; ".join(reasons)
    return True, "measured by the named runtime with resolved provenance"


def classify(record, require_named_runtime=False):
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

    envelope.extend(_validate_generator_side(record))
    envelope.extend(_validate_oracle_side(record, require_named_runtime))
    if envelope:
        return {"envelope": envelope, "family": [], "status": []}

    try:
        family_findings = families.spec_for(family).checks(record)
    except (KeyError, TypeError, IndexError) as exc:
        return {
            "envelope": [f"family checks could not run on this record: {exc}"],
            "family": [],
            "status": [],
        }
    status = _validate_declared_status(record, family_findings)
    return {"envelope": envelope, "family": family_findings, "status": status}


def validate_record(record, check_declared_status=True, require_named_runtime=False):
    """Flat list of findings. Empty means the record is acceptable as-is."""
    layers = classify(record, require_named_runtime=require_named_runtime)
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
    if not isinstance(record["scenario"], dict) or not record["scenario"]:
        findings.append("scenario must be a non-empty object")
    candidate = record["candidate_prediction"]
    if candidate is not None:
        if not isinstance(candidate, dict):
            findings.append("candidate_prediction must be an object or null")
        elif candidate.get("kind") != "non_authoritative_guess":
            findings.append(
                "candidate_prediction.kind must be 'non_authoritative_guess'"
            )
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
    return findings


def _validate_oracle_side(record, require_named_runtime):
    findings = []
    oracle = record["oracle"]
    if not isinstance(oracle, dict):
        return ["oracle must be an object"]
    missing = [key for key in ORACLE_KEYS if key not in oracle]
    if missing:
        findings.append(f"oracle is missing: {', '.join(missing)}")
        return findings
    if not isinstance(oracle["configuration"], dict) or not oracle["configuration"]:
        findings.append("oracle.configuration must be a non-empty object")
    if not isinstance(oracle["units"], dict) or not oracle["units"]:
        findings.append("oracle.units must be a non-empty object")
    if not isinstance(oracle["stages"], list) or not oracle["stages"]:
        findings.append("oracle.stages must list at least one executed stage")
    if oracle["repo"] != oracles.REPO_SLUG and oracle["implementation"] == "reference":
        findings.append(f"reference oracle must declare repo {oracles.REPO_SLUG!r}")
    commit = oracle["commit"]
    if not isinstance(commit, str) or not commit.strip() or commit == "unknown":
        findings.append("oracle.commit must be a resolved commit, not 'unknown'")
    if not canon.is_digest(oracle.get("module_digest", "")):
        findings.append("oracle.module_digest must be a sha256 digest")
    if oracle["implementation"] not in ("reference", "named-runtime", "mixed"):
        findings.append(f"unknown oracle.implementation: {oracle['implementation']!r}")
    else:
        findings.extend(_validate_stage_consistency(oracle))
    if require_named_runtime and oracle["implementation"] != "named-runtime":
        findings.append(
            "oracle.implementation is not 'named-runtime' and a named runtime was required"
        )

    result = record["result"]
    if not isinstance(result, dict) or not result:
        findings.append("result must be a non-empty object (curation fails closed)")
        return findings
    measured = result.get("measured")
    if not isinstance(measured, dict) or not measured:
        findings.append("result.measured must be a non-empty object")
    if result.get("produced_by") != oracle["id"]:
        findings.append(
            f"result.produced_by {result.get('produced_by')!r} does not match "
            f"oracle.id {oracle['id']!r}"
        )
    if record["result_hash"] != canon.digest(result):
        findings.append("result_hash does not cover the stored result")

    provenance = record["provenance"]
    if not isinstance(provenance, dict):
        findings.append("provenance must be an object")
    else:
        kind = provenance.get("kind")
        if kind not in ALLOWED_PROVENANCE_KIND:
            findings.append(f"provenance.kind must be one of {sorted(ALLOWED_PROVENANCE_KIND)}")
        elif kind not in TRAINING_PROVENANCE_KIND:
            findings.append("provenance.kind must not be 'unknown' on a new record")
    return findings


def _validate_stage_consistency(oracle):
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
    kinds = set()
    for position, stage in enumerate(stages):
        if not isinstance(stage, dict):
            findings.append(f"oracle.stages[{position}] is not an object")
            continue
        kind = stage.get("implementation")
        kinds.add(kind)
        if kind == "named-runtime":
            for field in ("version", "runtime_commit"):
                value = stage.get(field)
                if not isinstance(value, str) or not value.strip():
                    findings.append(
                        f"oracle.stages[{position}] claims a named runtime but has no {field}"
                    )
        elif kind == "reference":
            if stage.get("module_digest") != oracle["module_digest"]:
                findings.append(
                    f"oracle.stages[{position}] module_digest does not match oracle.module_digest"
                )
        else:
            findings.append(
                f"oracle.stages[{position}].implementation must be 'reference' or "
                f"'named-runtime', got {kind!r}"
            )
    declared = oracle["implementation"]
    if declared == "named-runtime" and kinds != {"named-runtime"}:
        findings.append(
            "oracle.implementation is 'named-runtime' but not every stage was run "
            f"by a named runtime: {sorted(str(kind) for kind in kinds)}"
        )
    if declared == "reference" and kinds != {"reference"}:
        findings.append(
            "oracle.implementation is 'reference' but the stages disagree: "
            f"{sorted(str(kind) for kind in kinds)}"
        )
    if declared == "mixed" and kinds != {"reference", "named-runtime"}:
        findings.append(
            "oracle.implementation is 'mixed' but the stages are not mixed: "
            f"{sorted(str(kind) for kind in kinds)}"
        )

    availability = oracle.get("availability")
    if not isinstance(availability, dict):
        findings.append("oracle.availability must be an object")
        return findings
    if oracle.get("runtime_bound") != availability.get("all_bound"):
        findings.append("oracle.runtime_bound disagrees with oracle.availability.all_bound")
    if declared == "named-runtime":
        unbound = availability.get("unbound") or []
        if unbound:
            findings.append(
                "oracle.implementation is 'named-runtime' but these runtimes were "
                f"not bound: {', '.join(str(name) for name in unbound)}"
            )
    return findings


def _validate_declared_status(record, findings_so_far):
    validation = record.get("validation")
    if not isinstance(validation, dict):
        return ["validation must be an object"]
    status = validation.get("status")
    if status not in ("accepted", "rejected"):
        return [f"validation.status must be accepted or rejected, got {status!r}"]
    out = []
    reasons = validation.get("reasons") or []
    if status == "accepted" and findings_so_far:
        out.append("validation.status is 'accepted' but the record fails its own checks")
    if status == "rejected":
        if not reasons:
            out.append("validation.status is 'rejected' but no reason is recorded")
        elif sorted(reasons) != sorted(findings_so_far):
            # A rejected record is still evidence; its stated reason has to be
            # the reason it actually fails, or the rejection log is fiction.
            out.append(
                "validation.reasons do not match the recomputed findings: "
                f"stored {sorted(reasons)}, recomputed {sorted(findings_so_far)}"
            )
    if validation.get("publishable") and record["oracle"]["implementation"] != "named-runtime":
        out.append(
            "validation.publishable is true for a record measured by a reference "
            "implementation"
        )
    return out


def reproduce(record, environ=None):
    """Re-run the oracle from the stored scenario and compare the measurement.

    Returns ``(status, detail)`` where status is one of ``reproduced``,
    ``mismatch``, or ``unavailable``.
    """
    spec = families.spec_for(record["family"])
    request = spec.build_request(record["scenario"], record["intervention"])
    adapter = spec.oracle(environ)
    if adapter.implementation != record["oracle"]["implementation"]:
        return "unavailable", (
            f"record was measured by {record['oracle']['implementation']!r} but this "
            f"environment resolves to {adapter.implementation!r}"
        )
    try:
        run = adapter.run(record["family"], request)
    except oracles.OracleError as exc:
        return "unavailable", str(exc)
    replay = {
        "produced_by": adapter.oracle_id,
        "measured": run.measured,
        "units": run.units,
    }
    if canon.digest(replay) == record["result_hash"]:
        return "reproduced", record["result_hash"]
    return "mismatch", (
        f"expected {record['result_hash']}, recomputed {canon.digest(replay)}"
    )
