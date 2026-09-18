#!/usr/bin/env python3
"""CLI walk, manifest assembly, and report emission for validate_run."""

import argparse
import json
import sys
import tempfile
from pathlib import Path

if __package__:
    from . import _assert_direct_sibling, _expose_package_sibling
    _assert_direct_sibling("validate_run_cli")
    from .validate_run_input import parse_exact_json_record as _default_parse_record
else:
    getattr(sys.modules.get("pipelines"), "_join_package_sibling", lambda name: None)(
        "validate_run_cli"
    )
    from validate_run_input import parse_exact_json_record as _default_parse_record


def parse_args(argv=None):
    parser = argparse.ArgumentParser(
        description="Validate a dated factory run under outputs/raw/<date>/.",
    )
    parser.add_argument(
        "--write",
        action="store_true",
        help="write manifest.json into run_dir (default: print totals only)",
    )
    parser.add_argument("run_dir", help="run directory containing .jsonl files")
    return parser.parse_args(argv)


def _empty_file_entry(rel):
    return {"file": str(rel), "records": 0, "kinds": {}, "errors": []}


def _decode_jsonl(path, rel):
    try:
        return path.read_bytes().decode("utf-8"), None
    except UnicodeDecodeError as exc:
        return None, f"{rel}: invalid UTF-8: {exc}"


def _validate_physical_lines(text, rel, check_line, parse_record):
    records = 0
    kinds = {}
    errors = []
    # JSONL is delimited by literal LF bytes.  ``str.splitlines()`` also
    # splits at U+2028/U+2029, which are valid characters inside a JSON
    # string and would turn one valid record into several invalid lines.
    for lineno, line in enumerate(text.split("\n"), 1):
        if not line.strip():
            continue
        where = f"{rel}:{lineno}"
        obj, input_error = parse_record(line)
        if input_error is not None:
            errors.append(f"{where}: {input_error}")
            continue
        errs, kind = check_line(obj, where)
        records += 1
        kinds[kind] = kinds.get(kind, 0) + 1
        errors.extend(errs)
    return records, kinds, errors


def _validate_jsonl_file(path, run_dir, check_line, parse_record):
    rel = path.relative_to(run_dir)
    entry = _empty_file_entry(rel)
    text, decode_error = _decode_jsonl(path, rel)
    if decode_error is not None:
        entry["errors"].append(decode_error)
        return entry
    records, kinds, errors = _validate_physical_lines(
        text, rel, check_line, parse_record
    )
    entry["records"] = records
    entry["kinds"] = kinds
    entry["errors"] = errors
    return entry


def assemble_manifest(run_dir, check_line, parse_record):
    """Walk ``run_dir`` JSONL files and return the in-memory manifest."""
    manifest = {"run_dir": str(run_dir), "files": [], "totals": {}, "errors": []}
    kind_totals = {}
    for path in sorted(run_dir.rglob("*.jsonl")):
        entry = _validate_jsonl_file(path, run_dir, check_line, parse_record)
        for kind, count in entry["kinds"].items():
            kind_totals[kind] = kind_totals.get(kind, 0) + count
        manifest["files"].append(entry)
        manifest["errors"].extend(entry["errors"])
    manifest["totals"] = {
        "files": len(manifest["files"]),
        "records": sum(item["records"] for item in manifest["files"]),
        "by_kind": kind_totals,
        "error_count": len(manifest["errors"]),
    }
    return manifest


def emit_report(manifest):
    print(json.dumps(manifest["totals"], indent=2))
    for err in manifest["errors"]:
        print("ERROR:", err, file=sys.stderr)
    return 1 if manifest["errors"] else 0


def _write_manifest(run_dir, manifest):
    payload = json.dumps(manifest, indent=2) + "\n"
    with tempfile.TemporaryDirectory(dir=run_dir, prefix=".manifest-") as raw:
        staged = Path(raw) / "manifest.json"
        staged.write_text(payload)
        staged.replace(run_dir / "manifest.json")


def main(argv=None, *, check_line, parse_record=None):
    """Run the public CLI. ``check_line`` is the facade's live router."""
    parse_record = _default_parse_record if parse_record is None else parse_record
    args = parse_args(argv)
    run_dir = Path(args.run_dir).resolve()
    manifest = assemble_manifest(run_dir, check_line, parse_record)
    if args.write:
        _write_manifest(run_dir, manifest)
    sys.exit(emit_report(manifest))


if __package__:
    _expose_package_sibling(__name__)
