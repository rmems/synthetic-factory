"""Record parsing, validation, identity accounting, and reference replay."""

import sys

if __package__:
    from . import _assert_direct_sibling, _expose_package_sibling
    _assert_direct_sibling("oracle_validate_records")
else:
    getattr(sys.modules.get("pipelines"), "_join_package_sibling", lambda name: None)(
        "oracle_validate_records"
    )


class RecordChecks:
    """Process captured records while preserving live facade validation seams."""

    def __init__(self, api):
        self.api = api

    def _verdict_for_file(self, name):
        """The verdict a run file name reserves, or None."""
        return next(
            (verdict for verdict in ("accepted", "rejected") if name.startswith(f"{verdict}-")),
            None,
        )

    def _parse_record_line(self, line, where, scope):
        """Parse one JSONL line into a record object, or None with a finding."""
        try:
            text = line.decode("utf-8") if isinstance(line, bytes) else line
            item = self.api.strict_json_loads(text)
        except (ValueError, RecursionError) as exc:
            scope.totals["parse_failures"] += 1
            scope.report(where, f"JSON parse error: {exc}")
            return None
        if not isinstance(item, dict):
            scope.totals["parse_failures"] += 1
            scope.report(where, "record is not a JSON object")
            return None
        return item

    def _duplicate_id_finding(self, item, where, seen_ids):
        """Claim this record's id, reporting the coordinate that claimed it first."""
        identifier = item.get("id")
        if not isinstance(identifier, str):
            return None
        if identifier in seen_ids:
            return f"duplicate record id {identifier!r}; first seen at {seen_ids[identifier]}"
        seen_ids[identifier] = where
        return None

    def _classify_layers(self, item, require_runtime, expected_commit=None):
        """Classify one record, containing any internal failure as an envelope finding."""
        try:
            return self.api.record.classify(
                item,
                require_named_runtime=require_runtime,
                expected_commit=expected_commit,
            )
        except Exception as exc:  # final boundary around one untrusted record
            return {
                "envelope": [
                    f"record validation raised an internal exception: {type(exc).__name__}"
                ],
                "family": [],
                "status": [],
            }

    def _fatal_findings(self, item, layers, identity_finding, scope):
        """The findings that make one record invalid, in emission order."""
        fatal = layers["envelope"] + layers["status"]
        if identity_finding:
            fatal.append(identity_finding)
        family = item.get("family")
        if family != scope.path.parent.name:
            fatal.append(
                f"record family {family!r} does not match directory {scope.path.parent.name!r}"
            )
        declared_verdict = (
            item.get("validation", {}).get("status")
            if isinstance(item.get("validation"), dict)
            else None
        )
        expected_verdict = self.api._verdict_for_file(scope.path.name)
        if expected_verdict and declared_verdict != expected_verdict:
            fatal.append(
                f"record declares verdict {declared_verdict!r} but is filed in "
                f"{scope.path.name!r}, which is reserved for {expected_verdict!r} records"
            )
        return fatal

    def _count_valid_record(self, item, layers, totals):
        """Roll one valid record into the per-run counters."""
        if layers["family"]:
            totals["rejected"] += 1
        else:
            totals["accepted"] += 1
        implementation = item["oracle"]["implementation"]
        if implementation == "reference":
            totals["reference_oracle"] += 1
        elif implementation == "named-runtime":
            totals["named_runtime"] += 1
        else:
            totals["mixed_oracle"] += 1
        if item["validation"].get("publishable"):
            totals["publishable"] += 1

    def _reproduce_record(self, item, where, scope):
        """Re-derive one record's oracle result and count the outcome."""
        try:
            if __package__:
                from .oracle_grounded import native_gate
            else:
                from oracle_grounded import native_gate
            environment = native_gate.replay_environ() if native_gate.is_native_record(item) else None
            if item["oracle"]["implementation"] == "reference":
                environment = {}
            if native_gate.is_native_record(item) and environment is None:
                status, detail = "unavailable", "native replay requires an explicit oracle Rust binary"
            else:
                status, detail = self.api.record.reproduce(item, environ=environment)
        except Exception as exc:  # defensive boundary around stored data
            status = "invalid"
            detail = f"reproduction raised {type(exc).__name__}"
        scope.totals[f"reproduce_{status}"] += 1
        if status != "reproduced":
            # The record is already tallied as accepted or rejected by
            # _count_valid_record; charging "invalid" as well would make
            # accepted + rejected + invalid exceed records in the report.  The
            # failure still fails the run through the reported finding, and the
            # outcome stays visible in the report's reproduce_* buckets.
            scope.report(where, f"requested oracle reproduction was {status}: {detail}")

    def _validate_one_record(self, item, where, scope):
        """Apply every per-record rule, updating the file's totals and findings."""
        identity_finding = self.api._duplicate_id_finding(item, where, scope.seen_ids)
        if scope.selected and item.get("family") not in scope.selected:
            self._count_skipped_record(where, identity_finding, scope)
            return
        scope.totals["records"] += 1
        layers = self.api._classify_layers(item, scope.require_runtime, scope.expected_commit)
        fatal = self.api._fatal_findings(item, layers, identity_finding, scope)
        if fatal:
            self._report_invalid_record(where, fatal, scope)
            return
        self.api._count_valid_record(item, layers, scope.totals)
        if scope.reproduce:
            self.api._reproduce_record(item, where, scope)

    def _count_skipped_record(self, where, identity_finding, scope):
        scope.totals["skipped"] += 1
        if identity_finding:
            scope.totals["invalid"] += 1
            scope.report(where, identity_finding)

    def _report_invalid_record(self, where, findings, scope):
        scope.totals["invalid"] += 1
        for finding in findings:
            scope.report(where, finding)

    def validate_file(self, snapshot, scope):
        expected_verdict = self.api._verdict_for_file(scope.path.name)
        parsed_records = []
        for number, line in enumerate(self.api.io.BytesIO(snapshot.body), start=1):
            if not line.strip():
                continue
            where = f"{scope.path}:{number}"
            item = self.api._parse_record_line(line, where, scope)
            if item is None:
                continue
            parsed_records.append(
                self.api.ParsedRecord(
                    item=item,
                    where=where,
                    relative=scope.relative,
                    verdict=expected_verdict,
                )
            )
            self.api._validate_one_record(item, where, scope)
        return scope.totals, scope.errors, parsed_records


if __package__:
    _expose_package_sibling(__name__)
