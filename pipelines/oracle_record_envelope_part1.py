"""Cohesive checks extracted from oracle_record_envelope.py."""

def _nonempty_object(value):
    return isinstance(value, dict) and bool(value)

class EnvelopeChecksPart1:
    def _oracle_shape_findings(self, oracle, findings, expected_commit=None):
        """Shape and identity checks on the oracle envelope itself.

        ``expected_commit`` is a commit the caller has already resolved against
        the repository (a run manifest's oracle commit). When provided, a record
        stamped with a different commit is rejected by string comparison instead
        of launching its own repository resolution, so a run holding thousands of
        distinct forged commits cannot turn validation into repeated git calls.
        """
        if not _nonempty_object(oracle["configuration"]):
            findings.append("oracle.configuration must be a non-empty object")
        if not _nonempty_object(oracle["units"]):
            findings.append("oracle.units must be a non-empty object")
        if not isinstance(oracle["stages"], list) or not oracle["stages"]:
            findings.append("oracle.stages must list at least one executed stage")
        if oracle["repo"] != self.api.oracles.REPO_SLUG:
            findings.append(f"oracle must declare repo {self.api.oracles.REPO_SLUG!r}")
        self._source_commit_findings(oracle["commit"], expected_commit, findings)
        if not self.api.canon.is_digest(oracle.get("module_digest", "")):
            findings.append("oracle.module_digest must be a sha256 digest")

    def _source_commit_findings(self, commit, expected_commit, findings):
        if not self.api.oracles.is_source_commit(commit):
            findings.append("oracle.commit must be a resolved lowercase 40- or 64-hex source commit")
        elif expected_commit is not None and commit != expected_commit:
            findings.append(
                "oracle.commit does not match the run manifest's resolved oracle commit"
            )
        elif self.api.oracles.resolve_source_commit(commit) != commit:
            findings.append(
                "oracle.commit does not resolve to that commit object in the source repository"
            )

    def _oracle_implementation_findings(self, oracle, family, findings):
        """Checks that apply once the declared implementation is a known kind."""
        findings.extend(self.api._validate_stage_consistency(oracle, family))
        if oracle.get("module_digest") != self.api.oracles.module_digest():
            findings.append(
                "oracle.module_digest does not match the current reference implementation"
            )
        if oracle["implementation"] in ("reference", "mixed"):
            if oracle.get("module") != self.api.oracles.MODULE_PATH:
                findings.append(f"reference oracle.module must be {self.api.oracles.MODULE_PATH!r}")
        expected_authority = {
            "reference": "reference-simulator",
            "named-runtime": "measured-runtime",
            "mixed": "mixed-reference-and-runtime",
        }[oracle["implementation"]]
        if oracle.get("authority") != expected_authority:
            findings.append(
                f"oracle.authority must be {expected_authority!r} for "
                f"implementation {oracle['implementation']!r}"
            )

    def _oracle_spec_findings(self, oracle, family, require_named_runtime, findings):
        """The oracle envelope must match the family's declared contract."""
        spec = self.api.families.spec_for(family)
        if oracle.get("type") != spec.oracle_type:
            findings.append(
                f"oracle.type {oracle.get('type')!r} does not match family oracle type "
                f"{spec.oracle_type!r}"
            )
        if oracle.get("requested_runtime") != list(spec.runtimes):
            findings.append(
                f"oracle.requested_runtime does not match the runtimes specified for {family!r}"
            )
        if oracle.get("units") != spec.units:
            findings.append("oracle.units does not match the family units contract")
        if require_named_runtime and oracle["implementation"] != "named-runtime":
            findings.append(
                "oracle.implementation is not 'named-runtime' and a named runtime was required"
            )

    def _result_findings(self, record, oracle, findings):
        """Validate the result block. False when curation must stop here."""
        result = record["result"]
        if not _nonempty_object(result):
            findings.append("result must be a non-empty object (curation fails closed)")
            return False
        measured = result.get("measured")
        if not _nonempty_object(measured):
            findings.append("result.measured must be a non-empty object")
        if result.get("produced_by") != oracle["id"]:
            findings.append(
                f"result.produced_by {result.get('produced_by')!r} does not match "
                f"oracle.id {oracle['id']!r}"
            )
        result_units = result.get("units")
        if not _nonempty_object(result_units):
            findings.append("result.units must be a non-empty object")
        elif result_units != oracle["units"]:
            findings.append("result.units does not exactly match oracle.units")
        if record["result_hash"] != self.api.canon.digest(result):
            findings.append("result_hash does not cover the stored result")
        return True
