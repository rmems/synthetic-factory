"""Manifest record bindings and family summaries.

The caller supplies its live facade so callback and limit overrides remain visible.
"""

import sys
from dataclasses import dataclass, field

if __package__:
    from . import _assert_direct_sibling, _expose_package_sibling
    _assert_direct_sibling("oracle_validate_manifest_records")
else:
    getattr(sys.modules.get("pipelines"), "_join_package_sibling", lambda name: None)(
        "oracle_validate_manifest_records"
    )


@dataclass
class FamilyEvidence:
    """Cross-record observations accumulated for one family."""

    indexes: list = field(default_factory=list)
    implementations: list = field(default_factory=list)
    rejection_reasons: set = field(default_factory=set)


class ManifestRecordChecks:
    """Validate captured manifest data using the caller's live validation seams."""

    def __init__(self, api):
        self.api = api

    def _summary(self, records, manifest_path, label, errors):
        scores = []
        for parsed in records:
            validation = parsed.item.get("validation")
            if not isinstance(validation, dict):
                errors.append(f"{manifest_path}: {label} contains a record without validation")
                continue
            score = validation.get("candidate_prediction_correct")
            if score is not None and not isinstance(score, bool):
                errors.append(f"{manifest_path}: {label} contains a non-boolean candidate score")
                continue
            if score is not None:
                scores.append(score)
        return {
            "records": len(records),
            "candidate_scored": len(scores),
            "candidate_correct": sum(1 for score in scores if score),
        }


    def _record_index(self, parsed, context):
        """The proposal index encoded in a record id, or None when malformed."""
        identifier = parsed.item.get("id")
        match = (
            self.api.re.fullmatch(
                rf"{self.api.re.escape(context.family)}-r([0-9]{{1,8}})-([0-9]{{1,10}})",
                identifier,
            )
            if isinstance(identifier, str)
            else None
        )
        if match is None:
            context.report(f"{parsed.where} has no canonical family id")
            return None
        if context.header.round_ok and int(match.group(1)) != context.header.round_number:
            context.report(f"{parsed.where} id round does not match manifest")
        return int(match.group(2))


    def _record_oracle_binding_errors(self, parsed, oracle, index, context):
        """Bind one record's oracle block to the manifest, returning its implementation."""
        header = context.header
        implementation = oracle.get("implementation")
        if not isinstance(implementation, str):
            context.report(f"{parsed.where} oracle.implementation must be a string")
            implementation = None
        self._oracle_source_errors(parsed, oracle, context)
        if self.api._plain_int(header.master_seed) and index is not None:
            self.api._record_seed_errors(parsed, oracle, index, context)
        meta = parsed.item.get("meta")
        if not isinstance(meta, dict) or meta.get("round") != header.round_number:
            context.report(f"{parsed.where} meta.round disagrees")
        return implementation


    def _oracle_source_errors(self, parsed, oracle, context):
        header = context.header
        if oracle.get("commit") != header.commit:
            context.report(f"{parsed.where} oracle.commit disagrees")
        if oracle.get("dirty") is not header.dirty:
            context.report(f"{parsed.where} oracle.dirty disagrees")
        if oracle.get("module_digest") != header.module_digest:
            context.report(f"{parsed.where} oracle.module_digest disagrees")

    def _record_seed_errors(self, parsed, oracle, index, context):
        """Both the oracle and generator seeds must derive from the manifest seed."""
        expected_seed = self.api.seed_from_label(context.header.master_seed, f"{context.family}:{index}")
        if oracle.get("seed") != expected_seed:
            context.report(f"{parsed.where} oracle.seed does not derive from the manifest seed")
        generator = parsed.item.get("generator")
        if not isinstance(generator, dict) or generator.get("seed") != expected_seed:
            context.report(f"{parsed.where} generator.seed does not derive from the manifest seed")


    def _record_availability_errors(self, parsed, oracle, context):
        """Runtime availability probes must stay identical across the run."""
        availability = oracle.get("availability")
        if not isinstance(availability, dict):
            # The record envelope already rejects this shape; report rather than
            # skip so this cross-check never silently passes a malformed block.
            context.report(f"{parsed.where} has malformed runtime availability")
            return
        record_probes = availability.get("runtimes")
        if not isinstance(record_probes, list):
            context.report(f"{parsed.where} has malformed runtime availability")
            record_probes = []
        for probe in record_probes:
            if not (isinstance(probe, dict) and isinstance(probe.get("runtime"), str)):
                context.report(f"{parsed.where} has malformed runtime availability")
                continue
            try:
                normalized = self.api.canon.normalize(probe)
            except (TypeError, ValueError, RecursionError) as exc:
                context.report(
                    f"{parsed.where} has malformed runtime availability: {type(exc).__name__}"
                )
                continue
            previous = context.probe_values.setdefault(probe["runtime"], normalized)
            if previous != normalized:
                context.report("runtime availability changes within the run")


    def _collect_rejection_reasons(self, parsed, reasons, context):
        """Accumulate the declared rejection reasons for one rejected record."""
        validation = parsed.item.get("validation")
        declared = validation.get("reasons") if isinstance(validation, dict) else None
        if not isinstance(declared, list) or not all(
            isinstance(reason, str) for reason in declared
        ):
            context.report(f"{parsed.where} has malformed rejection reasons")
            return
        reasons.update(declared)


    def _indexes_are_complete(self, indexes, context):
        """Whether the captured ids cover each proposal index exactly once."""
        if not context.header.count_ok:
            return False
        return len(indexes) == context.header.count_per_family and all(
            index == expected for expected, index in enumerate(sorted(indexes))
        )


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


if __package__:
    _expose_package_sibling(__name__)
