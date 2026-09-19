"""Cohesive checks extracted from oracle_record_envelope.py."""

class EnvelopeChecksPart2:
    def _provenance_findings(self, record, oracle, findings):
        """The provenance block must describe a simulated, oracle-grounded record."""
        provenance = record["provenance"]
        if not isinstance(provenance, dict):
            findings.append("provenance must be an object")
            return
        unknown = sorted(key for key in provenance if key not in self.api.PROVENANCE_ALLOWED_KEYS)
        if unknown:
            findings.append(
                "provenance carries unauthenticated sibling keys: " + ", ".join(unknown)
            )
        self._provenance_kind_findings(provenance.get("kind"), findings)
        self._provenance_field_findings(provenance, oracle, findings)

    def _provenance_field_findings(self, provenance, oracle, findings):
        if provenance.get("oracle_grounded") is not True:
            findings.append("provenance.oracle_grounded must be true")
        if provenance.get("claimed") != oracle.get("authority"):
            findings.append("provenance.claimed must match oracle.authority")
        if provenance.get("generator_authored") != list(self.api.GENERATOR_SECTIONS):
            findings.append("provenance.generator_authored does not match the generator sections")
        if provenance.get("oracle_authored") != ["result", "oracle.stages"]:
            findings.append("provenance.oracle_authored does not match the oracle-authored sections")

    def _provenance_kind_findings(self, kind, findings):
        if kind not in self.api.ALLOWED_PROVENANCE_KIND:
            findings.append(f"provenance.kind must be one of {sorted(self.api.ALLOWED_PROVENANCE_KIND)}")
        elif kind not in self.api.TRAINING_PROVENANCE_KIND:
            findings.append("provenance.kind must not be 'unknown' on a new record")
        elif kind != "simulated":
            findings.append(
                "provenance.kind must be 'simulated'; the sf-oracle protocol does "
                "not attest physical hardware execution"
            )

    def _envelope_membership(self, oracle, findings):
        missing = [key for key in self.api.ORACLE_KEYS if key not in oracle]
        if missing:
            findings.append(f"oracle is missing: {', '.join(missing)}")
            return False
        unknown = sorted(key for key in oracle if key not in self.api.ORACLE_ALLOWED_KEYS)
        if unknown:
            findings.append(
                "oracle carries unauthenticated sibling keys: " + ", ".join(unknown)
            )
        return True

    def _validate_oracle_side(self, record, require_named_runtime, expected_commit=None):
        findings = []
        oracle = record["oracle"]
        if not isinstance(oracle, dict):
            return ["oracle must be an object"]
        if not self._envelope_membership(oracle, findings):
            return findings
        self.api._oracle_shape_findings(oracle, findings, expected_commit)
        if oracle["implementation"] not in ("reference", "named-runtime", "mixed"):
            findings.append(f"unknown oracle.implementation: {oracle['implementation']!r}")
        else:
            self.api._oracle_implementation_findings(oracle, record["family"], findings)
        self.api._oracle_spec_findings(oracle, record["family"], require_named_runtime, findings)
        if not self.api._result_findings(record, oracle, findings):
            return findings
        self.api._provenance_findings(record, oracle, findings)
        return findings
