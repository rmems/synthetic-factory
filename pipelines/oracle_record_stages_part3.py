"""Cohesive checks extracted from oracle_record_stages.py."""

class StageChecksPart3:
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
