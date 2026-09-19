"""Cohesive checks extracted from oracle_record_stages.py."""

class StageChecksPart6:
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
            self._reference_adapter_findings(stage, position, reference_adapter, findings)
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

    def _reference_adapter_findings(self, stage, position, reference_adapter, findings):
        """The stage's declared oracle id and version must match the adapter's."""
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
