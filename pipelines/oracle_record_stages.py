"""Ordered validation of oracle stages and declared runtime availability."""

import sys

if __package__:
    from . import _assert_direct_sibling, _expose_package_sibling
    _assert_direct_sibling("oracle_record_stages")
else:
    getattr(sys.modules.get("pipelines"), "_join_package_sibling", lambda name: None)(
        "oracle_record_stages"
    )


class StageChecks:
    """Compare stage evidence through the record facade's live validation seams."""

    def __init__(self, api):
        self.api = api

    def _reference_adapters_for(self, reference_oracle):
        """The per-stage reference adapters behind one family oracle."""
        if isinstance(reference_oracle, self.api.oracles.ChainOracle):
            return [adapter for _name, adapter, _build in reference_oracle._steps]
        return [reference_oracle]

    def _named_runtime_stage_findings(self, stage, position, requested_runtime, findings):
        """A stage claiming a named runtime must carry that runtime's own evidence."""
        for field_name in ("version", "runtime_commit"):
            value = stage.get(field_name)
            if not isinstance(value, str) or not value.strip():
                findings.append(
                    f"oracle.stages[{position}] claims a named runtime but has no {field_name}"
                )
        if not self.api.oracles.is_runtime_commit(stage.get("runtime_commit")):
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

    def _reference_stage_findings(self, stage, position, reference_adapter, evidence):
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
        if stage.get("module_digest") != self.api.oracles.module_digest():
            findings.append(
                f"oracle.stages[{position}] module_digest does not match the "
                "current reference implementation"
            )

    def _stage_kind_findings(self, stages, evidence):
        """Check each stage against the authority it claims. Returns the kinds seen."""
        findings = evidence.findings
        spec = evidence.spec
        kinds = set()
        for position, stage in enumerate(stages):
            if not isinstance(stage, dict):
                findings.append(f"oracle.stages[{position}] is not an object")
                continue
            unknown = sorted(key for key in stage if key not in self.api.STAGE_ALLOWED_KEYS)
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
                self.api._named_runtime_stage_findings(stage, position, requested_runtime, findings)
            elif kind == "reference":
                self.api._reference_stage_findings(stage, position, reference_adapter, evidence)
            else:
                findings.append(
                    f"oracle.stages[{position}].implementation must be 'reference' or "
                    f"'named-runtime', got {kind!r}"
                )
        return kinds

    def _expected_stage_names(self, family):
        """The stage names one family's oracle path must produce, in order."""
        if family == self.api.families.CREDIT_FAMILY:
            return [f"{family}:critic", f"{family}:plasticity"]
        return [family]

    def _stage_alignment_findings(self, stages, evidence):
        """Stage names and per-stage requested runtimes must follow the family path."""
        findings = evidence.findings
        expected_stage_names = self.api._expected_stage_names(evidence.family)
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
            self._stage_runtime_alignment(stage, position, requested, findings)

    def _stage_runtime_alignment(self, stage, position, requested, findings):
        if not isinstance(requested, list) or position >= len(requested):
            return
        if stage.get("requested_runtime") != requested[position]:
            findings.append(
                f"oracle.stages[{position}].requested_runtime does not match "
                "oracle.requested_runtime"
            )

    def _declared_kind_findings(self, kinds, evidence):
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

    def _oracle_identity_findings(self, stages, evidence):
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

    def _probe_alignment_findings(self, probes, requested, stages, evidence):
        """The declared probes must describe the requested runtimes and the stages."""
        findings = evidence.findings
        expected_probes = [
            {
                "runtime": runtime,
                "binding_env": self.api.oracles.env_key(runtime),
                "bound": probe.get("bound") if isinstance(probe, dict) else None,
            }
            for runtime, probe in zip(requested, probes)
        ]
        if len(probes) != len(requested) or probes != expected_probes:
            findings.append(
                "oracle.availability.runtimes must exactly describe the requested runtimes"
            )
        self._stage_binding_findings(probes, stages, findings)

    def _stage_binding_findings(self, probes, stages, findings):
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

    def _availability_rollup_findings(self, availability, probes, requested, findings):
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

    def _availability_findings(self, stages, evidence):
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
            self.api._probe_alignment_findings(probes, requested, stages, evidence)
            self.api._availability_rollup_findings(availability, probes, requested, findings)
        if oracle["implementation"] == "named-runtime":
            unbound = availability.get("unbound") or []
            if unbound:
                findings.append(
                    "oracle.implementation is 'named-runtime' but these runtimes were "
                    f"not bound: {', '.join(str(name) for name in unbound)}"
                )

    def _validate_stage_consistency(self, oracle, family):
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
        spec = self.api.families.spec_for(family)
        reference_oracle = spec.oracle({})
        evidence = self.api._StageEvidence(
            oracle=oracle,
            family=family,
            spec=spec,
            reference_oracle=reference_oracle,
            reference_adapters=self.api._reference_adapters_for(reference_oracle),
            findings=findings,
        )
        kinds = self.api._stage_kind_findings(stages, evidence)
        self.api._stage_alignment_findings(stages, evidence)
        self.api._declared_kind_findings(kinds, evidence)
        self.api._oracle_identity_findings(stages, evidence)
        self.api._availability_findings(stages, evidence)
        return findings


if __package__:
    _expose_package_sibling(__name__)
