"""Project an oracle-grounded run into leak-checked text training views.

Reads a run written by ``oracle_generate.py`` through the shared oracle
validator -- ``authenticate_manifest`` captures every manifested file once and
``validate_run_snapshot`` validates those same captured bytes -- and refuses the
run unless it validates cleanly. Each accepted, publishable, simulated record of
the five neuromorphic families becomes one row of each shape; every other record
is listed in ``VIEWS.json`` with its refusal code. Every rendered row is
re-checked by ``view_findings``; any finding aborts before anything is written.

Writes ``<family>.sft.jsonl``, ``<family>.chat.jsonl``, ``<family>.choice.jsonl``
and ``VIEWS.json`` into a brand-new directory. The view is a projection: it
makes no training-readiness claim.

Usage:
  python3 pipelines/oracle_text_views.py <run_dir> --out <new_dir> [--json]

Exit status: 0 written; 1 a rendered row has leak findings (nothing written);
2 a coded refusal (a missing or unauthenticated run, or a destination that
exists, names ``outputs/raw/`` or lies inside the run).
"""

from __future__ import annotations

import argparse
import hashlib
import sys
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

if __package__:
    from . import _assert_direct_sibling, _expose_package_sibling

    _assert_direct_sibling("oracle_text_views")
    from . import oracle_text_view_output as output
    from . import oracle_text_view_rows as views
    from . import oracle_text_view_vocabulary as tv
    from . import oracle_validate as validator
    from .exact_json import dumps_exact_json
    from .operator_paths import confine
else:
    getattr(sys.modules.get("pipelines"), "_join_package_sibling", lambda name: None)(
        "oracle_text_views"
    )
    import oracle_text_view_output as output
    import oracle_text_view_rows as views
    import oracle_text_view_vocabulary as tv
    import oracle_validate as validator
    from exact_json import dumps_exact_json
    from operator_paths import confine

PROGRAM = "oracle_text_views"
EXIT_OK, EXIT_FINDINGS, EXIT_REFUSED = 0, 1, 2


@dataclass(frozen=True)
class AuthenticatedRun:
    """The validated families, the parsed records and their source digests."""

    name: str
    families: tuple[str, ...]
    records: tuple[tuple[str, dict[str, Any]], ...]
    sources: dict[str, str]


@dataclass
class Projection:
    """Rows per family and kind, refused records, and any leak findings."""

    rows: dict[str, dict[str, list[dict[str, Any]]]]
    refused: list[dict[str, str]] = field(default_factory=list)
    findings: list[dict[str, str]] = field(default_factory=list)
    records: Counter = field(default_factory=Counter)


def _validated(run_dir: Path) -> tuple[Any, Any]:
    try:
        authentication = validator.authenticate_manifest(run_dir)
        report, errors = validator.validate_run_snapshot(run_dir, authentication)
    except (OSError, ValueError) as exc:
        raise tv.TextViewRefusal(
            tv.FINDING_RUN_NOT_AUTHENTICATED, f"{type(exc).__name__}: {exc}"
        ) from exc
    tv.refuse_when(
        bool(errors) or not report.get("manifest_valid"), tv.FINDING_RUN_NOT_AUTHENTICATED,
        f"the oracle validator reported {len(errors)} findings"
        + (f"; first: {errors[0]}" if errors else ""),
    )
    return authentication[0], authentication[1]


def read_run(run_dir: Path) -> AuthenticatedRun:
    """The records of an authenticated, cleanly validating run, parsed from captured bytes."""

    tv.refuse_when(
        not run_dir.is_dir(), tv.FINDING_RUN_DIR_MISSING, f"not a directory: {run_dir.name}"
    )
    manifest, snapshots = _validated(run_dir)
    records = tuple(
        (snapshot.relative, validator.strict_json_loads(line.decode("utf-8")))
        for snapshot in snapshots
        for line in bytes(snapshot.body).splitlines()
        if line.strip()
    )
    sources = {
        snapshot.relative: hashlib.sha256(bytes(snapshot.body)).hexdigest()
        for snapshot in snapshots
    }
    families = tuple(name for name in tv.FAMILIES if name in manifest["families"])
    return AuthenticatedRun(run_dir.name, families, records, sources)


def _rows_of(record: dict[str, Any]) -> dict[str, dict[str, Any]]:
    """Every row shape for a gated record, before its leak check."""

    return {kind: views.render_row(record, kind) for kind in tv.ROW_KINDS}


def _gated_rows(record: dict[str, Any]) -> tuple[dict[str, dict[str, Any]], tuple | None]:
    """``(rows, None)`` for a positive record, ``({}, (code, message))`` otherwise."""

    refusal = views.refusal_of(record)
    if refusal is not None:
        return {}, refusal
    try:
        return _rows_of(record), None
    except tv.TextViewRefusal as exc:
        return {}, (exc.code, exc.message)


def _project_record(projection: Projection, source: str, record: dict[str, Any]) -> None:
    family, identifier = record.get("family"), str(record.get("id"))
    projection.records[family] += 1
    rows, refusal = _gated_rows(record)
    if refusal is not None:
        projection.refused.append(
            {"code": refusal[0], "family": str(family), "id": identifier, "source": source}
        )
        return
    by_kind = projection.rows.setdefault(family, {kind: [] for kind in tv.ROW_KINDS})
    for kind, row in rows.items():
        projection.findings.extend(
            {"code": code, "id": identifier, "kind": kind}
            for code in views.view_findings(record, row)
        )
        by_kind[kind].append(row)


def project(run: AuthenticatedRun) -> Projection:
    """Render every record of the run; refusals and findings are collected, not raised."""

    projection = Projection(
        {family: {kind: [] for kind in tv.ROW_KINDS} for family in run.families}
    )
    for source, record in run.records:
        _project_record(projection, source, record)
    return projection


def summary_of(run: AuthenticatedRun, projection: Projection, files: dict[str, bytes]) -> dict:
    refused = Counter(entry["family"] for entry in projection.refused)
    families = {
        family: {
            "records": projection.records[family],
            "refused": refused[family],
            "rows": {kind: len(rows) for kind, rows in projection.rows[family].items()},
        }
        for family in run.families
    }
    return {
        "families": families,
        "files": output.file_entries(files),
        "format": tv.VIEW_FORMAT,
        "note": tv.PROJECTION_NOTE,
        "refused": projection.refused,
        "source": {"files": run.sources, "run": run.name},
        "totals": {
            "records": sum(projection.records.values()),
            "refused": len(projection.refused),
            "rows": sum(len(rows[tv.KIND_SFT]) for rows in projection.rows.values()),
        },
    }


def build(run_dir: Path, out: Path) -> tuple[int, dict[str, Any]]:
    """Read, project, check and write; ``(exit status, report)``. Refusals raise."""

    output.check_destination(out)
    tv.refuse_when(
        out == run_dir or run_dir in out.parents, tv.FINDING_DESTINATION_INSIDE_RUN,
        "the destination lies inside the run it projects",
    )
    run = read_run(run_dir)
    projection = project(run)
    if projection.findings:
        return EXIT_FINDINGS, {"findings": projection.findings}
    files = output.view_files(projection.rows)
    summary = summary_of(run, projection, files)
    files[tv.SUMMARY_FILENAME] = output.summary_bytes(summary)
    output.write_new_tree(out, files)
    return EXIT_OK, summary


def _argument_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog=PROGRAM, description=__doc__.split("\n\n")[0])
    parser.add_argument("run_dir", help="an oracle_generate.py run directory")
    parser.add_argument("--out", required=True, help="a new directory for the view files")
    parser.add_argument("--json", action="store_true", help="print the report as JSON")
    return parser


def _emit(report: dict[str, Any], as_json: bool, status: int) -> None:
    if as_json:
        print(dumps_exact_json(report, sort_keys=True, indent=2))
    elif status == EXIT_OK:
        totals = report["totals"]
        print(
            f"{PROGRAM}: wrote {totals['rows']} rows of each shape from {totals['records']} "
            f"records ({totals['refused']} refused)"
        )
    elif status == EXIT_FINDINGS:
        for finding in report["findings"]:
            line = f"{finding['id']} {finding['kind']}: {finding['code']}"
            print(f"{PROGRAM}: {line}", file=sys.stderr)
    else:
        refusal = report["refusal"]
        print(f"{PROGRAM}: {refusal['code']}: {refusal['message']}", file=sys.stderr)


def main(argv: list[str] | None = None) -> int:
    parser = _argument_parser()
    args = parser.parse_args(sys.argv[1:] if argv is None else argv)
    run_dir = confine(parser, args.run_dir, argument="run_dir")
    out = confine(parser, args.out, argument="--out")
    try:
        status, report = build(run_dir, out)
    except tv.TextViewRefusal as exc:
        status, report = EXIT_REFUSED, {"refusal": {"code": exc.code, "message": exc.message}}
    _emit(report, args.json, status)
    return status


if __package__:
    _expose_package_sibling(__name__)


if __name__ == "__main__":
    sys.exit(main())
