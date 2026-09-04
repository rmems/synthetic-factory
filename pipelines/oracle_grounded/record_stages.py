"""Stage-evidence validation: an authority claim must match the stages that ran.

Without these checks, relabelling ``implementation`` from ``reference`` to
``named-runtime`` would be enough to make a simulator's output look like a
measurement from the named runtime. The stages are the evidence: a
named-runtime stage carries the runtime's own version and commit, and a
reference stage carries the digest of the simulator source that ran.
"""

from dataclasses import dataclass

from . import families, oracles
from .record_envelope import STAGE_ALLOWED_KEYS

# A stage that is not even an object contributes no implementation kind; this
# sentinel keeps that distinct from a dict whose kind is absent (None).
_NOT_AN_OBJECT = object()


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
        return [adapter for _name, adapter, _build in reference_oracle.steps]
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


def _reference_adapter_identity_findings(stage, position, reference_adapter, findings):
    """The stage must name the canonical adapter that stands in for the runtime."""
    if reference_adapter is None:
        return
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


def _reference_stage_findings(stage, position, reference_adapter, evidence):
    """A reference stage must match the simulator source that actually ran."""
    findings = evidence.findings
    _reference_adapter_identity_findings(stage, position, reference_adapter, findings)
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


def _stage_findings(stage, position, evidence):
    """Check one stage against the authority it claims; returns its kind."""
    findings = evidence.findings
    if not isinstance(stage, dict):
        findings.append(f"oracle.stages[{position}] is not an object")
        return _NOT_AN_OBJECT
    unknown = sorted(key for key in stage if key not in STAGE_ALLOWED_KEYS)
    if unknown:
        findings.append(
            f"oracle.stages[{position}] carries unauthenticated sibling keys: "
            + ", ".join(unknown)
        )
    kind = stage.get("implementation")
    spec = evidence.spec
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
    return kind


def _stage_kind_findings(stages, evidence):
    """Check each stage against the authority it claims. Returns the kinds seen."""
    kinds = set()
    for position, stage in enumerate(stages):
        kind = _stage_findings(stage, position, evidence)
        if kind is not _NOT_AN_OBJECT:
            kinds.add(kind)
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
        _requested_runtime_finding(stage, position, requested, findings)


def _requested_runtime_finding(stage, position, requested, findings):
    """Each stage's requested runtime must restate the oracle-level list."""
    if not isinstance(requested, list) or position >= len(requested):
        return
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
    _probe_description_findings(probes, requested, evidence.findings)
    _probe_stage_agreement_findings(probes, stages, evidence.findings)


def _probe_description_findings(probes, requested, findings):
    """The probe list must restate the requested runtimes, nothing else."""
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


def _probe_stage_agreement_findings(probes, stages, findings):
    """A bound probe means a named-runtime stage; an unbound one, a reference stage."""
    if len(probes) != len(stages):
        return
    for position, (probe, stage) in enumerate(zip(probes, stages, strict=True)):
        if not isinstance(probe, dict) or not isinstance(stage, dict):
            continue
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
    _unbound_named_runtime_finding(oracle, availability, findings)


def _unbound_named_runtime_finding(oracle, availability, findings):
    """A named-runtime claim with unbound runtimes is a contradiction."""
    if oracle["implementation"] != "named-runtime":
        return
    unbound = availability.get("unbound") or []
    if unbound:
        findings.append(
            "oracle.implementation is 'named-runtime' but these runtimes were "
            f"not bound: {', '.join(str(name) for name in unbound)}"
        )


def _validate_stage_consistency(oracle, family):
    """A record cannot label itself with an authority its stages do not show."""
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
