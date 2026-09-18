"""Cohesive checks extracted from oracle_validate_manifest.py."""

class ManifestChecksPart2:
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
