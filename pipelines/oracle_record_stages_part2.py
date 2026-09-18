"""Cohesive checks extracted from oracle_record_stages.py."""

class StageChecksPart2:
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
        unbound = [
            runtime
            for runtime in requested
            if not isinstance(runtime, str) or runtime not in bound
        ]
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
