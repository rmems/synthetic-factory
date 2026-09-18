"""Model-channel commands: generate, discover-openrouter, vllm-spec.

Exit codes: 0 on success, 2 on a coded refusal or usage error.
"""
from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from ._contract import bind_import_twin, dumps_exact_json, load_strict_json
from . import generate
from . import openai_client
from . import openrouter
from . import source_policy as policy
from . import vllm as vllm_mod


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="model_channel_cli.py", description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)

    gen = commands.add_parser("generate", help="bounded task into candidate records")
    gen.add_argument("--path-id", required=True)
    gen.add_argument("--task", type=Path, required=True)
    gen.add_argument("--endpoint", required=True)
    gen.add_argument("--out", type=Path, required=True)
    gen.add_argument("--api-key", default=None)
    gen.add_argument("--openrouter-snapshot", type=Path, default=None)
    gen.add_argument("--runtime-json", type=Path, default=None)
    gen.add_argument("--produced-at", default=None)
    gen.add_argument("--json", action="store_true")

    disc = commands.add_parser(
        "discover-openrouter",
        help="list models in a distillable snapshot (not an admit-list)",
    )
    disc.add_argument("--snapshot", type=Path, required=True)
    disc.add_argument("--json", action="store_true")

    spec = commands.add_parser("vllm-spec", help="print the pinned local vLLM launch spec")
    spec.add_argument("--path-id", required=True)
    spec.add_argument("--runtime-version", required=True)
    spec.add_argument("--device", required=True)
    spec.add_argument("--container-image", default=None)
    spec.add_argument("--container-digest", default=None)
    spec.add_argument("--json", action="store_true")
    return parser


def _print(payload: Any, as_json: bool) -> None:
    if as_json:
        sys.stdout.write(dumps_exact_json(payload) + "\n")
        return
    if isinstance(payload, dict):
        sys.stdout.write(json.dumps(payload, indent=2, allow_nan=False) + "\n")
        return
    sys.stdout.write(str(payload) + "\n")


def _input_object(path: Path) -> dict:
    payload = load_strict_json(path.read_bytes())
    if not isinstance(payload, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return payload


def _run_generate(args: argparse.Namespace) -> int:
    task = _input_object(args.task)
    runtime = None
    if args.runtime_json is not None:
        runtime = _input_object(args.runtime_json)
    attempted = 1
    rejected: list[str] = []
    accepted: list[dict[str, Any]] = []
    try:
        record = generate.generate_candidate(
            args.path_id,
            task,
            endpoint=args.endpoint,
            api_key=args.api_key,
            runtime=runtime,
            openrouter_snapshot=args.openrouter_snapshot,
            generated_at=args.produced_at,
        )
        accepted.append(record)
    except (
        generate.GenerateError,
        policy.SourcePolicyError,
        openrouter.OpenRouterError,
        openai_client.OpenAIClientError,
        vllm_mod.VLLMSpecError,
    ) as exc:
        rejected.append(str(exc))
    summary = generate.write_run(
        args.out,
        path_id=args.path_id,
        records=accepted,
        attempted=attempted,
        rejected=rejected,
        produced_at=args.produced_at or record_stamp(accepted),
    )
    _print(summary, args.json)
    return 0 if accepted else 2


def record_stamp(accepted: list[dict[str, Any]]) -> str:
    if accepted:
        meta = accepted[0].get("meta") or {}
        stamp = meta.get("generated_at")
        if isinstance(stamp, str) and stamp:
            return stamp
    return generate._utc_now()


def _run_discover(args: argparse.Namespace) -> int:
    snapshot = openrouter.load_snapshot(args.snapshot)
    admitted = {row["model_id"] for row in policy.reviewed_rows()
                if row["channel"] == "openrouter_api"}
    listing = []
    for item in snapshot["data"]:
        model_id = item.get("id") if isinstance(item, Mapping) else None
        listing.append(
            {
                "id": model_id,
                "in_reviewed_pilot": model_id in admitted,
                "distillable_catalog_member": True,
            }
        )
    payload = {
        "source_url": snapshot.get("source_url"),
        "retrieved_at": snapshot.get("retrieved_at"),
        "count": len(listing),
        "models": listing,
        "authority": "snapshot_membership_not_hardcoded_allow_list",
    }
    _print(payload, args.json)
    return 0


def _run_vllm_spec(args: argparse.Namespace) -> int:
    spec = vllm_mod.launch_spec(
        args.path_id,
        runtime_version=args.runtime_version,
        device=args.device,
        container_image=args.container_image,
        container_digest=args.container_digest,
    )
    _print(spec, args.json)
    return 0


def run(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        if args.command == "generate":
            return _run_generate(args)
        if args.command == "discover-openrouter":
            return _run_discover(args)
        if args.command == "vllm-spec":
            return _run_vllm_spec(args)
    except (
        generate.GenerateError,
        policy.SourcePolicyError,
        openrouter.OpenRouterError,
        openai_client.OpenAIClientError,
        vllm_mod.VLLMSpecError,
        OSError,
        ValueError,
    ) as exc:
        sys.stderr.write(f"{exc}\n")
        return 2
    parser.error(f"unknown command {args.command}")
    return 2


if __name__ == "__main__":
    raise SystemExit(run())


bind_import_twin(__name__)
