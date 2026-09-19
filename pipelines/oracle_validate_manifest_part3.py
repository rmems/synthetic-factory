"""Cohesive checks extracted from oracle_validate_manifest.py."""

class ManifestChecksPart3:
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
