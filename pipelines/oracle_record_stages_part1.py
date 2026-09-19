"""Cohesive checks extracted from oracle_record_stages.py."""

class StageChecksPart1:
    def _expected_stage_names(self, family):
        """The stage names one family's oracle path must produce, in order."""
        if family == self.api.families.CREDIT_FAMILY:
            return [f"{family}:critic", f"{family}:plasticity"]
        return [family]

    def _stage_alignment_findings(self, stages, evidence):
        """Stage names and per-stage requested runtimes must follow the family path."""
        findings = evidence.findings
        expected_stage_names = self._expected_stage_names(evidence.family)
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
