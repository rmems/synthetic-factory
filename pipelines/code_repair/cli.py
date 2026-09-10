#!/usr/bin/env python3
"""Code-repair commands: catalog-check, generate, replay, publish, export, render.

Exit codes: 0 when the command succeeded with nothing to report, 1 when it
ran and reports catalog findings, 2 on a coded refusal or a usage error. ``--json`` prints one object
with a ``code`` field per finding so an agent never parses prose.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from . import catalog as cat
from . import catalog_check as cc
from . import executor as ex
from . import export
from . import generate
from . import publication
from . import replay
from . import views
from . import record_validation as validation
from . import vocabulary as cv
from ._contract import bind_import_twin, envelope, oc

__all__ = ["build_parser", "run"]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="code_repair_cli.py", description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)

    check = commands.add_parser("catalog-check", help="every original passes; references agree")
    check.add_argument("--catalog", type=Path, required=True)
    check.add_argument("--timeout-s", type=float, default=cv.DEFAULT_TIMEOUT_S)
    check.add_argument("--json", action="store_true")

    gen = commands.add_parser("generate", help="seeded candidates into a new run directory")
    gen.add_argument("--catalog", type=Path, required=True)
    gen.add_argument("--seed", type=int, required=True)
    gen.add_argument("--count", type=int, required=True)
    gen.add_argument("--out", type=Path, required=True)
    gen.add_argument("--produced-at", default=None, help="pinned ISO-8601 UTC instant")
    gen.add_argument("--timeout-s", type=float, default=cv.DEFAULT_TIMEOUT_S)
    gen.add_argument("--per-program-cap", type=int, default=cv.DEFAULT_PER_PROGRAM_CAP)
    gen.add_argument("--json", action="store_true")

    rep = commands.add_parser("replay", help="re-execute every positive record of a run")
    rep.add_argument("--run", type=Path, required=True)
    rep.add_argument("--catalog", type=Path, required=True)
    rep.add_argument("--out", type=Path, required=True)
    rep.add_argument("--timeout-s", type=float, default=cv.DEFAULT_TIMEOUT_S)
    rep.add_argument("--json", action="store_true")

    exp = commands.add_parser("export", help="evidence, SFT rows and consumer rows into a new tree")
    exp.add_argument("--run", type=Path, required=True)
    exp.add_argument("--catalog", type=Path, required=True)
    exp.add_argument("--out", type=Path, required=True)
    exp.add_argument("--replay", type=Path, default=None, help="a replay directory of this run")
    exp.add_argument("--lineage-cap", type=int, default=export.DEFAULT_LINEAGE_CAP)
    exp.add_argument("--admit", action="store_true", help="require completed round and fresh replay")
    exp.add_argument("--round-marker", type=Path, help="actual ROUND-rNN.complete.json")
    exp.add_argument("--json", action="store_true")

    pub = commands.add_parser("publish", help="freshly replay and publish a local transactional round")
    pub.add_argument("--run", type=Path, required=True)
    pub.add_argument("--factory-dir", type=Path, required=True)
    pub.add_argument("--round", type=int, required=True)
    pub.add_argument("--lineage-cap", type=int, default=export.DEFAULT_LINEAGE_CAP)
    pub.add_argument("--json", action="store_true")

    render = commands.add_parser("render", help="the SFT prompt/completion of one record")
    render.add_argument("run_dir", type=Path)
    render.add_argument("record_id")
    render.add_argument("--json", action="store_true")
    return parser


def _emit(payload: dict[str, Any], as_json: bool, text: str) -> None:
    print(json.dumps(payload, indent=2, sort_keys=True) if as_json else text)


def _catalog_check(args: argparse.Namespace) -> int:
    catalog = cat.load_catalog(args.catalog)
    findings = cc.catalog_check(catalog, ex.Executor(timeout_s=args.timeout_s))
    status = "findings" if findings else "ok"
    lines = [f"{f['code']} {f['program_id']}: {f['detail']}" for f in findings]
    text = "\n".join(lines) or f"catalog-check ok: {len(catalog.programs)} programs pass"
    payload = {
        "command": "catalog-check", "status": status, "catalog_id": catalog.catalog_id,
        "programs": len(catalog.programs), "findings": findings,
    }
    _emit(payload, args.json, text)
    return 1 if findings else 0


def _generate(args: argparse.Namespace) -> int:
    request = generate.RunRequest(
        args.catalog, args.out, args.seed, args.count, args.produced_at, args.timeout_s,
        args.per_program_cap,
    )
    summary = generate.run(request)
    text = (
        f"generated {summary['records']} records into {args.out} "
        f"(outcomes {summary['outcomes']}, skips {summary['skips']})"
    )
    _emit({"command": "generate", "status": "ok", "summary": summary}, args.json, text)
    return 0


def _replay(args: argparse.Namespace) -> int:
    request = replay.ReplayRequest(args.run, args.catalog, args.out, args.timeout_s)
    summary = replay.run(request)
    counts = summary["counts"]
    text = (
        f"replay {summary['status']}: {counts['passed']} of {counts['positives']} positives "
        f"passed, {counts['not_replayed']} not replayed (natural ineligibility); {args.out}"
    )
    failures = [
        {"code": e["code"], "record_id": e["record_id"], "detail": e["detail"]}
        for e in summary["records"] if e["status"] == "replayed" and e["code"] != cv.REPLAY_PASSED
    ]
    # A run with nothing to replay is a clean no-op: non-positives never fail a replay.
    status = "ok" if summary["status"] in ("passed", "nothing_to_replay") else "findings"
    payload = {"command": "replay", "status": status, "findings": failures, "summary": summary}
    _emit(payload, args.json, text)
    return 0 if status == "ok" else 1


def _export(args: argparse.Namespace) -> int:
    manifest = export.run(export.ExportRequest(
        args.run, args.out, args.replay, args.lineage_cap, catalog_dir=args.catalog,
        admit=args.admit, round_marker=args.round_marker,
    ))
    tables, admission = manifest["tables"], manifest["admission"]
    exported = tables["dispositions"].get("exported", 0)
    text = (
        f"exported {exported} rows from {tables['positives']} positives ({tables['per_split']}) "
        f"into {args.out}; training export {admission['training_export']}: "
        f"{', '.join(admission['blockers'])}"
    )
    _emit({"command": "export", "status": "ok", "manifest": manifest}, args.json, text)
    return 0


def _publish(args: argparse.Namespace) -> int:
    try:
        manifest = publication.publish_run(publication.PublishRequest(
            args.run, args.factory_dir, args.round, args.lineage_cap,
        ))
    except publication._transaction().TransactionError as exc:
        raise cv.RepairRefusal(cv.FINDING_EXPORT_INTEGRITY, str(exc)) from exc
    _emit({"command": "publish", "status": "ok", "manifest": manifest}, args.json,
          f"published {manifest['records']} records in local round {args.round}; "
          "fresh replay passed; no model training launched")
    return 0


def _load_record(run_dir: Path, record_id: str) -> dict[str, Any]:
    """The record with this id, refused unless the shared envelope and digest accept it."""

    path = run_dir / generate.CANDIDATES_FILENAME
    cv.refuse_when(not path.is_file(), cv.FINDING_RUN_FILE_MISSING, f"{path} is missing")
    for _lineno, record in oc.iter_jsonl(path):
        if isinstance(record, dict) and record.get("id") == record_id:
            validation.validate_shape(record)
            return record
    message = f"no record {cv.shown(record_id)} in {path}"
    raise cv.RepairRefusal(cv.FINDING_RECORD_NOT_FOUND, message)


def _render(args: argparse.Namespace) -> int:
    record = _load_record(args.run_dir, args.record_id)
    result = record["result"]
    if not views.is_positive(record):
        payload = {
            "command": "render", "status": "findings", "record_id": args.record_id,
            "findings": [{"code": cv.FINDING_RECORD_NOT_A_POSITIVE_EXAMPLE,
                          "outcome": result["outcome"], "oracle_status": result["oracle_status"],
                          "reason_codes": result["reason_codes"]}],
        }
        text = (
            f"{cv.FINDING_RECORD_NOT_A_POSITIVE_EXAMPLE}: {args.record_id} is {result['outcome']} "
            f"({result['oracle_status']}; {', '.join(result['reason_codes'])})"
        )
        _emit(payload, args.json, text)
        return 1
    row = {"prompt": views.render_prompt(views.public_view(record)),
           "completion": views.completion_of(record)}
    leaks = views.view_findings(record, row)
    payload = {
        "command": "render", "status": "findings" if leaks else "ok", "record_id": args.record_id,
        "findings": [{"code": code} for code in leaks],
        "sha256": {"broken": result["broken_sha256"], "repaired": result["repaired_sha256"],
                   "record": record["provenance"]["record_sha256"]},
    }
    if leaks:
        # A pair with a leak finding is never emitted, not even beside its findings.
        _emit(payload, args.json, "leak findings: " + ", ".join(leaks))
        return 1
    payload["sft"] = row
    _emit(payload, args.json, f"### prompt\n{row['prompt']}\n### completion\n{row['completion']}")
    return 0


_COMMANDS = {
    "catalog-check": _catalog_check, "generate": _generate, "render": _render, "replay": _replay,
    "export": _export, "publish": _publish,
}


def _refused(args: argparse.Namespace, refusal: envelope.ContractError) -> int:
    """A coded refusal: one JSON object on stdout under ``--json``, else ``CODE: prose``."""

    if getattr(args, "json", False):
        payload = {
            "command": args.command, "status": "refused",
            "code": getattr(refusal, "code", None), "message": str(refusal),
        }
        print(json.dumps(payload, sort_keys=True))
    else:
        print(str(refusal), file=sys.stderr)
    return 2


def run(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        return _COMMANDS[args.command](args)
    except envelope.ContractError as refusal:
        return _refused(args, refusal)


bind_import_twin(__name__)
