"""Run-level validation driver and CLI for the oracle run validator."""

import sys

if __package__:
    from . import _assert_direct_sibling, _expose_package_sibling
    _assert_direct_sibling("oracle_validate_run")
else:
    getattr(sys.modules.get("pipelines"), "_join_package_sibling", lambda name: None)(
        "oracle_validate_run"
    )


_PATH_ARGUMENTS = {
    "run_dir": "run_dir",
    "oracle_rust_bin": "--oracle-rust-bin",
}


class RunChecks:
    """Drive a whole-run validation pass through live facade seams."""

    def __init__(self, api):
        self.api = api

    def _argument_parser(self):
        parser = self.api.argparse.ArgumentParser(
            add_help=True, description=self.api.__doc__
        )
        parser.add_argument("run_dir", nargs="?")
        parser.add_argument("--family", action="append", dest="family_names")
        parser.add_argument(
            "--oracle-rust-bin",
            help="prebuilt native oracle executable; implies replay",
        )
        parser.add_argument("--require-runtime", action="store_true")
        parser.add_argument("--reproduce", action="store_true")
        parser.add_argument("--max-findings", type=int, default=50)
        return parser

    def parse_args(self, argv):
        return self._argument_parser().parse_args(argv)

    def validate_run(self, context):
        if __package__:
            from .oracle_grounded.native_gate import runtime_gate
        else:
            from oracle_grounded.native_gate import runtime_gate
        effective = self.api.replace(
            context,
            reproduce=context.reproduce or context.oracle_rust_bin is not None,
        )
        with runtime_gate(context.oracle_rust_bin):
            return self.api.validate_run_snapshot(
                context.run_dir,
                self.api.authenticate_manifest(context.run_dir),
                options=effective,
            )

    def _snapshot_expected_commit(self, manifest):
        # Resolve the manifest's oracle commit once; per-record validation then
        # binds each record to it by string comparison rather than resolving
        # every distinct stamped commit against the repository. The binding is
        # kept even when the manifest commit is invalid or missing -- an empty
        # sentinel then mismatches every record -- so a malformed run cannot
        # regain per-record repository lookups by breaking its own manifest.
        expected_commit = None
        if isinstance(manifest, dict):
            manifest_commit = manifest.get("oracle_commit")
            if isinstance(manifest_commit, str) and manifest_commit:
                expected_commit = manifest_commit
                if self.api.oracles.is_source_commit(manifest_commit):
                    # One resolution for the whole run; a definitive miss is
                    # negatively cached, so matching records add no lookups.
                    self.api.oracles.resolve_source_commit(manifest_commit)
            else:
                expected_commit = ""
        return expected_commit

    def _snapshot_metadata_errors(self, run_dir, manifest, snapshots, parsed_records):
        metadata_errors = []
        if isinstance(manifest, dict):
            try:
                metadata_errors = self.api._manifest_metadata_errors(
                    manifest, snapshots, parsed_records, run_dir
                )
            except Exception as exc:  # final boundary around untrusted manifest data
                metadata_errors = [
                    f"{self.api.Path(run_dir) / self.api.MANIFEST_FILENAME}: manifest "
                    f"metadata validation raised an internal exception: {type(exc).__name__}"
                ]
        return metadata_errors

    def validate_run_snapshot(self, run_dir, authentication, *, options=None):
        """Validate the same authenticated bytes retained by a source consumer."""
        manifest, snapshots, manifest_errors = authentication
        context = options or self.api.ValidationContext()
        totals = self.api.Counter()
        errors = []
        by_family = self.api.Counter()
        errors.extend(manifest_errors)
        expected_commit = self.api._snapshot_expected_commit(manifest)
        seen_ids = {}
        parsed_records = []
        for snapshot in snapshots:
            file_totals, file_errors, file_records = self.api.validate_file(
                snapshot,
                context,
                seen_ids=seen_ids,
                expected_commit=expected_commit,
            )
            totals.update(file_totals)
            errors.extend(file_errors)
            parsed_records.extend(file_records)
            if file_totals["records"]:
                # Skip zero entries so a --family filter reports only what it kept.
                by_family[snapshot.path.parent.name] += file_totals["records"]
        metadata_errors = self.api._snapshot_metadata_errors(
            run_dir, manifest, snapshots, parsed_records
        )
        errors.extend(metadata_errors)
        report = self._snapshot_report(
            run_dir,
            (snapshots, totals, by_family),
            not (manifest_errors or metadata_errors),
            context,
        )
        return report, errors

    def _snapshot_report(self, run_dir, parts, manifest_valid, context):
        snapshots, totals, by_family = parts
        report = {
            "run_dir": str(self.api.Path(run_dir).resolve()),
            "files": len(snapshots),
            "manifest_valid": manifest_valid,
            "records": totals["records"],
            "accepted": totals["accepted"],
            "rejected": totals["rejected"],
            "invalid": totals["invalid"],
            "parse_failures": totals["parse_failures"],
            "skipped": totals["skipped"],
            "reference_oracle": totals["reference_oracle"],
            "named_runtime": totals["named_runtime"],
            "mixed_oracle": totals["mixed_oracle"],
            "publishable": totals["publishable"],
            "by_family": dict(sorted(by_family.items())),
        }
        if context.reproduce:
            report["reproduce"] = {
                key.removeprefix("reproduce_"): value
                for key, value in sorted(totals.items())
                if key.startswith("reproduce_")
            }
        return report

    def _argument_error(self, args):
        """The usage failure for the parsed request, or None."""
        if not args.run_dir:
            print(
                "oracle_validate: a run directory is required",
                file=self.api.sys.stderr,
            )
            return 2
        if not args.run_dir.is_dir():
            print(
                f"oracle_validate: not a directory: {args.run_dir}",
                file=self.api.sys.stderr,
            )
            return 2
        return None

    def _selected_families(self, args):
        """The requested --family set, or an exit code when a name is unknown."""
        selected = set(args.family_names or ())
        unknown = sorted(selected - set(self.api.families.SPECS))
        if unknown:
            print(
                f"oracle_validate: unknown families: {', '.join(unknown)}",
                file=self.api.sys.stderr,
            )
            return None, 2
        return selected, None

    def _print_findings(self, errors, max_findings):
        """Print findings, bounded by --max-findings with a truncation count."""
        finding_limit = max(0, max_findings)
        for finding in errors[:finding_limit]:
            print(finding, file=self.api.sys.stderr)
        hidden = max(0, len(errors) - finding_limit)
        if hidden:
            print(f"... {hidden} more findings", file=self.api.sys.stderr)

    def main(self, argv=None):
        parser = self._argument_parser()
        args = parser.parse_args(
            list(self.api.sys.argv[1:] if argv is None else argv)
        )
        paths = self.api.confine_named(parser, args, _PATH_ARGUMENTS)
        args.run_dir = paths["run_dir"]
        args.oracle_rust_bin = paths["oracle_rust_bin"]
        error = self._argument_error(args)
        if error is not None:
            return error
        selected, error = self._selected_families(args)
        if error is not None:
            return error
        try:
            report, errors = self.api.validate_run(
                self.api.ValidationContext(
                    args.run_dir,
                    require_runtime=args.require_runtime,
                    reproduce=args.reproduce,
                    selected=selected,
                    oracle_rust_bin=args.oracle_rust_bin,
                )
            )
        except (OSError, ValueError) as exc:
            print(f"oracle_validate: {exc}", file=self.api.sys.stderr)
            return 2
        print(self.api.json.dumps(report, indent=2))
        self._print_findings(errors, args.max_findings)
        return 1 if errors else 0


if __package__:
    _expose_package_sibling(__name__)
