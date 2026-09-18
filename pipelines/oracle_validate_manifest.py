"""Manifest header, layout, and availability validation.

The caller supplies its live facade so callback and limit overrides remain visible.
"""

import sys

if __package__:
    from . import _assert_direct_sibling, _expose_package_sibling
    _assert_direct_sibling("oracle_validate_manifest")
else:
    getattr(sys.modules.get("pipelines"), "_join_package_sibling", lambda name: None)(
        "oracle_validate_manifest"
    )


class ManifestChecks:
    """Validate captured manifest data using the caller's live validation seams."""

    def __init__(self, api):
        self.api = api

    def _read_manifest_header(self, manifest):
        """Lift the manifest scalars into one bundle."""
        return self.api._ManifestHeader(
            round_number=manifest.get("round"),
            master_seed=manifest.get("seed"),
            count_per_family=manifest.get("count_per_family"),
            commit=manifest.get("oracle_commit"),
            dirty=manifest.get("oracle_dirty"),
            module_digest=manifest.get("module_digest"),
        )


    def _header_field_errors(self, context):
        """Range- and type-check the manifest scalar fields."""
        header = context.header
        if not header.round_ok:
            context.report(f"round must be an integer in [1, {self.api.MAX_ROUND}]")
        if not self.api._plain_int(header.master_seed):
            context.report("seed must be an integer")
        elif not 0 <= header.master_seed <= self.api.MAX_SEED:
            context.report(f"seed must lie in [0, {self.api.MAX_SEED}] (a 64-bit integer)")
        if not header.count_ok:
            context.report(f"count_per_family must be an integer in [1, {self.api.MAX_RUN_RECORDS}]")
        self._header_identity_errors(context)

    def _header_identity_errors(self, context):
        header = context.header
        if not self.api.oracles.is_source_commit(header.commit):
            context.report(
                "oracle_commit must be a resolved lowercase 40- or 64-hex source commit"
            )
        elif self.api.oracles.resolve_source_commit(header.commit) != header.commit:
            context.report("oracle_commit does not resolve in the source repository")
        if header.dirty is not None and not isinstance(header.dirty, bool):
            context.report("oracle_dirty must be boolean or null")
        if not self.api.canon.is_digest(header.module_digest):
            context.report("module_digest must be a sha256 digest")


    def _declared_families_block(self, manifest, context):
        """Validate the declared families mapping and return it."""
        declared = manifest.get("families")
        if not isinstance(declared, dict):
            context.report("families must be an object")
            return {}
        if not declared:
            context.report("families must declare at least one family")
        elif context.header.count_ok and (
            context.header.count_per_family * len(declared) > self.api.MAX_RUN_RECORDS
        ):
            context.report(
                f"count_per_family across declared families exceeds {self.api.MAX_RUN_RECORDS} records"
            )
        return declared


    def _run_file_layout(self, snapshots, context):
        """Map each captured file to ``(family, verdict, round)``."""
        header = context.header
        file_info = {}
        actual_families = set()
        for snapshot in snapshots:
            match = self.api._RUN_FILE_RE.fullmatch(snapshot.relative)
            if match is None:
                context.report(f"manifest path is not a canonical run file: {snapshot.relative}")
                continue
            family = match.group("family")
            file_round = int(match.group("round"))
            file_info[snapshot.relative] = (family, match.group("verdict"), file_round)
            actual_families.add(family)
            if family not in self.api.families.SPECS:
                context.report(f"run contains unknown family {family!r}")
            if header.round_ok and file_round != header.round_number:
                context.report(
                    f"{snapshot.relative} round {file_round} "
                    f"does not match manifest round {header.round_number}"
                )
        return file_info, actual_families


    def _family_file_pairing_errors(self, file_info, actual_families, context):
        """Each family must carry exactly one accepted and one rejected file."""
        header = context.header
        if not header.round_ok:
            return
        for family in sorted(actual_families):
            expected_files = {
                f"{family}/accepted-r{header.round_number:02d}.jsonl",
                f"{family}/rejected-r{header.round_number:02d}.jsonl",
            }
            actual_files = {relative for relative, info in file_info.items() if info[0] == family}
            if actual_files != expected_files:
                context.report(
                    f"family {family!r} must have exactly one accepted "
                    "and one rejected file for the manifest round"
                )


    def _expected_runtime_set(self, actual_families):
        """Every runtime the captured families request."""
        return {
            runtime
            for family in actual_families
            if family in self.api.families.SPECS
            for runtime in self.api.families.spec_for(family).runtimes
        }


    def _availability_probe_errors(self, probes, context):
        """Each declared probe must match the one captured in the records."""
        for probe in probes:
            if not isinstance(probe, dict) or not isinstance(probe.get("runtime"), str):
                # The sibling runtime-name check already rejects these shapes;
                # report rather than skip so a malformed probe can never pass.
                context.report("availability declares a malformed runtime probe")
                continue
            runtime = probe["runtime"]
            expected_probe = context.probe_values.get(runtime)
            if not self._probe_matches(probe, expected_probe):
                context.report(
                    f"availability for runtime {runtime!r} does not match captured records"
                )


    def _probe_matches(self, probe, expected_probe):
        if expected_probe is None or probe != expected_probe:
            return False
        runtime = probe["runtime"]
        return (probe.get("binding_env") == self.api.oracles.env_key(runtime)
                and isinstance(probe.get("bound"), bool))

    def _availability_rollup_errors(self, availability, probes, runtime_names, context):
        """``all_bound`` and ``unbound`` must follow from the declared probes."""
        # A set keeps this linear: probe counts are untrusted and bounded only by
        # the manifest byte limit. Non-string runtimes can never match a string
        # name, so excluding them from the set changes no outcome.
        bound = self._bound_runtime_names(probes)
        unbound = self._unbound_runtime_names(runtime_names, bound)
        if availability.get("all_bound") is not (not unbound):
            context.report("oracle_availability.all_bound disagrees")
        if availability.get("unbound") != unbound:
            context.report("oracle_availability.unbound disagrees")


    def _bound_runtime_names(self, probes):
        return {
            probe.get("runtime") for probe in probes
            if isinstance(probe, dict) and probe.get("bound") is True
            and isinstance(probe.get("runtime"), str)
        }

    def _unbound_runtime_names(self, runtime_names, bound):
        if not all(isinstance(runtime, str) for runtime in runtime_names):
            return []
        return [runtime for runtime in runtime_names if runtime not in bound]

    def _availability_block_errors(self, manifest, actual_families, context):
        """Validate the manifest's oracle_availability block."""
        availability = manifest.get("oracle_availability")
        if not isinstance(availability, dict):
            context.report("oracle_availability must be an object")
            return
        # Exactly the fields availability_report() emits; an undeclared sibling
        # would be an unsupported provenance claim in canonical run metadata.
        unknown = sorted(set(availability) - {"protocol", "runtimes", "all_bound", "unbound"})
        if unknown:
            context.report(
                "oracle_availability carries unauthenticated sibling keys: " + ", ".join(unknown)
            )
        probes = availability.get("runtimes")
        if availability.get("protocol") != self.api.oracles.PROTOCOL or not isinstance(probes, list):
            context.report("oracle_availability is malformed")
            return
        runtime_names = [
            probe.get("runtime") if isinstance(probe, dict) else None for probe in probes
        ]
        self._runtime_name_errors(runtime_names, actual_families, context)
        self.api._availability_probe_errors(probes, context)
        self.api._availability_rollup_errors(availability, probes, runtime_names, context)


    def _runtime_name_errors(self, runtime_names, actual_families, context):
        runtime_names_valid = all(isinstance(runtime, str) for runtime in runtime_names)
        if not runtime_names_valid:
            context.report("oracle_availability runtime names must be strings")
        elif (
            len(runtime_names) != len(set(runtime_names))
            or set(runtime_names) != self.api._expected_runtime_set(actual_families)
        ):
            context.report("oracle_availability runtimes do not match families")

    def _manifest_metadata_errors(self, manifest, snapshots, parsed_records, run_dir):
        """Bind manifest metadata and summaries to the captured record snapshot."""
        context = self.api._MetadataContext(
            header=self.api._read_manifest_header(manifest),
            manifest_path=self.api.Path(run_dir) / "manifest.json",
            errors=[],
            probe_values={},
        )
        # The manifest is canonical run metadata that no other digest covers, so
        # its vocabulary is closed: an undeclared sibling would be an unsupported
        # provenance claim riding along with an otherwise valid run.
        unknown = sorted(set(manifest) - self.api.MANIFEST_ALLOWED_KEYS)
        if unknown:
            context.report("manifest carries unauthenticated sibling keys: " + ", ".join(unknown))
        self.api._header_field_errors(context)
        declared_families = self.api._declared_families_block(manifest, context)

        file_info, actual_families = self.api._run_file_layout(snapshots, context)
        if set(declared_families) != actual_families:
            context.report("families keys do not match captured family directories")
        self.api._family_file_pairing_errors(file_info, actual_families, context)

        by_family = self.api._group_records_by_family(parsed_records, file_info, actual_families)
        expected_summaries = {
            family: self.api._family_summary(family, by_family.get(family, []), context.bound(family))
            for family in sorted(actual_families)
        }
        if declared_families != expected_summaries:
            context.report(
                "per-family counts, reasons, scores, or oracle summaries "
                "do not match the captured records"
            )
        if context.header.module_digest != self.api.oracles.module_digest():
            context.report("module_digest does not match the current reference implementation")

        self.api._availability_block_errors(manifest, actual_families, context)
        self.api._manifest_note_errors(manifest, parsed_records, context)
        return context.errors


    def _manifest_note_errors(self, manifest, parsed_records, context):
        """The note is derived provenance, not free text: recompute it.

        ``build_manifest`` chooses between exactly two notes based on whether any
        captured record is publishable.  An unvalidated note could otherwise claim
        external attestation or publishability that no record carries.
        """
        any_publishable = any(
            isinstance(parsed.item.get("validation"), dict)
            and parsed.item["validation"].get("publishable") is True
            for parsed in parsed_records
        )
        expected = self.api.MANIFEST_NOTE_PUBLISHABLE if any_publishable else self.api.MANIFEST_NOTE_UNPUBLISHABLE
        if manifest.get("note") != expected:
            context.report("note does not match the publishability of the captured records")


if __package__:
    _expose_package_sibling(__name__)
