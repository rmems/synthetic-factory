"""Cohesive checks extracted from oracle_validate_manifest_records.py."""

from dataclasses import dataclass, field

@dataclass
class FamilyEvidence:
    """Cross-record observations accumulated for one family."""

    indexes: list = field(default_factory=list)
    implementations: list = field(default_factory=list)
    rejection_reasons: set = field(default_factory=set)

class ManifestRecordChecksPart2:
    def _family_summary(self, family, records, context):
        """Validate one family's records and rebuild the summary it must declare."""
        header = context.header
        if header.count_ok and len(records) != header.count_per_family:
            context.report(
                f"family {family!r} has {len(records)} captured records, "
                f"expected {header.count_per_family}"
            )
        evidence = FamilyEvidence()
        by_verdict = self._records_by_verdict(records)
        accepted, rejected = by_verdict["accepted"], by_verdict["rejected"]
        for parsed in records:
            self._collect_record_evidence(parsed, context, evidence)
        if header.count_ok and not self.api._indexes_are_complete(evidence.indexes, context):
            context.report(f"family {family!r} ids do not cover each proposal index once")
        if len(set(evidence.implementations)) > 1:
            context.report(f"family {family!r} mixes oracle implementations")
        return {
            "proposed": header.count_per_family,
            "accepted": self.api._summary(
                accepted, context.manifest_path, f"families[{family!r}].accepted", context.errors
            ),
            "rejected": {
                "records": len(rejected),
                "reasons": sorted(evidence.rejection_reasons),
            },
            "oracle": self._oracle_summary(family, evidence),
        }

    def _records_by_verdict(self, records):
        by_verdict = {"accepted": [], "rejected": []}
        for parsed in records:
            if parsed.verdict == "accepted":
                by_verdict["accepted"].append(parsed)
            elif parsed.verdict == "rejected":
                by_verdict["rejected"].append(parsed)
        return by_verdict

    def _oracle_summary(self, family, evidence):
        spec = self.api.families.SPECS.get(family)
        return {
            "requested_runtime": list(spec.runtimes) if spec is not None else [],
            "implementation": evidence.implementations[0] if evidence.implementations else None,
        }

    def _collect_record_evidence(self, parsed, context, evidence):
        index = self.api._record_index(parsed, context)
        if index is not None:
            evidence.indexes.append(index)
        oracle = parsed.item.get("oracle")
        if not isinstance(oracle, dict):
            context.report(f"{parsed.where} has no oracle object")
            return
        implementation = self.api._record_oracle_binding_errors(parsed, oracle, index, context)
        if implementation is not None:
            evidence.implementations.append(implementation)
        self.api._record_availability_errors(parsed, oracle, context)
        if parsed.verdict == "rejected":
            self.api._collect_rejection_reasons(parsed, evidence.rejection_reasons, context)

    def _group_records_by_family(self, parsed_records, file_info, actual_families):
        """Bucket parsed records under the family directory that carried them."""
        by_family = {family: [] for family in actual_families}
        for parsed in parsed_records:
            info = file_info.get(parsed.relative)
            if info is not None:
                by_family.setdefault(info[0], []).append(parsed)
        return by_family
