"""Oracle-side validation: the oracle, result, and provenance blocks.

These checks bind a record's authority claims to verifiable facts: the commit
and module digest must identify real code, the result must name the oracle the
record declares, and the provenance block must describe a simulated,
oracle-grounded record in the closed vocabulary of ``record_envelope``.
"""

from . import canon, families, oracles
from .record_envelope import (
    ALLOWED_PROVENANCE_KIND,
    GENERATOR_SECTIONS,
    ORACLE_ALLOWED_KEYS,
    ORACLE_KEYS,
    PROVENANCE_ALLOWED_KEYS,
    TRAINING_PROVENANCE_KIND,
)
from .record_stages import _validate_stage_consistency


def _oracle_container_findings(oracle, findings):
    """The blocks the oracle envelope must carry, before any deeper check."""
    if not isinstance(oracle["configuration"], dict) or not oracle["configuration"]:
        findings.append("oracle.configuration must be a non-empty object")
    if not isinstance(oracle["units"], dict) or not oracle["units"]:
        findings.append("oracle.units must be a non-empty object")
    if not isinstance(oracle["stages"], list) or not oracle["stages"]:
        findings.append("oracle.stages must list at least one executed stage")
    if oracle["repo"] != oracles.REPO_SLUG:
        findings.append(f"oracle must declare repo {oracles.REPO_SLUG!r}")


def _oracle_commit_findings(oracle, findings, expected_commit):
    """The stamped commit must resolve, or match the run's resolved commit."""
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


def _oracle_shape_findings(oracle, findings, expected_commit=None):
    """Shape and identity checks on the oracle envelope itself.

    ``expected_commit`` is a commit the caller has already resolved against
    the repository (a run manifest's oracle commit). When provided, a record
    stamped with a different commit is rejected by string comparison instead
    of launching its own repository resolution, so a run holding thousands of
    distinct forged commits cannot turn validation into repeated git calls.
    """
    _oracle_container_findings(oracle, findings)
    _oracle_commit_findings(oracle, findings, expected_commit)
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


def _result_units_findings(result, oracle, findings):
    """result.units must exist and restate oracle.units exactly."""
    result_units = result.get("units")
    if not isinstance(result_units, dict) or not result_units:
        findings.append("result.units must be a non-empty object")
    elif result_units != oracle["units"]:
        findings.append("result.units does not exactly match oracle.units")


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
    _result_units_findings(result, oracle, findings)
    if record["result_hash"] != canon.digest(result):
        findings.append("result_hash does not cover the stored result")
    return True


def _provenance_kind_findings(provenance, findings):
    """provenance.kind must be 'simulated' in the closed provenance vocabulary."""
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
    _provenance_kind_findings(provenance, findings)
    grounded = provenance.get("oracle_grounded")
    if not (isinstance(grounded, bool) and grounded):
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
