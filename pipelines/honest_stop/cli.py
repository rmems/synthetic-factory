"""CLI for the honest-stop family.

``generate`` requires ``--dry-run`` and does not call a model. ``export`` refuses
``--publish`` and any token. Exit 0 is success, 1 is a failed check, 2 is a refusal.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from . import vocabulary as cv
from ._contract import bind_import_twin, dumps_exact_json
from .export_stub import export_plan, write_stub
from .gate import check_bytes
from .generate import dry_run_plan
from .validate import validate_text

__all__ = ["main", "run"]


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="honest_stop_cli.py", description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    _add_generate(commands)
    _add_record_command(commands, "validate", "structurally check one JSON record")
    _add_record_command(commands, "gate", "re-execute one JSON record in a subprocess")
    _add_export(commands)
    return parser


def _add_generate(commands: argparse._SubParsersAction) -> None:
    generate = commands.add_parser("generate", help="plan a run; --dry-run is required")
    generate.add_argument("--dry-run", action="store_true")
    generate.add_argument("--seed", type=int, required=True)
    generate.add_argument("--count", type=int, required=True)
    generate.add_argument("--produced-at", default=None)


def _add_record_command(commands: argparse._SubParsersAction, name: str, help_text: str) -> None:
    command = commands.add_parser(name, help=help_text)
    command.add_argument("record", type=Path)


def _add_export(commands: argparse._SubParsersAction) -> None:
    export = commands.add_parser("export", help="print or write an empty export manifest")
    export.add_argument("--dry-run", action="store_true")
    export.add_argument("--out", type=Path, default=None)
    export.add_argument("--publish", action="store_true")
    export.add_argument("--token", default=None)


def _emit(payload: dict) -> int:
    sys.stdout.write(dumps_exact_json(payload) + "\n")
    return 0


def _generate(args: argparse.Namespace) -> int:
    if not args.dry_run:
        raise cv.FamilyError(
            "live_generation_disabled",
            "pass --dry-run; this slice does not call a model or write records",
        )
    plan = dry_run_plan(seed=args.seed, count=args.count, produced_at=args.produced_at)
    return _emit(plan)


def _record_text(path: Path) -> tuple[str, ...]:
    try:
        text = path.read_bytes().decode("utf-8")
    except UnicodeDecodeError:
        return ("record.json",)
    return validate_text(text)


def _validate(args: argparse.Namespace) -> int:
    codes = _record_text(args.record)
    _emit({"ok": not codes, "codes": list(codes)})
    return 0 if not codes else 1


def _gate(args: argparse.Namespace) -> int:
    report = check_bytes(args.record.read_bytes())
    _emit(
        {
            "accepted": report.accepted,
            "code": report.code,
            "measured_blocker": report.measured_blocker,
            "counterfactual_holds": report.counterfactual_holds,
        }
    )
    return 0 if report.accepted else 1


def _export(args: argparse.Namespace) -> int:
    if args.publish:
        raise cv.FamilyError("export.publish_disabled", "Hugging Face publish is disabled")
    if args.token:
        raise cv.FamilyError("export.token", "refusing a Hugging Face token")
    if args.dry_run and args.out is not None:
        raise cv.FamilyError("export.dry_run", "refusing --out with --dry-run")
    plan = write_stub(args.out) if args.out is not None else export_plan()
    return _emit(plan)


def run(argv: list[str] | None = None) -> int:
    """Dispatch one subcommand."""

    args = _parser().parse_args(argv)
    handler = {
        "generate": _generate,
        "validate": _validate,
        "gate": _gate,
        "export": _export,
    }[args.command]
    try:
        return handler(args)
    except cv.FamilyError as exc:
        print(f"refused: {exc}", file=sys.stderr)
        return 2
    except OSError as exc:
        print(f"refused: io: {exc}", file=sys.stderr)
        return 2


main = run

bind_import_twin(__name__)
