"""Cohesive checks extracted from oracle_validate_manifest.py."""

class ManifestChecksPart2:
    def _family_summaries(self, declared_families, parsed_records, layout, context):
        """Rebuild each family's declared summary from the captured records."""
        file_info, actual_families = layout
        by_family = self.api._group_records_by_family(parsed_records, file_info, actual_families)
        expected_summaries = {
            family: self.api._family_summary(
                family, by_family.get(family, []), context.bound(family)
            )
            for family in sorted(actual_families)
        }
        if declared_families != expected_summaries:
            context.report(
                "per-family counts, reasons, scores, or oracle summaries "
                "do not match the captured records"
            )

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

        self._family_summaries(
            declared_families, parsed_records, (file_info, actual_families), context
        )
        if context.header.module_digest != self.api.oracles.module_digest():
            context.report("module_digest does not match the current reference implementation")

        self.api._availability_block_errors(manifest, actual_families, context)
        self.api._manifest_note_errors(manifest, parsed_records, context)
        return context.errors
