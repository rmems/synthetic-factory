"""Cohesive checks extracted from oracle_validate_manifest_records.py."""

class ManifestRecordChecksPart1:
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

    def _indexes_are_complete(self, indexes, context):
        """Whether the captured ids cover each proposal index exactly once."""
        if not context.header.count_ok:
            return False
        return len(indexes) == context.header.count_per_family and all(
            index == expected for expected, index in enumerate(sorted(indexes))
        )
