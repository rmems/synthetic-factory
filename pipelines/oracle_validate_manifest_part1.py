"""Cohesive checks extracted from oracle_validate_manifest.py."""

class ManifestChecksPart1:
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
