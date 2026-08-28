"""Argparse entry for ``curate_coding``.

Imported lazily from :func:`curate_coding.main` so this module can call
back into the transform without a load-time cycle.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

_PIPELINES = Path(__file__).resolve().parent
if str(_PIPELINES) not in sys.path:
    sys.path.insert(0, str(_PIPELINES))

import curate_coding as cc  # noqa: E402


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=cc.__doc__)
    parser.add_argument("source", type=Path, help="legacy episode JSONL to inspect")
    parser.add_argument("--output-jsonl", type=Path)
    parser.add_argument("--manifest-jsonl", type=Path)
    parser.add_argument(
        "--output-dir",
        type=Path,
        help="new lane root for directory-wide curation",
    )
    parser.add_argument(
        "--verify",
        action="store_true",
        help="fail when any curated step or manifest entry breaks the lane contract",
    )
    parser.add_argument(
        "--expect-source-steps",
        type=int,
        help="require the manifest to account for exactly this many source steps",
    )
    return parser


def _is_verifying(args: argparse.Namespace) -> bool:
    if args.verify:
        return True
    return args.expect_source_steps is not None


def _reject_negative_expected_steps(
    parser: argparse.ArgumentParser,
    args: argparse.Namespace,
) -> None:
    if args.expect_source_steps is None:
        return
    if args.expect_source_steps >= 0:
        return
    parser.error("--expect-source-steps must not be negative")


def _directory_option_conflicts(
    parser: argparse.ArgumentParser,
    args: argparse.Namespace,
    verifying: bool,
) -> None:
    if args.output_jsonl is not None:
        parser.error("--output-dir cannot be combined with file output options")
    if args.manifest_jsonl is not None:
        parser.error("--output-dir cannot be combined with file output options")
    if verifying:
        parser.error("--output-dir cannot be combined with --verify")
    if not args.source.is_dir():
        parser.error("--output-dir requires a source directory")


def _main_output_dir(parser: argparse.ArgumentParser, args: argparse.Namespace) -> int:
    _reject_negative_expected_steps(parser, args)
    _directory_option_conflicts(parser, args, _is_verifying(args))
    try:
        result = cc.curate_run(args.source, args.output_dir)
    except (FileExistsError, OSError, ValueError) as exc:
        parser.error(str(exc))
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


def _output_replaces_source(output_jsonl: Path | None, source: Path) -> bool:
    if output_jsonl is None:
        return False
    return output_jsonl.resolve(strict=False) == source.resolve()


def _requested_destinations(args: argparse.Namespace) -> list[Path]:
    destinations = []
    if args.output_jsonl is not None:
        destinations.append(args.output_jsonl)
    if args.manifest_jsonl is not None:
        destinations.append(args.manifest_jsonl)
    return destinations


def _write_curation_outputs(
    args: argparse.Namespace,
    result: dict[str, Any],
    summary: dict[str, Any],
) -> int:
    if args.output_jsonl is not None:
        cc.write_new_jsonl(args.output_jsonl, result["records"])
    if args.manifest_jsonl is not None:
        cc.write_new_jsonl(args.manifest_jsonl, result["manifest"])
    print(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


def _print_violations(violations: list[str]) -> None:
    for violation in violations:
        print(f"VIOLATION: {violation}", file=sys.stderr)


def _verified_file_run(args: argparse.Namespace, result: dict[str, Any]) -> int:
    violations = cc.verify_curation(
        result, expected_source_steps=args.expect_source_steps
    )
    summary = dict(result["summary"])
    summary["verification"] = {
        "expected_source_steps": args.expect_source_steps,
        "violations": violations,
    }
    if not violations:
        return _write_curation_outputs(args, result, summary)
    print(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True))
    _print_violations(violations)
    return 2


def _main_source_file(parser: argparse.ArgumentParser, args: argparse.Namespace) -> int:
    _reject_negative_expected_steps(parser, args)
    if args.source.is_dir():
        parser.error("a source directory requires --output-dir")
    if _output_replaces_source(args.output_jsonl, args.source):
        parser.error("output must not replace the source")
    try:
        cc.preflight_destinations(_requested_destinations(args))
    except (FileExistsError, ValueError) as exc:
        parser.error(str(exc))
    result = cc.curate_jsonl(args.source)
    if not _is_verifying(args):
        return _write_curation_outputs(args, result, result["summary"])
    return _verified_file_run(args, result)


def run(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)
    if args.output_dir is not None:
        return _main_output_dir(parser, args)
    return _main_source_file(parser, args)
