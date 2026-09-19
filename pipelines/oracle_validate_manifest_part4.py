"""Cohesive checks extracted from oracle_validate_manifest.py."""

class ManifestChecksPart4:
    def _expected_runtime_set(self, actual_families):
        """Every runtime the captured families request."""
        return {
            runtime
            for family in actual_families
            if family in self.api.families.SPECS
            for runtime in self.api.families.spec_for(family).runtimes
        }

    def _probe_matches(self, probe, expected_probe):
        if expected_probe is None or probe != expected_probe:
            return False
        runtime = probe["runtime"]
        return (probe.get("binding_env") == self.api.oracles.env_key(runtime)
                and isinstance(probe.get("bound"), bool))

    def _availability_probe_errors(self, probes, context):
        """Each declared probe must match the one captured in the records."""
        for probe in probes:
            runtime = self._declared_probe_runtime(probe, context)
            if runtime is None:
                continue
            if not self._probe_matches(probe, context.probe_values.get(runtime)):
                context.report(
                    f"availability for runtime {runtime!r} does not match captured records"
                )

    def _declared_probe_runtime(self, probe, context):
        if not isinstance(probe, dict) or not isinstance(probe.get("runtime"), str):
            # The sibling runtime-name check already rejects these shapes;
            # report rather than skip so a malformed probe can never pass.
            context.report("availability declares a malformed runtime probe")
            return None
        return probe["runtime"]

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
