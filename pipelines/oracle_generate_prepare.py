"""Validated run inputs: arguments, selection, binding, stamp, reservation."""

from pathlib import Path
import sys

if __package__:
    from . import _assert_direct_sibling, _expose_package_sibling

    _assert_direct_sibling("oracle_generate_prepare")
else:
    getattr(sys.modules.get("pipelines"), "_join_package_sibling", lambda name: None)(
        "oracle_generate_prepare"
    )


class GenerationPreparation:

    def __init__(self, api):
        self.api = api

    def _argument_errors(self, args):
        """Presence and range checks on the parsed arguments. Exit code, or None."""
        if not args.out_dir:
            print("oracle_generate: an output directory is required", file=sys.stderr)
            return 2
        if not 1 <= args.count <= self.api.MAX_COUNT:
            print(
                f"oracle_generate: --count must be in [1, {self.api.MAX_COUNT}]",
                file=sys.stderr,
            )
            return 2
        if not 1 <= args.round_number <= self.api.MAX_ROUND:
            print(
                f"oracle_generate: --round must be in [1, {self.api.MAX_ROUND}]",
                file=sys.stderr,
            )
            return 2
        if not 0 <= args.seed <= self.api.rng.MAX_SEED:
            print(
                f"oracle_generate: --seed must be in [0, {self.api.rng.MAX_SEED}] (a 64-bit integer)",
                file=sys.stderr,
            )
            return 2
        return None

    def _select_families(self, args):
        """The requested families, de-duplicated in order. (selected, exit code)."""
        default = tuple(self.api.native_profiles.PROFILES) if args.backend == 'rust' else self.api.families.FAMILY_NAMES
        selected = list(dict.fromkeys(args.family_names or default))
        if args.backend == 'rust' and any(name not in self.api.native_profiles.PROFILES for name in selected):
            print('oracle_generate: Rust backend supports only encoder and neuron families', file=sys.stderr)
            return None, 2
        unknown = [name for name in selected if name not in self.api.families.SPECS]
        if unknown:
            print(f"oracle_generate: unknown families: {', '.join(unknown)}", file=sys.stderr)
            return None, 2
        if args.count * len(selected) > self.api.MAX_RUN_RECORDS:
            print(
                "oracle_generate: requested run would contain "
                f"{args.count * len(selected)} records; maximum is {self.api.MAX_RUN_RECORDS}",
                file=sys.stderr,
            )
            return None, 2
        return selected, None

    def _stamp_contradicts_checkout(self, commit, _availability):
        """Whether an explicit --oracle-commit may not be trusted.

    Both reference and named-runtime measurements can be publishable, so an
    explicit stamp must name the checkout supplying the implementation.
    """
        checkout_commit, _checkout_dirty = self.api.oracles.resolve_commit()
        return (
            self.api.oracles.resolve_source_commit(commit) is not None
            and checkout_commit != commit
        )

    def _checkout_stamp(self, dirty):
        """Commit (and an unpinned dirty flag) resolved from the working tree."""
        commit, resolved_dirty = self.api.oracles.resolve_commit()
        return commit, resolved_dirty if dirty is None else dirty

    def _explicit_stamp(self, args, availability):
        """(commit, dirty, exit code) for an explicit --oracle-commit."""
        commit, dirty = args.oracle_commit, args.oracle_dirty
        if self.api._stamp_contradicts_checkout(commit, availability):
            checkout_commit, _checkout_dirty = self.api.oracles.resolve_commit()
            print(
                f"oracle_generate: --oracle-commit {commit!r} does not match the "
                f"checked-out HEAD ({checkout_commit}); oracle measurements can "
                "produce publishable output, so the stamped commit must name the "
                "checkout that supplied the implementation sources",
                file=sys.stderr,
            )
            return None, None, 2
        if dirty is not None:
            return commit, dirty, None
        # An explicit commit stamp must not leave the dirty flag
        # unresolved: a bound named runtime can make this run's records
        # publishable, and null dirty state is not resolved provenance.
        _checkout_commit, checkout_dirty = self.api.oracles.resolve_commit()
        if checkout_dirty is not None:
            return commit, checkout_dirty, None
        if any(probe["bound"] for probe in availability["runtimes"]):
            print(
                "oracle_generate: could not resolve the working tree's dirty "
                "state; a bound named runtime can produce publishable output, "
                "so pass --oracle-dirty or --no-oracle-dirty explicitly",
                file=sys.stderr,
            )
            return None, None, 3
        return commit, dirty, None

    def _resolve_stamp(self, args, availability):
        """Resolve the oracle commit and dirty flag. (commit, dirty, exit code)."""
        if args.oracle_commit is None:
            commit, dirty = self.api._checkout_stamp(args.oracle_dirty)
        else:
            commit, dirty, error = self.api._explicit_stamp(args, availability)
            if error is not None:
                return None, None, error
        if commit == "unknown":
            print(
                "oracle_generate: could not resolve the oracle commit; pass "
                "--oracle-commit to stamp it explicitly",
                file=sys.stderr,
            )
            return None, None, 3
        resolved_commit = self.api.oracles.resolve_source_commit(commit)
        if resolved_commit is None:
            print(
                "oracle_generate: --oracle-commit must resolve to an existing lowercase "
                "40- or 64-hex commit in this source repository",
                file=sys.stderr,
            )
            return None, None, 2
        return resolved_commit, dirty, None

    def _requested_runtimes(self, selected):
        """Every runtime the selected families request, in first-seen order."""
        return tuple(
            dict.fromkeys(
                runtime for family in selected for runtime in self.api.families.spec_for(family).runtimes
            )
        )

    def _bind_runtimes(self, args, selected):
        """Runtime environ and availability for the selected families. (availability, exit)."""
        args.runtime_environ = {}
        if args.backend == 'rust':
            try:
                args.runtime_environ = self.api.native_runtime.runtime_environ(args.oracle_rust_bin)
            except self.api.oracles.OracleError as exc:
                print(f'oracle_generate: {exc}', file=sys.stderr)
                return None, 3
        availability = self.api.oracles.availability_report(self.api._requested_runtimes(selected), args.runtime_environ)
        if args.require_runtime and not availability["all_bound"]:
            print(
                "oracle_generate: --require-runtime was passed but these oracles are "
                f"not bound: {', '.join(availability['unbound'])}",
                file=sys.stderr,
            )
            return None, 3
        return availability, None

    def _reserve_destination(self, args):
        """The fail-closed destination reservation. ((out_dir, lock_fd, parent_fd), exit)."""
        out_dir = Path(args.out_dir)
        raw_error = self.api._raw_destination_error(out_dir)
        if raw_error is not None:
            print(f"oracle_generate: {raw_error}", file=sys.stderr)
            return None, 2
        try:
            lock_descriptor, parent_fd = self.api.reserve_run(out_dir)
        except OSError as exc:
            print(f"oracle_generate: {exc}", file=sys.stderr)
            return None, 2
        return (out_dir, lock_descriptor, parent_fd), None

    def _prepared_inputs(self, args):
        """(PreparedRun, exit code): validated inputs but argument shape."""
        selected, error = self.api._select_families(args)
        if error is not None:
            return None, error
        availability, error = self.api._bind_runtimes(args, selected)
        if error is not None:
            return None, error
        commit, dirty, error = self.api._resolve_stamp(args, availability)
        if error is not None:
            return None, error
        reservation, error = self.api._reserve_destination(args)
        if error is not None:
            return None, error
        out_dir, lock_descriptor, parent_fd = reservation
        return self.api.PreparedRun(
            selected, availability, commit, dirty, out_dir, lock_descriptor, parent_fd
        ), None

    def _prepare_run(self, args):
        """(PreparedRun, exit code): the validated transaction inputs."""
        error = self.api._argument_errors(args)
        prepared = None
        if error is None:
            prepared, error = self._prepared_inputs(args)
        return (prepared, None) if error is None else (None, error)


if __package__:
    _expose_package_sibling(__name__)
