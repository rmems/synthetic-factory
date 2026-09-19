"""Cohesive checks extracted from oracle_record_stages.py."""

class StageChecksPart5:
    def _reference_adapters_for(self, reference_oracle):
        """The per-stage reference adapters behind one family oracle."""
        if isinstance(reference_oracle, self.api.oracles.ChainOracle):
            return [adapter for _name, adapter, _build in reference_oracle._steps]
        return [reference_oracle]

    def _stage_shape_findings(self, stage, position, findings):
        """Reject non-object stages and undeclared keys. Returns the declared kind."""
        if not isinstance(stage, dict):
            findings.append(f"oracle.stages[{position}] is not an object")
            return None
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
            return None
        return kind

    def _dispatch_stage_kind(self, stage, position, kind, evidence):
        """Bind one well-shaped stage to the authority it claims."""
        spec = evidence.spec
        requested_runtime = spec.runtimes[position] if position < len(spec.runtimes) else None
        reference_adapter = (
            evidence.reference_adapters[position]
            if position < len(evidence.reference_adapters)
            else None
        )
        if kind == "named-runtime":
            self.api._named_runtime_stage_findings(
                stage, position, requested_runtime, evidence.findings
            )
        elif kind == "reference":
            self.api._reference_stage_findings(stage, position, reference_adapter, evidence)
        else:
            evidence.findings.append(
                f"oracle.stages[{position}].implementation must be 'reference' or "
                f"'named-runtime', got {kind!r}"
            )

    def _stage_kind_findings(self, stages, evidence):
        """Check each stage against the authority it claims. Returns the kinds seen."""
        kinds = set()
        for position, stage in enumerate(stages):
            kind = self._stage_shape_findings(stage, position, evidence.findings)
            if kind is None:
                continue
            kinds.add(kind)
            self._dispatch_stage_kind(stage, position, kind, evidence)
        return kinds
