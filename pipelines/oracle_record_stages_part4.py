"""Cohesive checks extracted from oracle_record_stages.py."""

class StageChecksPart4:
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

    def _bound_probe_names(self, probes):
        """The runtimes whose declared probe bound successfully."""
        # A set keeps this linear on untrusted probe counts; non-string runtimes
        # can never match a string name, so excluding them changes no outcome.
        return {
            probe.get("runtime")
            for probe in probes
            if isinstance(probe, dict)
            and probe.get("bound") is True
            and isinstance(probe.get("runtime"), str)
        }

    def _availability_rollup_findings(self, availability, probes, requested, findings):
        """all_bound and unbound must be derived from the declared probes."""
        bound = self._bound_probe_names(probes)
        unbound = [
            runtime
            for runtime in requested
            if not isinstance(runtime, str) or runtime not in bound
        ]
        if availability.get("all_bound") is not (not unbound):
            findings.append("oracle.availability.all_bound is not derived from runtimes")
        if availability.get("unbound") != unbound:
            findings.append("oracle.availability.unbound is not derived from runtimes")

    def _named_runtime_unbound_findings(self, oracle, availability, findings):
        """A named-runtime record may not leave requested runtimes unbound."""
        if oracle["implementation"] != "named-runtime":
            return
        unbound = availability.get("unbound") or []
        if unbound:
            findings.append(
                "oracle.implementation is 'named-runtime' but these runtimes were "
                f"not bound: {', '.join(str(name) for name in unbound)}"
            )

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
            self._probe_alignment_findings(probes, requested, stages, evidence)
            self._availability_rollup_findings(availability, probes, requested, findings)
        self._named_runtime_unbound_findings(oracle, availability, findings)
