"""Cohesive checks extracted from oracle_validate_manifest_records.py."""

class ManifestRecordChecksPart3:
    def _summary(self, records, manifest_path, label, errors):
        scores = []
        prefix = f"{manifest_path}: {label}"
        for parsed in records:
            self._summary_score(parsed, prefix, errors, scores)
        return {
            "records": len(records),
            "candidate_scored": len(scores),
            "candidate_correct": sum(1 for score in scores if score),
        }

    def _summary_score(self, parsed, prefix, errors, scores):
        """Accumulate one record's candidate score, or report its bad shape."""
        validation = parsed.item.get("validation")
        if not isinstance(validation, dict):
            errors.append(f"{prefix} contains a record without validation")
            return
        score = validation.get("candidate_prediction_correct")
        if score is not None and not isinstance(score, bool):
            errors.append(f"{prefix} contains a non-boolean candidate score")
            return
        if score is not None:
            scores.append(score)

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
            self._record_probe_error(parsed, probe, context)

    def _record_probe_error(self, parsed, probe, context):
        """Bind one declared probe into the run-wide probe set."""
        if not (isinstance(probe, dict) and isinstance(probe.get("runtime"), str)):
            context.report(f"{parsed.where} has malformed runtime availability")
            return
        try:
            normalized = self.api.canon.normalize(probe)
        except (TypeError, ValueError, RecursionError) as exc:
            context.report(
                f"{parsed.where} has malformed runtime availability: {type(exc).__name__}"
            )
            return
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
