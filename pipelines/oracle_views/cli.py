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

from . import output, rows
from . import vocabulary as tv
from ._contract import bind_import_twin, confine, dumps_exact_json, validator

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
    first = f"; first: {errors[0]}" if errors else ""
    tv.refuse_when(
        bool(errors) or not report.get("manifest_valid"), tv.FINDING_RUN_NOT_AUTHENTICATED,
        f"the oracle validator reported {len(errors)} findings{first}",
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

    return {kind: rows.render_row(record, kind) for kind in tv.ROW_KINDS}


def _gated_rows(record: dict[str, Any]) -> tuple[dict[str, dict[str, Any]], tuple | None]:
    """``(rows, None)`` for a positive record, ``({}, (code, message))`` otherwise."""

    refusal = rows.refusal_of(record)
    if refusal is not None:
        return {}, refusal
    try:
        return _rows_of(record), None
    except tv.TextViewRefusal as exc:
        return {}, (exc.code, exc.message)


def _empty_kinds() -> dict[str, list[dict[str, Any]]]:
    return {kind: [] for kind in tv.ROW_KINDS}


def _project_record(projection: Projection, source: str, record: dict[str, Any]) -> None:
    family, identifier = str(record.get("family")), str(record.get("id"))
    projection.records[family] += 1
    rendered, refusal = _gated_rows(record)
    if refusal is not None:
        projection.refused.append(
            {"code": refusal[0], "family": family, "id": identifier, "source": source}
        )
        return
    by_kind = projection.rows.setdefault(family, _empty_kinds())
    for kind, row in rendered.items():
        projection.findings.extend(
            {"code": code, "id": identifier, "kind": kind}
            for code in rows.view_findings(record, row)
        )
        by_kind[kind].append(row)


def project(run: AuthenticatedRun) -> Projection:
    """Render every record of the run; refusals and findings are collected, not raised."""

    projection = Projection({family: _empty_kinds() for family in run.families})
    for source, record in run.records:
        _project_record(projection, source, record)
    return projection


def _family_counts(run: AuthenticatedRun, projection: Projection) -> dict[str, Any]:
    refused = Counter(entry["family"] for entry in projection.refused)
    return {
        family: {
            "records": projection.records[family],
            "refused": refused[family],
            "rows": {kind: len(items) for kind, items in projection.rows[family].items()},
        }
        for family in run.families
    }


def summary_of(run: AuthenticatedRun, projection: Projection, files: dict[str, bytes]) -> dict:
    """The ``VIEWS.json`` content: counts, refusals, source and output digests."""

    return {
        "families": _family_counts(run, projection),
        "files": output.file_entries(files),
        "format": tv.VIEW_FORMAT,
        "note": tv.PROJECTION_NOTE,
        "refused": projection.refused,
        "source": {"files": run.sources, "run": run.name},
        "totals": {
            "records": sum(projection.records.values()),
            "refused": len(projection.refused),
            "rows": sum(len(by_kind[tv.KIND_SFT]) for by_kind in projection.rows.values()),
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


def _confined(parser: argparse.ArgumentParser, value: str, argument: str) -> Path:
    path = confine(parser, value, argument=argument)
    if path is None:
        parser.error(f"{argument} is required")
    return path


def _text_report(report: dict[str, Any], status: int) -> tuple[list[str], bool]:
    """The human-readable lines for ``report`` and whether they belong on stderr."""

    if status == EXIT_OK:
        totals = report["totals"]
        line = (
            f"{PROGRAM}: wrote {totals['rows']} rows of each shape from {totals['records']} "
            f"records ({totals['refused']} refused)"
        )
        return [line], False
    if status == EXIT_FINDINGS:
        return [
            f"{PROGRAM}: {item['id']} {item['kind']}: {item['code']}"
            for item in report["findings"]
        ], True
    refusal = report["refusal"]
    return [f"{PROGRAM}: {refusal['code']}: {refusal['message']}"], True


def _emit(report: dict[str, Any], as_json: bool, status: int) -> None:
    if as_json:
        print(dumps_exact_json(report, sort_keys=True, indent=2))
        return
    lines, to_stderr = _text_report(report, status)
    stream = sys.stderr if to_stderr else sys.stdout
    for line in lines:
        print(line, file=stream)


def main(argv: list[str] | None = None) -> int:
    parser = _argument_parser()
    args = parser.parse_args(sys.argv[1:] if argv is None else argv)
    run_dir = _confined(parser, args.run_dir, "run_dir")
    out = _confined(parser, args.out, "--out")
    try:
        status, report = build(run_dir, out)
    except tv.TextViewRefusal as exc:
        status, report = EXIT_REFUSED, {"refusal": {"code": exc.code, "message": exc.message}}
    _emit(report, args.json, status)
    return status


bind_import_twin(__name__)
