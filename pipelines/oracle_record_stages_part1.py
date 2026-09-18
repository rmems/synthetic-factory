"""Cohesive checks extracted from oracle_record_stages.py."""

class StageChecksPart1:
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
            if not isinstance(kind, str):
                findings.append(
                    f"oracle.stages[{position}].implementation must be a string, "
                    f"got {type(kind).__name__}"
                )
                continue
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
