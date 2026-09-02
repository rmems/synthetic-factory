#!/usr/bin/env python3
"""Destination artifacts, run summary, and commit authentication for compose runs."""

from __future__ import annotations

import json
import sys
from typing import Any, Callable, Mapping

if __package__:
    from . import _assert_direct_sibling, _expose_package_sibling

    _assert_direct_sibling("compose_curated_run_artifacts")
    from . import compose_contract as _contract
    from . import compose_curated_run_context as _run_context
else:
    getattr(sys.modules.get("pipelines"), "_join_package_sibling", lambda name: None)(
        "compose_curated_run_artifacts"
    )
    import compose_contract as _contract
    import compose_curated_run_context as _run_context

COMPOSE_NAME = _contract.COMPOSE_NAME
COMPOSE_VERSION = _contract.COMPOSE_VERSION
LANE_ORDER = _contract.LANE_ORDER
MANIFEST_DIRNAME = _contract.MANIFEST_DIRNAME
MANIFEST_FILENAME = _contract.MANIFEST_FILENAME
RECORDS_DIRNAME = _contract.RECORDS_DIRNAME
REWARD_SIDECAR_FILENAME = _contract.REWARD_SIDECAR_FILENAME
SUMMARY_FILENAME = _contract.SUMMARY_FILENAME
ComposeError = _contract.ComposeError
sha256_hex = _contract.sha256_hex
ComposeRunState = _run_context.ComposeRunState
DestinationServices = _run_context.DestinationServices
ReportServices = _run_context.ReportServices
SourceFileContext = _run_context.SourceFileContext
SummaryCommitContext = _run_context.SummaryCommitContext
SummaryContext = _run_context.SummaryContext


def write_emitted_records(
    state: ComposeRunState,
    context: SourceFileContext,
    emitted: list[str],
    services: DestinationServices,
) -> None:
    output_path = f"{RECORDS_DIRNAME}/{context.relative}"
    digest = services.write_new_text(
        context.destination_target,
        output_path,
        "".join(line + "\n" for line in emitted),
    )
    state.outputs.append({"path": output_path, "records": len(emitted), "sha256": digest})
    state.counts["output_files"] += 1


def write_compose_provenance(
    state: ComposeRunState, destination_target: Any, services: DestinationServices
) -> tuple[str, str]:
    manifest_sha256 = services.write_new_text(
        destination_target,
        f"{MANIFEST_DIRNAME}/{MANIFEST_FILENAME}",
        "".join(line + "\n" for line in state.manifest_lines),
    )
    sidecar_sha256 = services.write_new_text(
        destination_target,
        f"{MANIFEST_DIRNAME}/{REWARD_SIDECAR_FILENAME}",
        "".join(line + "\n" for line in state.sidecar_lines),
    )
    return manifest_sha256, sidecar_sha256


def authenticate_composed_artifacts(
    pinned_destination: Any,
    expected_digests: Mapping[str, str],
    services: DestinationServices,
) -> None:
    pinned_destination.verify_binding()
    for relative, expected_digest in sorted(expected_digests.items()):
        _path, payload = services.read_exact_regular_file(
            pinned_destination.root,
            relative,
            f"compose artifact {relative}",
        )
        if sha256_hex(payload) != expected_digest:
            raise ComposeError(f"compose artifact {relative} changed before compose commit")
    pinned_destination.verify_binding()


def summary_counts(state: ComposeRunState) -> dict[str, int]:
    counts = state.counts
    return {
        "source_files": counts["source_files"],
        "source_records": counts["source_records"],
        "blank_lines": counts["blank_lines"],
        "retained": counts["retained"],
        "excluded": counts["excluded"],
        "output_files": counts["output_files"],
        "reward_sidecars": len(state.sidecar_lines),
    }


def compose_run_summary(
    state: ComposeRunState,
    context: SummaryContext,
    services: ReportServices,
) -> dict[str, Any]:
    return {
        "compose_name": COMPOSE_NAME,
        "compose_version": COMPOSE_VERSION,
        "source_run": str(context.resolved_source),
        "destination": str(context.destination_path),
        "lane_order": list(LANE_ORDER),
        "transforms": services.transform_contract(),
        "calibration": context.calibration_descriptor,
        "calibrated_records": context.calibrated_records,
        "counts": summary_counts(state),
        "lane_actions": {
            lane: dict(sorted(actions.items())) for lane, actions in state.lane_actions.items()
        },
        "exclusions": dict(sorted(state.exclusions.items())),
        "outputs": state.outputs,
        "manifest": {
            "path": f"{MANIFEST_DIRNAME}/{MANIFEST_FILENAME}",
            "entries": len(state.manifest_lines),
            "sha256": context.manifest_sha256,
        },
        "reward_sidecars": {
            "path": f"{MANIFEST_DIRNAME}/{REWARD_SIDECAR_FILENAME}",
            "entries": len(state.sidecar_lines),
            "sha256": context.sidecar_sha256,
        },
        "audit": services.audit_records(context.records_dir, state.counts["retained"]),
    }


def commit_compose_summary(
    state: ComposeRunState,
    context: SummaryCommitContext,
    services: DestinationServices,
    authenticate: Callable[..., None] = authenticate_composed_artifacts,
) -> None:
    pinned_destination = context.pinned_destination
    summary = context.summary
    summary_sha256 = services.write_new_text(
        pinned_destination,
        SUMMARY_FILENAME,
        json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
    )
    expected_digests = {item["path"]: item["sha256"] for item in state.outputs}
    expected_digests.update(
        {
            summary["manifest"]["path"]: (
                summary["manifest"]["sha256"]
                if context.manifest_sha256 is None
                else context.manifest_sha256
            ),
            summary["reward_sidecars"]["path"]: (
                summary["reward_sidecars"]["sha256"]
                if context.sidecar_sha256 is None
                else context.sidecar_sha256
            ),
            SUMMARY_FILENAME: summary_sha256,
        }
    )
    authenticate(pinned_destination, expected_digests, services)


if __package__:
    _expose_package_sibling(__name__)
