"""The neuromorphic oracle-grounded record contract: build, validate, reproduce.

This is the domain contract for the five families of issue #77, built on the
shared, domain-neutral envelope in ``.envelope`` (#172). The envelope supplies
the section names, the repository-wide ``provenance.kind`` vocabulary, the
bounded reserved-key walker, and the ``proposal_of`` subtree; this module owns
everything the domain contracts disagree on -- the ``canon`` digest dialect
behind ``proposal_hash`` and ``result_hash``, the neuromorphic reserved-key
set, oracle stages, availability, ``reproduce``, and the validation-status
vocabulary.

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
import sys
from dataclasses import dataclass

from . import canon, families, generators, oracles, schema_validation, source_policy
from . import envelope as _shared_envelope
from .envelope import (
    GENERATOR_SECTIONS,
    MAX_RESERVED_KEY_HITS,
    is_enum_value,
    reserved_key_hits,
)
from . import rng as _rng
from . import record_replay as _record_replay
from .rng import Rng, seed_from_label

MAX_SEED = _rng.MAX_SEED
proposal_of = _shared_envelope.proposal_of

ALLOWED_PROVENANCE_KIND = _shared_envelope.PROVENANCE_KINDS
TRAINING_PROVENANCE_KIND = _shared_envelope.TRAINING_PROVENANCE_KINDS

if __package__.startswith("pipelines."):
    from .. import oracle_record_stages as _stages
    from .. import oracle_record_envelope as _record_envelope
    from .. import oracle_record_generator as _record_generator
else:
    import oracle_record_stages as _stages
    import oracle_record_envelope as _record_envelope
    import oracle_record_generator as _record_generator

SCHEMA_ID = "oracle-grounded/v1"
ENVELOPE_KEYS = tuple(
    (
        "schema id family generator scenario intervention "
        "candidate_prediction proposal_hash oracle result result_hash "
        "provenance validation meta"
    ).split()
)
ORACLE_KEYS = tuple(
    (
        "id type implementation authority requested_runtime runtime_bound "
        "repo commit dirty module module_digest version configuration "
        "seed units stages availability"
    ).split()
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
# generator subtrees only; the oracle is of course free to use them. The
# bounded walk itself is the envelope's; this set is the neuromorphic contract's.
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
# ``provenance.kind`` and its training-eligible subset are the envelope's
# (schemas/provenance.md vocabulary; `real` is never emitted). They are bound
# above under this module's historical names for its callers.


class GenerationError(RuntimeError):
    """A record could not be produced; the caller decides whether to skip."""


@dataclass(frozen=True)
class RecordRunContext:
    """Run-level provenance stamped identically on every record of one pass."""

    round_number: int = 1
    commit: object = None
    dirty: object = None
    environ: object = None
    model: object = None
    factory: str = "oracle-grounded"
    backend: str = "reference"


@dataclass(frozen=True)
class _Subject:
    """One record's identity inside a run: family, position, seed, spec."""

    family: str
    index: int
    record_seed: int
    spec: object
    run: RecordRunContext


@dataclass(frozen=True)
class _Outcome:
    """What executing the oracle produced plus resolved stored provenance."""

    execution: object
    commit: object
    dirty: object
    record_seed: int
    availability: dict


@dataclass(frozen=True)
class _RecordParts:
    """The three subtrees one record assembles around."""

    proposal: dict
    oracle: dict
    result: dict


def _reserved_key_hits(value):
    """Paths of oracle-reserved keys in the generator sections of ``value``.

    The bounded walk is the envelope's; only the reserved-key set is this
    contract's. At most ``MAX_RESERVED_KEY_HITS`` paths are collected, because
    one hit already rejects the record.
    """
    return reserved_key_hits(value, RESERVED_GENERATOR_KEYS)


def _reserved_key_listing(hits):
    """Human-readable path list, marking when the bounded scan stopped early."""
    listed = ", ".join(sorted(hits))
    if len(hits) >= MAX_RESERVED_KEY_HITS:
        listed += ", ... (scan capped)"
    return listed


def _record_id_parts(family, identifier):
    """The (round, index) a record id encodes, or None when it is malformed.

    The id grammar is this contract's: ``build_record`` mints
    ``{family}-r{round:02d}-{index:04d}``, so the same shape is what a
    retained id is checked against.
    """
    match = re.fullmatch(rf"{re.escape(family)}-r([0-9]+)-([0-9]+)", identifier)
    if match is None:
        return None
    return int(match.group(1)), int(match.group(2))


def _backend_spec(family, backend, environ):
    """The family spec and effective environ for the selected oracle backend."""
    if backend not in ('reference', 'rust'):
        raise GenerationError('unsupported oracle backend')
    if backend == 'reference':
        return families.spec_for(family), environ
    from . import native_profiles, native_runtime
    if family not in native_profiles.PROFILES:
        raise GenerationError('Rust backend does not support this family')
    return (
        families.spec_for_profile(family, native_profiles.PROFILES[family]),
        native_runtime.runtime_environ(base=environ),
    )


def _resolved_provenance(commit, dirty):
    """Fill an unpinned commit (and its dirty flag) from the working tree."""
    if commit is not None:
        return commit, dirty
    resolved_commit, resolved_dirty = oracles.resolve_commit()
    return resolved_commit, resolved_dirty if dirty is None else dirty


def _proposal(subject):
    """The generator sections, normalized before the oracle sees them.

    Round the proposal to canonical precision *before* the oracle sees it.
    Otherwise the oracle measures full-precision inputs while the record
    stores rounded ones, and replaying the stored scenario reproduces a
    slightly different measurement.
    """
    rng = Rng(subject.record_seed)
    scenario, intervention, candidate = subject.spec.propose(rng)
    scenario = canon.normalize(scenario)
    intervention = canon.normalize(intervention)
    candidate = canon.normalize(candidate)
    proposal = {
        "generator": generators.generator_block(
            subject.record_seed,
            f"{subject.family}#{subject.index}",
            model=subject.run.model,
        ),
        "scenario": scenario,
        "intervention": intervention,
        "candidate_prediction": candidate,
    }
    reserved = _reserved_key_hits(proposal)
    if reserved:
        raise GenerationError(
            f"generator emitted oracle-reserved keys: {_reserved_key_listing(reserved)}"
        )
    return proposal


def _measure(adapter, request, subject, environ):
    """Execute the oracle and resolve the run's stored provenance."""
    execution = adapter.run(subject.family, request)
    commit, dirty = _resolved_provenance(subject.run.commit, subject.run.dirty)
    availability = oracles.availability_report(subject.spec.runtimes, environ)
    return _Outcome(execution, commit, dirty, subject.record_seed, availability)


def _oracle_block(adapter, spec, request, outcome):
    return {
        "id": adapter.oracle_id,
        "type": adapter.oracle_type,
        "implementation": adapter.implementation,
        "authority": adapter.authority,
        "requested_runtime": list(spec.runtimes),
        "runtime_bound": outcome.availability["all_bound"],
        "repo": oracles.REPO_SLUG,
        "commit": outcome.commit,
        "dirty": outcome.dirty,
        "module": oracles.MODULE_PATH,
        "module_digest": oracles.module_digest(),
        "version": adapter.version,
        "description": adapter.description,
        "configuration": request["configuration"],
        # The reference oracles draw no randomness of their own; this is the
        # seed that produced the scenario they were handed.
        "seed": outcome.record_seed,
        "units": outcome.execution.units,
        "stages": outcome.execution.stages,
        "availability": outcome.availability,
    }


def _assemble(subject, parts):
    record = {
        "schema": SCHEMA_ID,
        "id": f"{subject.family}-r{subject.run.round_number:02d}-{subject.index:04d}",
        "family": subject.family,
        "generator": parts.proposal["generator"],
        "scenario": parts.proposal["scenario"],
        "intervention": parts.proposal["intervention"],
        "candidate_prediction": parts.proposal["candidate_prediction"],
        "proposal_hash": canon.digest(parts.proposal),
        "oracle": parts.oracle,
        "result": parts.result,
        "result_hash": canon.digest(parts.result),
        "provenance": {
            "kind": "simulated",
            "claimed": parts.oracle["authority"],
            "oracle_grounded": True,
            "generator_authored": list(GENERATOR_SECTIONS),
            "oracle_authored": ["result", "oracle.stages"],
        },
        "validation": {},
        "meta": {
            "factory": subject.run.factory,
            "round": subject.run.round_number,
            "tags": ["oracle-grounded", subject.family, parts.oracle["implementation"]],
        },
    }
    record["validation"] = assess(record)
    return canon.normalize(record)


def build_record(family, index, seed, run=None):
    """Propose a scenario, execute the oracle, and assemble one record."""
    run = run or RecordRunContext()
    spec, environ = _backend_spec(family, run.backend, run.environ)
    subject = _Subject(family, index, seed_from_label(seed, f"{family}:{index}"), spec, run)
    proposal = _proposal(subject)
    request = spec.build_request(proposal["scenario"], proposal["intervention"])
    adapter = spec.oracle(environ)
    outcome = _measure(adapter, request, subject, environ)
    result = {
        "produced_by": adapter.oracle_id,
        "measured": outcome.execution.measured,
        "units": outcome.execution.units,
    }
    parts = _RecordParts(proposal, _oracle_block(adapter, spec, request, outcome), result)
    return _assemble(subject, parts)


def assess(record):
    """Run every check and produce the record's own validation block."""
    # The validation block is what this function is constructing.  Validate
    # every other schema and invariant now, then authenticate the completed
    # block when the record is read back through ``validate_record``.
    layers = classify(record, check_declared_status=False)
    findings = layers["envelope"] + layers["family"]
    spec = families.spec_for_record(record)
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


# Why a record may be published, by the oracle implementation that measured
# it. A deterministic in-repo reference simulator is an authoritative oracle
# for training-candidate data when its measurement is reproducible (#171): the
# record is simulated provenance and its oracle.module_digest matches the
# current reference sources. A named external runtime is optional stronger
# evidence and is recorded exactly as before.
PUBLISHABLE_REASONS = {
    "reference": (
        "measured by the in-repo reference simulator at the current module "
        "digest with resolved stored provenance (#171); the named runtime is "
        "not bound, so this is a reproducible simulation, not a runtime "
        "attestation"
    ),
    "mixed": (
        "measured by the in-repo reference simulator at the current module "
        "digest and through the named-runtime protocol with resolved stored "
        "provenance (#171); neither path provides external attestation"
    ),
    "named-runtime": (
        "measured through the named-runtime protocol with resolved stored "
        "provenance; the protocol does not provide external attestation"
    ),
}


def _simulator_publication_blockers(record, oracle):
    """Why a reference or mixed measurement is not publishable (#171).

    The in-repo simulator earns publication only when its measurement can be
    reproduced from the sources this validator is running: the record must be
    simulated provenance and carry the current ``oracle.module_digest``. A
    digest nothing here can reproduce keeps ``publishable`` false.
    """
    reasons = []
    provenance = record.get("provenance")
    kind = provenance.get("kind") if isinstance(provenance, dict) else None
    if kind != "simulated":
        reasons.append(
            f"provenance.kind is {kind!r}; a reference-simulator measurement is "
            "publishable only as 'simulated' provenance"
        )
    if oracle.get("module_digest") != oracles.module_digest():
        reasons.append(
            "oracle.module_digest does not match the current reference sources, "
            "so the simulator measurement cannot be reproduced here; publication "
            "requires a reproducible digest"
        )
    return reasons


def _identity_publication_blockers(record):
    """Custom provenance may describe diagnostics, but not reviewed authority."""
    generator, meta = record.get("generator"), record.get("meta")
    if not isinstance(generator, dict) or not isinstance(meta, dict):
        return ["generator and factory identity must match the reviewed procedural policy"]
    claims = (generator.get("name"), generator.get("version"), meta.get("factory"))
    expected = tuple(source_policy.POLICY[key] for key in ("generator", "generator_version", "family"))
    if claims != expected:
        return ["generator and factory identity must match the reviewed procedural policy"]
    return []


def publishability(record, findings=()):
    """Whether this record may be published as an authoritative measurement.

    A deterministic in-repo reference simulator is an authoritative oracle when
    its measurement is reproducible (#171): simulated provenance at the current
    ``module_digest``. A named external runtime remains optional stronger
    evidence and is recorded exactly as before. An unresolved commit or dirty
    state, an unreproducible digest, or any validation finding refuses
    publication.
    """
    oracle = record["oracle"]
    implementation = oracle["implementation"]
    reasons = _identity_publication_blockers(record)
    if not is_enum_value(implementation, PUBLISHABLE_REASONS):
        reasons.append(f"unknown oracle.implementation: {implementation!r}")
    elif implementation != "named-runtime":
        reasons.extend(_simulator_publication_blockers(record, oracle))
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
    return True, PUBLISHABLE_REASONS[implementation]


def _layers(envelope, family=(), status=()):
    return {"envelope": list(envelope), "family": list(family), "status": list(status)}


def _envelope_gate_findings(record, check_declared_status):
    """Structural findings that stop classification before content checks."""
    if not isinstance(record, dict):
        return ["record is not a JSON object"]
    if record.get("schema") != SCHEMA_ID:
        return [f"schema must be {SCHEMA_ID!r}, got {record.get('schema')!r}"]
    missing = [key for key in ENVELOPE_KEYS if key not in record]
    if missing:
        return [f"missing envelope keys: {', '.join(missing)}"]
    family = record["family"]
    if family not in families.SPECS:
        return [f"unknown dataset family: {family!r}"]
    findings = []
    if not isinstance(record.get("id"), str) or not record["id"]:
        findings.append("id must be a non-empty string")
    findings.extend(_schema_gate_findings(record, family, check_declared_status))
    return findings


def _schema_gate_findings(record, family, check_declared_status):
    # The checked-in JSON Schemas are executable curation constraints, not
    # documentation.  Keep this stdlib-only through the local subset validator.
    try:
        return schema_validation.validate_record_schemas(
            record,
            family,
            include_validation=check_declared_status,
        )
    except Exception as exc:
        return [f"record schema validation could not run: {type(exc).__name__}"]


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
    envelope = _envelope_gate_findings(record, check_declared_status)
    if envelope:
        return _layers(envelope)

    envelope.extend(_validate_generator_side(record))
    envelope.extend(_validate_oracle_side(record, require_named_runtime, expected_commit))
    if envelope:
        return _layers(envelope)

    try:
        family_findings = families.spec_for_record(record).checks(record)
    except Exception as exc:
        return _layers(
            [f"family checks could not run on this record: {type(exc).__name__}"]
        )
    envelope.extend(_reference_replay_findings(record))
    status = (_validate_declared_status(record, family_findings)
              if check_declared_status and not envelope else [])
    return _layers(envelope, family_findings, status)


def _reference_replay_findings(record):
    """Authenticate reference execution after bounded proposal and family checks."""
    if record["oracle"]["implementation"] != "reference":
        return []
    try:
        status, detail = reproduce(record, environ={})
    except Exception as exc:
        return [f"reference replay could not run: {type(exc).__name__}"]
    if status != "reproduced":
        return [f"reference replay {status}: {detail}"]
    return []


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
    return _record_generator.GeneratorChecks(sys.modules[__name__]).validate(record)


def _oracle_shape_findings(oracle, findings, expected_commit=None):
    return _record_envelope.EnvelopeChecks(sys.modules[__name__])._oracle_shape_findings(oracle, findings, expected_commit)


def _oracle_implementation_findings(oracle, family, findings):
    return _record_envelope.EnvelopeChecks(sys.modules[__name__])._oracle_implementation_findings(oracle, family, findings)


def _oracle_spec_findings(oracle, family, require_named_runtime, findings):
    return _record_envelope.EnvelopeChecks(sys.modules[__name__])._oracle_spec_findings(oracle, family, require_named_runtime, findings)


def _result_findings(record, oracle, findings):
    return _record_envelope.EnvelopeChecks(sys.modules[__name__])._result_findings(record, oracle, findings)


def _provenance_findings(record, oracle, findings):
    return _record_envelope.EnvelopeChecks(sys.modules[__name__])._provenance_findings(record, oracle, findings)


def _validate_oracle_side(record, require_named_runtime, expected_commit=None):
    return _record_envelope.EnvelopeChecks(sys.modules[__name__])._validate_oracle_side(record, require_named_runtime, expected_commit)


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
    return _stages.StageChecks(sys.modules[__name__])._reference_adapters_for(reference_oracle)


def _named_runtime_stage_findings(stage, position, requested_runtime, findings):
    return _stages.StageChecks(sys.modules[__name__])._named_runtime_stage_findings(stage, position, requested_runtime, findings)


def _reference_stage_findings(stage, position, reference_adapter, evidence):
    return _stages.StageChecks(sys.modules[__name__])._reference_stage_findings(stage, position, reference_adapter, evidence)


def _stage_kind_findings(stages, evidence):
    return _stages.StageChecks(sys.modules[__name__])._stage_kind_findings(stages, evidence)


def _expected_stage_names(family):
    return _stages.StageChecks(sys.modules[__name__])._expected_stage_names(family)


def _stage_alignment_findings(stages, evidence):
    return _stages.StageChecks(sys.modules[__name__])._stage_alignment_findings(stages, evidence)


def _declared_kind_findings(kinds, evidence):
    return _stages.StageChecks(sys.modules[__name__])._declared_kind_findings(kinds, evidence)


def _oracle_identity_findings(stages, evidence):
    return _stages.StageChecks(sys.modules[__name__])._oracle_identity_findings(stages, evidence)


def _probe_alignment_findings(probes, requested, stages, evidence):
    return _stages.StageChecks(sys.modules[__name__])._probe_alignment_findings(probes, requested, stages, evidence)


def _availability_rollup_findings(availability, probes, requested, findings):
    return _stages.StageChecks(sys.modules[__name__])._availability_rollup_findings(availability, probes, requested, findings)


def _availability_findings(stages, evidence):
    return _stages.StageChecks(sys.modules[__name__])._availability_findings(stages, evidence)


def _validate_stage_consistency(oracle, family):
    return _stages.StageChecks(sys.modules[__name__])._validate_stage_consistency(oracle, family)


def _declared_verdict_findings(validation, findings_so_far):
    """The stored status, reasons, and layer checks against recomputation."""
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
    return out


def _declared_score_findings(record, validation):
    spec = families.spec_for_record(record)
    try:
        expected_score = spec.score(record)
    except Exception:
        expected_score = None
    if validation.get("candidate_prediction_correct") is not expected_score:
        return [
            "validation.candidate_prediction_correct does not match the "
            f"recomputed candidate score {expected_score!r}"
        ]
    return []


def _declared_publishability_findings(record, validation, findings_so_far):
    expected_publishable, expected_reason = publishability(record, findings_so_far)
    out = []
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


def _validate_declared_status(record, findings_so_far):
    validation = record.get("validation")
    if not isinstance(validation, dict):
        return ["validation must be an object"]
    return (
        _declared_verdict_findings(validation, findings_so_far)
        + _declared_score_findings(record, validation)
        + _declared_publishability_findings(record, validation, findings_so_far)
    )


def reproduce(record, environ=None):
    """Re-run the oracle from the stored scenario and compare the measurement.

    Returns ``(status, detail)`` where status is one of ``reproduced``,
    ``mismatch``, ``unavailable``, or ``invalid``.  Malformed stored input is
    bounded as ``invalid`` instead of escaping as a validator traceback.
    """
    return _record_replay.reproduce(record, environ)
