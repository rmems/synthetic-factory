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
